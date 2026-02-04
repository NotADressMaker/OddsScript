#!/usr/bin/env python3
"""
ML Model Builder - Simplified Interface

Easy-to-use interface for building machine learning models for sports betting.
"""

from typing import List, Dict, Optional, Tuple, Any
import random
from lib.ml_models import (
    RandomForest, DecisionTree, NeuralNetwork,
    FeatureEngineering, ModelValidation, ActivationFunction
)
from lib.advanced_stats import AdvancedStats


class Model:
    """
    Fluent API for building ML models

    Makes it easy to build, train, and evaluate models for sports betting.

    Example:
        >>> model = (Model()
        ...          .for_classification()
        ...          .using_random_forest(n_trees=100)
        ...          .with_features(['team_rating', 'opponent_rating', 'home'])
        ...          .train(X_train, y_train))
        >>>
        >>> predictions = model.predict(X_test)
        >>> model.print_performance(y_test)
    """

    def __init__(self):
        self.model_type = None
        self.model = None
        self.task = 'classification'  # or 'regression'
        self.feature_names = []
        self.training_data = None
        self.is_trained = False
        self._name = "Model"
        self._normalize = False
        self._normalization_params = None

    def named(self, name: str):
        """Give the model a name"""
        self._name = name
        return self

    def for_classification(self):
        """Set task to classification (win/loss, cover/no cover)"""
        self.task = 'classification'
        return self

    def for_regression(self):
        """Set task to regression (predict points, margins, etc.)"""
        self.task = 'regression'
        return self

    def using_random_forest(self, n_trees: int = 100, max_depth: int = 10):
        """
        Use Random Forest model

        Args:
            n_trees: Number of trees (more = better but slower)
            max_depth: Maximum tree depth
        """
        criterion = 'gini' if self.task == 'classification' else 'mse'
        self.model = RandomForest(
            n_trees=n_trees,
            max_depth=max_depth,
            criterion=criterion
        )
        self.model_type = 'random_forest'
        return self

    def using_decision_tree(self, max_depth: int = 10):
        """
        Use Decision Tree model

        Args:
            max_depth: Maximum tree depth
        """
        criterion = 'gini' if self.task == 'classification' else 'mse'
        self.model = DecisionTree(
            max_depth=max_depth,
            criterion=criterion
        )
        self.model_type = 'decision_tree'
        return self

    def using_neural_network(self, hidden_layers: List[int] = None,
                            learning_rate: float = 0.1, epochs: int = 1000):
        """
        Use Neural Network model

        Args:
            hidden_layers: List of hidden layer sizes (e.g., [10, 5])
            learning_rate: Learning rate
            epochs: Training epochs
        """
        if hidden_layers is None:
            hidden_layers = [10, 5]

        # Will set input/output layers when training
        self.model = {
            'type': 'neural_network',
            'hidden_layers': hidden_layers,
            'learning_rate': learning_rate,
            'epochs': epochs
        }
        self.model_type = 'neural_network'
        return self

    def with_features(self, feature_names: List[str]):
        """
        Set feature names for documentation

        Args:
            feature_names: List of feature names
        """
        self.feature_names = feature_names
        return self

    def with_normalization(self, method: str = 'standard'):
        """
        Enable feature normalization

        Args:
            method: 'standard' (z-score) or 'minmax' (0-1 scaling)
        """
        self._normalize = True
        self._normalization_method = method
        return self

    def train(self, X: List[List[float]], y: List[float]):
        """
        Train the model

        Args:
            X: Training features [n_samples x n_features]
            y: Training labels
        """
        if self.model is None:
            raise ValueError("No model selected. Use .using_random_forest() or similar")

        # Normalize if requested
        if self._normalize:
            X, self._normalization_params = FeatureEngineering.normalize_features(
                X, method=self._normalization_method
            )

        # Handle neural network (needs layer sizes)
        if self.model_type == 'neural_network':
            n_features = len(X[0])
            layer_sizes = (
                [n_features] +
                self.model['hidden_layers'] +
                [1]
            )

            self.model = NeuralNetwork(
                layer_sizes=layer_sizes,
                learning_rate=self.model['learning_rate'],
                epochs=self.model['epochs']
            )

        # Train
        self.model.fit(X, y)
        self.training_data = (X, y)
        self.is_trained = True

        return self

    def predict(self, X: List[List[float]]) -> List[float]:
        """
        Make predictions

        Args:
            X: Features to predict on

        Returns:
            Predictions
        """
        if not self.is_trained:
            raise ValueError("Model not trained. Call .train() first")

        # Normalize if needed
        if self._normalize and self._normalization_params:
            X_normalized = []
            for row in X:
                normalized_row = [
                    (row[j] - self._normalization_params[j]['mean']) /
                    self._normalization_params[j]['std']
                    for j in range(len(row))
                ]
                X_normalized.append(normalized_row)
            X = X_normalized

        return self.model.predict(X)

    def predict_proba(self, X: List[List[float]]) -> List[float]:
        """
        Predict probabilities (for classification)

        For Random Forest/Decision Tree, returns class predictions.
        For Neural Network, returns probabilities.
        """
        predictions = self.predict(X)

        # For neural networks, predictions are already probabilities
        if self.model_type == 'neural_network':
            return predictions

        # For tree models, convert to binary probabilities
        return predictions

    def evaluate(self, X_test: List[List[float]], y_test: List[float]) -> Dict:
        """
        Evaluate model performance

        Args:
            X_test: Test features
            y_test: Test labels

        Returns:
            Performance metrics
        """
        predictions = self.predict(X_test)

        if self.task == 'classification':
            # Classification metrics
            metrics = ModelValidation.calculate_classification_metrics(
                y_test, predictions, n_classes=2
            )
            return {
                'accuracy': metrics.accuracy,
                'precision': metrics.precision,
                'recall': metrics.recall,
                'f1_score': metrics.f1_score,
                'confusion_matrix': metrics.confusion_matrix
            }
        else:
            # Regression metrics
            return ModelValidation.calculate_regression_metrics(y_test, predictions)

    def cross_validate(self, X: List[List[float]], y: List[float],
                      k: int = 5) -> Dict:
        """
        Perform k-fold cross-validation

        Args:
            X: Features
            y: Labels
            k: Number of folds

        Returns:
            Cross-validation results
        """
        # Determine model class and params
        if self.model_type == 'random_forest':
            model_class = RandomForest
            params = {
                'n_trees': self.model.n_trees,
                'max_depth': self.model.max_depth,
                'criterion': self.model.criterion
            }
        elif self.model_type == 'decision_tree':
            model_class = DecisionTree
            params = {
                'max_depth': self.model.max_depth,
                'criterion': self.model.criterion
            }
        else:
            raise ValueError("Cross-validation not implemented for neural networks")

        scoring = 'accuracy' if self.task == 'classification' else 'r2'

        result = ModelValidation.k_fold_cross_validation(
            X, y, model_class, params, k=k, scoring=scoring
        )

        return {
            'mean_score': result.mean_score,
            'std_score': result.std_score,
            'fold_scores': result.fold_scores
        }

    def feature_importance(self) -> Dict[str, float]:
        """
        Get feature importance scores

        Returns:
            Dictionary mapping feature names to importance
        """
        if not self.is_trained:
            raise ValueError("Model not trained")

        if self.model_type in ['random_forest', 'decision_tree']:
            importance = self.model.get_feature_importance()

            if self.feature_names:
                return {
                    self.feature_names[i]: importance.get(i, 0)
                    for i in range(len(self.feature_names))
                }
            return importance
        else:
            return {}  # Neural networks don't have feature importance

    def print_performance(self, X_test: List[List[float]],
                         y_test: List[float]):
        """Print formatted performance report"""
        metrics = self.evaluate(X_test, y_test)

        print(f"\n{'='*60}")
        print(f"MODEL PERFORMANCE: {self._name}")
        print(f"{'='*60}")
        print(f"Model Type: {self.model_type.replace('_', ' ').title()}")
        print(f"Task: {self.task.title()}")

        if self.task == 'classification':
            print(f"\nAccuracy:  {metrics['accuracy']:.3f}")
            print(f"Precision: {metrics['precision']:.3f}")
            print(f"Recall:    {metrics['recall']:.3f}")
            print(f"F1 Score:  {metrics['f1_score']:.3f}")

            print(f"\nConfusion Matrix:")
            for row in metrics['confusion_matrix']:
                print(f"  {row}")
        else:
            print(f"\nR²:   {metrics['r_squared']:.3f}")
            print(f"RMSE: {metrics['rmse']:.3f}")
            print(f"MAE:  {metrics['mae']:.3f}")

        # Feature importance
        if self.model_type in ['random_forest', 'decision_tree']:
            importance = self.feature_importance()
            if importance:
                print(f"\nFeature Importance:")
                sorted_features = sorted(
                    importance.items(),
                    key=lambda x: x[1],
                    reverse=True
                )
                for name, score in sorted_features:
                    print(f"  {name}: {score:.3f}")

        print(f"{'='*60}\n")

        return self

    def add_on(self, X: List[List[float]], y: List[float],
               name: Optional[str] = None, n_trees: int = 50,
               max_depth: int = 6, normalize: Optional[str] = 'standard'):
        """
        Train an add-on model that learns the residuals from this model.

        This creates a simple "addition model" that improves the base model
        by fitting a second model to the leftover error.

        Args:
            X: Training features
            y: Training labels
            name: Optional name for the add-on model
            n_trees: Number of trees for the add-on Random Forest
            max_depth: Max depth for the add-on Random Forest
            normalize: Feature normalization method ('standard', 'minmax', or None)

        Returns:
            AdditiveModel that combines base + add-on predictions
        """
        if not self.is_trained:
            raise ValueError("Base model not trained. Call .train() first")

        base_predictions = self.predict(X)
        residuals = [
            y[i] - base_predictions[i]
            for i in range(len(y))
        ]

        add_on_model = (Model()
                        .named(name or f"{self._name} Add-On")
                        .for_regression()
                        .using_random_forest(n_trees=n_trees, max_depth=max_depth))

        if normalize:
            add_on_model.with_normalization(normalize)

        add_on_model.train(X, residuals)

        return AdditiveModel(self, add_on_model)


