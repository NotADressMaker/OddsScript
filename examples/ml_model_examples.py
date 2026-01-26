#!/usr/bin/env python3
"""
ML Model Building Examples

Shows how to build custom machine learning models for sports betting.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.model_builder import Model, ModelBuilder, DataHelper, build_model, quick_model, split_data

print("SportsBetLang - ML Model Examples")
print("=" * 60)
print()

# ========================================
# Example 1: Quick Model (Fast Start)
# ========================================
print("EXAMPLE 1: Quick Model")
print("-" * 60)

# Create sample data
X, y = DataHelper.create_sample_data(n_samples=200, task='classification')

# Split data
X_train, X_test, y_train, y_test = split_data(X, y, test_size=0.2)

# Quick model with defaults
model = quick_model(X_train, y_train, task='classification')

# Evaluate
accuracy = model.evaluate(X_test, y_test)['accuracy']
print(f"Quick model accuracy: {accuracy:.3f}")
print()

# ========================================
# Example 2: Game Prediction Model
# ========================================
print("EXAMPLE 2: Game Prediction Model")
print("-" * 60)

# Use pre-configured template
model = (ModelBuilder.game_prediction_model(
            feature_names=['team_rating', 'opponent_rating', 'home_advantage'])
         .train(X_train, y_train))

# Make predictions
predictions = model.predict(X_test)
print(f"Predictions: {predictions[:5]}")

# Print performance report
model.print_performance(X_test, y_test)

# ========================================
# Example 3: Custom Model with Fluent API
# ========================================
print("EXAMPLE 3: Custom Model with Fluent API")
print("-" * 60)

# Build custom model step-by-step
model = (Model()
         .named("NBA Spread Model")
         .for_classification()
         .using_random_forest(n_trees=150, max_depth=12)
         .with_features(['off_rating', 'def_rating', 'pace', 'rest_days'])
         .with_normalization('standard')
         .train(X_train, y_train))

# Evaluate
metrics = model.evaluate(X_test, y_test)
print(f"Accuracy: {metrics['accuracy']:.3f}")
print(f"Precision: {metrics['precision']:.3f}")
print(f"Recall: {metrics['recall']:.3f}")
print()

# ========================================
# Example 4: Total Points Regression
# ========================================
print("EXAMPLE 4: Total Points Regression")
print("-" * 60)

# Create regression data
X_reg, y_reg = DataHelper.create_sample_data(n_samples=200, task='regression')
X_train_r, X_test_r, y_train_r, y_test_r = split_data(X_reg, y_reg)

# Build regression model
model = (ModelBuilder.total_points_model(
            feature_names=['team_ppg', 'opp_ppg', 'pace'])
         .train(X_train_r, y_train_r))

# Predict and evaluate
predictions = model.predict(X_test_r)
metrics = model.evaluate(X_test_r, y_test_r)

print(f"R²: {metrics['r_squared']:.3f}")
print(f"RMSE: {metrics['rmse']:.3f}")
print(f"Sample predictions: {predictions[:5]}")
print()

# ========================================
# Example 5: Neural Network Model
# ========================================
print("EXAMPLE 5: Neural Network Model")
print("-" * 60)

# Build neural network
model = (Model()
         .named("Deep Learning Predictor")
         .for_classification()
         .using_neural_network(
             hidden_layers=[10, 5],
             learning_rate=0.1,
             epochs=500
         )
         .with_normalization('standard')
         .train(X_train, y_train))

# Evaluate
metrics = model.evaluate(X_test, y_test)
print(f"Neural Network Accuracy: {metrics['accuracy']:.3f}")
print()

# ========================================
# Example 6: Decision Tree Model
# ========================================
print("EXAMPLE 6: Decision Tree")
print("-" * 60)

model = (Model()
         .named("Simple Decision Tree")
         .for_classification()
         .using_decision_tree(max_depth=8)
         .with_features(['feature_1', 'feature_2', 'feature_3'])
         .train(X_train, y_train))

# Get feature importance
importance = model.feature_importance()
print("Feature Importance:")
for feature, score in importance.items():
    print(f"  {feature}: {score:.3f}")
print()

# ========================================
# Example 7: Cross-Validation
# ========================================
print("EXAMPLE 7: Cross-Validation")
print("-" * 60)

# Build model (don't train yet)
model = (Model()
         .for_classification()
         .using_random_forest(n_trees=50, max_depth=8))

# Cross-validate
cv_results = model.cross_validate(X, y, k=5)

print(f"Cross-Validation Results (5-fold):")
print(f"Mean Score: {cv_results['mean_score']:.3f}")
print(f"Std Dev: {cv_results['std_score']:.3f}")
print(f"Fold Scores: {[f'{s:.3f}' for s in cv_results['fold_scores']]}")
print()

# ========================================
# Example 8: Player Props Model
# ========================================
print("EXAMPLE 8: Player Props Model")
print("-" * 60)

# Use player props template
model = (ModelBuilder.player_props_model(
            feature_names=['minutes', 'usage_rate', 'matchup_rating'])
         .train(X_train_r, y_train_r))

model.print_performance(X_test_r, y_test_r)

# ========================================
# Example 9: Data Preparation
# ========================================
print("EXAMPLE 9: Feature Engineering")
print("-" * 60)

# Add polynomial features
X_poly = DataHelper.add_polynomial_features(X_train, degree=2)
print(f"Original features: {len(X_train[0])}")
print(f"With polynomial features: {len(X_poly[0])}")

# Add rolling statistics
data_series = [10, 12, 15, 11, 13, 16, 14]
rolling_features = DataHelper.add_rolling_stats(data_series, windows=[3, 5])
print(f"Rolling features created: {len(rolling_features)}")

# Normalize features
X_norm, params = DataHelper.normalize(X_train, method='standard')
print(f"Normalized {len(X_norm)} samples")
print()

# ========================================
# Example 10: Spread Coverage Model
# ========================================
print("EXAMPLE 10: Spread Coverage Model")
print("-" * 60)

model = (ModelBuilder.spread_model(
            feature_names=['rating_diff', 'rest_advantage', 'home'])
         .train(X_train, y_train))

# Make predictions with probabilities
predictions = model.predict(X_test)
probabilities = model.predict_proba(X_test)

print(f"Predictions: {predictions[:5]}")
print(f"Probabilities: {probabilities[:5]}")
print()

# ========================================
# Example 11: Complete Workflow
# ========================================
print("EXAMPLE 11: Complete ML Workflow")
print("-" * 60)

# 1. Create data
print("1. Creating training data...")
X, y = DataHelper.create_sample_data(n_samples=500, task='classification')

# 2. Split data
print("2. Splitting into train/test...")
X_train, X_test, y_train, y_test = split_data(X, y, test_size=0.2)

# 3. Build model
print("3. Building Random Forest model...")
model = (build_model()
         .named("Complete Workflow Model")
         .for_classification()
         .using_random_forest(n_trees=100, max_depth=10)
         .with_features(['team_elo', 'opponent_elo', 'home_court'])
         .with_normalization('standard'))

# 4. Train model
print("4. Training model...")
model.train(X_train, y_train)

# 5. Evaluate
print("5. Evaluating performance...")
metrics = model.evaluate(X_test, y_test)

# 6. Print results
print("\nResults:")
print(f"  Accuracy: {metrics['accuracy']:.3f}")
print(f"  Precision: {metrics['precision']:.3f}")
print(f"  Recall: {metrics['recall']:.3f}")
print(f"  F1 Score: {metrics['f1_score']:.3f}")

# 7. Feature importance
importance = model.feature_importance()
print("\nTop Features:")
for feature, score in sorted(importance.items(), key=lambda x: x[1], reverse=True):
    print(f"  {feature}: {score:.3f}")
print()

print("=" * 60)
print("All examples complete!")
print()
print("Key Takeaways:")
print("  - Use quick_model() for fast prototyping")
print("  - Use ModelBuilder templates for common scenarios")
print("  - Use Model() fluent API for full customization")
print("  - Always split data and validate performance")
print("  - Feature engineering can improve results")
