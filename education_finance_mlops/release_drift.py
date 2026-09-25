"""Schema, missingness, and distribution checks that can block a batch before scoring."""

from __future__ import annotations

from bisect import bisect_right
from math import log
from statistics import median
from typing import Any

PSI_LIMIT = 0.25
MISSINGNESS_DELTA_LIMIT = 0.10
MEDIAN_LOG_SHIFT_LIMIT = 0.30
# PSI on deciles reacts weakly when the spread widens around a stable median.
# The spread uses MAD so the outliers the model should flag do not trigger it.
SPREAD_RATIO_LIMIT = 1.25


def _mad(values: list[float]) -> float:
    center = median(values)
    return median(abs(value - center) for value in values)


def _missing_rate(rows: list[dict[str, Any]], field: str) -> float:
    return sum(row.get(field) is None for row in rows) / len(rows)


def population_stability_index(reference: list[float], candidate: list[float], bins: int = 10) -> float:
    ordered = sorted(reference)
    edges = [ordered[int(len(ordered) * i / bins)] for i in range(1, bins)]

    def shares(values: list[float]) -> list[float]:
        counts = [0] * bins
        for value in values:
            counts[bisect_right(edges, value)] += 1
        return [max(count / len(values), 1e-4) for count in counts]

    return round(sum((c - r) * log(c / r) for r, c in zip(shares(reference), shares(candidate))), 6)


def assess_release_drift(reference: list[dict[str, Any]], candidate: list[dict[str, Any]], target: str) -> dict[str, Any]:
    """Compare a candidate year with the reference year on raw release rows."""
    if not reference or not candidate:
        return {"status": "blocked", "reasons": ["reference or candidate batch is empty"]}
    reasons: list[str] = []
    missing_fields = sorted(set(reference[0]) - set(candidate[0]))
    if missing_fields:
        reasons.append(f"missing schema fields: {', '.join(missing_fields)}")
        return {"status": "blocked", "reasons": reasons}
    missing_delta = round(_missing_rate(candidate, target) - _missing_rate(reference, target), 4)
    if missing_delta > MISSINGNESS_DELTA_LIMIT:
        reasons.append(f"{target} missingness rose by {missing_delta:.3f}")
    ref_values = [log(row[target]) for row in reference if row.get(target) and row[target] > 0]
    cand_values = [log(row[target]) for row in candidate if row.get(target) and row[target] > 0]
    psi = population_stability_index(ref_values, cand_values)
    if psi > PSI_LIMIT:
        reasons.append(f"{target} PSI {psi:.3f} exceeds {PSI_LIMIT:.2f}")
    shift = round(median(cand_values) - median(ref_values), 4)
    if abs(shift) > MEDIAN_LOG_SHIFT_LIMIT:
        reasons.append(f"{target} median log shift {shift:.3f} exceeds {MEDIAN_LOG_SHIFT_LIMIT:.2f}")
    spread_ratio = round(_mad(cand_values) / max(_mad(ref_values), 1e-9), 4)
    if spread_ratio > SPREAD_RATIO_LIMIT or spread_ratio < 1 / SPREAD_RATIO_LIMIT:
        reasons.append(f"{target} log spread ratio {spread_ratio:.3f} is outside [{1 / SPREAD_RATIO_LIMIT:.2f}, {SPREAD_RATIO_LIMIT:.2f}]")
    return {
        "status": "blocked" if reasons else "passed",
        "reasons": reasons,
        "measures": {"psi": psi, "median_log_shift": shift, "spread_ratio": spread_ratio, "missingness_delta": missing_delta,
                     "reference_rows": len(reference), "candidate_rows": len(candidate)},
        "limits": {"psi": PSI_LIMIT, "spread_ratio": SPREAD_RATIO_LIMIT, "median_log_shift": MEDIAN_LOG_SHIFT_LIMIT, "missingness_delta": MISSINGNESS_DELTA_LIMIT},
    }
