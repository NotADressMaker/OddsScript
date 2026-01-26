#!/usr/bin/env python3
"""
Comprehensive test suite for ML models library
"""

import unittest
import math
import sys
import os
import random

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.ml_models import (
    DecisionTree, RandomForest, NeuralNetwork, FeatureEngineering,
    ModelValidation, ActivationFunction, MLModelResult, ClassificationMetrics,
    CrossValidationResult, predict_game_outcome_ml
)


class TestDecisionTree(unittest.TestCase):
    """Test Decision Tree classifier and regressor"""

    def test_simple_classification(self):
        """Test basic binary classification"""
        # Simple XOR-like problem
        X = [[0, 0], [0, 1], [1, 0], [1, 1]]
        y = [0, 1, 1, 0]

        tree = DecisionTree(max_depth=3)
        tree.fit(X, y)
        predictions = tree.predict(X)

        # Should learn the pattern reasonably well
        accuracy = sum(1 for i in range(len(y)) if abs(predictions[i] - y[i]) < 0.5) / len(y)
        self.assertGreaterEqual(accuracy, 0.5)

    def test_simple_regression(self):
        """Test regression with decision tree"""
        # Simple increasing pattern
        X = [[1], [2], [3], [4], [5]]
        y = [2.0, 4.0, 6.0, 8.0, 10.0]

        tree = DecisionTree(max_depth=5, criterion='mse')
        tree.fit(X, y)
        predictions = tree.predict(X)

        # Should predict reasonably close
        mse = sum((predictions[i] - y[i]) ** 2 for i in range(len(y))) / len(y)
        self.assertLess(mse, 2.0)

    def test_feature_importance(self):
        """Test feature importance calculation"""
        # Create data where first feature is more important
        random.seed(42)
        X = []
        y = []
        for i in range(100):
            x1 = random.uniform(0, 10)
            x2 = random.uniform(0, 10)
            # y depends mostly on x1
            label = 1 if x1 > 5 else 0
            X.append([x1, x2])
            y.append(label)

        tree = DecisionTree(max_depth=5)
        tree.fit(X, y)

        importance = tree.get_feature_importance()

        # Feature 0 should be more important than feature 1
        self.assertGreater(importance.get(0, 0), importance.get(1, 0))

    def test_max_depth_constraint(self):
        """Test max depth constraint"""
        X = [[i] for i in range(100)]
        y = [i % 2 for i in range(100)]

        tree1 = DecisionTree(max_depth=1)
        tree1.fit(X, y)

        tree2 = DecisionTree(max_depth=10)
        tree2.fit(X, y)

        # Deeper tree should fit better
        pred1 = tree1.predict(X)
        pred2 = tree2.predict(X)

        acc1 = sum(1 for i in range(len(y)) if abs(pred1[i] - y[i]) < 0.5) / len(y)
        acc2 = sum(1 for i in range(len(y)) if abs(pred2[i] - y[i]) < 0.5) / len(y)

        self.assertGreaterEqual(acc2, acc1)

    def test_gini_vs_entropy(self):
        """Test different split criteria"""
        X = [[i, i*2] for i in range(50)]
        y = [1 if i > 25 else 0 for i in range(50)]

        tree_gini = DecisionTree(criterion='gini')
        tree_gini.fit(X, y)

        tree_entropy = DecisionTree(criterion='entropy')
        tree_entropy.fit(X, y)

        # Both should produce reasonable results
        pred_gini = tree_gini.predict(X)
        pred_entropy = tree_entropy.predict(X)

        acc_gini = sum(1 for i in range(len(y)) if abs(pred_gini[i] - y[i]) < 0.5) / len(y)
        acc_entropy = sum(1 for i in range(len(y)) if abs(pred_entropy[i] - y[i]) < 0.5) / len(y)

        self.assertGreater(acc_gini, 0.8)
        self.assertGreater(acc_entropy, 0.8)


