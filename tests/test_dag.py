from pathlib import Path
import importlib.util
import unittest

DAG_PATH = Path(__file__).resolve().parents[1] / "dags" / "education_monitoring_demo.py"


class DemoDagTests(unittest.TestCase):
    def test_imports_without_airflow(self):
        spec = importlib.util.spec_from_file_location("education_monitoring_demo", DAG_PATH)
        spec.loader.exec_module(importlib.util.module_from_spec(spec))

    def test_is_unscheduled_paused_and_credential_free(self):
        content = DAG_PATH.read_text(encoding="utf-8")
        self.assertIn("schedule=None", content)
        self.assertIn("is_paused_upon_creation=True", content)
        for forbidden in ("token", "password", "secret", "KAGGLE_"):
            self.assertNotIn(forbidden, content)


if __name__ == "__main__":
    unittest.main()
