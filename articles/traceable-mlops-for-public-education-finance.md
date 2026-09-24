# Building a traceable MLOps pipeline for public education-finance indicators

Municipality-year indicators are easy to turn into a score and hard to interpret responsibly. The useful engineering problem is smaller: make a review signal reproducible, show the data and model lineage behind it, and stop scoring when the input changes beyond an agreed boundary.

This reference implementation starts with a synthetic fixture. The fixture contains four municipality-year rows across two years in one region. Training uses 2023 and evaluation uses 2024, so the baseline never learns from the period it evaluates. It calculates the regional mean and population standard deviation of expenditure per student, then flags a later record when its absolute z-score reaches the review threshold.

The fixture evaluation covers two 2024 rows and emits one review signal. That result says nothing about a municipality, a school, or a public policy. It demonstrates that a time-aware workflow can produce a narrow, inspectable queue. Each entry exposes the observed expenditure value, the peer mean, the peer standard deviation, and the regional slice. A reviewer still needs the underlying reporting context.

Lineage matters before model selection. The local registry keeps the feature baseline, evaluation output, dataset pin, and code revision together. The dataset pin carries a source, version, schema version, and manifest digest. The future public-data path will replace the fixture with a reviewed, pinned education release. It will not accept a changed manifest silently.

Monitoring is part of the same boundary. The scoring command validates the input schema and checks configured mean shifts for enrollment, expenditure per student, and revenue per student. A breached limit blocks the batch rather than returning a reassuring-looking score from data that no longer resembles the training input.

The implementation is intentionally modest. It does not claim to identify fraud, allocate resources, evaluate schools, or predict policy outcomes. Those questions need domain review, stronger study design, and evidence that this fixture cannot provide. The reference proves a local train, evaluate, register, monitor, and score path that another engineer can reproduce.
