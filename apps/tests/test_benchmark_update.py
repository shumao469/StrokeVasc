"""Public aggregate schema tests: no dataset, model or GPU access."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest

APPS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APPS))
from benchmark_update import load_development_update, validate_development_update


class BenchmarkUpdateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.auto = load_development_update(APPS.parent)

    def test_complete_fixed_rows(self):
        self.assertEqual(sum(len(item) for item in self.data["summaries"].values()), 18)
        self.assertEqual(self.data["review"]["model_policy_records"], 360)
        self.assertEqual(self.data["interface"]["binary_heads_fitted"], 8)

    def test_dynamic_dice_does_not_imply_point_correction(self):
        row = self.data["summaries"]["YZ"]["NEW_MRA_LATE_HARD0.05"]
        baseline = self.data["summaries"]["YZ"]["NONE"]
        self.assertGreater(row["sampled_macro_Dice"]["mean"], baseline["sampled_macro_Dice"]["mean"])
        self.assertEqual(row["corrected_points"]["sum"], 0)
        self.assertEqual(row["new_error_points"]["sum"], 0)

    def test_auto_scope_stays_separate(self):
        self.assertEqual(self.auto["fits"], 0)
        self.assertEqual(self.auto["encoder_forwards"], 40)
        self.assertEqual(self.auto["AUTO_B"]["status"], "NOT_ADMITTED")

    def test_incomplete_policies_rejected(self):
        broken = deepcopy(self.data)
        del broken["summaries"]["YZ"]["COUNT8"]
        with self.assertRaises(ValueError):
            validate_development_update(broken)

    def test_patient_or_state_fields_rejected(self):
        for key in ("patient_id", "case_ids", "state_dict", "coefficients", "access_token"):
            broken = deepcopy(self.data)
            broken[key] = "synthetic forbidden field"
            with self.assertRaises(ValueError):
                validate_development_update(broken)

    def test_absolute_paths_rejected(self):
        broken = deepcopy(self.data)
        broken["extra"] = "/mnt/private/example"
        with self.assertRaises(ValueError):
            validate_development_update(broken)


if __name__ == "__main__":
    unittest.main()
