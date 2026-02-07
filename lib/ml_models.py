#!/usr/bin/env python3
"""
Machine Learning Models for Sports Betting

Advanced ML models including:
- Decision Trees and Random Forests
- Gradient Boosting
- Neural Networks
- Ensemble Methods
- Feature Engineering
- Model Validation
- Cross-validation
- Regularization techniques
"""

import math
import random
import statistics
from typing import List, Tuple, Dict, Optional, Callable, Any, Union
from dataclasses import dataclass
from collections import defaultdict, Counter
from enum import Enum


class ActivationFunction(Enum):
    """Neural network activation functions"""
    SIGMOID = "sigmoid"
    RELU = "relu"
    TANH = "tanh"
    LEAKY_RELU = "leaky_relu"


@dataclass
class MLModelResult:
    """Results from ML model"""
    predictions: List[float]
    probabilities: Optional[List[List[float]]]
    feature_importance: Optional[Dict[str, float]]
    accuracy: Optional[float]
    mse: Optional[float]
    r_squared: Optional[float]


@dataclass
class ClassificationMetrics:
    """Classification model evaluation metrics"""
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    confusion_matrix: List[List[int]]
    roc_auc: Optional[float]


@dataclass
class CrossValidationResult:
    """Cross-validation results"""
    fold_scores: List[float]
    mean_score: float
    std_score: float
    best_fold: int
    worst_fold: int