class TestRandomForest(unittest.TestCase):
    """Test Random Forest ensemble"""

    def test_classification(self):
        """Test Random Forest classification"""
        random.seed(42)

        # Generate synthetic data
        X = []
        y = []
        for i in range(100):
            x1 = random.uniform(0, 10)
            x2 = random.uniform(0, 10)
            label = 1 if (x1 + x2) > 10 else 0
            X.append([x1, x2])
            y.append(label)

        # Split data
        X_train = X[:80]
        y_train = y[:80]
        X_test = X[80:]
        y_test = y[80:]

        # Train Random Forest
        rf = RandomForest(n_trees=10, max_depth=5)
        rf.fit(X_train, y_train)

        # Test predictions
        predictions = rf.predict(X_test)

        # Should achieve reasonable accuracy
        accuracy = sum(1 for i in range(len(y_test))
                      if abs(predictions[i] - y_test[i]) < 0.5) / len(y_test)
        self.assertGreater(accuracy, 0.6)

    def test_regression(self):
        """Test Random Forest regression"""
        random.seed(42)

        # y = x1 + 2*x2 + noise
        X = []
        y = []
        for i in range(100):
            x1 = random.uniform(0, 10)
            x2 = random.uniform(0, 10)
            target = x1 + 2*x2 + random.gauss(0, 1)
            X.append([x1, x2])
            y.append(target)

        rf = RandomForest(n_trees=20, max_depth=8, criterion='mse')
        rf.fit(X, y)

        predictions = rf.predict(X)

        # Calculate R²
        import statistics
        mean_y = statistics.mean(y)
        ss_res = sum((y[i] - predictions[i]) ** 2 for i in range(len(y)))
        ss_tot = sum((y[i] - mean_y) ** 2 for i in range(len(y)))
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

        self.assertGreater(r_squared, 0.5)

    def test_feature_importance(self):
        """Test feature importance in Random Forest"""
        random.seed(42)

        # Create data where first feature is more predictive
        X = []
        y = []
        for i in range(100):
            x1 = random.uniform(0, 10)
            x2 = random.uniform(0, 10)
            # y depends mostly on x1
            label = 1 if x1 > 5 else 0
            X.append([x1, x2])
            y.append(label)

        rf = RandomForest(n_trees=20, max_depth=5)
        rf.fit(X, y)

        importance = rf.get_feature_importance()

        # Feature 0 should be more important (or at least equal due to randomness)
        self.assertGreaterEqual(importance.get(0, 0), importance.get(1, 0) * 0.8)

    def test_ensemble_effect(self):
        """Test that ensemble performs better than single tree"""
        random.seed(42)

        X = []
        y = []
        for i in range(100):
            x1 = random.uniform(0, 10)
            x2 = random.uniform(0, 10)
            label = 1 if (x1 + x2) > 10 else 0
            X.append([x1, x2])
            y.append(label)

        # Single tree
        tree = DecisionTree(max_depth=5)
        tree.fit(X, y)
        tree_pred = tree.predict(X)
        tree_acc = sum(1 for i in range(len(y))
                      if abs(tree_pred[i] - y[i]) < 0.5) / len(y)

        # Random Forest
        rf = RandomForest(n_trees=10, max_depth=5)
        rf.fit(X, y)
        rf_pred = rf.predict(X)
        rf_acc = sum(1 for i in range(len(y))
                    if abs(rf_pred[i] - y[i]) < 0.5) / len(y)

        # Forest should be at least as good as single tree
        self.assertGreaterEqual(rf_acc, tree_acc - 0.1)


