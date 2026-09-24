# Model card: regional z-score baseline

## Intended use

The baseline identifies municipality-year educational-finance records whose `expenditure_per_student` differs materially from the historical distribution of the same region. The output helps an analyst decide which source records deserve contextual review.

## Prohibited use

Do not use the output to determine eligibility, allocate resources, rank schools or municipalities, assess people, identify fraud, make compliance determinations, or claim a causal explanation. The score is not a prediction of policy quality or correctness.

## Method

The model groups historical training rows by region and calculates the mean and population standard deviation for `expenditure_per_student`. A later-year record receives the absolute z-score of its difference from that peer mean. The current review threshold is 2.0. The standard deviation floor is 1.0 to avoid division by zero.

## Evaluation and monitoring

The fixture run trains through 2023 and evaluates 2024. It evaluates two rows, emits one review signal, and records the single North-region peer slice. These numbers describe only the synthetic fixture. Schema validation and configured mean-shift checks run before batch scoring; a breach blocks the batch.

## Human review

Each queue entry contains the observed value, peer mean, peer standard deviation, region, and score. A reviewer must inspect source coverage, reporting context, and data quality before taking any downstream action.

## Limitations

The baseline has no causal model, uncertainty interval, missingness imputation, population weighting, or external validation. A future public dataset release requires separate source, terms, coverage, and model-validation review.