class DecisionTree:
    """Decision tree for classification and regression"""

    def __init__(self, max_depth: int = 10, min_samples_split: int = 2,
                 min_samples_leaf: int = 1, criterion: str = 'gini'):
        """
        Initialize decision tree

        Args:
            max_depth: Maximum tree depth
            min_samples_split: Minimum samples to split a node
            min_samples_leaf: Minimum samples in a leaf node
            criterion: Split criterion ('gini', 'entropy', 'mse')
        """
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.min_samples_leaf = min_samples_leaf
        self.criterion = criterion
        self.tree = None
        self.feature_importance = {}

    def _gini_impurity(self, y: List[int]) -> float:
        """Calculate Gini impurity for classification"""
        if not y:
            return 0

        counts = Counter(y)
        total = len(y)
        impurity = 1.0

        for count in counts.values():
            prob = count / total
            impurity -= prob ** 2

        return impurity

    def _entropy(self, y: List[int]) -> float:
        """Calculate entropy for classification"""
        if not y:
            return 0

        counts = Counter(y)
        total = len(y)
        entropy = 0.0

        for count in counts.values():
            if count > 0:
                prob = count / total
                entropy -= prob * math.log2(prob)

        return entropy

    def _mse(self, y: List[float]) -> float:
        """Calculate MSE for regression"""
        if not y:
            return 0

        mean = statistics.mean(y)
        return sum((val - mean) ** 2 for val in y) / len(y)

    def _calculate_impurity(self, y: Union[List[int], List[float]]) -> float:
        """Calculate impurity based on criterion"""
        if self.criterion == 'gini':
            return self._gini_impurity(y)
        elif self.criterion == 'entropy':
            return self._entropy(y)
        elif self.criterion == 'mse':
            return self._mse(y)
        else:
            raise ValueError(f"Unknown criterion: {self.criterion}")

    def _find_best_split(self, X: List[List[float]], y: List[float],
                        feature_indices: List[int]) -> Tuple[int, float, float]:
        """
        Find the best feature and threshold to split on

        Returns:
            (best_feature, best_threshold, best_gain)
        """
        best_gain = -float('inf')
        best_feature = None
        best_threshold = None

        current_impurity = self._calculate_impurity(y)

        for feature_idx in feature_indices:
            # Get unique values for this feature
            feature_values = sorted(set(row[feature_idx] for row in X))

            # Try splits at midpoints
            for i in range(len(feature_values) - 1):
                threshold = (feature_values[i] + feature_values[i + 1]) / 2

                # Split data
                left_y = [y[j] for j in range(len(X)) if X[j][feature_idx] <= threshold]
                right_y = [y[j] for j in range(len(X)) if X[j][feature_idx] > threshold]

                # Check minimum samples constraint
                if len(left_y) < self.min_samples_leaf or len(right_y) < self.min_samples_leaf:
                    continue

                # Calculate information gain
                n = len(y)
                left_impurity = self._calculate_impurity(left_y)
                right_impurity = self._calculate_impurity(right_y)

                weighted_impurity = (len(left_y) / n * left_impurity +
                                   len(right_y) / n * right_impurity)

                gain = current_impurity - weighted_impurity

                if gain > best_gain:
                    best_gain = gain
                    best_feature = feature_idx
                    best_threshold = threshold

        return best_feature, best_threshold, best_gain

    def _build_tree(self, X: List[List[float]], y: List[float],
                   depth: int, feature_indices: List[int]) -> Dict:
        """Recursively build decision tree"""
        # Check stopping conditions
        if (depth >= self.max_depth or
            len(y) < self.min_samples_split or
            len(set(y)) == 1):
            # Leaf node
            if self.criterion in ['gini', 'entropy']:
                # Classification: return most common class
                value = Counter(y).most_common(1)[0][0]
            else:
                # Regression: return mean
                value = statistics.mean(y)

            return {'leaf': True, 'value': value, 'samples': len(y)}

        # Find best split
        best_feature, best_threshold, best_gain = self._find_best_split(
            X, y, feature_indices
        )

        if best_feature is None or best_gain <= 0:
            # Can't split further
            if self.criterion in ['gini', 'entropy']:
                value = Counter(y).most_common(1)[0][0]
            else:
                value = statistics.mean(y)

            return {'leaf': True, 'value': value, 'samples': len(y)}

        # Update feature importance
        if best_feature not in self.feature_importance:
            self.feature_importance[best_feature] = 0
        self.feature_importance[best_feature] += best_gain * len(y)

        # Split data
        left_indices = [i for i in range(len(X)) if X[i][best_feature] <= best_threshold]
        right_indices = [i for i in range(len(X)) if X[i][best_feature] > best_threshold]

        left_X = [X[i] for i in left_indices]
        left_y = [y[i] for i in left_indices]
        right_X = [X[i] for i in right_indices]
        right_y = [y[i] for i in right_indices]

        # Recursively build subtrees
        return {
            'leaf': False,
            'feature': best_feature,
            'threshold': best_threshold,
            'left': self._build_tree(left_X, left_y, depth + 1, feature_indices),
            'right': self._build_tree(right_X, right_y, depth + 1, feature_indices),
            'samples': len(y)
        }

    def fit(self, X: List[List[float]], y: List[float]) -> None:
        """Train the decision tree"""
        feature_indices = list(range(len(X[0])))
        self.tree = self._build_tree(X, y, 0, feature_indices)

        # Normalize feature importance
        total_importance = sum(self.feature_importance.values())
        if total_importance > 0:
            self.feature_importance = {
                k: v / total_importance
                for k, v in self.feature_importance.items()
            }

    def _predict_one(self, x: List[float], node: Dict) -> float:
        """Predict single sample"""
        if node['leaf']:
            return node['value']

        if x[node['feature']] <= node['threshold']:
            return self._predict_one(x, node['left'])
        else:
            return self._predict_one(x, node['right'])

    def predict(self, X: List[List[float]]) -> List[float]:
        """Make predictions"""
        if self.tree is None:
            raise ValueError("Model not trained. Call fit() first.")

        return [self._predict_one(x, self.tree) for x in X]

    def get_feature_importance(self) -> Dict[int, float]:
        """Get feature importance scores"""
        return self.feature_importance.copy()


