"""Robust peer-group anomaly triage on the public SIOPE municipality-year release.

The signal is how far a municipality's reported investment per basic-education
student sits from comparable municipalities (same macro-region and population
band) in earlier years. It is a prompt for a human to read the declaration,
never a finding of error or misconduct.
"""

from __future__ import annotations

from collections import defaultdict
import hashlib
import json
from math import exp, log
from statistics import median
from typing import Any, Iterable

FEATURE_SCHEMA_VERSION = "siope-peer/2"
MODEL_TYPE = "robust-peer-zscore"
TARGET = "investment_per_basic_education_student"
THRESHOLD = 3.5
MIN_PEER_ROWS = 30
STATUTORY_MDE_MINIMUM = 25.0

REGIONS = {
    "North": {"AC", "AM", "AP", "PA", "RO", "RR", "TO"},
    "Northeast": {"AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"},
    "Southeast": {"ES", "MG", "RJ", "SP"},
    "South": {"PR", "RS", "SC"},
    "Center-West": {"DF", "GO", "MS", "MT"},
}
REGION_OF = {state: region for region, states in REGIONS.items() for state in states}
POPULATION_BANDS = ((10_000, "<10k"), (50_000, "10k-50k"), (200_000, "50k-200k"), (float("inf"), ">=200k"))
RELEASE_FIELDS = {"municipality_code", "year", "state_code", "population", TARGET, "mde_minimum_share_pct"}
RELATIVE_TARGET = "relative_investment"