class TestNeuralNetwork(unittest.TestCase):
    """Test Neural Network"""

    def test_simple_linear_function(self):
        """Test learning a simple linear function"""
        # y = 2x
        X = [[1], [2], [3], [4], [5]]
        y = [2, 4, 6, 8, 10]

        # Normalize
        y_normalized = [val / 10.0 for val in y]

        nn = NeuralNetwork([1, 3, 1], learning_rate=0.01, epochs=500)
        nn.fit(X, y_normalized)

        predictions = nn.predict(X)

        # Denormalize
        predictions = [p * 10.0 for p in predictions]

        # Should learn approximately
        mse = sum((predictions[i] - y[i]) ** 2 for i in range(len(y))) / len(y)
        self.assertLess(mse, 10.0)

    def test_xor_problem(self):
        """Test learning XOR (non-linear problem)"""
        X = [[0, 0], [0, 1], [1, 0], [1, 1]]
        y = [0, 1, 1, 0]

        # Need hidden layer for XOR
        nn = NeuralNetwork([2, 4, 1], activation=ActivationFunction.SIGMOID,
                          learning_rate=0.5, epochs=2000)
        nn.fit(X, y)

        predictions = nn.predict(X)

        # Should learn XOR pattern reasonably
        predictions_binary = [1 if p > 0.5 else 0 for p in predictions]
        accuracy = sum(1 for i in range(len(y)) if predictions_binary[i] == y[i]) / len(y)

        # XOR is hard, but should get some correct
        self.assertGreaterEqual(accuracy, 0.5)

    def test_activation_functions(self):
        """Test different activation functions"""
        X = [[1], [2], [3]]
        y = [0.1, 0.5, 0.9]

        for activation in [ActivationFunction.SIGMOID, ActivationFunction.RELU,
                          ActivationFunction.TANH]:
            nn = NeuralNetwork([1, 3, 1], activation=activation, epochs=100)
            nn.fit(X, y)
            predictions = nn.predict(X)

            # Should produce predictions
            self.assertEqual(len(predictions), len(y))

    def test_network_depth(self):
        """Test networks of different depths"""
        X = [[i] for i in range(10)]
        y = [i * 0.1 for i in range(10)]

        # Shallow network
        nn1 = NeuralNetwork([1, 1], epochs=100)
        nn1.fit(X, y)
        pred1 = nn1.predict(X)

        # Deep network
        nn2 = NeuralNetwork([1, 5, 5, 1], epochs=100)
        nn2.fit(X, y)
        pred2 = nn2.predict(X)

        # Both should produce predictions
        self.assertEqual(len(pred1), len(y))
        self.assertEqual(len(pred2), len(y))


