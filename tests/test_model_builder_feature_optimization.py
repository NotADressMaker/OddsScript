#!/usr/bin/env python3
"""Tests for model-builder feature-importance optimization."""

import os
import random
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.model_builder import Model


class TestModelBuilderFeatureOptimization(unittest.TestCase):
    def setUp(self):
        random.seed(42)
        self.X = []
        self.y = []
        for _ in range(120):
            rating_diff = random.uniform(-20, 20)
            rest_edge = random.uniform(-3, 3)
            market_noise = random.uniform(-100, 100)
            travel_noise = random.uniform(-50, 50)
            self.X.append([rating_diff, rest_edge, market_noise, travel_noise])
            self.y.append(1 if rating_diff + (rest_edge * 2) > 0 else 0)

    def test_important_variables_are_sorted_with_names_and_indices(self):
        model = (Model()
                 .for_classification()
                 .using_random_forest(n_trees=30, max_depth=5)
                 .with_features(['rating_diff', 'rest_edge', 'market_noise', 'travel_noise'])
                 .train(self.X, self.y))

        important = model.important_variables(top_n=2)

        self.assertEqual(len(important), 2)
        self.assertGreaterEqual(important[0]['importance'], important[1]['importance'])
        self.assertIn(important[0]['feature'], {'rating_diff', 'rest_edge'})
        self.assertIsInstance(important[0]['index'], int)

    def test_optimize_features_retrains_and_accepts_full_feature_rows(self):
        model = (Model()
                 .for_classification()
                 .using_random_forest(n_trees=30, max_depth=5)
                 .with_features(['rating_diff', 'rest_edge', 'market_noise', 'travel_noise'])
                 .optimize_features(self.X, self.y, top_n=2))

        self.assertEqual(len(model.feature_names), 2)
        self.assertLessEqual(len(model._selected_feature_indices), 2)

        full_predictions = model.predict(self.X[:10])
        filtered_X = [[row[i] for i in model._selected_feature_indices] for row in self.X[:10]]
        filtered_predictions = model.predict(filtered_X)

        self.assertEqual(full_predictions, filtered_predictions)

    def test_minmax_normalization_still_predicts_after_feature_optimization(self):
        model = (Model()
                 .for_classification()
                 .using_random_forest(n_trees=20, max_depth=4)
                 .with_features(['rating_diff', 'rest_edge', 'market_noise', 'travel_noise'])
                 .with_normalization('minmax')
                 .optimize_features(self.X, self.y, top_n=2))

        predictions = model.predict(self.X[:5])

        self.assertEqual(len(predictions), 5)


if __name__ == '__main__':
    unittest.main()