class RandomForest:
    """Random Forest ensemble model"""

    def __init__(self, n_trees: int = 100, max_depth: int = 10,
                 min_samples_split: int = 2, max_features: Optional[int] = None,
                 criterion: str = 'gini', bootstrap: bool = True):
        """
        Initialize Random Forest

        Args:
            n_trees: Number of trees in forest
            max_depth: Maximum depth of each tree
            min_samples_split: Minimum samples to split a node
            max_features: Number of features to consider for each split (None = all features)
            criterion: Split criterion
            bootstrap: Whether to use bootstrap sampling
        """
        self.n_trees = n_trees
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.max_features = max_features
        self.criterion = criterion
        self.bootstrap = bootstrap
        self.trees = []
        self.feature_indices = []

    def fit(self, X: List[List[float]], y: List[float]) -> None:
        """Train the random forest"""
        n_samples = len(X)
        n_features = len(X[0])

        if self.max_features is None:
            max_features = int(math.sqrt(n_features))
        else:
            max_features = self.max_features

        self.trees = []
        self.feature_indices = []

        for _ in range(self.n_trees):
            # Bootstrap sampling
            if self.bootstrap:
                indices = [random.randint(0, n_samples - 1) for _ in range(n_samples)]
                X_sample = [X[i] for i in indices]
                y_sample = [y[i] for i in indices]
            else:
                X_sample = X
                y_sample = y

            # Random feature selection
            feature_subset = random.sample(range(n_features), max_features)
            self.feature_indices.append(feature_subset)

            # Create feature-selected data
            X_subset = [[row[i] for i in feature_subset] for row in X_sample]

            # Train tree
            tree = DecisionTree(
                max_depth=self.max_depth,
                min_samples_split=self.min_samples_split,
                criterion=self.criterion
            )
            tree.fit(X_subset, y_sample)
            self.trees.append(tree)

    def predict(self, X: List[List[float]]) -> List[float]:
        """Make predictions by averaging all trees"""
        if not self.trees:
            raise ValueError("Model not trained. Call fit() first.")

        # Get predictions from each tree
        all_predictions = []
        for tree, feature_subset in zip(self.trees, self.feature_indices):
            X_subset = [[row[i] for i in feature_subset] for row in X]
            predictions = tree.predict(X_subset)
            all_predictions.append(predictions)

        # Average predictions (regression) or vote (classification)
        if self.criterion == 'mse':
            # Regression: average
            return [
                statistics.mean(all_predictions[i][j] for i in range(self.n_trees))
                for j in range(len(X))
            ]
        else:
            # Classification: majority vote
            final_predictions = []
            for j in range(len(X)):
                votes = [all_predictions[i][j] for i in range(self.n_trees)]
                final_predictions.append(Counter(votes).most_common(1)[0][0])
            return final_predictions

    def get_feature_importance(self) -> Dict[int, float]:
        """Get aggregated feature importance across all trees"""
        importance = defaultdict(float)

        for tree, feature_subset in zip(self.trees, self.feature_indices):
            tree_importance = tree.get_feature_importance()
            for subset_idx, global_idx in enumerate(feature_subset):
                if subset_idx in tree_importance:
                    importance[global_idx] += tree_importance[subset_idx]

        # Normalize
        total = sum(importance.values())
        if total > 0:
            importance = {k: v / total for k, v in importance.items()}

        return dict(importance)


