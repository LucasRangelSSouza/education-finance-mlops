from __future__ import annotations

import argparse
import json
from pathlib import Path

from .contracts import DatasetPin, load_rows, manifest_hash
from .features import build_features
from .model import evaluate, score, train_baseline
from .monitoring import assess_drift
from .registry import load_registered_model, register_model


def main() -> None:
    parser = argparse.ArgumentParser(description="Transparent municipality-year anomaly-triage MLOps reference.")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("train", "score"):
        command = commands.add_parser(name)
        command.add_argument("--data", type=Path, required=True)
        command.add_argument("--registry", type=Path, required=True)
    train = commands.choices["train"]
    train.add_argument("--train-through-year", type=int, required=True)
    train.add_argument("--evaluation-year", type=int, required=True)
    train.add_argument("--code-revision", default="local")
    score_command = commands.choices["score"]
    score_command.add_argument("--reference-data", type=Path, required=True)
    score_command.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = load_rows(args.data)
    if args.command == "train":
        features = build_features(rows)
        model = train_baseline(features, args.train_through_year)
        evaluation = evaluate(features, model, args.evaluation_year)
        pin = DatasetPin("fixture", "v1", manifest_hash(rows), "1.0")
        pin.validate()
        result = register_model(args.registry, model, pin.__dict__, evaluation, args.code_revision)
        print(json.dumps({"status": "registered", "evaluation": result["evaluation"], "registry": str(args.registry)}, indent=2))
    else:
        reference = load_rows(args.reference_data)
        drift = assess_drift(reference, rows)
        if drift["status"] == "blocked":
            raise SystemExit(json.dumps(drift, indent=2))
        registered = load_registered_model(args.registry)
        queue = score(build_features(rows), registered["model"])
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps({"review_queue": queue, "drift": drift, "model_lineage": registered}, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"status": "scored", "review_signals": len(queue), "output": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()
