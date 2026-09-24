from __future__ import annotations

from collections import defaultdict
from statistics import fmean, pstdev
from typing import Any


MODEL_TYPE = "regional-zscore-baseline"


def train_baseline(features: list[dict[str, Any]], train_through_year: int) -> dict[str, Any]:
    training = [row for row in features if row["year"] <= train_through_year]
    if not training:
        raise ValueError("time-aware training split is empty")
    grouped: dict[str, list[float]] = defaultdict(list)
    for row in training:
        grouped[row["region"]].append(float(row["expenditure_per_student"]))
    peers = {
        region: {"mean": round(fmean(values), 8), "stddev": round(max(pstdev(values), 1.0), 8), "count": len(values)}
        for region, values in sorted(grouped.items())
    }
    return {"model_type": MODEL_TYPE, "train_through_year": train_through_year, "peer_statistics": peers}


def score(features: list[dict[str, Any]], model: dict[str, Any], threshold: float = 2.0) -> list[dict[str, Any]]:
    if model.get("model_type") != MODEL_TYPE:
        raise ValueError("unsupported model type")
    review_queue: list[dict[str, Any]] = []
    for row in features:
        peer = model["peer_statistics"].get(row["region"])
        if peer is None:
            continue
        z_score = round((float(row["expenditure_per_student"]) - peer["mean"]) / peer["stddev"], 6)
        if abs(z_score) >= threshold:
            review_queue.append({
                "municipality_code": row["municipality_code"],
                "year": row["year"],
                "review_signal": "expenditure_per_student_peer_deviation",
                "anomaly_score": abs(z_score),
                "evidence": {
                    "observed_expenditure_per_student": row["expenditure_per_student"],
                    "peer_mean": peer["mean"],
                    "peer_stddev": peer["stddev"],
                    "region": row["region"],
                },
                "human_review_required": True,
                "decision_prohibited": True,
            })
    return sorted(review_queue, key=lambda item: (-item["anomaly_score"], item["municipality_code"]))


def evaluate(features: list[dict[str, Any]], model: dict[str, Any], evaluation_year: int) -> dict[str, Any]:
    held_out = [row for row in features if row["year"] == evaluation_year]
    if not held_out:
        raise ValueError("time-aware evaluation split is empty")
    queue = score(held_out, model)
    by_region: dict[str, int] = defaultdict(int)
    for row in held_out:
        by_region[row["region"]] += 1
    return {"evaluation_year": evaluation_year, "evaluated_rows": len(held_out), "review_signals": len(queue), "peer_slices": dict(sorted(by_region.items()))}