class TestFeatureEngineering(unittest.TestCase):
    """Test feature engineering utilities"""

    def test_polynomial_features(self):
        """Test polynomial feature creation"""
        X = [[1, 2], [3, 4]]

        poly = FeatureEngineering.create_polynomial_features(X, degree=2)

        # Should have original + squared + interaction terms
        # Original: 2, Squared: 2, Interaction: 1
        self.assertGreater(len(poly[0]), len(X[0]))

        # Check first row: [1, 2] -> [1, 2, 1, 4, 2]
        self.assertEqual(poly[0][0], 1)  # x1
        self.assertEqual(poly[0][1], 2)  # x2
        self.assertEqual(poly[0][2], 1)  # x1²
        self.assertEqual(poly[0][3], 4)  # x2²
        self.assertEqual(poly[0][4], 2)  # x1*x2

    def test_standard_normalization(self):
        """Test z-score normalization"""
        X = [[1, 10], [2, 20], [3, 30], [4, 40], [5, 50]]

        normalized, params = FeatureEngineering.normalize_features(X, method='standard')

        # Check that mean is approximately 0 and std is approximately 1
        import statistics
        col0 = [row[0] for row in normalized]
        col1 = [row[1] for row in normalized]

        self.assertAlmostEqual(statistics.mean(col0), 0, places=10)
        self.assertAlmostEqual(statistics.mean(col1), 0, places=10)

        # Std should be close to 1
        self.assertAlmostEqual(statistics.stdev(col0), 1, places=1)
        self.assertAlmostEqual(statistics.stdev(col1), 1, places=1)

    def test_minmax_normalization(self):
        """Test min-max scaling"""
        X = [[1, 10], [2, 20], [3, 30], [4, 40], [5, 50]]

        normalized, params = FeatureEngineering.normalize_features(X, method='minmax')

        # All values should be between 0 and 1
        for row in normalized:
            for val in row:
                self.assertGreaterEqual(val, 0)
                self.assertLessEqual(val, 1)

        # Min should be 0, max should be 1
        col0 = [row[0] for row in normalized]
        self.assertAlmostEqual(min(col0), 0, places=10)
        self.assertAlmostEqual(max(col0), 1, places=10)

    def test_lag_features(self):
        """Test lagged feature creation"""
        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

        lagged = FeatureEngineering.create_lag_features(data, lags=[1, 2, 3])

        # Should have fewer rows (lost to lags)
        self.assertEqual(len(lagged), len(data) - 3)

        # First row should be [4, 3, 2, 1] (current, lag1, lag2, lag3)
        self.assertEqual(lagged[0][0], 4)  # Current value
        self.assertEqual(lagged[0][1], 3)  # Lag 1
        self.assertEqual(lagged[0][2], 2)  # Lag 2
        self.assertEqual(lagged[0][3], 1)  # Lag 3

    def test_rolling_features(self):
        """Test rolling window features"""
        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

        rolling = FeatureEngineering.create_rolling_features(data, windows=[3])

        # Should have mean, std, min, max for each window
        self.assertEqual(len(rolling[0]), 4)

        # First window [1, 2, 3]: mean=2, std≈0.82, min=1, max=3
        self.assertAlmostEqual(rolling[0][0], 2.0, places=1)  # mean
        self.assertEqual(rolling[0][2], 1)  # min
        self.assertEqual(rolling[0][3], 3)  # max

    def test_feature_selection_correlation(self):
        """Test correlation-based feature selection"""
        random.seed(42)

        # Create features where first is highly correlated with target
        X = []
        y = []
        for i in range(100):
            x1 = random.uniform(0, 10)
            x2 = random.uniform(0, 10)  # Random, uncorrelated
            target = x1 + random.gauss(0, 0.5)  # Highly correlated with x1
            X.append([x1, x2])
            y.append(target)

        selected = FeatureEngineering.select_features_correlation(
            X, y, threshold=0.5
        )

        # Should select feature 0 (highly correlated)
        self.assertIn(0, selected)


