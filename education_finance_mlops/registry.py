from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def register_model(path: Path, model: dict[str, Any], dataset: dict[str, Any], evaluation: dict[str, Any], code_revision: str) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"model": model, "dataset": dataset, "evaluation": evaluation, "code_revision": code_revision}
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def load_registered_model(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
