# Project memory

## Current state

- v0.2.0 reads the pinned Kaggle release `lucasrangelss/brazil-education-data-lake` version 1 (manifest SHA-256 `44f25960…3506`, 27,830 rows, SIOPE 2019-2023) through `kagglehub` and verifies every file.
- Model `siope-peer/2`: log of investment per basic-education student / same-year national median; robust z per macro-region x population band; threshold 3.5. Global baseline stored beside it.
- 2026-09-25 run at commit `6be582d`: 2022 batch scored (96 signals); 2023 batch blocked by MAD spread ratio 1.384 ([run record](docs/evidence/education-release-v1-run-2026-09-25.md)). Two runs byte-identical.
- 14 unit tests pass locally.

## Decisions

- Review triage only; the CLI refuses other intended uses ([ADR 0001](docs/adr/0001-review-queue-not-decision-engine.md)).
- Year-relative feature and MAD spread gate ([ADR 0002](docs/adr/0002-year-relative-feature-and-spread-gate.md)).
- No PNCP features.

## Next verifiable task

Find the cause of the 2023 dispersion change before refitting on 2023; then consider enrollment-mix peers once the data release includes Censo aggregates.