class NeuralNetwork:
    """Simple feedforward neural network"""

    def __init__(self, layer_sizes: List[int], activation: ActivationFunction = ActivationFunction.SIGMOID,
                 learning_rate: float = 0.1, epochs: int = 100):
        """
        Initialize neural network

        Args:
            layer_sizes: List of layer sizes [input, hidden1, hidden2, ..., output]
            activation: Activation function
            learning_rate: Learning rate for gradient descent
            epochs: Number of training epochs
        """
        self.layer_sizes = layer_sizes
        self.activation = activation
        self.learning_rate = learning_rate
        self.epochs = epochs
        self.weights = []
        self.biases = []

        # Initialize weights and biases
        for i in range(len(layer_sizes) - 1):
            # Xavier initialization
            limit = math.sqrt(6.0 / (layer_sizes[i] + layer_sizes[i + 1]))
            w = [[random.uniform(-limit, limit) for _ in range(layer_sizes[i])]
                 for _ in range(layer_sizes[i + 1])]
            b = [0.0 for _ in range(layer_sizes[i + 1])]

            self.weights.append(w)
            self.biases.append(b)

    def _activate(self, x: float) -> float:
        """Apply activation function"""
        if self.activation == ActivationFunction.SIGMOID:
            return 1 / (1 + math.exp(-max(min(x, 500), -500)))  # Clip to prevent overflow
        elif self.activation == ActivationFunction.RELU:
            return max(0, x)
        elif self.activation == ActivationFunction.TANH:
            return math.tanh(x)
        elif self.activation == ActivationFunction.LEAKY_RELU:
            return x if x > 0 else 0.01 * x
        else:
            return x

    def _activate_derivative(self, x: float) -> float:
        """Derivative of activation function"""
        if self.activation == ActivationFunction.SIGMOID:
            s = self._activate(x)
            return s * (1 - s)
        elif self.activation == ActivationFunction.RELU:
            return 1.0 if x > 0 else 0.0
        elif self.activation == ActivationFunction.TANH:
            t = math.tanh(x)
            return 1 - t * t
        elif self.activation == ActivationFunction.LEAKY_RELU:
            return 1.0 if x > 0 else 0.01
        else:
            return 1.0

    def _forward(self, x: List[float]) -> Tuple[List[List[float]], List[List[float]]]:
        """Forward pass through network"""
        activations = [x]
        z_values = []

        for i in range(len(self.weights)):
            # Compute z = Wx + b
            z = []
            for j in range(len(self.weights[i])):
                val = sum(self.weights[i][j][k] * activations[-1][k]
                         for k in range(len(activations[-1])))
                val += self.biases[i][j]
                z.append(val)

            z_values.append(z)

            # Apply activation
            a = [self._activate(zi) for zi in z]
            activations.append(a)

        return activations, z_values

    def _backward(self, x: List[float], y: float,
                  activations: List[List[float]], z_values: List[List[float]]) -> None:
        """Backward pass to update weights"""
        # Output layer error
        output = activations[-1][0]
        delta = (output - y) * self._activate_derivative(z_values[-1][0])
        deltas = [[delta]]

        # Backpropagate errors
        for i in range(len(self.weights) - 2, -1, -1):
            layer_delta = []
            for j in range(len(self.weights[i])):
                error = sum(deltas[0][k] * self.weights[i + 1][k][j]
                           for k in range(len(deltas[0])))
                layer_delta.append(error * self._activate_derivative(z_values[i][j]))
            deltas.insert(0, layer_delta)

        # Update weights and biases
        for i in range(len(self.weights)):
            for j in range(len(self.weights[i])):
                for k in range(len(self.weights[i][j])):
                    gradient = deltas[i][j] * activations[i][k]
                    self.weights[i][j][k] -= self.learning_rate * gradient

                self.biases[i][j] -= self.learning_rate * deltas[i][j]

    def fit(self, X: List[List[float]], y: List[float]) -> None:
        """Train the neural network"""
        for epoch in range(self.epochs):
            for i in range(len(X)):
                activations, z_values = self._forward(X[i])
                self._backward(X[i], y[i], activations, z_values)

    def predict(self, X: List[List[float]]) -> List[float]:
        """Make predictions"""
        predictions = []
        for x in X:
            activations, _ = self._forward(x)
            predictions.append(activations[-1][0])
        return predictions


@dataclass
class TeamScoringPosterior:
    """Posterior estimates for a team's scoring ability"""
    mean: float
    variance: float
    n_games: int
    total_points: float