def add_relative_target(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Divide the target by the national median of the same year.

    Nominal investment per student rises every year, so an absolute threshold
    would flag growth, not deviation. The median uses only same-year rows,
    so no information crosses the time split.
    """
    rows = [dict(row) for row in rows]
    by_year: dict[int, list[float]] = defaultdict(list)
    for row in rows:
        value = row.get(TARGET)
        if value is not None and value > 0:
            by_year[int(row["year"])].append(value)
    medians = {year: median(values) for year, values in by_year.items()}
    for row in rows:
        value = row.get(TARGET)
        row[RELATIVE_TARGET] = value / medians[int(row["year"])] if value is not None and value > 0 else None
    return rows


def population_band(population: int | None) -> str:
    if not population:
        return "unknown"
    return next(label for limit, label in POPULATION_BANDS if population < limit)


def build_release_features(rows: Iterable[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Map release rows to model rows; rows without a positive target are excluded and counted."""
    features: list[dict[str, Any]] = []
    excluded: dict[str, int] = defaultdict(int)
    for row in add_relative_target(rows):
        missing = RELEASE_FIELDS - row.keys()
        if missing:
            raise ValueError(f"release row lacks contract fields: {sorted(missing)}")
        value = row[TARGET]
        if value is None:
            excluded["target_missing"] += 1
            continue
        if value <= 0:
            excluded["target_not_positive"] += 1
            continue
        region = REGION_OF.get(row["state_code"])
        if region is None:
            raise ValueError(f"unknown state code: {row['state_code']}")
        features.append({
            "municipality_code": row["municipality_code"],
            "year": int(row["year"]),
            "state_code": row["state_code"],
            "peer_group": f"{region}|{population_band(row['population'])}",
            "log_target": log(row[RELATIVE_TARGET]),
            TARGET: value,
            "mde_minimum_share_pct": row["mde_minimum_share_pct"],
        })
    features.sort(key=lambda item: (item["year"], item["municipality_code"]))
    return features, dict(sorted(excluded.items()))


def _robust_stats(values: list[float]) -> dict[str, float]:
    center = median(values)
    mad = median(abs(value - center) for value in values)
    return {"median": round(center, 10), "mad": round(max(mad, 1e-6), 10), "count": len(values)}


def train(features: list[dict[str, Any]], train_through_year: int, grouping: str = "peer") -> dict[str, Any]:
    """Fit median/MAD of log target per peer group on years <= train_through_year only."""
    training = [row for row in features if row["year"] <= train_through_year]
    if not training:
        raise ValueError("time-aware training split is empty")
    grouped: dict[str, list[float]] = defaultdict(list)
    for row in training:
        grouped[row["peer_group"] if grouping == "peer" else "all"].append(row["log_target"])
    fallback = _robust_stats([row["log_target"] for row in training])
    groups = {key: _robust_stats(values) for key, values in sorted(grouped.items()) if len(values) >= MIN_PEER_ROWS}
    model = {
        "model_type": MODEL_TYPE,
        "grouping": grouping,
        "feature_schema": FEATURE_SCHEMA_VERSION,
        "target": TARGET,
        "threshold": THRESHOLD,
        "train_through_year": train_through_year,
        "training_rows": len(training),
        "groups": groups,
        "fallback": fallback,
    }
    model["model_id"] = hashlib.sha256(json.dumps(model, sort_keys=True).encode()).hexdigest()[:16]
    return model


def robust_z(row: dict[str, Any], model: dict[str, Any]) -> tuple[float, str]:
    key = row["peer_group"] if model["grouping"] == "peer" else "all"
    stats = model["groups"].get(key)
    source = key
    if stats is None:
        stats, source = model["fallback"], "fallback:all"
    return round(0.6745 * (row["log_target"] - stats["median"]) / stats["mad"], 6), source


def score(features: list[dict[str, Any]], model: dict[str, Any]) -> list[dict[str, Any]]:
    if model.get("model_type") != MODEL_TYPE:
        raise ValueError("unsupported model type")
    queue = []
    for row in features:
        z, peer_source = robust_z(row, model)
        if abs(z) < model["threshold"]:
            continue
        queue.append({
            "municipality_code": row["municipality_code"],
            "year": row["year"],
            "review_signal": "investment_per_student_peer_deviation",
            "direction": "above_peers" if z > 0 else "below_peers",
            "robust_z": z,
            "evidence": {
                TARGET: row[TARGET],
                "peer_group": peer_source,
                "peer_median_relative_to_national": round(exp(model["groups"].get(peer_source, model["fallback"])["median"]), 4),
                "mde_minimum_share_pct": row["mde_minimum_share_pct"],
            },
            "human_review_required": True,
            "decision_prohibited": True,
        })
    return sorted(queue, key=lambda item: (-abs(item["robust_z"]), item["municipality_code"]))


def evaluate(features: list[dict[str, Any]], model: dict[str, Any], evaluation_year: int) -> dict[str, Any]:
    """Describe the held-out year. There are no ground-truth anomaly labels, so no accuracy is claimed."""
    held_out = [row for row in features if row["year"] == evaluation_year]
    if not held_out:
        raise ValueError("time-aware evaluation split is empty")
    if evaluation_year <= model["train_through_year"]:
        raise ValueError("evaluation year must follow the training window")
    queue = score(held_out, model)
    flagged = {row["municipality_code"] for row in queue}
    slices: dict[str, dict[str, int]] = defaultdict(lambda: {"rows": 0, "signals": 0})
    for row in held_out:
        slices[row["peer_group"]]["rows"] += 1
        slices[row["peer_group"]]["signals"] += row["municipality_code"] in flagged
    previous_year = [row for row in features if row["year"] == evaluation_year - 1]
    previous_flags = {row["municipality_code"] for row in score(previous_year, model)} if previous_year else set()
    below_mde = [row for row in held_out if row["mde_minimum_share_pct"] is not None and row["mde_minimum_share_pct"] < STATUTORY_MDE_MINIMUM]
    return {
        "evaluation_year": evaluation_year,
        "evaluated_rows": len(held_out),
        "review_signals": len(queue),
        "signal_rate": round(len(queue) / len(held_out), 4),
        "above_peers": sum(row["direction"] == "above_peers" for row in queue),
        "below_peers": sum(row["direction"] == "below_peers" for row in queue),
        "persistence_from_previous_year": round(len(flagged & previous_flags) / len(flagged), 4) if flagged else 0.0,
        "statutory_context": {
            "rows_below_mde_minimum": len(below_mde),
            "signals_below_mde_minimum": sum(row["municipality_code"] in flagged for row in below_mde),
            "note": "descriptive co-occurrence only; the model does not use or predict this threshold",
        },
        "peer_slices": {key: slices[key] for key in sorted(slices)},
    }