class AdditiveModel:
    """
    Combines a base model with an add-on residual model.

    The final prediction is base_prediction + residual_prediction.
    """

    def __init__(self, base_model: Model, residual_model: Model):
        self.base_model = base_model
        self.residual_model = residual_model
        self.task = base_model.task
        self._name = f"{base_model._name} + {residual_model._name}"

    def _combined_predictions(self, X: List[List[float]]) -> List[float]:
        base_predictions = self.base_model.predict(X)
        residual_predictions = self.residual_model.predict(X)
        return [
            base_predictions[i] + residual_predictions[i]
            for i in range(len(base_predictions))
        ]

    def predict(self, X: List[List[float]]) -> List[float]:
        """
        Return predictions for the combined model.

        For classification, returns class labels (0/1).
        For regression, returns numeric predictions.
        """
        combined = self._combined_predictions(X)

        if self.task == 'classification':
            return [1 if value >= 0.5 else 0 for value in combined]

        return combined

    def predict_proba(self, X: List[List[float]]) -> List[float]:
        """
        Return probabilities for classification, or numeric predictions for regression.
        """
        combined = self._combined_predictions(X)

        if self.task == 'classification':
            return [min(1.0, max(0.0, value)) for value in combined]

        return combined

    def evaluate(self, X_test: List[List[float]], y_test: List[float]) -> Dict:
        """
        Evaluate combined model performance.
        """
        predictions = self.predict(X_test)

        if self.task == 'classification':
            metrics = ModelValidation.calculate_classification_metrics(
                y_test, predictions, n_classes=2
            )
            return {
                'accuracy': metrics.accuracy,
                'precision': metrics.precision,
                'recall': metrics.recall,
                'f1_score': metrics.f1_score,
                'confusion_matrix': metrics.confusion_matrix
            }

        return ModelValidation.calculate_regression_metrics(y_test, predictions)


