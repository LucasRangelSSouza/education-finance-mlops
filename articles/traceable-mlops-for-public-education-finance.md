# Building a traceable MLOps pipeline for public education-finance indicators

**Versioned reference:** [v0.2.0](https://github.com/LucasRangelSSouza/education-finance-mlops/tree/v0.2.0)

Municipality-year indicators are easy to turn into a score and hard to interpret responsibly. The engineering problem worth solving is smaller: make a review signal reproducible, show the data and model lineage behind it, and stop scoring when the input changes beyond an agreed boundary. Version 0.2.0 does this on real public data, and the most useful result is a batch it refused to score.

## The data

The companion project [brazil-public-data-map](https://github.com/LucasRangelSSouza/brazil-public-data-map) publishes `lucasrangelss/brazil-education-data-lake` on Kaggle. Version 1 holds 27,830 annual municipal declarations to SIOPE, FNDE's education budget system, for 2019 through 2023, joined to IBGE municipality codes. The pipeline pins that version by manifest hash and checks every file before it reads a row.

The model looks at one declared value: investment per basic-education student. Values are as declared, not audited, and some are implausible. That is the point of a triage tool.

## The model

The raw value is a poor feature. Nominal investment per student rose about 30% from 2022 to 2023, so any fixed threshold would flag growth. The pipeline divides each value by the national median of the same year and takes the log. Using the same year only keeps later information out of earlier decisions.

Municipalities are compared with peers in the same macro-region and population band. For each group, the model stores the median and the median absolute deviation from the training years. A later declaration more than 3.5 robust standard deviations from its group median becomes a review signal. A single-group global baseline runs alongside it for comparison.

Training through 2020 and describing 2021, the peer model flagged 93 of 5,566 rows (1.67%); the global baseline flagged 15. Training through 2021 and describing 2022 gave 89 signals (1.60%). There are no anomaly labels, so these are rates, not accuracy. The run also counts how many signals fall below the constitutional 25% education-spending minimum: 7 of 93 in 2021. That is co-occurrence. The model does not use the threshold.

## The batch that was blocked

Before any batch is scored, the candidate year is compared with the evaluation year: schema, missingness, population stability index, median shift, and spread. The 2022 batch passed (PSI 0.029, spread ratio 1.086) and produced 96 signals.

The 2023 batch is the instructive one. The first version of the drift check had only schema, missingness, PSI, and median shift. On nominal values it blocked 2023 at PSI 0.615, for the wrong reason. After the switch to the relative feature, PSI fell to 0.233, under the 0.25 limit, and the batch went through. It produced 921 signals, about ten times the evaluated rate, most of them in Northeast municipalities of 10,000 to 50,000 people, above their peers.

The median of the relative feature had not moved. Its spread had widened by about 38%, and decile PSI is not very sensitive to a symmetric widening around a fixed centre. The fix was a spread gate based on median absolute deviation, which the model's own outliers cannot trigger. With it, 2023 is blocked at a spread ratio of 1.384 and a drift report is written instead of a queue.

The data does not say why the spread widened. A change in funding rules is one candidate, but the release carries no evidence for it. A person should find out before refitting on 2023. Absorbing the change silently would teach the baseline that the new dispersion is normal.

## Lineage and reproduction

Every registry and queue file records the dataset slug, version, manifest hash, data build commit, code commit, feature schema, model ID, and intended use. Two runs at the same commit produced byte-identical files. The CLI accepts only `review_triage` as an intended use and refuses allocation, eligibility, sanction, audit-finding, and ranking uses by name.

```powershell
python -m pip install -e ".[release]"
make check
make reproduce
```

The pipeline does not identify fraud, evaluate schools, or explain policy outcomes. It produces a short, inspectable queue from public data and it stops when the data no longer looks like what it was trained on.