class BayesianHierarchicalTotalsModel:
    """
    Bayesian hierarchical model for totals predictions.

    Treats each team's scoring ability as a latent variable drawn from a league-wide
    distribution, then updates team beliefs game by game.

    Args:
        league_mean: Prior mean points per team per game
        league_std: Prior standard deviation of team scoring ability
        game_std: Observation standard deviation per game
    """

    def __init__(self, league_mean: float = 110.0, league_std: float = 12.0,
                 game_std: float = 14.0):
        self.league_mean = league_mean
        self.league_std = league_std
        self.game_std = game_std
        self.team_stats = defaultdict(lambda: {"n": 0, "sum": 0.0})

    def fit(self, games: List[Any]) -> "BayesianHierarchicalTotalsModel":
        """
        Fit model with historical game data.

        Supports:
            - {"team": "BOS", "points": 112}
            - {"home_team": "BOS", "away_team": "NYK", "home_points": 112, "away_points": 105}
            - ("BOS", 112)
            - ("BOS", "NYK", 112, 105)
        """
        for game in games:
            for team, points in self._parse_game(game):
                self.update_game(team, points)
        return self

    def update_game(self, team: str, points: float) -> None:
        """Update model with a single team score observation."""
        stats = self.team_stats[team]
        stats["n"] += 1
        stats["sum"] += float(points)

    def get_team_posterior(self, team: str) -> TeamScoringPosterior:
        """Return posterior mean/variance for a team."""
        stats = self.team_stats.get(team, {"n": 0, "sum": 0.0})
        mean, variance = self._posterior_params(stats["n"], stats["sum"])
        return TeamScoringPosterior(
            mean=mean,
            variance=variance,
            n_games=stats["n"],
            total_points=stats["sum"]
        )

    def predict_total(self, team_a: str, team_b: str, total_line: Optional[float] = None,
                      ci: float = 0.8) -> Dict[str, float]:
        """
        Predict total points distribution for a matchup.

        Returns mean, standard deviation, and a symmetric confidence interval.
        """
        posterior_a = self.get_team_posterior(team_a)
        posterior_b = self.get_team_posterior(team_b)

        mean_total = posterior_a.mean + posterior_b.mean
        total_variance = (
            posterior_a.variance + self.game_std ** 2 +
            posterior_b.variance + self.game_std ** 2
        )
        std_total = math.sqrt(total_variance)

        z_score = self._z_for_ci(ci)
        ci_lower = mean_total - z_score * std_total
        ci_upper = mean_total + z_score * std_total

        result = {
            "mean_total": mean_total,
            "std_total": std_total,
            "ci_lower": ci_lower,
            "ci_upper": ci_upper,
            "team_a_mean": posterior_a.mean,
            "team_b_mean": posterior_b.mean
        }

        if total_line is not None:
            over_prob = self._probability_over(mean_total, std_total, total_line)
            result["over_probability"] = over_prob
            result["under_probability"] = 1 - over_prob

        return result

    def probability_over(self, team_a: str, team_b: str, total_line: float) -> float:
        """Return probability that total points exceeds the line."""
        prediction = self.predict_total(team_a, team_b, total_line=total_line)
        return prediction["over_probability"]

    def _posterior_params(self, n_games: int, total_points: float) -> Tuple[float, float]:
        """Compute conjugate normal posterior for team scoring ability."""
        tau2 = self.league_std ** 2
        sigma2 = self.game_std ** 2

        if n_games == 0:
            return self.league_mean, tau2

        sample_mean = total_points / n_games
        posterior_variance = 1.0 / (1.0 / tau2 + n_games / sigma2)
        posterior_mean = posterior_variance * (
            self.league_mean / tau2 + n_games * sample_mean / sigma2
        )

        return posterior_mean, posterior_variance

    def _parse_game(self, game: Any) -> List[Tuple[str, float]]:
        """Normalize supported game formats into (team, points) pairs."""
        if isinstance(game, dict):
            if "team" in game:
                points = game.get("points", game.get("score"))
                if points is None:
                    raise ValueError("Game dict with 'team' must include 'points' or 'score'.")
                return [(game["team"], float(points))]

            if "home_team" in game and "away_team" in game:
                home_points = game.get("home_points", game.get("home_score"))
                away_points = game.get("away_points", game.get("away_score"))
                if home_points is None or away_points is None:
                    raise ValueError("Home/away game dict must include points or score fields.")
                return [
                    (game["home_team"], float(home_points)),
                    (game["away_team"], float(away_points))
                ]

        if isinstance(game, (list, tuple)):
            if len(game) == 2:
                team, points = game
                return [(team, float(points))]
            if len(game) == 4:
                home_team, away_team, home_points, away_points = game
                return [
                    (home_team, float(home_points)),
                    (away_team, float(away_points))
                ]

        raise ValueError("Unsupported game format for Bayesian hierarchical totals model.")

    @staticmethod
    def _z_for_ci(ci: float) -> float:
        """Return z-score for common confidence intervals."""
        z_map = {
            0.8: 1.2816,
            0.9: 1.6449,
            0.95: 1.96,
            0.99: 2.576
        }
        return z_map.get(ci, 1.96)

    @staticmethod
    def _probability_over(mean_total: float, std_total: float, total_line: float) -> float:
        """Compute probability of total exceeding a line under a normal assumption."""
        if std_total <= 0:
            return 1.0 if mean_total > total_line else 0.0
        z = (total_line - mean_total) / (std_total * math.sqrt(2))
        cdf = 0.5 * (1 + math.erf(z))
        return max(0.0, min(1.0, 1 - cdf))


