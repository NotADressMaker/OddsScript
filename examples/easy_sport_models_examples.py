#!/usr/bin/env python3
"""
Easy Sport Models Examples

Shows the simplified interface for sport-specific ML models.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.easy_sport_models import (
    EasySportModel,
    quick_nba_prediction,
    quick_nfl_prediction,
    quick_soccer_btts,
    validate_nba_data,
    validate_sport_data,
    train_and_predict,
    AutoFeatures
)
import random

print("VigScript - Easy Sport Models")
print("=" * 60)
print()

# ========================================
# Example 1: EasySportModel - Simple Usage
# ========================================
print("EXAMPLE 1: EasySportModel - Simple NBA Prediction")
print("-" * 60)

# Create sample NBA games
random.seed(42)
nba_games = []

for _ in range(200):
    game = {
        'team_offensive_rating': random.uniform(105, 118),
        'team_defensive_rating': random.uniform(105, 118),
        'opponent_offensive_rating': random.uniform(105, 118),
        'opponent_defensive_rating': random.uniform(105, 118),
        'home_court': random.choice([0, 1]),
        'rest_days_team': random.randint(0, 4),
        'rest_days_opponent': random.randint(0, 4),
        'pace': random.uniform(95, 105),
    }

    # Calculate result
    team_net = game['team_offensive_rating'] - game['team_defensive_rating']
    opp_net = game['opponent_offensive_rating'] - game['opponent_defensive_rating']
    diff = team_net - opp_net + (3 if game['home_court'] else 0)
    win_prob = 1 / (1 + 10 ** (-diff / 15))
    game['result'] = 1 if random.random() < win_prob else 0

    nba_games.append(game)

# Create and train model (SO EASY!)
model = EasySportModel('nba', 'game_winner')
model.fit(nba_games)

# Show performance
model.summary()

# Predict a new game
new_game = {
    'team_offensive_rating': 115.0,
    'team_defensive_rating': 107.5,
    'opponent_offensive_rating': 110.2,
    'opponent_defensive_rating': 109.8,
    'home_court': 1,
    'rest_days_team': 2,
    'rest_days_opponent': 1,
    'pace': 100.5
}

prediction = model.predict(new_game)
probability = model.predict_proba(new_game)

print(f"Prediction: {'WIN' if prediction == 1 else 'LOSS'}")
print(f"Win Probability: {probability:.1%}")
print()

# ========================================
# Example 2: Quick Prediction Functions
# ========================================
print("EXAMPLE 2: Quick Prediction Functions")
print("-" * 60)

# NBA quick prediction (no model training needed)
win_prob = quick_nba_prediction(
    team_off_rtg=115.0,
    team_def_rtg=107.5,
    opp_off_rtg=110.2,
    opp_def_rtg=109.8,
    home=True,
    rest_team=2,
    rest_opp=1,
    pace=100.5
)
print(f"NBA Quick Prediction: {win_prob:.1%} win probability")

# NFL quick prediction
nfl_prob = quick_nfl_prediction(
    team_dvoa=15.0,
    opp_dvoa=5.0,
    home=True,
    temperature=35,  # Cold game
    wind_speed=20    # Windy
)
print(f"NFL Quick Prediction: {nfl_prob:.1%} win probability (cold & windy)")

# Soccer BTTS
btts_prob = quick_soccer_btts(
    team_goals_avg=1.8,
    opp_goals_avg=1.5,
    team_clean_sheets=0.30,
    opp_clean_sheets=0.35
)
print(f"Soccer BTTS Probability: {btts_prob:.1%}")
print()

# ========================================
# Example 3: Data Validation
# ========================================
print("EXAMPLE 3: Data Validation")
print("-" * 60)

# Validate NBA data
valid, errors = validate_nba_data(nba_games[:5])
if valid:
    print("✓ NBA data is valid!")
else:
    print("✗ Data errors found:")
    for error in errors:
        print(f"  - {error}")

# Create invalid data to show validation
invalid_game = {
    'team_offensive_rating': 115.0,
    # Missing other required fields
}

valid, errors = validate_sport_data('nba', 'game_winner', [invalid_game])
if not valid:
    print("\n✗ Invalid game detected:")
    for error in errors[:3]:
        print(f"  - {error}")
print()

# ========================================
# Example 4: AutoFeatures Helper
# ========================================
print("EXAMPLE 4: AutoFeatures - Automatic Feature Creation")
print("-" * 60)

# NBA - Create features from basic stats
team_stats = {
    'off_rtg': 115.0,
    'def_rtg': 107.5,
    'pace': 102.0,
    'rest_days': 2
}

opp_stats = {
    'off_rtg': 110.2,
    'def_rtg': 109.8,
    'pace': 99.0,
    'rest_days': 1
}

game_info = {
    'home': True
}

# Automatically create all required features
nba_features = AutoFeatures.nba_game_features(team_stats, opp_stats, game_info)

print("Created NBA features:")
for key, value in nba_features.items():
    print(f"  {key}: {value}")
print()

# NFL - Create features with weather
nfl_team = {'off_dvoa': 15.0, 'def_dvoa': -8.0}
nfl_opp = {'off_dvoa': 5.0, 'def_dvoa': -3.0}
nfl_game = {'home': True, 'temp': 28, 'wind': 18}

nfl_features = AutoFeatures.nfl_game_features(nfl_team, nfl_opp, nfl_game)

print("Created NFL features:")
for key, value in nfl_features.items():
    print(f"  {key}: {value:.3f}" if isinstance(value, float) else f"  {key}: {value}")
print()

# ========================================
# Example 5: End-to-End Workflow
# ========================================
print("EXAMPLE 5: End-to-End Workflow")
print("-" * 60)

# Upcoming games to predict
upcoming_games = [
    {
        'team_offensive_rating': 116.0,
        'team_defensive_rating': 108.0,
        'opponent_offensive_rating': 111.0,
        'opponent_defensive_rating': 110.0,
        'home_court': 1,
        'rest_days_team': 2,
        'rest_days_opponent': 2,
        'pace': 101.0
    },
    {
        'team_offensive_rating': 109.0,
        'team_defensive_rating': 112.0,
        'opponent_offensive_rating': 114.0,
        'opponent_defensive_rating': 107.0,
        'home_court': 0,
        'rest_days_team': 1,
        'rest_days_opponent': 3,
        'pace': 98.0
    },
    {
        'team_offensive_rating': 113.5,
        'team_defensive_rating': 109.5,
        'opponent_offensive_rating': 112.0,
        'opponent_defensive_rating': 110.5,
        'home_court': 1,
        'rest_days_team': 3,
        'rest_days_opponent': 1,
        'pace': 102.5
    }
]

# Complete workflow in one function call
predictions = train_and_predict(
    sport='nba',
    model_type='game_winner',
    historical_games=nba_games,
    new_games=upcoming_games,
    show_performance=True
)

print("Predictions for upcoming games:")
for i, pred in enumerate(predictions, 1):
    result = "WIN" if pred == 1 else "LOSS"
    print(f"  Game {i}: {result}")
print()

# ========================================
# Example 6: Multiple Sports
# ========================================
print("EXAMPLE 6: Multiple Sports - Easy Switching")
print("-" * 60)

# Create NFL data
nfl_games = []
for _ in range(150):
    game = {
        'team_offensive_dvoa': random.uniform(-20, 25),
        'team_defensive_dvoa': random.uniform(-20, 25),
        'opponent_offensive_dvoa': random.uniform(-20, 25),
        'opponent_defensive_dvoa': random.uniform(-20, 25),
        'home_field': random.choice([0, 1]),
        'weather_factor': random.uniform(0, 0.5),
        'rest_days_team': random.choice([3, 7, 10, 14]),
        'rest_days_opponent': random.choice([3, 7, 10, 14]),
    }

    team_total = game['team_offensive_dvoa'] - game['team_defensive_dvoa']
    opp_total = game['opponent_offensive_dvoa'] - game['opponent_defensive_dvoa']
    diff = team_total - opp_total + (2 if game['home_field'] else 0)
    diff -= game['weather_factor'] * 5
    win_prob = 1 / (1 + 10 ** (-diff / 10))
    game['result'] = 1 if random.random() < win_prob else 0

    nfl_games.append(game)

# Train NFL model (same interface!)
nfl_model = EasySportModel('nfl', 'game_winner')
nfl_model.fit(nfl_games)
nfl_metrics = nfl_model.evaluate()

print(f"NFL Model Accuracy: {nfl_metrics['accuracy']:.3f}")

# Create Soccer data
soccer_games = []
for _ in range(180):
    game = {
        'team_goals_for_avg': random.uniform(1.0, 2.5),
        'opponent_goals_for_avg': random.uniform(1.0, 2.5),
        'team_clean_sheet_pct': random.uniform(0.20, 0.50),
        'opponent_clean_sheet_pct': random.uniform(0.20, 0.50),
        'league_btts_frequency': 0.50,
    }

    team_scores = (1 - game['opponent_clean_sheet_pct']) * (game['team_goals_for_avg'] / 1.5)
    opp_scores = (1 - game['team_clean_sheet_pct']) * (game['opponent_goals_for_avg'] / 1.5)
    btts_prob = team_scores * opp_scores * game['league_btts_frequency']

    game['result'] = 1 if random.random() < btts_prob else 0
    soccer_games.append(game)

# Train Soccer model (same interface!)
soccer_model = EasySportModel('soccer', 'btts')
soccer_model.fit(soccer_games)
soccer_metrics = soccer_model.evaluate()

print(f"Soccer BTTS Model Accuracy: {soccer_metrics['accuracy']:.3f}")
print()

# ========================================
# Example 7: Required Features
# ========================================
print("EXAMPLE 7: Check Required Features")
print("-" * 60)

nba_model_check = EasySportModel('nba', 'spread')
print("NBA Spread Model requires:")
for i, feature in enumerate(nba_model_check.required_features(), 1):
    print(f"  {i}. {feature}")
print()

nhl_model_check = EasySportModel('nhl', 'total_goals')
print("NHL Total Goals Model requires:")
for i, feature in enumerate(nhl_model_check.required_features(), 1):
    print(f"  {i}. {feature}")
print()

# ========================================
# Example 8: Batch Predictions
# ========================================
print("EXAMPLE 8: Batch Predictions")
print("-" * 60)

# Predict multiple games at once
batch_games = [
    AutoFeatures.nba_game_features(
        {'off_rtg': 116, 'def_rtg': 108, 'pace': 102, 'rest_days': 2},
        {'off_rtg': 111, 'def_rtg': 110, 'pace': 99, 'rest_days': 1},
        {'home': True}
    ),
    AutoFeatures.nba_game_features(
        {'off_rtg': 109, 'def_rtg': 112, 'pace': 98, 'rest_days': 1},
        {'off_rtg': 114, 'def_rtg': 107, 'pace': 103, 'rest_days': 3},
        {'home': False}
    ),
    AutoFeatures.nba_game_features(
        {'off_rtg': 113, 'def_rtg': 110, 'pace': 100, 'rest_days': 2},
        {'off_rtg': 112, 'def_rtg': 111, 'pace': 101, 'rest_days': 2},
        {'home': True}
    )
]

print("Batch predictions:")
for i, game in enumerate(batch_games, 1):
    pred = model.predict(game)
    prob = model.predict_proba(game)
    home_status = "Home" if game['home_court'] == 1 else "Away"
    print(f"  Game {i} ({home_status}): {'WIN' if pred == 1 else 'LOSS'} ({prob:.1%})")
print()

# ========================================
# Example 9: Model Comparison
# ========================================
print("EXAMPLE 9: Compare Different Models")
print("-" * 60)

# Try different NBA models
print("Training NBA models...")

game_winner = EasySportModel('nba', 'game_winner')
game_winner.fit(nba_games)
gw_metrics = game_winner.evaluate()

print(f"Game Winner Model:  {gw_metrics['accuracy']:.3f} accuracy")

# Note: For spread/totals, you'd need different data with those features
print()

# ========================================
# Example 10: Error Handling
# ========================================
print("EXAMPLE 10: Error Handling")
print("-" * 60)

try:
    # Try to predict without training
    untrained = EasySportModel('nba', 'game_winner')
    untrained.predict(new_game)
except RuntimeError as e:
    print(f"✓ Caught expected error: {e}")

try:
    # Try to predict with missing features
    incomplete_game = {'team_offensive_rating': 115}
    model.predict(incomplete_game)
except ValueError as e:
    print(f"✓ Caught expected error: {e}")
print()

print("=" * 60)
print("All examples complete!")
print()
print("Key Takeaways:")
print("  1. EasySportModel makes training simple - just pass dicts!")
print("  2. Quick prediction functions for instant results")
print("  3. AutoFeatures creates required features automatically")
print("  4. train_and_predict() is complete end-to-end workflow")
print("  5. Same interface works for ALL sports")
print("  6. Data validation catches errors early")
print("  7. Required features are documented")