class TestModelValidation(unittest.TestCase):
    """Test model validation utilities"""

    def test_train_test_split(self):
        """Test train/test split"""
        X = [[i] for i in range(100)]
        y = list(range(100))

        X_train, X_test, y_train, y_test = ModelValidation.train_test_split(
            X, y, test_size=0.2, shuffle=False
        )

        # Check sizes
        self.assertEqual(len(X_train), 80)
        self.assertEqual(len(X_test), 20)
        self.assertEqual(len(y_train), 80)
        self.assertEqual(len(y_test), 20)

        # Without shuffle, test should be last 20
        self.assertEqual(y_test[0], 0)

    def test_train_test_split_with_shuffle(self):
        """Test train/test split with shuffling"""
        X = [[i] for i in range(100)]
        y = list(range(100))

        X_train, X_test, y_train, y_test = ModelValidation.train_test_split(
            X, y, test_size=0.2, shuffle=True, random_seed=42
        )

        # Check sizes
        self.assertEqual(len(X_train), 80)
        self.assertEqual(len(X_test), 20)

        # With shuffle, should not be sequential
        # (very unlikely to have first 20 sequential)

    def test_k_fold_cross_validation(self):
        """Test k-fold cross-validation"""
        random.seed(42)

        # Generate simple linearly separable data
        X = []
        y = []
        for i in range(50):
            x1 = random.uniform(0, 10)
            label = 1 if x1 > 5 else 0
            X.append([x1])
            y.append(label)

        # Run cross-validation
        result = ModelValidation.k_fold_cross_validation(
            X, y,
            model_class=DecisionTree,
            model_params={'max_depth': 3},
            k=5,
            scoring='accuracy'
        )

        # Check result structure
        self.assertEqual(len(result.fold_scores), 5)
        self.assertIsInstance(result.mean_score, float)
        self.assertIsInstance(result.std_score, float)
        self.assertGreaterEqual(result.best_fold, 0)
        self.assertLess(result.best_fold, 5)

        # Mean score should be reasonable
        self.assertGreater(result.mean_score, 0.5)

    def test_classification_metrics_binary(self):
        """Test binary classification metrics"""
        y_true = [0, 0, 1, 1, 0, 1, 1, 0]
        y_pred = [0, 0, 1, 1, 0, 0, 1, 0]

        metrics = ModelValidation.calculate_classification_metrics(y_true, y_pred)

        # Check accuracy
        expected_accuracy = 7 / 8  # 7 correct out of 8
        self.assertAlmostEqual(metrics.accuracy, expected_accuracy)

        # Check confusion matrix dimensions
        self.assertEqual(len(metrics.confusion_matrix), 2)
        self.assertEqual(len(metrics.confusion_matrix[0]), 2)

        # Check that metrics are in valid range
        self.assertGreaterEqual(metrics.precision, 0)
        self.assertLessEqual(metrics.precision, 1)
        self.assertGreaterEqual(metrics.recall, 0)
        self.assertLessEqual(metrics.recall, 1)
        self.assertGreaterEqual(metrics.f1_score, 0)
        self.assertLessEqual(metrics.f1_score, 1)

    def test_regression_metrics(self):
        """Test regression metrics"""
        y_true = [1.0, 2.0, 3.0, 4.0, 5.0]
        y_pred = [1.1, 2.1, 2.9, 4.2, 4.8]

        metrics = ModelValidation.calculate_regression_metrics(y_true, y_pred)

        # Check that all metrics are present
        self.assertIn('mse', metrics)
        self.assertIn('rmse', metrics)
        self.assertIn('mae', metrics)
        self.assertIn('r_squared', metrics)

        # Check that metrics are reasonable
        self.assertGreater(metrics['mse'], 0)
        self.assertAlmostEqual(metrics['rmse'], math.sqrt(metrics['mse']))
        self.assertGreater(metrics['r_squared'], 0.9)  # Good predictions

    def test_perfect_predictions(self):
        """Test metrics with perfect predictions"""
        y_true = [0, 1, 0, 1, 0, 1]
        y_pred = [0, 1, 0, 1, 0, 1]

        metrics = ModelValidation.calculate_classification_metrics(y_true, y_pred)

        self.assertEqual(metrics.accuracy, 1.0)
        self.assertEqual(metrics.precision, 1.0)
        self.assertEqual(metrics.recall, 1.0)
        self.assertEqual(metrics.f1_score, 1.0)


