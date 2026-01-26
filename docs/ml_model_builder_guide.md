# ML Model Builder Guide

Build custom machine learning models for sports betting predictions with ease.

## Table of Contents

- [Quick Start](#quick-start)
- [Model Class (Fluent API)](#model-class-fluent-api)
- [ModelBuilder Templates](#modelbuilder-templates)
- [DataHelper Utilities](#datahelper-utilities)
- [Complete Examples](#complete-examples)
- [Best Practices](#best-practices)

## Quick Start

```python
from lib.model_builder import quick_model, split_data, DataHelper

# Create sample data
X, y = DataHelper.create_sample_data(n_samples=200, task='classification')

# Split into train/test
X_train, X_test, y_train, y_test = split_data(X, y, test_size=0.2)

# Train quick model
model = quick_model(X_train, y_train, task='classification')

# Evaluate
metrics = model.evaluate(X_test, y_test)
print(f"Accuracy: {metrics['accuracy']:.3f}")
```

## Model Class (Fluent API)

The `Model` class provides a fluent, chainable interface for building ML models.

### Creating a Model

```python
from lib.model_builder import Model

# Start with Model()
model = Model()
```

### Setting Task Type

```python
# Classification (win/loss, cover/no cover)
model.for_classification()

# Regression (predict points, margins, totals)
model.for_regression()
```

### Choosing Model Type

#### Random Forest

Best for: General purpose, feature importance analysis

```python
model.using_random_forest(
    n_trees=100,      # More trees = better but slower
    max_depth=10      # Tree depth (prevent overfitting)
)
```

#### Decision Tree

Best for: Interpretability, understanding decision rules

```python
model.using_decision_tree(
    max_depth=10      # Maximum tree depth
)
```

#### Neural Network

Best for: Complex patterns, non-linear relationships

```python
model.using_neural_network(
    hidden_layers=[10, 5],    # Network architecture
    learning_rate=0.1,        # Learning rate
    epochs=1000               # Training iterations
)
```

### Adding Features

```python
# Document your features
model.with_features([
    'team_rating',
    'opponent_rating',
    'home_advantage',
    'rest_days'
])
```

### Normalization

```python
# Standard scaling (z-score)
model.with_normalization('standard')

# Min-max scaling (0-1)
model.with_normalization('minmax')
```

### Training

```python
# Train the model
model.train(X_train, y_train)
```

### Making Predictions

```python
# Predict outcomes
predictions = model.predict(X_test)

# Get probabilities (classification)
probabilities = model.predict_proba(X_test)
```

### Evaluation

```python
# Get metrics dictionary
metrics = model.evaluate(X_test, y_test)

# Classification metrics
print(f"Accuracy: {metrics['accuracy']}")
print(f"Precision: {metrics['precision']}")
print(f"Recall: {metrics['recall']}")
print(f"F1 Score: {metrics['f1_score']}")

# Regression metrics
print(f"R²: {metrics['r_squared']}")
print(f"RMSE: {metrics['rmse']}")
print(f"MAE: {metrics['mae']}")
```

### Formatted Output

```python
# Print beautiful performance report
model.print_performance(X_test, y_test)
```

Output:
```
============================================================
MODEL PERFORMANCE: Game Prediction
============================================================
Model Type: Random Forest
Task: Classification

Accuracy:  0.875
Precision: 0.863
Recall:    0.891
F1 Score:  0.877

Confusion Matrix:
  [35, 5]
  [4, 36]

Feature Importance:
  team_rating: 0.456
  opponent_rating: 0.389
  home_advantage: 0.155
============================================================
```

### Feature Importance

```python
# Get feature importance (Random Forest/Decision Tree)
importance = model.feature_importance()

for feature, score in importance.items():
    print(f"{feature}: {score:.3f}")
```

### Cross-Validation

```python
# K-fold cross-validation
cv_results = model.cross_validate(X, y, k=5)

print(f"Mean Score: {cv_results['mean_score']:.3f}")
print(f"Std Dev: {cv_results['std_score']:.3f}")
print(f"Fold Scores: {cv_results['fold_scores']}")
```

### Complete Fluent Example

```python
# Chain everything together
model = (Model()
         .named("NBA Spread Model")
         .for_classification()
         .using_random_forest(n_trees=150, max_depth=12)
         .with_features(['off_rtg', 'def_rtg', 'pace', 'rest'])
         .with_normalization('standard')
         .train(X_train, y_train))

# Evaluate
model.print_performance(X_test, y_test)

# Predict
predictions = model.predict(X_new)
```

## ModelBuilder Templates

Pre-configured models for common betting scenarios.

### Game Prediction Model

Predict win/loss outcomes.

```python
from lib.model_builder import ModelBuilder

model = ModelBuilder.game_prediction_model(
    feature_names=['team_elo', 'opponent_elo', 'home']
)

model.train(X_train, y_train)
predictions = model.predict(X_test)
```

**Configuration:**
- Task: Classification
- Model: Random Forest (100 trees, depth 10)
- Normalization: Standard scaling

### Spread Model

Predict if team covers the spread.

```python
model = ModelBuilder.spread_model(
    feature_names=['rating_diff', 'spread', 'rest_advantage']
)

model.train(X_train, y_train)
model.print_performance(X_test, y_test)
```

**Configuration:**
- Task: Classification
- Model: Random Forest (150 trees, depth 12)
- Normalization: Standard scaling

### Total Points Model

Predict total points scored in a game.

```python
model = ModelBuilder.total_points_model(
    feature_names=['team_ppg', 'opp_ppg', 'pace', 'def_efficiency']
)

model.train(X_train, y_train)
predictions = model.predict(X_test)
```

**Configuration:**
- Task: Regression
- Model: Random Forest (100 trees, depth 15)
- Normalization: Standard scaling

### Player Props Model

Predict player performance (points, rebounds, etc.).

```python
model = ModelBuilder.player_props_model(
    feature_names=['minutes', 'usage_rate', 'matchup_rating']
)

model.train(X_train, y_train)
metrics = model.evaluate(X_test, y_test)
```

**Configuration:**
- Task: Regression
- Model: Random Forest (80 trees, depth 12)
- Normalization: Min-max scaling

### Quick Model

Fast prototyping with sensible defaults.

```python
# Classification
model = ModelBuilder.quick_model(X_train, y_train, task='classification')

# Regression
model = ModelBuilder.quick_model(X_train, y_train, task='regression')
```

## DataHelper Utilities

Helper functions for data preparation.

### Split Data

```python
from lib.model_builder import DataHelper

# Split into train/test sets
X_train, X_test, y_train, y_test = DataHelper.split_data(
    X, y,
    test_size=0.2    # 20% for testing
)
```

### Polynomial Features

Add squares and interactions.

```python
# Add polynomial features
X_poly = DataHelper.add_polynomial_features(
    X,
    degree=2    # Add x², x*y interactions
)

# Example: [a, b] becomes [a, b, a², a*b, b²]
```

### Rolling Statistics

Create time-series features.

```python
# Add rolling averages
data = [10, 12, 15, 11, 13, 16, 14]

rolling_features = DataHelper.add_rolling_stats(
    data,
    windows=[3, 5, 10]    # 3-game, 5-game, 10-game averages
)
```

### Normalization

```python
# Normalize features
X_normalized, params = DataHelper.normalize(
    X,
    method='standard'    # or 'minmax'
)

# Use params to normalize new data the same way
```

### Create Sample Data

Generate test data for experimentation.

```python
# Classification data
X, y = DataHelper.create_sample_data(
    n_samples=200,
    task='classification'
)

# Regression data
X, y = DataHelper.create_sample_data(
    n_samples=200,
    task='regression'
)
```

## Complete Examples

### Example 1: NBA Game Prediction

```python
from lib.model_builder import Model, split_data

# Prepare your data
# X = [[team_off_rtg, team_def_rtg, opp_off_rtg, opp_def_rtg, home], ...]
# y = [1, 0, 1, 1, 0, ...]  # 1 = win, 0 = loss

# Split data
X_train, X_test, y_train, y_test = split_data(X, y, test_size=0.2)

# Build model
model = (Model()
         .named("NBA Game Predictor")
         .for_classification()
         .using_random_forest(n_trees=100, max_depth=10)
         .with_features([
             'team_offensive_rating',
             'team_defensive_rating',
             'opponent_offensive_rating',
             'opponent_defensive_rating',
             'home_court_advantage'
         ])
         .with_normalization('standard')
         .train(X_train, y_train))

# Evaluate
model.print_performance(X_test, y_test)

# Predict new games
new_game = [[112.5, 108.2, 110.1, 109.5, 1]]  # Home game
prediction = model.predict(new_game)
probability = model.predict_proba(new_game)

print(f"Prediction: {'Win' if prediction[0] == 1 else 'Loss'}")
print(f"Win Probability: {probability[0]:.1%}")
```

### Example 2: NFL Total Points

```python
from lib.model_builder import ModelBuilder, DataHelper

# Your data
# X = [[team_ppg, opp_ppg, team_pace, weather, ...], ...]
# y = [45.5, 51.0, 38.5, ...]  # Actual total points

# Create and train model
model = (ModelBuilder.total_points_model(
            feature_names=[
                'team_points_per_game',
                'opponent_points_per_game',
                'offensive_pace',
                'weather_factor'
            ])
         .train(X_train, y_train))

# Cross-validate
cv_results = model.cross_validate(X, y, k=5)
print(f"Cross-validation R²: {cv_results['mean_score']:.3f} ± {cv_results['std_score']:.3f}")

# Predict
predictions = model.predict(X_test)
metrics = model.evaluate(X_test, y_test)

print(f"RMSE: {metrics['rmse']:.2f} points")
```

### Example 3: Feature Engineering Workflow

```python
from lib.model_builder import Model, DataHelper

# Start with basic features
X = [[rating, opp_rating, home] for ...]

# Add polynomial features
X_poly = DataHelper.add_polynomial_features(X, degree=2)

# Split data
X_train, X_test, y_train, y_test = DataHelper.split_data(X_poly, y)

# Build model
model = (Model()
         .for_classification()
         .using_random_forest(n_trees=150)
         .with_normalization('standard')
         .train(X_train, y_train))

# Compare performance
print(f"With polynomial features: {model.evaluate(X_test, y_test)['accuracy']:.3f}")
```

### Example 4: Neural Network for Complex Patterns

```python
model = (Model()
         .named("Deep Learning Model")
         .for_classification()
         .using_neural_network(
             hidden_layers=[20, 10, 5],    # 3 hidden layers
             learning_rate=0.05,
             epochs=2000
         )
         .with_features([
             'feature_1', 'feature_2', 'feature_3',
             'feature_4', 'feature_5', 'feature_6'
         ])
         .with_normalization('standard')    # Important for neural nets!
         .train(X_train, y_train))

model.print_performance(X_test, y_test)
```

## Best Practices

### 1. Always Split Your Data

```python
# Never test on training data
X_train, X_test, y_train, y_test = split_data(X, y, test_size=0.2)
```

### 2. Use Normalization

Especially important for:
- Neural Networks (required)
- When features have different scales
- Distance-based algorithms

```python
model.with_normalization('standard')
```

### 3. Start with Random Forest

Random Forests are excellent for:
- Getting started quickly
- Feature importance analysis
- Robust performance
- Less prone to overfitting

```python
model.using_random_forest(n_trees=100, max_depth=10)
```

### 4. Prevent Overfitting

**Limit tree depth:**
```python
.using_random_forest(n_trees=100, max_depth=8)  # Shallower trees
```

**Use cross-validation:**
```python
cv_results = model.cross_validate(X, y, k=5)
```

**More training data:**
```python
# Aim for at least 100-200 samples
```

### 5. Feature Engineering Matters

```python
# Add domain knowledge
# - Rolling averages for recent form
# - Rest days
# - Head-to-head records
# - Home/away splits
# - Weather factors

# Use polynomial features for interactions
X_poly = DataHelper.add_polynomial_features(X, degree=2)
```

### 6. Interpretability vs Accuracy

**For interpretability:**
```python
.using_decision_tree(max_depth=5)  # Easy to visualize
```

**For accuracy:**
```python
.using_random_forest(n_trees=200, max_depth=15)
```

**For complex patterns:**
```python
.using_neural_network(hidden_layers=[20, 10])
```

### 7. Name Your Models

```python
model.named("2024 NBA Playoff Model")
```

Makes reports clearer and helps track different versions.

### 8. Document Your Features

```python
model.with_features([
    'team_offensive_rating',    # Points per 100 possessions
    'team_defensive_rating',    # Opp points per 100 possessions
    'rest_days',                # Days since last game
    'home_court'                # 1 if home, 0 if away
])
```

### 9. Validate Performance

```python
# Use multiple metrics
metrics = model.evaluate(X_test, y_test)

# Classification
print(f"Accuracy: {metrics['accuracy']}")      # Overall correctness
print(f"Precision: {metrics['precision']}")    # When you predict 1, how often right?
print(f"Recall: {metrics['recall']}")          # Of all 1s, how many did you catch?
print(f"F1: {metrics['f1_score']}")            # Harmonic mean of precision/recall

# Regression
print(f"R²: {metrics['r_squared']}")           # Variance explained
print(f"RMSE: {metrics['rmse']}")              # Average error magnitude
print(f"MAE: {metrics['mae']}")                # Mean absolute error
```

### 10. Feature Importance

```python
# Understand what drives predictions
importance = model.feature_importance()

for feature, score in sorted(importance.items(), key=lambda x: x[1], reverse=True):
    print(f"{feature}: {score:.3f}")
```

## Common Workflows

### Workflow 1: Quick Prototyping

```python
from lib.model_builder import quick_model, split_data, DataHelper

X, y = DataHelper.create_sample_data(200)
X_train, X_test, y_train, y_test = split_data(X, y)

model = quick_model(X_train, y_train)
print(f"Accuracy: {model.evaluate(X_test, y_test)['accuracy']:.3f}")
```

### Workflow 2: Production Model

```python
from lib.model_builder import Model, DataHelper

# Prepare data
X_train, X_test, y_train, y_test = split_data(X, y)

# Build model
model = (Model()
         .named("Production NBA Model v2.1")
         .for_classification()
         .using_random_forest(n_trees=200, max_depth=12)
         .with_features(feature_names)
         .with_normalization('standard')
         .train(X_train, y_train))

# Cross-validate
cv = model.cross_validate(X, y, k=10)
print(f"CV Score: {cv['mean_score']:.3f} ± {cv['std_score']:.3f}")

# Final evaluation
model.print_performance(X_test, y_test)

# Save predictions
predictions = model.predict(X_new_games)
```

### Workflow 3: Compare Models

```python
from lib.model_builder import Model, split_data

X_train, X_test, y_train, y_test = split_data(X, y)

# Random Forest
rf = Model().for_classification().using_random_forest().train(X_train, y_train)
rf_acc = rf.evaluate(X_test, y_test)['accuracy']

# Decision Tree
dt = Model().for_classification().using_decision_tree().train(X_train, y_train)
dt_acc = dt.evaluate(X_test, y_test)['accuracy']

# Neural Network
nn = Model().for_classification().using_neural_network().train(X_train, y_train)
nn_acc = nn.evaluate(X_test, y_test)['accuracy']

print(f"Random Forest: {rf_acc:.3f}")
print(f"Decision Tree: {dt_acc:.3f}")
print(f"Neural Network: {nn_acc:.3f}")
```

## Tips for Better Models

1. **More data is better** - Aim for 200+ samples minimum
2. **Feature quality > quantity** - 5 good features beat 20 mediocre ones
3. **Domain knowledge helps** - Use your sports knowledge
4. **Test on unseen data** - Never tune on test set
5. **Cross-validate** - Get stable performance estimates
6. **Start simple** - Begin with decision tree, move to random forest
7. **Normalize when needed** - Always for neural networks
8. **Track feature importance** - Learn what matters
9. **Prevent overfitting** - Limit depth, use more data
10. **Iterate** - Build, test, improve, repeat

## See Also

- [Simple API Guide](simple_api_guide.md) - For Kelly criterion, EV calculations
- [Advanced Stats Guide](advanced_stats_guide.md) - For statistical methods
- [Examples](../examples/ml_model_examples.py) - Complete working examples

---

For more information, see the main [README](../README.md).
