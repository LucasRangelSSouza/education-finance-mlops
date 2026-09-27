# Education release version 3 compatibility run

The release resolver verified Kaggle version 3 of `lucasrangelss/brazil-education-data-lake` against manifest SHA-256 `311ffeba83b6ccac3d423703b77acb96e6de5ca7c4a86cc9c82881b719caa86d` before reading the semantic layer.

The 2022 evaluation completed with the existing peer model. The 2023 score was blocked by the pre-existing robust spread gate: the relative-investment spread ratio was `1.3843`, outside the approved interval `[0.80, 1.25]`. The new municipal enrollment field is not a model feature, so this run does not claim a new model result.

The CLI requires `--dataset-version 3`; version 1 remains the default pin until a separately reviewed model change chooses otherwise.
