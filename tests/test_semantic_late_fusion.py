"""Synthetic, data-independent interface checks."""
import math
import unittest

from strokepointpp.semantic_late_fusion import (
    mean_semantic_probabilities, source_presence_probability, stable_sigmoid,
)


class SemanticLateFusionTests(unittest.TestCase):
    def test_stable_sigmoid(self):
        self.assertEqual(stable_sigmoid(0), 0.5)
        self.assertEqual(stable_sigmoid(1000), 1.0)
        self.assertEqual(stable_sigmoid(-1000), 0.0)
        self.assertAlmostEqual(stable_sigmoid(2), 1 - stable_sigmoid(-2))

    def test_source_scaler_is_used(self):
        result = source_presence_probability((3, 8), feature_mean=(1, 2),
            feature_scale=(2, 3), coefficients=(0.2, -0.1), intercept=0.5)
        self.assertAlmostEqual(result, stable_sigmoid(0.5))

    def test_semantic_mean_preserves_target_coordinates(self):
        self.assertEqual(mean_semantic_probabilities(((0, 1), (1, 0),
            (0.25, 0.75), (0.75, 0.25))), (0.5, 0.5))

    def test_hidden_mean_is_not_probability_mean(self):
        probabilities = ((stable_sigmoid(0),), (stable_sigmoid(4),))
        self.assertNotAlmostEqual(mean_semantic_probabilities(probabilities)[0], stable_sigmoid(2))

    def test_invalid_logits(self):
        for value in (math.nan, math.inf, -math.inf):
            with self.assertRaises(ValueError):
                stable_sigmoid(value)

    def test_invalid_vectors(self):
        with self.assertRaises(ValueError):
            source_presence_probability((1,), feature_mean=(0, 0), feature_scale=(1,),
                coefficients=(1,), intercept=0)
        with self.assertRaises(ValueError):
            source_presence_probability((1,), feature_mean=(0,), feature_scale=(0,),
                coefficients=(1,), intercept=0)

    def test_invalid_probability_tables(self):
        for rows in ((), ((),), ((0.5,), (0.5, 0.6)), ((1.1,),), ((math.nan,),)):
            with self.assertRaises(ValueError):
                mean_semantic_probabilities(rows)


if __name__ == "__main__":
    unittest.main()
