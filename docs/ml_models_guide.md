# Machine Learning Models Guide

Complete guide to using machine learning models for sports betting predictions in SportsBetLang.

## Table of Contents

- [Overview](#overview)
- [Decision Trees](#decision-trees)
- [Random Forests](#random-forests)
- [Neural Networks](#neural-networks)
- [Bayesian Hierarchical Models](#bayesian-hierarchical-models)
- [Feature Engineering](#feature-engineering)
- [Model Validation](#model-validation)
- [Complete Examples](#complete-examples)
- [Best Practices](#best-practices)
- [Integration with Advanced Stats](#integration-with-advanced-stats)

## Overview

The ML models library provides sophisticated machine learning algorithms specifically designed for sports betting analytics:

- **Decision Trees**: Interpretable models for classification and regression
- **Random Forests**: Ensemble methods for robust predictions
- **Neural Networks**: Deep learning for complex patterns
- **Feature Engineering**: Tools to create and select powerful features
- **Model Validation**: Cross-validation and evaluation metrics

## Decision Trees

Decision trees create interpretable models by learning decision rules from data.

### Basic Usage

```python
from lib.ml_models import DecisionTree

# Prepare data
# Features: [offensive_rating, defensive_rating, home_advantage]
X_train = [
    [8.5, 7.2, 1],
    [6.8, 8.1, 0],
    [7.9, 6.5, 1],
    [5.2, 7.8, 0]
]
y_train = [1, 0, 1, 0]  # Win/Loss

# Train classifier
tree = DecisionTree(max_depth=5, criterion='gini')
tree.fit(X_train, y_train)

# Make predictions
X_test = [[7.5, 7.0, 1]]
predictions = tree.predict(X_test)
print(f"Predicted outcome: {predictions[0]}")
```

### Parameters

- **max_depth**: Maximum tree depth (prevents overfitting)
- **min_samples_split**: Minimum samples required to split a node
- **min_samples_leaf**: Minimum samples required in a leaf node
- **criterion**: Split criterion ('gini', 'entropy' for classification; 'mse' for regression)

### Feature Importance

```python
# Get feature importance scores
importance = tree.get_feature_importance()

feature_names = ['Offense', 'Defense', 'Home']
for idx, name in enumerate(feature_names):
    score = importance.get(idx, 0)
    print(f"{name}: {score:.3f}")
```

### Regression Example

```python
# Predict points scored
X_train = [[30, 0.25], [35, 0.30], [25, 0.20]]  # [minutes, usage_rate]
y_train = [15.5, 22.3, 12.1]  # Points scored

tree = DecisionTree(max_depth=10, criterion='mse')
tree.fit(X_train, y_train)

X_test = [[32, 0.28]]
predicted_points = tree.predict(X_test)
print(f"Predicted points: {predicted_points[0]:.1f}")
```

## Random Forests

Random Forests are ensemble models that combine multiple decision trees for more robust predictions.

### Basic Usage

```python
from lib.ml_models import RandomForest

# Train Random Forest classifier
rf = RandomForest(
    n_trees=100,
    max_depth=10,
    max_features=None,  # Auto-select sqrt(n_features)
    criterion='gini',
    bootstrap=True
)

rf.fit(X_train, y_train)
predictions = rf.predict(X_test)
```

### Parameters

- **n_trees**: Number of trees in the forest (more trees = more stable but slower)
- **max_depth**: Maximum depth of each tree
- **max_features**: Number of features to consider for each split
- **bootstrap**: Whether to use bootstrap sampling
- **criterion**: Split criterion ('gini', 'entropy', 'mse')

### NFL Game Prediction Example

```python
import random
from lib.ml_models import RandomForest, ModelValidation

# Generate training data
X_train = []
y_train = []

for i in range(200):
    # Features: [team_elo, opponent_elo, home, rest_days]
    team_elo = random.uniform(1300, 1700)
    opp_elo = random.uniform(1300, 1700)
    home = random.choice([0, 1])
    rest = random.randint(3, 10)

    # Win probability based on ELO difference + home advantage
    elo_diff = team_elo - opp_elo
    home_bonus = 50 if home else 0
    win_prob = 1 / (1 + 10 ** (-(elo_diff + home_bonus) / 400))

    outcome = 1 if random.random() < win_prob else 0

    X_train.append([team_elo, opp_elo, home, rest])
    y_train.append(outcome)

# Train model
rf = RandomForest(n_trees=50, max_depth=8)
rf.fit(X_train, y_train)

# Predict next game
X_next = [[1580, 1520, 1, 7]]  # Home team with slight ELO advantage
pred = rf.predict(X_next)
print(f"Win probability: {pred[0]}")

# Feature importance
importance = rf.get_feature_importance()
features = ['Team ELO', 'Opponent ELO', 'Home', 'Rest Days']
for idx, name in enumerate(features):
    print(f"{name}: {importance.get(idx, 0):.3f}")
```

### Regression with Random Forest

```python
# Predict total points in a game
X_train = []
y_train = []

for i in range(150):
    # Features: [team_avg_points, opp_avg_points, pace, total_line]
    team_pts = random.uniform(20, 32)
    opp_pts = random.uniform(20, 32)
    pace = random.uniform(60, 75)
    total_line = random.uniform(40, 55)

    # Simulate actual total
    actual_total = (team_pts + opp_pts) * (pace / 65) + random.gauss(0, 3)

    X_train.append([team_pts, opp_pts, pace, total_line])
    y_train.append(actual_total)

# Train regression model
rf = RandomForest(n_trees=100, max_depth=12, criterion='mse')
rf.fit(X_train, y_train)

# Predict
X_test = [[27.5, 24.8, 68, 48.5]]
predicted_total = rf.predict(X_test)
print(f"Predicted total: {predicted_total[0]:.1f}")
```

## Neural Networks

Simple feedforward neural networks for learning complex patterns.

### Basic Usage

```python
from lib.ml_models import NeuralNetwork, ActivationFunction

# Create network: 3 inputs -> 5 hidden -> 1 output
nn = NeuralNetwork(
    layer_sizes=[3, 5, 1],
    activation=ActivationFunction.SIGMOID,
    learning_rate=0.1,
    epochs=1000
)

# Train
nn.fit(X_train, y_train)

# Predict
predictions = nn.predict(X_test)
```

### Activation Functions

- **SIGMOID**: Good for binary classification (output 0-1)
- **RELU**: Fast training, good for hidden layers
- **TANH**: Output -1 to 1, centered around 0
- **LEAKY_RELU**: Prevents "dying ReLU" problem

### Betting Outcome Prediction

```python
# Normalize data first
from lib.ml_models import FeatureEngineering

# Features: [odds, line, team_form, opponent_form]
X_train = []
y_train = []

for i in range(300):
    odds = random.uniform(1.5, 3.0)
    line = random.uniform(-10, 10)
    team_form = random.uniform(0.3, 0.7)
    opp_form = random.uniform(0.3, 0.7)

    # Win probability
    prob = (team_form / (team_form + opp_form)) * (2.0 / odds)
    outcome = 1 if random.random() < prob else 0

    X_train.append([odds, line, team_form, opp_form])
    y_train.append(outcome)

# Normalize features
X_normalized, params = FeatureEngineering.normalize_features(X_train, method='standard')

# Train neural network
nn = NeuralNetwork(
    layer_sizes=[4, 8, 4, 1],
    activation=ActivationFunction.RELU,
    learning_rate=0.05,
    epochs=2000
)

nn.fit(X_normalized, y_train)

# Predict
X_test = [[2.1, -3.5, 0.58, 0.52]]
# Normalize using same parameters
X_test_norm = [
    [(X_test[0][j] - params[j]['mean']) / params[j]['std']
     for j in range(len(X_test[0]))]
]
prediction = nn.predict(X_test_norm)
print(f"Win probability: {prediction[0]:.3f}")
```

## Bayesian Hierarchical Models

Bayesian hierarchical models treat team scoring as distributions rather than single-point estimates, which helps quantify uncertainty in totals markets.

**Best for:** Analysts, researchers, patient bettors.

**Idea: Totals are distributions, not numbers.**

- Team scoring abilities as latent variables
- Shrink extreme teams toward league average
- Update beliefs game by game

### Strengths

- Handles uncertainty cleanly
- Excellent early season

### Weaknesses

- Complex to implement
- Slower to compute

### Totals Distribution Example

```python
from lib.ml_models import BayesianHierarchicalTotalsModel

games = [
    {"home_team": "BOS", "away_team": "NYK", "home_points": 112, "away_points": 105},
    {"home_team": "BOS", "away_team": "MIA", "home_points": 118, "away_points": 111}
]

model = BayesianHierarchicalTotalsModel(league_mean=110, league_std=12, game_std=14)
model.fit(games)

prediction = model.predict_total("BOS", "NYK", total_line=218.5, ci=0.9)
print(f"Mean total: {prediction['mean_total']:.1f}")
print(f"90% CI: {prediction['ci_lower']:.1f}-{prediction['ci_upper']:.1f}")
print(f"Over prob: {prediction['over_probability']:.3f}")
```

## Feature Engineering

Tools to create, transform, and select powerful features.

### Polynomial Features

```python
from lib.ml_models import FeatureEngineering

# Original features
X = [[2, 3], [4, 5]]

# Create polynomial features (degree 2)
X_poly = FeatureEngineering.create_polynomial_features(X, degree=2)

# X_poly now includes:
# - Original features: x1, x2
# - Squared terms: x1², x2²
# - Interaction terms: x1*x2
```

### Feature Normalization

```python
# Standard normalization (z-score)
X_normalized, params = FeatureEngineering.normalize_features(
    X,
    method='standard'
)

# Min-max normalization (0-1 scaling)
X_scaled, params = FeatureEngineering.normalize_features(
    X,
    method='minmax'
)

# Apply same normalization to new data
X_new_norm = [
    [(X_new[0][j] - params[j]['mean']) / params[j]['std']
     for j in range(len(X_new[0]))]
]
```

### Time Series Features

```python
# Create lagged features
scoring_history = [23, 27, 24, 30, 28, 26, 31, 29]

lagged_features = FeatureEngineering.create_lag_features(
    scoring_history,
    lags=[1, 2, 3]  # Use previous 3 games
)

# Each row: [current_score, lag1, lag2, lag3]
print(lagged_features[0])  # [30, 24, 27, 23]

# Create rolling window features
rolling_features = FeatureEngineering.create_rolling_features(
    scoring_history,
    windows=[3, 5]  # 3-game and 5-game windows
)

# Each row contains: [mean, std, min, max] for each window
```

### Feature Selection

```python
# Select features based on correlation with target
X_train = [...]  # Your features
y_train = [...]  # Your target

selected_indices = FeatureEngineering.select_features_correlation(
    X_train,
    y_train,
    threshold=0.1  # Keep features with |correlation| >= 0.1
)

# Keep only selected features
X_selected = [[row[i] for i in selected_indices] for row in X_train]
```

## Model Validation

Tools for evaluating and validating ML models.

### Train-Test Split

```python
from lib.ml_models import ModelValidation

X_train, X_test, y_train, y_test = ModelValidation.train_test_split(
    X, y,
    test_size=0.2,  # 20% for testing
    shuffle=True,
    random_seed=42
)
```

### K-Fold Cross-Validation

```python
from lib.ml_models import RandomForest, ModelValidation

# Cross-validate Random Forest
cv_result = ModelValidation.k_fold_cross_validation(
    X, y,
    model_class=RandomForest,
    model_params={'n_trees': 50, 'max_depth': 8},
    k=5,  # 5-fold CV
    scoring='accuracy'
)

print(f"Mean accuracy: {cv_result.mean_score:.3f}")
print(f"Std deviation: {cv_result.std_score:.3f}")
print(f"Fold scores: {cv_result.fold_scores}")
```

### Classification Metrics

```python
# After making predictions
y_true = [0, 1, 1, 0, 1, 1, 0, 0]
y_pred = [0, 1, 1, 0, 0, 1, 0, 1]

metrics = ModelValidation.calculate_classification_metrics(y_true, y_pred)

print(f"Accuracy: {metrics.accuracy:.3f}")
print(f"Precision: {metrics.precision:.3f}")
print(f"Recall: {metrics.recall:.3f}")
print(f"F1 Score: {metrics.f1_score:.3f}")
print(f"Confusion Matrix:")
for row in metrics.confusion_matrix:
    print(row)
```

### Regression Metrics

```python
y_true = [10.5, 12.3, 9.8, 14.2, 11.7]
y_pred = [10.2, 12.5, 9.5, 14.0, 11.9]

metrics = ModelValidation.calculate_regression_metrics(y_true, y_pred)

print(f"MSE: {metrics['mse']:.3f}")
print(f"RMSE: {metrics['rmse']:.3f}")
print(f"MAE: {metrics['mae']:.3f}")
print(f"R²: {metrics['r_squared']:.3f}")
```

## Complete Examples

### Example 1: NBA Player Points Prediction

```python
import random
from lib.ml_models import RandomForest, FeatureEngineering, ModelValidation

# Generate training data
X = []
y = []

for i in range(500):
    # Features: [minutes, usage_rate, fg_pct, ft_rate, opp_def_rating]
    minutes = random.uniform(20, 40)
    usage = random.uniform(0.15, 0.35)
    fg_pct = random.uniform(0.40, 0.55)
    ft_rate = random.uniform(0.15, 0.35)
    opp_def = random.uniform(100, 115)

    # Points formula (simplified)
    points = (minutes * usage * 50 * fg_pct +
              minutes * ft_rate * 2 -
              (opp_def - 105) * 0.1 +
              random.gauss(0, 2))

    X.append([minutes, usage, fg_pct, ft_rate, opp_def])
    y.append(points)

# Normalize features
X_norm, params = FeatureEngineering.normalize_features(X, method='standard')

# Train-test split
X_train, X_test, y_train, y_test = ModelValidation.train_test_split(
    X_norm, y, test_size=0.2, random_seed=42
)

# Train Random Forest
rf = RandomForest(n_trees=100, max_depth=15, criterion='mse')
rf.fit(X_train, y_train)

# Evaluate
predictions = rf.predict(X_test)
metrics = ModelValidation.calculate_regression_metrics(y_test, predictions)

print(f"Points Prediction Model Performance:")
print(f"R²: {metrics['r_squared']:.3f}")
print(f"RMSE: {metrics['rmse']:.2f} points")
print(f"MAE: {metrics['mae']:.2f} points")

# Feature importance
importance = rf.get_feature_importance()
feature_names = ['Minutes', 'Usage Rate', 'FG%', 'FT Rate', 'Opp Defense']
print("\nFeature Importance:")
for idx, name in enumerate(feature_names):
    print(f"  {name}: {importance.get(idx, 0):.3f}")

# Predict for a specific player
player_stats = [[32, 0.28, 0.48, 0.25, 108]]
player_norm = [
    [(player_stats[0][j] - params[j]['mean']) / params[j]['std']
     for j in range(len(player_stats[0]))]
]
predicted_points = rf.predict(player_norm)
print(f"\nPredicted points: {predicted_points[0]:.1f}")
```

### Example 2: NFL Spread Betting Model

```python
from lib.ml_models import (
    RandomForest, FeatureEngineering, ModelValidation, DecisionTree
)

# Historical game data
X = []
y = []  # 1 if covered spread, 0 if not

for i in range(300):
    # Features: [elo_diff, spread, home, rest_advantage, weather]
    elo_diff = random.uniform(-200, 200)
    spread = random.uniform(-14, 14)
    home = random.choice([0, 1])
    rest_adv = random.randint(-3, 3)
    weather = random.choice([0, 1])  # 0 = good, 1 = bad

    # Covered spread probability
    adjusted_diff = elo_diff + (50 if home else 0) + (rest_adv * 10)
    expected_margin = adjusted_diff / 25
    covered = 1 if expected_margin > spread else 0

    X.append([elo_diff, spread, home, rest_adv, weather])
    y.append(covered)

# Add polynomial features
X_poly = FeatureEngineering.create_polynomial_features(X, degree=2)

# Normalize
X_norm, params = FeatureEngineering.normalize_features(X_poly, method='standard')

# Cross-validation
cv_result = ModelValidation.k_fold_cross_validation(
    X_norm, y,
    model_class=RandomForest,
    model_params={'n_trees': 75, 'max_depth': 10},
    k=5,
    scoring='accuracy'
)

print(f"Spread Betting Model - Cross-Validation:")
print(f"Mean Accuracy: {cv_result.mean_score:.3f}")
print(f"Std Dev: {cv_result.std_score:.3f}")
print(f"Fold Scores: {[f'{s:.3f}' for s in cv_result.fold_scores]}")

# Train final model
rf = RandomForest(n_trees=75, max_depth=10)
rf.fit(X_norm, y)

# Predict next game
next_game = [[80, -3.5, 1, 3, 0]]
next_poly = FeatureEngineering.create_polynomial_features(next_game, degree=2)
next_norm = [
    [(next_poly[0][j] - params[j]['mean']) / params[j]['std']
     for j in range(len(next_poly[0]))]
]

cover_prob = rf.predict(next_norm)
print(f"\nProbability of covering spread: {cover_prob[0]:.3f}")
```

### Example 3: Betting Strategy Optimization

```python
from lib.ml_models import NeuralNetwork, FeatureEngineering, ModelValidation
from lib.advanced_stats import AdvancedStats

# Historical betting data
X = []
y = []  # ROI

for i in range(400):
    # Features: [true_prob, offered_odds, kelly_fraction, confidence]
    true_prob = random.uniform(0.4, 0.7)
    offered_odds = random.uniform(1.5, 3.5)
    kelly_frac = random.uniform(0.25, 1.0)
    confidence = random.uniform(0.5, 0.95)

    # Expected value
    implied_prob = 1 / offered_odds
    edge = true_prob - implied_prob

    # Simulate ROI
    if edge > 0:
        roi = edge * kelly_frac * 100 + random.gauss(0, 10)
    else:
        roi = edge * 100 + random.gauss(0, 15)

    X.append([true_prob, offered_odds, kelly_frac, confidence])
    y.append(roi)

# Normalize
X_norm, params = FeatureEngineering.normalize_features(X, method='minmax')

# Train neural network
nn = NeuralNetwork(
    layer_sizes=[4, 10, 5, 1],
    activation=ActivationFunction.RELU,
    learning_rate=0.01,
    epochs=3000
)

X_train, X_test, y_train, y_test = ModelValidation.train_test_split(
    X_norm, y, test_size=0.2, random_seed=42
)

nn.fit(X_train, y_train)

# Evaluate
predictions = nn.predict(X_test)
metrics = ModelValidation.calculate_regression_metrics(y_test, predictions)

print(f"Betting Strategy Optimization Model:")
print(f"R²: {metrics['r_squared']:.3f}")
print(f"RMSE: {metrics['rmse']:.2f}%")

# Optimize next bet
bet_scenarios = [
    [0.58, 2.1, 0.5, 0.85],
    [0.58, 2.1, 0.75, 0.85],
    [0.58, 2.1, 1.0, 0.85]
]

print("\nOptimal Kelly Fraction:")
for scenario in bet_scenarios:
    scenario_norm = [[(scenario[j] - params[j]['min']) / params[j]['range']
                     for j in range(len(scenario))]]
    expected_roi = nn.predict(scenario_norm)
    print(f"Kelly {scenario[2]:.0%}: Expected ROI = {expected_roi[0]:.2f}%")
```

## Best Practices

### 1. Always Normalize Features

Different scales can hurt model performance:

```python
# BAD: Features have very different scales
X = [[1500, 0.58], [1620, 0.62]]  # ELO and win rate

# GOOD: Normalize first
X_norm, params = FeatureEngineering.normalize_features(X, method='standard')
```

### 2. Use Cross-Validation

Never rely on a single train-test split:

```python
# GOOD: Use cross-validation
cv_result = ModelValidation.k_fold_cross_validation(
    X, y,
    model_class=RandomForest,
    model_params={'n_trees': 50},
    k=5
)
```

### 3. Avoid Overfitting

- Limit tree depth
- Use enough trees in Random Forests
- Don't train neural networks for too many epochs
- Use cross-validation to detect overfitting

```python
# Control overfitting with hyperparameters
rf = RandomForest(
    n_trees=100,      # More trees = more stable
    max_depth=8,      # Limit depth
    min_samples_leaf=5  # Require minimum samples in leaves
)
```

### 4. Feature Engineering is Critical

Good features matter more than complex models:

```python
# Add domain knowledge
def create_betting_features(games):
    features = []
    for game in games:
        # Raw stats
        pts_for = game['points_for']
        pts_against = game['points_against']

        # Engineered features
        point_diff = pts_for - pts_against
        scoring_rate = pts_for / game['possessions']

        # Rolling averages
        last_3_avg = calculate_recent_form(game, window=3)

        features.append([pts_for, pts_against, point_diff,
                        scoring_rate, last_3_avg])

    return features
```

### 5. Validate on Holdout Data

Always keep a final test set:

```python
# Split data three ways
X_train, X_temp, y_train, y_temp = ModelValidation.train_test_split(
    X, y, test_size=0.3
)

X_val, X_test, y_val, y_test = ModelValidation.train_test_split(
    X_temp, y_temp, test_size=0.5
)

# Train on train set
# Tune on validation set
# Final evaluation on test set (only once!)
```

### 6. Track Feature Importance

Understand what drives predictions:

```python
rf = RandomForest(n_trees=100, max_depth=10)
rf.fit(X_train, y_train)

importance = rf.get_feature_importance()

# Review and remove unimportant features
for idx, score in importance.items():
    if score < 0.01:
        print(f"Feature {idx} contributes little (score: {score:.4f})")
```

### 7. Ensemble Multiple Models

Combine different models for robustness:

```python
# Train multiple models
rf = RandomForest(n_trees=100, max_depth=10)
rf.fit(X_train, y_train)

tree = DecisionTree(max_depth=8)
tree.fit(X_train, y_train)

# Average predictions
rf_pred = rf.predict(X_test)
tree_pred = tree.predict(X_test)
ensemble_pred = [(rf_pred[i] + tree_pred[i]) / 2 for i in range(len(X_test))]
```

## Integration with Advanced Stats

Combine ML models with statistical analysis:

```python
from lib.ml_models import RandomForest, ModelValidation
from lib.advanced_stats import AdvancedStats

# 1. Use Bayesian inference for priors
prior_win_prob = AdvancedStats.bayesian_win_probability(wins=15, losses=7)

# 2. Use Monte Carlo for uncertainty
def simulate_game_outcome():
    # Use ML model prediction as base probability
    base_prob = rf.predict([[...]])[0]
    # Add uncertainty
    return 1 if random.random() < base_prob else 0

mc_result = AdvancedStats.monte_carlo_simulation(
    simulate_game_outcome,
    n_simulations=10000
)

# 3. Use Kelly Criterion for bet sizing
win_prob = rf.predict(X_next)[0]
odds = 2.5
kelly_fraction = AdvancedStats.kelly_optimal_size(win_prob, odds)

print(f"ML Model Win Prob: {win_prob:.3f}")
print(f"Kelly Bet Size: {kelly_fraction:.2%}")

# 4. Bootstrap confidence intervals for predictions
predictions = [rf.predict([[...]])[0] for _ in range(100)]
ci = AdvancedStats.bootstrap_confidence_interval(
    predictions,
    statistic_func=statistics.mean,
    n_bootstrap=1000
)

print(f"Prediction CI: [{ci['ci_lower']:.3f}, {ci['ci_upper']:.3f}]")
```

## Troubleshooting

### Poor Model Performance

1. Check feature scaling
2. Add more relevant features
3. Try different model parameters
4. Collect more training data
5. Check for data leakage

### Overfitting

- Reduce max_depth
- Increase min_samples_leaf
- Use cross-validation
- Add regularization (future feature)

### Slow Training

- Reduce n_trees or epochs
- Reduce feature dimensionality
- Use feature selection

### Unstable Predictions

- Use Random Forests instead of single trees
- Normalize features
- Add more training data
- Use cross-validation to check stability

## API Reference

See inline documentation in `lib/ml_models.py` for detailed API reference.

---

For more information:
- [Advanced Statistics Guide](advanced_stats_guide.md)
- [Data Storage Guide](data_storage_guide.md)
- [Horse Racing Guide](horse_racing_guide.md)
