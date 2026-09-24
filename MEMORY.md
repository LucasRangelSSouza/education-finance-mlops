# Project memory

## Current state

The fixture-first local MLOps path is implemented: validate input, build deterministic features, train a time-aware regional baseline, evaluate a later year, write local registry lineage, check drift, and emit a review queue. The latest verified local commands are the README quick-start commands; they pass with the synthetic fixture.

## Decisions

- The use case is municipality-year indicator anomaly triage only.
- Scores require human review and never make a decision or finding.
- The first model uses no PNCP features because procurement values and education expenditure are not interchangeable.
- The repository contains no Kaggle credential or release downloader. A future reviewed Kaggle dataset replaces the fixture through a pinned manifest contract.

## Next task

Add a reviewed public education release only after it exists in the companion data-map project. Then implement the resolver and validate the actual source contract before claiming Kaggle-backed execution.
