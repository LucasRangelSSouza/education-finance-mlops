# Data contract

The training input is a municipality-year table. Every row requires `municipality_code`, `year`, `region`, `enrollment`, `expenditure_per_student`, and `revenue_per_student`. Municipality codes must be seven-character strings; years must be integers; numeric values must be non-negative.

The runtime creates a `DatasetPin` with a source identifier, source version, manifest SHA-256, and schema version. The fixture supplies this information locally. A future Kaggle-backed resolver must reject a missing version, changed manifest, changed schema, or missing approval record before training or scoring.

The feature pipeline uses values from the scored municipality-year only. It does not derive target information from later years. `balance_ratio` expresses the difference between revenue and expenditure as a share of revenue. `log_enrollment` is a monotonic transform of enrollment. The baseline uses `expenditure_per_student` for its first review signal because it is directly inspectable by a reviewer.

The project excludes person-level records, school rankings, individual outcomes, and free-text fields from this contract.
