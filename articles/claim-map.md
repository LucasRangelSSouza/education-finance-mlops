# Claim-to-evidence map

| Claim | Evidence | Status |
| --- | --- | --- |
| The pipeline reads a pinned, hash-verified public release. | `education_finance_mlops/release.py`; `tests/test_release_pipeline.py` (unapproved and altered release tests); run record. | Supported |
| Nominal investment per student rose about 30% from 2022 to 2023. | Run record: nominal median log shift 0.2598 (e^0.26 = 1.30). | Supported |
| Peer model flagged 93 of 5,566 rows in 2021 and 89 in 2022. | `docs/evidence/education-release-v1-run-2026-09-25.md`. | Supported |
| The 2022 batch passed drift and produced 96 signals. | Run record, 2022 section. | Supported |
| Without the spread gate, 2023 passed PSI and produced 921 signals. | Run with feature schema `siope-peer/2` before the spread check was added; recorded in the run record and ADR 0002. | Supported (pre-change run, not preserved as an artifact) |
| 2023 is blocked at spread ratio 1.384. | Run record; `a-2023/drift_report.json` hash. | Supported |
| Two runs produced byte-identical files. | Run record hashes; `test_two_runs_are_identical`. | Supported |
| The spread widening was caused by a funding-rule change. | No evidence in the release. | Not claimed |
| The model identifies real-world errors or fraud. | No labels or validation. | Not claimed |
