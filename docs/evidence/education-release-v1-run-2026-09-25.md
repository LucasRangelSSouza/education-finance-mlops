# Pipeline run on education release v1

**Date:** 2026-09-25  
**Code commit:** `6be582dfed6ca40b4d5b3586cb212eb68822fd06`  
**Dataset:** [`lucasrangelss/brazil-education-data-lake`](https://www.kaggle.com/datasets/lucasrangelss/brazil-education-data-lake), version 1, manifest SHA-256 `44f259602a688432dddbae6b0306a6957514a634d57d94a0abd3cff30f4b3506`, built at data-map commit `379da099`  
**Environment:** Windows 11, Python 3.12, public download through `kagglehub` without a Kaggle credential

## Commands

```powershell
python -m education_finance_mlops run-release --train-through-year 2020 --evaluation-year 2021 --score-year 2022 --output artifacts/a-2022
python -m education_finance_mlops run-release --train-through-year 2021 --evaluation-year 2022 --score-year 2023 --output artifacts/a-2023
```

Each command was run twice into separate folders. Every output file was byte-identical across the two runs.

## Input

The release has 27,830 municipality-year rows for 2019 through 2023. Thirty rows report zero investment per basic-education student and are excluded before training; the registry records that count. The model input is each municipality's investment per basic-education student divided by the national median of the same year, on a log scale. Dividing by the same-year median removes nominal growth without letting later years inform earlier ones.

## Batch 2022: scored

| Step | Result |
|---|---|
| Training | years 2019-2020, 11,102 rows, 18 peer groups (macro-region x population band) with at least 30 rows, model `ba382720d49b6020` |
| Held-out evaluation, 2021 | peer model: 93 signals of 5,566 rows (1.67%), 89 above peers, 4 below; global baseline: 15 signals (0.27%) |
| Drift, 2022 vs 2021 | relative feature PSI 0.029, median shift 0.00, spread ratio 1.086: passed. On nominal values the PSI would have been 1.635. |
| Scoring, 2022 | 96 review signals, 92 above peers and 4 below |

## Batch 2023: blocked

| Step | Result |
|---|---|
| Training | years 2019-2021, 16,668 rows, 19 peer groups, model `918f471d8f3059d5` |
| Held-out evaluation, 2022 | peer model: 89 signals (1.60%); global baseline: 24 (0.43%) |
| Drift, 2023 vs 2022 | relative feature PSI 0.233 (limit 0.25), median shift 0.00, spread ratio 1.384 (limit 1.25): **blocked** |

The 2023 batch was not scored. A drift report was written instead. Before the spread check existed, the same batch passed the PSI limit and produced 921 signals, about ten times the evaluated rate, concentrated in Northeast municipalities of 10,000 to 50,000 inhabitants above their peers. The spread of the relative feature widened in 2023 while the median stayed fixed. This data does not show why. A reviewer should establish the cause, for example a funding-rule change, before the model is refit on 2023 or its signals are read.

## What the evaluation shows and does not show

There are no ground-truth anomaly labels. The run reports signal counts, slices, direction, and year-over-year persistence (33% of the 2021 signals were also flagged when the same model scored 2020, a training year). It reports how many signals fall below the 25% education maintenance and development minimum (7 of 93 in 2021, against 1,090 such rows in that year). That is co-occurrence only: the model neither uses nor predicts the threshold. No accuracy, precision, or recall is claimed.

## Output hashes

| File | SHA-256 |
|---|---|
| `a-2022/registry.json` | `e11ea9fd5430004d5fe5d85a1f996fde95ed071632da86c5620f9d518c7c3e1e` |
| `a-2022/review_queue.json` | `d6421340660446a4c0cdb4233fa62e820664dabb33c5167f331edc5c17385a23` |
| `a-2023/registry.json` | `2dda83ef7a2257621976ff2448bc0f127731bb66cafd151e26630c820a6a3793` |
| `a-2023/drift_report.json` | `073c1896b8e69726f2ef0f48a1d49e00150ae1490bc04e9488dddc46aa94e651` |

The files embed the code commit, so a run at another commit produces different bytes.
