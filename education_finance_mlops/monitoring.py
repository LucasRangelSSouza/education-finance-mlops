from __future__ import annotations

from statistics import fmean
from typing import Any

from .contracts import REQUIRED_FIELDS, validate_rows


def assess_drift(reference: list[dict[str, Any]], candidate: list[dict[str, Any]], mean_shift_limit: float = 0.35) -> dict[str, Any]:
    validate_rows(reference)
    validate_rows(candidate)
    candidate_fields = set(candidate[0])
    missing = sorted(REQUIRED_FIELDS - candidate_fields)
    if missing:
        return {"status": "blocked", "reasons": [f"missing schema fields: {', '.join(missing)}"]}
    reasons: list[str] = []
    for field in ("enrollment", "expenditure_per_student", "revenue_per_student"):
        reference_mean = fmean(float(row[field]) for row in reference)
        candidate_mean = fmean(float(row[field]) for row in candidate)
        relative_shift = abs(candidate_mean - reference_mean) / max(abs(reference_mean), 1.0)
        if relative_shift > mean_shift_limit:
            reasons.append(f"{field} mean shift {relative_shift:.3f} exceeds {mean_shift_limit:.3f}")
    return {"status": "blocked" if reasons else "passed", "reasons": reasons}
