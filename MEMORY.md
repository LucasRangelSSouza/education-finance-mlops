# Project memory

## Current state

- v0.2.0 keeps version 1 as its default pin and supports an explicit version-3 compatibility run for `lucasrangelss/brazil-education-data-lake` (manifest SHA-256 `311ffeba…a86d`). Version 3 adds a reviewed 2023 municipal enrollment aggregate and preserves 27,830 rows.
- Model `siope-peer/2`: log of investment per basic-education student / same-year national median; robust z per macro-region x population band; threshold 3.5. Global baseline stored beside it.
- 2026-09-25 run at commit `6be582d`: 2022 batch scored (96 signals); 2023 batch blocked by MAD spread ratio 1.384 ([run record](docs/evidence/education-release-v1-run-2026-09-25.md)). Two runs byte-identical.
- The 2026-09-27 version-3 compatibility run verified the package hashes, reproduced the 2022 evaluation, and blocked 2023 for the same spread ratio 1.3843. `dags/education_monitoring_demo.py` is an unscheduled, paused demonstration DAG.

## Decisions

- Review triage only; the CLI refuses other intended uses ([ADR 0001](docs/adr/0001-review-queue-not-decision-engine.md)).
- Year-relative feature and MAD spread gate ([ADR 0002](docs/adr/0002-year-relative-feature-and-spread-gate.md)).
- No PNCP features.

## Next verifiable task

Find the cause of the 2023 dispersion change before refitting on 2023; then consider enrollment-mix peers once the data release includes Censo aggregates.
