import json
from pathlib import Path
import tempfile
import unittest

from education_finance_mlops.contracts import load_rows
from education_finance_mlops.features import build_features
from education_finance_mlops.model import evaluate, score, train_baseline
from education_finance_mlops.monitoring import assess_drift
from education_finance_mlops.registry import register_model


ROOT = Path(__file__).resolve().parents[1]


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.rows = load_rows(ROOT / "data" / "municipality_year_fixture.json")
        self.features = build_features(self.rows)

    def test_time_aware_baseline_emits_review_signals_not_decisions(self):
        model = train_baseline(self.features, 2023)
        queue = score([row for row in self.features if row["year"] == 2024], model)
        self.assertEqual(queue[0]["municipality_code"], "1100023")
        self.assertTrue(queue[0]["human_review_required"])
        self.assertTrue(queue[0]["decision_prohibited"])
        self.assertEqual(evaluate(self.features, model, 2024)["review_signals"], 1)

    def test_drift_can_block_a_batch(self):
        candidate = [dict(row, expenditure_per_student=row["expenditure_per_student"] * 3) for row in self.rows]
        result = assess_drift(self.rows, candidate)
        self.assertEqual(result["status"], "blocked")

    def test_registry_keeps_dataset_model_and_code_lineage(self):
        model = train_baseline(self.features, 2023)
        with tempfile.TemporaryDirectory() as directory:
            result = register_model(Path(directory) / "registry.json", model, {"source": "fixture", "version": "v1"}, {"review_signals": 1}, "abc123")
        self.assertEqual(result["code_revision"], "abc123")
        self.assertEqual(result["dataset"]["source"], "fixture")


if __name__ == "__main__":
    unittest.main()