class ModelBuilder:
    """
    Helper class for common model building scenarios

    Provides templates for common sports betting models.
    """

    @staticmethod
    def game_prediction_model(feature_names: List[str] = None) -> Model:
        """
        Create a model for predicting game outcomes (win/loss)

        Args:
            feature_names: List of feature names

        Returns:
            Configured Model instance
        """
        model = (Model()
                .named("Game Prediction")
                .for_classification()
                .using_random_forest(n_trees=100, max_depth=10)
                .with_normalization('standard'))

        if feature_names:
            model.with_features(feature_names)

        return model

    @staticmethod
    def spread_model(feature_names: List[str] = None) -> Model:
        """
        Create a model for predicting if team covers spread

        Args:
            feature_names: List of feature names

        Returns:
            Configured Model instance
        """
        model = (Model()
                .named("Spread Coverage")
                .for_classification()
                .using_random_forest(n_trees=150, max_depth=12)
                .with_normalization('standard'))

        if feature_names:
            model.with_features(feature_names)

        return model

    @staticmethod
    def total_points_model(feature_names: List[str] = None) -> Model:
        """
        Create a model for predicting total points scored

        Args:
            feature_names: List of feature names

        Returns:
            Configured Model instance
        """
        model = (Model()
                .named("Total Points")
                .for_regression()
                .using_random_forest(n_trees=100, max_depth=15)
                .with_normalization('standard'))

        if feature_names:
            model.with_features(feature_names)

        return model

    @staticmethod
    def player_props_model(feature_names: List[str] = None) -> Model:
        """
        Create a model for predicting player props (points, rebounds, etc.)

        Args:
            feature_names: List of feature names

        Returns:
            Configured Model instance
        """
        model = (Model()
                .named("Player Props")
                .for_regression()
                .using_random_forest(n_trees=80, max_depth=12)
                .with_normalization('minmax'))

        if feature_names:
            model.with_features(feature_names)

        return model

    @staticmethod
    def quick_model(X_train: List[List[float]], y_train: List[float],
                   task: str = 'classification') -> Model:
        """
        Create and train a quick model with defaults

        Args:
            X_train: Training features
            y_train: Training labels
            task: 'classification' or 'regression'

        Returns:
            Trained model
        """
        if task == 'classification':
            model = (Model()
                    .for_classification()
                    .using_random_forest(n_trees=50, max_depth=8)
                    .train(X_train, y_train))
        else:
            model = (Model()
                    .for_regression()
                    .using_random_forest(n_trees=50, max_depth=10)
                    .train(X_train, y_train))

        return model


