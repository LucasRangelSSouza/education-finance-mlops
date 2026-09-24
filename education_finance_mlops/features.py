from __future__ import annotations

from typing import Any


FEATURE_SCHEMA_VERSION = "1.0"


def build_features(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build deterministic, contemporaneous municipality-year features only."""
    features: list[dict[str, Any]] = []
    for row in sorted(rows, key=lambda item: (item["year"], item["municipality_code"])):
        enrollment = float(row["enrollment"])
        if enrollment == 0:
            raise ValueError("enrollment must be greater than zero for feature construction")
        expenditure = float(row["expenditure_per_student"])
        revenue = float(row["revenue_per_student"])
        features.append({
            "municipality_code": row["municipality_code"],
            "year": row["year"],
            "region": row["region"],
            "expenditure_per_student": expenditure,
            "revenue_per_student": revenue,
            "balance_ratio": round((revenue - expenditure) / max(revenue, 1.0), 8),
            "log_enrollment": round(__import__("math").log1p(enrollment), 8),
        })
    return features
