"""Train, evaluate, register, drift-check, and score from one verified release."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any

from . import peer_model
from .release import VerifiedRelease
from .release_drift import assess_release_drift

SUPPORTED_USE = "review_triage"
PROHIBITED_USES = frozenset({"funding_allocation", "eligibility", "sanction", "audit_finding", "ranking"})


def check_intended_use(intended_use: str) -> None:
    if intended_use in PROHIBITED_USES:
        raise ValueError(f"intended use '{intended_use}' is prohibited; outputs are review signals only")
    if intended_use != SUPPORTED_USE:
        raise ValueError(f"unsupported intended use '{intended_use}'; only '{SUPPORTED_USE}' is supported")


def code_commit() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def load_release_rows(release: VerifiedRelease) -> list[dict[str, Any]]:
    import pyarrow.parquet as pq

    return pq.read_table(release.semantic_layer).to_pylist()


def _write(path: Path, payload: Any) -> str:
    body = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    path.write_text(body, encoding="utf-8", newline="\n")
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def run_release_pipeline(
    release: VerifiedRelease,
    output_dir: Path,
    train_through_year: int,
    evaluation_year: int,
    score_year: int,
    intended_use: str = SUPPORTED_USE,
) -> dict[str, Any]:
    check_intended_use(intended_use)
    if not train_through_year < evaluation_year < score_year:
        raise ValueError("years must satisfy train_through_year < evaluation_year < score_year")
    rows = load_release_rows(release)
    features, excluded = peer_model.build_release_features(rows)
    development = [row for row in features if row["year"] <= evaluation_year]

    candidates = {grouping: peer_model.train(development, train_through_year, grouping) for grouping in ("global", "peer")}
    evaluation = {grouping: peer_model.evaluate(development, model, evaluation_year) for grouping, model in candidates.items()}
    selected = candidates["peer"]
    lineage = {
        "dataset": release.lineage(),
        "code_commit": code_commit(),
        "feature_schema": peer_model.FEATURE_SCHEMA_VERSION,
        "model_id": selected["model_id"],
        "intended_use": intended_use,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    registry = {"model": selected, "baseline": candidates["global"], "evaluation": evaluation, "lineage": lineage, "excluded_rows": excluded}
    registry_sha = _write(output_dir / "registry.json", registry)

    reference = [row for row in rows if row["year"] == evaluation_year]
    batch = [row for row in rows if row["year"] == score_year]
    relative = peer_model.add_relative_target(reference + batch)
    drift = assess_release_drift(
        [row for row in relative if row["year"] == evaluation_year],
        [row for row in relative if row["year"] == score_year],
        peer_model.RELATIVE_TARGET,
    )
    drift["nominal_target"] = assess_release_drift(reference, batch, peer_model.TARGET).get("measures")
    result: dict[str, Any] = {"registry_sha256": registry_sha, "drift": drift, "evaluation": evaluation, "excluded_rows": excluded}
    if drift["status"] == "blocked":
        result["status"] = "blocked"
        result["drift_report_sha256"] = _write(output_dir / "drift_report.json", {"drift": drift, "lineage": lineage, "score_year": score_year})
        return result

    queue = peer_model.score([row for row in features if row["year"] == score_year], selected)
    result["status"] = "scored"
    result["review_signals"] = len(queue)
    result["queue_sha256"] = _write(output_dir / "review_queue.json", {"score_year": score_year, "review_queue": queue, "drift": drift, "lineage": lineage})
    return result
