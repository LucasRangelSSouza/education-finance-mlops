# ADR 0002: Year-relative feature and a spread gate

## Context

On release v1, the first drift check blocked 2023 because nominal investment per student rose about 30% over 2022 (PSI 0.615). That is growth, not deviation. After switching to a year-relative feature, the 2023 PSI fell to 0.233 and the batch passed, yet it produced 921 signals, about ten times the evaluated rate. The feature's spread had widened while its median stayed at zero, and decile PSI barely reacted.

## Decision

The model and the drift check use the target divided by the same-year national median. The drift check adds a spread ratio based on median absolute deviation, blocking outside [0.80, 1.25]. MAD was chosen over standard deviation because a few extreme declarations, which the model exists to flag, would otherwise move the gate.

## Consequences

Nominal growth no longer blocks every new year. A structural change in dispersion blocks scoring until a person reviews it. The 2023 batch of release v1 is blocked. Nominal-value measures remain in the drift report for context.

## Alternatives considered

- Deflating by an inflation index: needs an external series and still misses funding-rule changes.
- Raising the PSI limit: would have passed the 2023 batch.
- Refitting on 2023 immediately: would absorb an unexplained change into the baseline.
