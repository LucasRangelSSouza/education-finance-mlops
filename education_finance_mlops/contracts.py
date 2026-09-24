from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = {"municipality_code", "year", "region", "enrollment", "expenditure_per_student", "revenue_per_student"}


@dataclass(frozen=True)
class DatasetPin:
    source: str
    version: str
    manifest_sha256: str
    schema_version: str

    def validate(self) -> None:
        if not self.source or not self.version or not self.schema_version:
            raise ValueError("dataset pin requires source, version, and schema_version")
        if len(self.manifest_sha256) != 64:
            raise ValueError("dataset pin requires a manifest SHA-256")


def load_rows(path: Path) -> list[dict[str, Any]]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise ValueError("dataset must be a JSON list")
    validate_rows(rows)
    return rows


def validate_rows(rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError("dataset is empty")
    for index, row in enumerate(rows):
        missing = REQUIRED_FIELDS - row.keys()
        if missing:
            raise ValueError(f"row {index} missing fields: {', '.join(sorted(missing))}")
        if not isinstance(row["municipality_code"], str) or len(row["municipality_code"]) != 7:
            raise ValueError(f"row {index} has an invalid municipality_code")
        if not isinstance(row["year"], int):
            raise ValueError(f"row {index} has an invalid year")
        for field in ("enrollment", "expenditure_per_student", "revenue_per_student"):
            if not isinstance(row[field], (int, float)) or row[field] < 0:
                raise ValueError(f"row {index} has an invalid {field}")


def manifest_hash(rows: list[dict[str, Any]]) -> str:
    body = json.dumps(rows, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()