class FeatureEngineering:
    """Feature engineering utilities for sports betting"""

    @staticmethod
    def create_polynomial_features(X: List[List[float]], degree: int = 2) -> List[List[float]]:
        """
        Create polynomial features up to specified degree

        Args:
            X: Input features [n_samples x n_features]
            degree: Polynomial degree

        Returns:
            Expanded feature matrix
        """
        if degree < 1:
            raise ValueError("Degree must be at least 1")

        result = []
        for row in X:
            new_row = list(row)  # Original features

            # Add polynomial features
            if degree >= 2:
                # Squared terms
                for val in row:
                    new_row.append(val ** 2)

                # Interaction terms
                for i in range(len(row)):
                    for j in range(i + 1, len(row)):
                        new_row.append(row[i] * row[j])

            if degree >= 3:
                # Cubic terms
                for val in row:
                    new_row.append(val ** 3)

            result.append(new_row)

        return result

    @staticmethod
    def normalize_features(X: List[List[float]], method: str = 'standard') -> Tuple[List[List[float]], Dict]:
        """
        Normalize features

        Args:
            X: Input features
            method: 'standard' (z-score) or 'minmax' (0-1 scaling)

        Returns:
            Normalized features and scaling parameters
        """
        n_features = len(X[0])
        params = {}

        if method == 'standard':
            # Calculate mean and std for each feature
            for j in range(n_features):
                col = [X[i][j] for i in range(len(X))]
                mean = statistics.mean(col)
                std = statistics.stdev(col) if len(col) > 1 else 1.0
                params[j] = {'mean': mean, 'std': std if std > 0 else 1.0}

            # Normalize
            result = []
            for row in X:
                new_row = [
                    (row[j] - params[j]['mean']) / params[j]['std']
                    for j in range(n_features)
                ]
                result.append(new_row)

        elif method == 'minmax':
            # Calculate min and max for each feature
            for j in range(n_features):
                col = [X[i][j] for i in range(len(X))]
                min_val = min(col)
                max_val = max(col)
                params[j] = {'min': min_val, 'max': max_val,
                           'range': max_val - min_val if max_val != min_val else 1.0}

            # Normalize
            result = []
            for row in X:
                new_row = [
                    (row[j] - params[j]['min']) / params[j]['range']
                    for j in range(n_features)
                ]
                result.append(new_row)

        else:
            raise ValueError(f"Unknown normalization method: {method}")

        return result, params

    @staticmethod
    def create_lag_features(data: List[float], lags: List[int]) -> List[List[float]]:
        """
        Create lagged features for time series

        Args:
            data: Time series data
            lags: List of lag periods [1, 2, 3, ...]

        Returns:
            Feature matrix with lagged values
        """
        max_lag = max(lags)
        result = []

        for i in range(max_lag, len(data)):
            row = [data[i]]  # Current value
            for lag in lags:
                row.append(data[i - lag])
            result.append(row)

        return result

    @staticmethod
    def create_rolling_features(data: List[float], windows: List[int]) -> List[List[float]]:
        """
        Create rolling window statistics features

        Args:
            data: Time series data
            windows: List of window sizes

        Returns:
            Feature matrix with rolling statistics
        """
        max_window = max(windows)
        result = []

        for i in range(max_window, len(data) + 1):
            row = []
            for window in windows:
                window_data = data[i - window:i]
                row.extend([
                    statistics.mean(window_data),
                    statistics.stdev(window_data) if len(window_data) > 1 else 0,
                    min(window_data),
                    max(window_data)
                ])
            result.append(row)

        return result

    @staticmethod
    def select_features_correlation(X: List[List[float]], y: List[float],
                                    threshold: float = 0.1) -> List[int]:
        """
        Select features based on correlation with target

        Args:
            X: Input features
            y: Target variable
            threshold: Minimum absolute correlation to keep feature

        Returns:
            List of selected feature indices
        """
        n_features = len(X[0])
        selected = []

        for j in range(n_features):
            # Calculate correlation between feature j and target
            x_col = [X[i][j] for i in range(len(X))]

            # Pearson correlation
            n = len(x_col)
            mean_x = statistics.mean(x_col)
            mean_y = statistics.mean(y)

            numerator = sum((x_col[i] - mean_x) * (y[i] - mean_y) for i in range(n))

            var_x = sum((x - mean_x) ** 2 for x in x_col)
            var_y = sum((yi - mean_y) ** 2 for yi in y)

            if var_x > 0 and var_y > 0:
                correlation = numerator / math.sqrt(var_x * var_y)

                if abs(correlation) >= threshold:
                    selected.append(j)

        return selected


