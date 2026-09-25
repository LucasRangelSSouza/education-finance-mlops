# Model card: robust peer-group triage (`siope-peer/2`)

## Intended use

Flag municipality-year SIOPE declarations whose investment per basic-education student sits far from comparable municipalities, so that an analyst can read the declaration in context. The only accepted `--intended-use` value is `review_triage`.

## Prohibited use

Eligibility, resource allocation, ranking of schools or municipalities, assessment of people, fraud or compliance findings, sanctions, and causal claims. The CLI refuses `funding_allocation`, `eligibility`, `sanction`, `audit_finding`, and `ranking`, and any other value than `review_triage`. Every queue entry carries `human_review_required` and `decision_prohibited`.

## Data

Pinned release `lucasrangelss/brazil-education-data-lake` version 1 (FNDE SIOPE annual municipal declarations 2019-2023 joined to IBGE codes). The resolver verifies the manifest hash and every file hash before reading. Rows with zero or missing investment per student are excluded and counted.

## Method

1. Divide investment per basic-education student by the national median of the same year, then take the log.
2. Peer group: macro-region x population band (<10k, 10k-50k, 50k-200k, >=200k). Groups with fewer than 30 training rows fall back to the national distribution.
3. Fit the median and median absolute deviation (MAD) of the feature per group on training years only.
4. Robust z = 0.6745 x (value - median) / MAD. A row with |z| >= 3.5 becomes a review signal.
5. A global baseline (one group) is trained and evaluated beside the peer model and stored in the registry.

## Evaluation

Time-aware: train through year T, describe year T+1, score year T+2. Without anomaly labels, the report gives signal rate by slice, direction, persistence from the previous year, and co-occurrence with the 25% education-spending minimum. Results for release v1 are in the [2026-09-25 run record](evidence/education-release-v1-run-2026-09-25.md): 1.67% of 2021 rows and 1.60% of 2022 rows were flagged.

## Monitoring

Before a batch is scored, the candidate year is compared with the evaluation year on the relative feature: schema, missingness rise (limit 0.10), PSI (limit 0.25), median log shift (limit 0.30), and MAD spread ratio (limit 1.25 either way). A breach writes a drift report and blocks the queue. The 2023 batch was blocked on spread ratio 1.384.

## Limitations

Declared values are not audited; some are implausible, which is part of what the model surfaces. The peer definition ignores rural/urban structure, enrollment mix, and funding-rule changes. Thresholds were set by convention (3.5 for robust z, 1.25 for spread), not tuned on outcomes. No uncertainty interval is reported.
