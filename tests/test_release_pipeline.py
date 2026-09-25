import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import pyarrow as pa
import pyarrow.parquet as pq

from education_finance_mlops import peer_model
from education_finance_mlops.release import PinnedRelease, ReleaseVerificationError, verify_release
from education_finance_mlops.release_drift import assess_release_drift, population_stability_index
from education_finance_mlops.release_pipeline import check_intended_use, run_release_pipeline


def row(code, year, value, state="GO", population=5000, mde=27.0):
    return {"id": f"{code}-{year}", "municipality_code": code, "year": year, "state_code": state,
            "population": population, "investment_per_basic_education_student": value, "mde_minimum_share_pct": mde}


def synthetic_rows(outlier_year=2023, shift=1.0):
    rows = []
    for year in (2020, 2021, 2022, 2023):
        for index in range(40):
            code = f"52{index:05d}"
            base = 8000 + index * 25
            rows.append(row(code, year, base * (shift if year == 2023 and index % 2 else 1.0)))
    rows.append(row("5299999", outlier_year, 90000.0, mde=18.0))
    rows.append(row("5299998", 2022, None))
    return rows


def build_release(directory: Path, rows: list[dict]) -> PinnedRelease:
    table = pa.Table.from_pylist(rows)
    files = []
    for layer in ("raw", "trusted", "semantic"):
        path = directory / f"{layer}_records.parquet"
        pq.write_table(table, path)
        files.append({"path": f"{layer}/records.parquet", "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    manifest_path = directory / "release_manifest.json"
    manifest_path.write_text(json.dumps({"files": files, "git_commit": "abc", "privacy_gate": "passed",
                                         "schema_version": "1.1", "row_counts": {"semantic": len(rows)}}), encoding="utf-8")
    return PinnedRelease("owner/edu", 1, hashlib.sha256(manifest_path.read_bytes()).hexdigest(), "1.1")


class ReleasePipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def run_pipeline(self, rows, out="out"):
        pin = build_release(self.dir, rows)
        return run_release_pipeline(verify_release(self.dir, pin), self.dir / out, 2021, 2022, 2023)

    def test_outlier_is_queued_with_lineage_and_review_labels(self):
        result = self.run_pipeline(synthetic_rows())
        self.assertEqual(result["status"], "scored")
        self.assertEqual(result["excluded_rows"], {"target_missing": 1})
        queue = json.loads((self.dir / "out" / "review_queue.json").read_text())
        top = queue["review_queue"][0]
        self.assertEqual(top["municipality_code"], "5299999")
        self.assertEqual(top["direction"], "above_peers")
        self.assertTrue(top["human_review_required"] and top["decision_prohibited"])
        self.assertEqual(queue["lineage"]["dataset"]["slug"], "owner/edu")
        self.assertEqual(queue["lineage"]["feature_schema"], peer_model.FEATURE_SCHEMA_VERSION)

    def test_two_runs_are_identical(self):
        rows = synthetic_rows()
        first = self.run_pipeline(rows, "a")
        second = self.run_pipeline(rows, "b")
        self.assertEqual(first["registry_sha256"], second["registry_sha256"])
        self.assertEqual(first["queue_sha256"], second["queue_sha256"])

    def test_distribution_shift_blocks_scoring(self):
        result = self.run_pipeline(synthetic_rows(shift=3.0))
        self.assertEqual(result["status"], "blocked")
        self.assertTrue((self.dir / "out" / "drift_report.json").exists())
        self.assertFalse((self.dir / "out" / "review_queue.json").exists())

    def test_training_never_sees_evaluation_or_score_years(self):
        features, _ = peer_model.build_release_features(synthetic_rows(outlier_year=2022))
        model = peer_model.train(features, 2021)
        self.assertEqual(model["training_rows"], 80)
        with self.assertRaisesRegex(ValueError, "must follow"):
            peer_model.evaluate(features, model, 2021)

    def test_prohibited_and_unknown_uses_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "prohibited"):
            check_intended_use("funding_allocation")
        with self.assertRaisesRegex(ValueError, "unsupported"):
            check_intended_use("forecasting")

    def test_unapproved_release_is_rejected(self):
        build_release(self.dir, synthetic_rows())
        with self.assertRaisesRegex(ReleaseVerificationError, "not the approved"):
            verify_release(self.dir, PinnedRelease("owner/edu", 2, "1" * 64, "1.1"))

    def test_altered_release_is_rejected(self):
        pin = build_release(self.dir, synthetic_rows())
        with (self.dir / "semantic_records.parquet").open("ab") as handle:
            handle.write(b"0")
        with self.assertRaisesRegex(ReleaseVerificationError, "hash mismatch"):
            verify_release(self.dir, pin)


class DriftTests(unittest.TestCase):
    def test_identical_distributions_have_zero_psi(self):
        values = [float(v) for v in range(100)]
        self.assertEqual(population_stability_index(values, values), 0.0)

    def test_missing_schema_field_blocks(self):
        reference = [row("5200001", 2022, 100.0)]
        candidate = [{key: value for key, value in reference[0].items() if key != "population"}]
        self.assertEqual(assess_release_drift(reference, candidate, peer_model.TARGET)["status"], "blocked")

    def test_missingness_rise_blocks(self):
        reference = [row(f"52{i:05d}", 2022, 100.0 + i) for i in range(20)]
        candidate = [row(f"52{i:05d}", 2023, None if i < 5 else 100.0 + i) for i in range(20)]
        result = assess_release_drift(reference, candidate, peer_model.TARGET)
        self.assertIn("missingness", " ".join(result["reasons"]))

    def test_wider_spread_around_a_stable_median_blocks(self):
        reference = [row(f"52{i:05d}", 2022, 1000.0 * (1 + 0.1 * ((i % 5) - 2))) for i in range(50)]
        candidate = [row(f"52{i:05d}", 2023, 1000.0 * (1 + 0.3 * ((i % 5) - 2))) for i in range(50)]
        result = assess_release_drift(reference, candidate, peer_model.TARGET)
        self.assertIn("spread ratio", " ".join(result["reasons"]))


if __name__ == "__main__":
    unittest.main()