class ModelValidation:
    """Model validation and evaluation utilities"""

    @staticmethod
    def train_test_split(X: List[List[float]], y: List[float],
                        test_size: float = 0.2, shuffle: bool = True,
                        random_seed: Optional[int] = None) -> Tuple:
        """
        Split data into training and testing sets

        Args:
            X: Features
            y: Labels
            test_size: Proportion of data for testing (0-1)
            shuffle: Whether to shuffle before splitting
            random_seed: Random seed for reproducibility

        Returns:
            X_train, X_test, y_train, y_test
        """
        if random_seed is not None:
            random.seed(random_seed)

        n_samples = len(X)
        n_test = int(n_samples * test_size)

        indices = list(range(n_samples))
        if shuffle:
            random.shuffle(indices)

        test_indices = indices[:n_test]
        train_indices = indices[n_test:]

        X_train = [X[i] for i in train_indices]
        X_test = [X[i] for i in test_indices]
        y_train = [y[i] for i in train_indices]
        y_test = [y[i] for i in test_indices]

        return X_train, X_test, y_train, y_test

    @staticmethod
    def k_fold_cross_validation(X: List[List[float]], y: List[float],
                                model_class, model_params: Dict,
                                k: int = 5, scoring: str = 'accuracy') -> CrossValidationResult:
        """
        Perform k-fold cross-validation

        Args:
            X: Features
            y: Labels
            model_class: Model class to instantiate
            model_params: Parameters for model initialization
            k: Number of folds
            scoring: Scoring metric ('accuracy', 'mse', 'r2')

        Returns:
            CrossValidationResult with fold scores
        """
        n_samples = len(X)
        fold_size = n_samples // k
        indices = list(range(n_samples))
        random.shuffle(indices)

        fold_scores = []

        for fold in range(k):
            # Create train/val split
            val_start = fold * fold_size
            val_end = val_start + fold_size if fold < k - 1 else n_samples

            val_indices = indices[val_start:val_end]
            train_indices = indices[:val_start] + indices[val_end:]

            X_train = [X[i] for i in train_indices]
            X_val = [X[i] for i in val_indices]
            y_train = [y[i] for i in train_indices]
            y_val = [y[i] for i in val_indices]

            # Train model
            model = model_class(**model_params)
            model.fit(X_train, y_train)

            # Evaluate
            predictions = model.predict(X_val)

            if scoring == 'accuracy':
                correct = sum(1 for i in range(len(y_val))
                            if abs(predictions[i] - y_val[i]) < 0.5)
                score = correct / len(y_val)
            elif scoring == 'mse':
                score = -statistics.mean((predictions[i] - y_val[i]) ** 2
                                        for i in range(len(y_val)))
            elif scoring == 'r2':
                mean_y = statistics.mean(y_val)
                ss_res = sum((y_val[i] - predictions[i]) ** 2 for i in range(len(y_val)))
                ss_tot = sum((y_val[i] - mean_y) ** 2 for i in range(len(y_val)))
                score = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
            else:
                raise ValueError(f"Unknown scoring metric: {scoring}")

            fold_scores.append(score)

        mean_score = statistics.mean(fold_scores)
        std_score = statistics.stdev(fold_scores) if len(fold_scores) > 1 else 0
        best_fold = fold_scores.index(max(fold_scores))
        worst_fold = fold_scores.index(min(fold_scores))

        return CrossValidationResult(
            fold_scores=fold_scores,
            mean_score=mean_score,
            std_score=std_score,
            best_fold=best_fold,
            worst_fold=worst_fold
        )

    @staticmethod
    def calculate_classification_metrics(y_true: List[int], y_pred: List[int],
                                        n_classes: int = 2) -> ClassificationMetrics:
        """
        Calculate comprehensive classification metrics

        Args:
            y_true: True labels
            y_pred: Predicted labels
            n_classes: Number of classes

        Returns:
            ClassificationMetrics with various evaluation metrics
        """
        # Confusion matrix
        confusion = [[0] * n_classes for _ in range(n_classes)]
        for i in range(len(y_true)):
            confusion[int(y_true[i])][int(y_pred[i])] += 1

        # Binary classification metrics
        if n_classes == 2:
            tp = confusion[1][1]
            tn = confusion[0][0]
            fp = confusion[0][1]
            fn = confusion[1][0]

            accuracy = (tp + tn) / len(y_true) if len(y_true) > 0 else 0
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        else:
            # Multiclass metrics (macro average)
            total_correct = sum(confusion[i][i] for i in range(n_classes))
            accuracy = total_correct / len(y_true) if len(y_true) > 0 else 0

            precisions = []
            recalls = []

            for i in range(n_classes):
                tp = confusion[i][i]
                fp = sum(confusion[j][i] for j in range(n_classes) if j != i)
                fn = sum(confusion[i][j] for j in range(n_classes) if j != i)

                p = tp / (tp + fp) if (tp + fp) > 0 else 0
                r = tp / (tp + fn) if (tp + fn) > 0 else 0

                precisions.append(p)
                recalls.append(r)

            precision = statistics.mean(precisions)
            recall = statistics.mean(recalls)
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

        return ClassificationMetrics(
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1,
            confusion_matrix=confusion,
            roc_auc=None  # Would need probability predictions
        )

    @staticmethod
    def calculate_regression_metrics(y_true: List[float], y_pred: List[float]) -> Dict[str, float]:
        """
        Calculate regression metrics

        Returns:
            Dictionary with MSE, RMSE, MAE, R²
        """
        n = len(y_true)

        # MSE and RMSE
        mse = sum((y_true[i] - y_pred[i]) ** 2 for i in range(n)) / n
        rmse = math.sqrt(mse)

        # MAE
        mae = sum(abs(y_true[i] - y_pred[i]) for i in range(n)) / n

        # R²
        mean_y = statistics.mean(y_true)
        ss_res = sum((y_true[i] - y_pred[i]) ** 2 for i in range(n))
        ss_tot = sum((y_true[i] - mean_y) ** 2 for i in range(n))
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

        return {
            'mse': mse,
            'rmse': rmse,
            'mae': mae,
            'r_squared': r_squared
        }


