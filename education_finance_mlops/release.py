"""Resolve the pinned education Kaggle release and verify it before any row is read.

The Kaggle package flattens layer paths (`semantic/records.parquet` becomes
`semantic_records.parquet`), so verification maps manifest paths to package names.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from typing import Callable


@dataclass(frozen=True)
class PinnedRelease:
    slug: str
    version: int
    manifest_sha256: str
    schema_version: str

    @property
    def handle(self) -> str:
        return f"{self.slug}/versions/{self.version}"


EDUCATION_RELEASE_V1 = PinnedRelease(
    slug="lucasrangelss/brazil-education-data-lake",
    version=1,
    manifest_sha256="44f259602a688432dddbae6b0306a6957514a634d57d94a0abd3cff30f4b3506",
    schema_version="1.1",
)


class ReleaseVerificationError(ValueError):
    """The local package differs from the approved release."""


@dataclass(frozen=True)
class VerifiedRelease:
    pin: PinnedRelease
    directory: Path
    manifest: dict

    @property
    def semantic_layer(self) -> Path:
        return self.directory / "semantic_records.parquet"

    def lineage(self) -> dict[str, object]:
        return {**asdict(self.pin), "source_build_commit": self.manifest["git_commit"], "row_counts": self.manifest["row_counts"]}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_release(directory: Path, pin: PinnedRelease = EDUCATION_RELEASE_V1) -> VerifiedRelease:
    manifest_path = directory / "release_manifest.json"
    if not manifest_path.is_file():
        raise ReleaseVerificationError("release_manifest.json is missing")
    actual = sha256_file(manifest_path)
    if actual != pin.manifest_sha256:
        raise ReleaseVerificationError(f"manifest hash {actual} is not the approved {pin.handle}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("privacy_gate") != "passed":
        raise ReleaseVerificationError("release privacy gate did not pass")
    if manifest.get("schema_version") != pin.schema_version:
        raise ReleaseVerificationError(f"unsupported schema version {manifest.get('schema_version')}")
    for entry in manifest["files"]:
        file_path = directory / entry["path"].replace("/", "_")
        if not file_path.is_file():
            raise ReleaseVerificationError(f"release file missing: {file_path.name}")
        if sha256_file(file_path) != entry["sha256"]:
            raise ReleaseVerificationError(f"release file hash mismatch: {file_path.name}")
    return VerifiedRelease(pin=pin, directory=directory, manifest=manifest)


def _kagglehub_download(handle: str) -> Path:
    import kagglehub

    return Path(kagglehub.dataset_download(handle))


def resolve_release(
    release_dir: Path | None = None,
    pin: PinnedRelease = EDUCATION_RELEASE_V1,
    downloader: Callable[[str], Path] = _kagglehub_download,
) -> VerifiedRelease:
    """Use a verified local copy when supplied, otherwise download the pinned public version."""
    directory = release_dir if release_dir is not None else downloader(pin.handle)
    return verify_release(Path(directory), pin)
