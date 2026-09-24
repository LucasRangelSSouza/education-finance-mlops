# Claim-to-evidence map

| Claim | Evidence | Status |
| --- | --- | --- |
| Training uses an earlier period than evaluation. | `tests/test_pipeline.py::test_time_aware_baseline_emits_review_signals_not_decisions`; fixture years 2023 and 2024. | Supported |
| The fixture evaluation emits one review signal from two evaluated rows. | Repeatable local `train` command; model card. | Supported |
| A drift breach blocks a batch. | `tests/test_pipeline.py::test_drift_can_block_a_batch`. | Supported |
| Every scoring result has model, dataset, and code lineage. | `tests/test_pipeline.py::test_registry_keeps_dataset_model_and_code_lineage`; local registry artifact. | Supported |
| The baseline identifies real-world errors or fraud. | No validation supports this claim. | Not claimed |
| The repository consumes a public Kaggle release today. | No approved release exists yet. | Not claimed |