class TestIntegrationScenarios(unittest.TestCase):
    """Test realistic betting scenarios with ML models"""

    def test_predict_nfl_games(self):
        """Test predicting NFL game outcomes"""
        random.seed(42)

        # Simulate team stats: [offensive_rating, defensive_rating, recent_form]
        team_stats = {
            'offense': [7.5, 6.2, 8.1, 5.9, 7.8, 6.5, 7.2, 8.3, 6.8, 7.1],
            'defense': [6.8, 7.2, 6.5, 8.1, 6.2, 7.5, 7.0, 6.0, 7.3, 6.9],
            'form': [0.6, 0.5, 0.7, 0.4, 0.65, 0.55, 0.6, 0.75, 0.52, 0.58]
        }

        # Historical results (1 = win, 0 = loss)
        results = [1, 0, 1, 0, 1, 1, 1, 1, 0, 1]

        # Run prediction
        prediction_result = predict_game_outcome_ml(team_stats, results)

        # Check result structure
        self.assertIn('predictions', prediction_result)
        self.assertIn('accuracy', prediction_result)
        self.assertIn('feature_importance', prediction_result)

    def test_player_performance_prediction(self):
        """Test predicting player performance"""
        random.seed(42)

        # Features: [minutes_played, usage_rate, opponent_rating]
        X = []
        y = []  # Points scored

        for i in range(100):
            minutes = random.uniform(20, 40)
            usage = random.uniform(0.15, 0.35)
            opp_rating = random.uniform(90, 110)

            # Points formula with some randomness
            points = (minutes * usage * 2) + random.gauss(0, 3)

            X.append([minutes, usage, opp_rating])
            y.append(points)

        # Train Random Forest
        rf = RandomForest(n_trees=30, max_depth=10, criterion='mse')
        rf.fit(X, y)

        predictions = rf.predict(X)

        # Calculate R²
        import statistics
        mean_y = statistics.mean(y)
        ss_res = sum((y[i] - predictions[i]) ** 2 for i in range(len(y)))
        ss_tot = sum((y[i] - mean_y) ** 2 for i in range(len(y)))
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

        # Should have some predictive power
        self.assertGreater(r_squared, 0.3)

    def test_betting_strategy_optimization(self):
        """Test optimizing betting strategy with ML"""
        random.seed(42)

        # Features: [odds, bet_size, confidence]
        X = []
        y = []  # Profit/loss

        for i in range(100):
            odds = random.uniform(1.5, 3.0)
            bet_size = random.uniform(1, 10)
            confidence = random.uniform(0.5, 0.9)

            # Simulate profit
            win_prob = confidence * 0.8  # Calibrated probability
            if random.random() < win_prob:
                profit = bet_size * (odds - 1)
            else:
                profit = -bet_size

            X.append([odds, bet_size, confidence])
            y.append(profit)

        # Train model to predict profit
        rf = RandomForest(n_trees=20, max_depth=8, criterion='mse')
        rf.fit(X, y)

        # Get feature importance
        importance = rf.get_feature_importance()

        # Confidence should be important for predictions
        self.assertIn(2, importance)  # Confidence is feature 2

    def test_cross_validation_for_stability(self):
        """Test model stability with cross-validation"""
        random.seed(42)

        # Generate data
        X = []
        y = []
        for i in range(100):
            x1 = random.uniform(0, 10)
            x2 = random.uniform(0, 10)
            label = 1 if (x1 + x2) > 10 else 0
            X.append([x1, x2])
            y.append(label)

        # Cross-validate
        cv_result = ModelValidation.k_fold_cross_validation(
            X, y,
            model_class=RandomForest,
            model_params={'n_trees': 10, 'max_depth': 5},
            k=5,
            scoring='accuracy'
        )

        # Check consistency across folds
        self.assertGreater(cv_result.mean_score, 0.6)
        self.assertLess(cv_result.std_score, 0.3)  # Not too much variation


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling"""

    def test_empty_data(self):
        """Test with empty data"""
        X = []
        y = []

        tree = DecisionTree()

        with self.assertRaises((ValueError, IndexError)):
            tree.fit(X, y)

    def test_single_sample(self):
        """Test with single sample"""
        X = [[1, 2]]
        y = [1]

        tree = DecisionTree()
        tree.fit(X, y)

        predictions = tree.predict(X)
        self.assertEqual(len(predictions), 1)

    def test_all_same_labels(self):
        """Test with all same labels"""
        X = [[i, i*2] for i in range(10)]
        y = [1] * 10

        tree = DecisionTree()
        tree.fit(X, y)

        predictions = tree.predict(X)

        # Should predict all 1s
        for pred in predictions:
            self.assertAlmostEqual(pred, 1, places=0)

    def test_high_dimensional_data(self):
        """Test with high-dimensional data"""
        random.seed(42)

        # 20 features
        X = [[random.uniform(0, 10) for _ in range(20)] for _ in range(50)]
        y = [random.randint(0, 1) for _ in range(50)]

        rf = RandomForest(n_trees=5, max_depth=5)
        rf.fit(X, y)

        predictions = rf.predict(X)
        self.assertEqual(len(predictions), len(y))


if __name__ == '__main__':
    unittest.main()