# Example usage and integration with sports betting

def predict_game_outcome_ml(team_stats: Dict[str, List[float]],
                            historical_results: List[int]) -> Dict[str, Any]:
    """
    Example: Use ML models to predict game outcome

    Args:
        team_stats: Dictionary of team statistics (features)
        historical_results: Past game results (labels)

    Returns:
        Predictions and model evaluation
    """
    # Prepare features
    X = []
    for key in sorted(team_stats.keys()):
        X.append(team_stats[key])

    # Transpose to get [n_samples x n_features]
    n_samples = len(X[0])
    X_formatted = [[X[j][i] for j in range(len(X))] for i in range(n_samples)]

    # Split data
    X_train, X_test, y_train, y_test = ModelValidation.train_test_split(
        X_formatted, historical_results, test_size=0.2, random_seed=42
    )

    # Train Random Forest
    rf = RandomForest(n_trees=50, max_depth=8, criterion='gini')
    rf.fit(X_train, y_train)
    predictions = rf.predict(X_test)

    # Evaluate
    metrics = ModelValidation.calculate_classification_metrics(y_test, predictions)

    return {
        'predictions': predictions,
        'accuracy': metrics.accuracy,
        'precision': metrics.precision,
        'recall': metrics.recall,
        'f1_score': metrics.f1_score,
        'confusion_matrix': metrics.confusion_matrix,
        'feature_importance': rf.get_feature_importance()
    }