class DataHelper:
    """
    Helper for preparing training data
    """

    @staticmethod
    def split_data(X: List[List[float]], y: List[float],
                   test_size: float = 0.2) -> Tuple:
        """
        Split data into train and test sets

        Args:
            X: Features
            y: Labels
            test_size: Fraction for test set (0-1)

        Returns:
            (X_train, X_test, y_train, y_test)
        """
        return ModelValidation.train_test_split(
            X, y, test_size=test_size, shuffle=True, random_seed=42
        )

    @staticmethod
    def add_polynomial_features(X: List[List[float]], degree: int = 2):
        """
        Add polynomial features (squares, interactions)

        Args:
            X: Original features
            degree: Polynomial degree

        Returns:
            Expanded features
        """
        return FeatureEngineering.create_polynomial_features(X, degree=degree)

    @staticmethod
    def add_rolling_stats(data: List[float], windows: List[int] = None):
        """
        Add rolling window statistics

        Args:
            data: Time series data
            windows: Window sizes (default [3, 5, 10])

        Returns:
            Features with rolling stats
        """
        if windows is None:
            windows = [3, 5, 10]

        return FeatureEngineering.create_rolling_features(data, windows)

    @staticmethod
    def normalize(X: List[List[float]], method: str = 'standard'):
        """
        Normalize features

        Args:
            X: Features
            method: 'standard' or 'minmax'

        Returns:
            (normalized_features, normalization_params)
        """
        return FeatureEngineering.normalize_features(X, method=method)

    @staticmethod
    def create_sample_data(n_samples: int = 100,
                          task: str = 'classification') -> Tuple:
        """
        Create sample data for testing

        Args:
            n_samples: Number of samples
            task: 'classification' or 'regression'

        Returns:
            (X, y)
        """
        random.seed(42)
        X = []
        y = []

        for _ in range(n_samples):
            # Features: [team_rating, opponent_rating, home]
            team_rating = random.uniform(1200, 1800)
            opp_rating = random.uniform(1200, 1800)
            home = random.choice([0, 1])

            X.append([team_rating, opp_rating, home])

            if task == 'classification':
                # Win probability based on rating difference
                rating_diff = team_rating - opp_rating + (50 if home else 0)
                win_prob = 1 / (1 + 10 ** (-rating_diff / 400))
                y.append(1 if random.random() < win_prob else 0)
            else:
                # Point margin
                rating_diff = team_rating - opp_rating + (50 if home else 0)
                margin = rating_diff / 25 + random.gauss(0, 5)
                y.append(margin)

        return X, y


# Convenient aliases
def build_model() -> Model:
    """Create a new model builder"""
    return Model()


def quick_model(X_train, y_train, task='classification') -> Model:
    """Quick model with defaults"""
    return ModelBuilder.quick_model(X_train, y_train, task)

def add_on_model(base_model: Model, X, y,
                 name: Optional[str] = None,
                 n_trees: int = 50,
                 max_depth: int = 6,
                 normalize: Optional[str] = 'standard') -> AdditiveModel:
    """
    Build an add-on (residual) model on top of a trained base model.

    Args:
        base_model: Trained Model instance
        X: Training features
        y: Training labels
        name: Optional name for the add-on model
        n_trees: Number of trees for the add-on Random Forest
        max_depth: Max depth for the add-on Random Forest
        normalize: Feature normalization method ('standard', 'minmax', or None)
    """
    return base_model.add_on(
        X, y,
        name=name,
        n_trees=n_trees,
        max_depth=max_depth,
        normalize=normalize
    )


def split_data(X, y, test_size=0.2):
    """Split data into train/test"""
    return DataHelper.split_data(X, y, test_size)
