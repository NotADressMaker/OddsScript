#!/usr/bin/env python3
"""
Sport-Specific ML Model Examples

Shows how to build machine learning models tailored for each sport.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.sport_models import (
    NBAModels, NFLModels, NHLModels, MLBModels,
    CollegeFootballModels, CollegeBasketballModels,
    SoccerModels, HorseRacingModels,
    get_sport_model
)
from lib.model_builder import DataHelper, split_data
import random

print("SportsBetLang - Sport-Specific ML Models")
print("=" * 60)
print()

# ========================================
# Example 1: NBA Game Winner Model
# ========================================
print("EXAMPLE 1: NBA Game Winner Model")
print("-" * 60)

# Prepare NBA game data
# Features: [off_rtg, def_rtg, opp_off_rtg, opp_def_rtg, home, rest_team, rest_opp, pace]
nba_X = []
nba_y = []

random.seed(42)
for _ in range(200):
    team_off = random.uniform(105, 118)
    team_def = random.uniform(105, 118)
    opp_off = random.uniform(105, 118)
    opp_def = random.uniform(105, 118)
    home = random.choice([0, 1])
    rest_team = random.randint(0, 4)
    rest_opp = random.randint(0, 4)
    pace = random.uniform(95, 105)

    nba_X.append([team_off, team_def, opp_off, opp_def, home, rest_team, rest_opp, pace])

    # Win probability based on net rating + home court
    net_rating = (team_off - team_def) - (opp_off - opp_def)
    net_rating += 3 if home else 0
    win_prob = 1 / (1 + 10 ** (-net_rating / 15))
    nba_y.append(1 if random.random() < win_prob else 0)

# Split data
X_train, X_test, y_train, y_test = split_data(nba_X, nba_y, test_size=0.2)

# Create NBA-specific model
nba_model = NBAModels.game_winner_model()

# Train
nba_model.train(X_train, y_train)

# Evaluate
metrics = nba_model.evaluate(X_test, y_test)
print(f"NBA Game Winner Model Accuracy: {metrics['accuracy']:.3f}")
print()

# ========================================
# Example 2: NFL Spread Model
# ========================================
print("EXAMPLE 2: NFL Spread Model")
print("-" * 60)

# Create NFL model using get_sport_model helper
nfl_model = get_sport_model('nfl', 'spread_model')

# Generate sample NFL data
# Features: [dvoa_diff, spread, home, weather, rest_advantage]
nfl_X = []
nfl_y = []

for _ in range(180):
    dvoa_diff = random.uniform(-20, 20)
    spread = random.uniform(-14, 14)
    home = random.choice([0, 1])
    weather = random.uniform(0, 1)  # 0=good, 1=bad
    rest_adv = random.randint(-7, 7)

    nfl_X.append([dvoa_diff, spread, home, weather, rest_adv])

    # Cover probability
    expected_margin = dvoa_diff * 0.3 + (3 if home else 0) - weather * 2
    covers = 1 if expected_margin > spread else 0
    nfl_y.append(covers)

X_train, X_test, y_train, y_test = split_data(nfl_X, nfl_y)

nfl_model.train(X_train, y_train)
print(f"NFL Spread Model Accuracy: {nfl_model.evaluate(X_test, y_test)['accuracy']:.3f}")
print()

# ========================================
# Example 3: NHL Total Goals Model
# ========================================
print("EXAMPLE 3: NHL Total Goals Model")
print("-" * 60)

nhl_model = NHLModels.total_goals_model()

# Features: [team_gf, opp_gf, team_xg, opp_xg, team_sv%, opp_sv%]
nhl_X = []
nhl_y = []

for _ in range(200):
    team_gf = random.uniform(2.5, 3.5)
    opp_gf = random.uniform(2.5, 3.5)
    team_xg = random.uniform(2.4, 3.6)
    opp_xg = random.uniform(2.4, 3.6)
    team_sv = random.uniform(0.900, 0.925)
    opp_sv = random.uniform(0.900, 0.925)

    nhl_X.append([team_gf, opp_gf, team_xg, opp_xg, team_sv, opp_sv])

    # Actual total goals with some variance
    expected_total = (team_gf + opp_gf) / 2 + (team_xg + opp_xg) / 2
    actual_total = expected_total + random.gauss(0, 1)
    nhl_y.append(actual_total)

X_train, X_test, y_train, y_test = split_data(nhl_X, nhl_y)

nhl_model.train(X_train, y_train)
metrics = nhl_model.evaluate(X_test, y_test)
print(f"NHL Total Goals Model RMSE: {metrics['rmse']:.3f} goals")
print()

# ========================================
# Example 4: MLB Run Line Model
# ========================================
print("EXAMPLE 4: MLB Run Line Model")
print("-" * 60)

mlb_model = MLBModels.run_line_model()

# Features: [run_diff, run_line, pitcher_quality_diff, home, park_factor]
mlb_X = []
mlb_y = []

for _ in range(200):
    run_diff = random.uniform(-2, 2)
    run_line = -1.5  # Standard MLB run line
    pitcher_diff = random.uniform(-1.5, 1.5)
    home = random.choice([0, 1])
    park_factor = random.uniform(0.9, 1.1)

    mlb_X.append([run_diff, run_line, pitcher_diff, home, park_factor])

    # Cover run line?
    expected_margin = run_diff + pitcher_diff * 0.5 + (0.3 if home else 0)
    expected_margin *= park_factor
    covers = 1 if expected_margin > abs(run_line) else 0
    mlb_y.append(covers)

X_train, X_test, y_train, y_test = split_data(mlb_X, mlb_y)

mlb_model.train(X_train, y_train)
print(f"MLB Run Line Model Accuracy: {mlb_model.evaluate(X_test, y_test)['accuracy']:.3f}")
print()

# ========================================
# Example 5: College Football Spread
# ========================================
print("EXAMPLE 5: College Football Spread Model")
print("-" * 60)

cfb_model = CollegeFootballModels.spread_model()

# Features: [rating_diff, spread, conf_matchup, home, rivalry]
cfb_X = []
cfb_y = []

for _ in range(180):
    rating_diff = random.uniform(-30, 30)
    spread = random.uniform(-24, 24)
    conf_matchup = random.uniform(0.8, 1.2)  # Conference strength matchup
    home = random.choice([0, 1])
    rivalry = random.choice([0, 0, 0, 1])  # 25% are rivalries

    cfb_X.append([rating_diff, spread, conf_matchup, home, rivalry])

    # Spread coverage with rivalry compression
    expected_margin = rating_diff * 0.4 + (3 if home else 0)
    if rivalry:
        expected_margin *= 0.7  # Rivalries are closer
    expected_margin *= conf_matchup

    covers = 1 if expected_margin > spread else 0
    cfb_y.append(covers)

X_train, X_test, y_train, y_test = split_data(cfb_X, cfb_y)

cfb_model.train(X_train, y_train)
print(f"CFB Spread Model Accuracy: {cfb_model.evaluate(X_test, y_test)['accuracy']:.3f}")
print()

# ========================================
# Example 6: March Madness Upsets
# ========================================
print("EXAMPLE 6: March Madness Upset Model")
print("-" * 60)

cbb_model = CollegeBasketballModels.march_madness_upset_model()

# Features: [seed_diff, rating_diff, tourney_exp_team, tourney_exp_opp, pace_diff]
cbb_X = []
cbb_y = []

# Simulate tournament games
for _ in range(150):
    seed_diff = random.randint(-15, 3)  # Lower seed - higher seed
    rating_diff = seed_diff * -2 + random.gauss(0, 3)
    tourney_exp_team = random.randint(0, 5)
    tourney_exp_opp = random.randint(0, 5)
    pace_diff = random.uniform(-5, 5)

    cbb_X.append([seed_diff, rating_diff, tourney_exp_team, tourney_exp_opp, pace_diff])

    # Upset probability (lower seed wins)
    upset_factor = -seed_diff * 0.3 + rating_diff * 0.2
    upset_factor += (tourney_exp_team - tourney_exp_opp) * 0.1
    upset_prob = 1 / (1 + 10 ** (-upset_factor / 10))

    upset = 1 if random.random() < upset_prob else 0
    cbb_y.append(upset)

X_train, X_test, y_train, y_test = split_data(cbb_X, cbb_y)

cbb_model.train(X_train, y_train)
print(f"March Madness Upset Model Accuracy: {cbb_model.evaluate(X_test, y_test)['accuracy']:.3f}")
print()

# ========================================
# Example 7: Soccer BTTS (Both Teams To Score)
# ========================================
print("EXAMPLE 7: Soccer BTTS Model")
print("-" * 60)

soccer_model = SoccerModels.btts_model()

# Features: [team_gf, opp_gf, team_clean_sheet_pct, opp_clean_sheet_pct, league_btts_freq]
soccer_X = []
soccer_y = []

for _ in range(200):
    team_gf = random.uniform(1.0, 2.5)
    opp_gf = random.uniform(1.0, 2.5)
    team_cs_pct = random.uniform(0.2, 0.5)
    opp_cs_pct = random.uniform(0.2, 0.5)
    league_btts = random.uniform(0.45, 0.60)

    soccer_X.append([team_gf, opp_gf, team_cs_pct, opp_cs_pct, league_btts])

    # BTTS probability
    team_scores_prob = 1 - opp_cs_pct + team_gf * 0.1
    opp_scores_prob = 1 - team_cs_pct + opp_gf * 0.1
    btts_prob = team_scores_prob * opp_scores_prob * league_btts

    btts = 1 if random.random() < btts_prob else 0
    soccer_y.append(btts)

X_train, X_test, y_train, y_test = split_data(soccer_X, soccer_y)

soccer_model.train(X_train, y_train)
print(f"Soccer BTTS Model Accuracy: {soccer_model.evaluate(X_test, y_test)['accuracy']:.3f}")
print()

# ========================================
# Example 8: Horse Racing Win Probability
# ========================================
print("EXAMPLE 8: Horse Racing Win Probability")
print("-" * 60)

horse_model = HorseRacingModels.win_probability_model()

# Features: [speed_fig, post_pos, jockey_win%, trainer_win%, track_cond, class, days_rest, earnings]
horse_X = []
horse_y = []

for _ in range(250):
    speed_fig = random.uniform(70, 110)
    post_pos = random.randint(1, 12)
    jockey_win_pct = random.uniform(0.10, 0.25)
    trainer_win_pct = random.uniform(0.10, 0.25)
    track_cond = random.uniform(0.8, 1.0)
    class_level = random.uniform(1, 5)
    days_rest = random.randint(7, 90)
    earnings = random.uniform(50000, 500000)

    horse_X.append([speed_fig, post_pos, jockey_win_pct, trainer_win_pct,
                    track_cond, class_level, days_rest, earnings])

    # Win probability
    base_prob = (speed_fig - 70) / 200
    base_prob += jockey_win_pct * 0.5
    base_prob += trainer_win_pct * 0.5
    base_prob *= track_cond
    if post_pos <= 3:
        base_prob *= 1.1
    elif post_pos >= 10:
        base_prob *= 0.9

    win = 1 if random.random() < base_prob else 0
    horse_y.append(win)

X_train, X_test, y_train, y_test = split_data(horse_X, horse_y)

horse_model.train(X_train, y_train)
print(f"Horse Racing Win Model Accuracy: {horse_model.evaluate(X_test, y_test)['accuracy']:.3f}")

# Feature importance for horse racing
importance = horse_model.feature_importance()
print("\nTop Factors for Horse Racing:")
sorted_importance = sorted(importance.items(), key=lambda x: x[1], reverse=True)
for feature, score in sorted_importance[:5]:
    print(f"  {feature}: {score:.3f}")
print()

# ========================================
# Example 9: Using get_sport_model Helper
# ========================================
print("EXAMPLE 9: Using get_sport_model() Helper")
print("-" * 60)

# Easy way to get any sport model
models_to_try = [
    ('nba', 'total_points'),
    ('nfl', 'game_winner'),
    ('nhl', 'puck_line'),
    ('mlb', 'total_runs'),
]

print("Available sport-specific models:")
for sport, model_type in models_to_try:
    model = get_sport_model(sport, model_type)
    print(f"  {sport.upper()} {model_type}: {model._name}")
print()

# ========================================
# Example 10: NBA Player Points Model
# ========================================
print("EXAMPLE 10: NBA Player Points Prediction")
print("-" * 60)

player_model = NBAModels.player_points_model()

# Features: [ppg, minutes, usage_rate, matchup_def_rating, home]
player_X = []
player_y = []

for _ in range(200):
    ppg = random.uniform(15, 30)
    minutes = random.uniform(28, 38)
    usage = random.uniform(0.20, 0.35)
    matchup_def = random.uniform(105, 118)
    home = random.choice([0, 1])

    player_X.append([ppg, minutes, usage, matchup_def, home])

    # Predicted points
    base_points = ppg
    base_points *= (minutes / 33)  # Minutes adjustment
    base_points *= (usage / 0.25)  # Usage adjustment
    base_points *= (112 / matchup_def)  # Matchup adjustment
    base_points += (1 if home else 0)
    actual_points = base_points + random.gauss(0, 3)

    player_y.append(actual_points)

X_train, X_test, y_train, y_test = split_data(player_X, player_y)

player_model.train(X_train, y_train)
metrics = player_model.evaluate(X_test, y_test)
print(f"Player Points RMSE: {metrics['rmse']:.2f} points")
print(f"R²: {metrics['r_squared']:.3f}")
print()

# ========================================
# Example 11: Custom Sport Model
# ========================================
print("EXAMPLE 11: Customizing Sport Models")
print("-" * 60)

# Start with sport template and customize
custom_nba = (NBAModels.game_winner_model()
              .named("Custom NBA Model v2.0")
              .using_random_forest(n_trees=250, max_depth=20))  # Override defaults

print(f"Customized model: {custom_nba._name}")
print(f"Features: {custom_nba.feature_names}")
print()

# ========================================
# Example 12: Cross-Sport Comparison
# ========================================
print("EXAMPLE 12: Cross-Sport Model Comparison")
print("-" * 60)

# Compare model performance across sports
print("Sport Model Performance Summary:")
print(f"  NBA Game Winner:      {metrics['accuracy']:.3f} accuracy")
print(f"  NFL Spread:           {nfl_model.evaluate(X_test, y_test)['accuracy']:.3f} accuracy")
print(f"  NHL Total Goals:      {nhl_model.evaluate(X_test, y_test)['rmse']:.3f} RMSE")
print(f"  MLB Run Line:         {mlb_model.evaluate(X_test, y_test)['accuracy']:.3f} accuracy")
print(f"  CFB Spread:           {cfb_model.evaluate(X_test, y_test)['accuracy']:.3f} accuracy")
print(f"  March Madness Upset:  {cbb_model.evaluate(X_test, y_test)['accuracy']:.3f} accuracy")
print(f"  Soccer BTTS:          {soccer_model.evaluate(X_test, y_test)['accuracy']:.3f} accuracy")
print(f"  Horse Racing Win:     {horse_model.evaluate(X_test, y_test)['accuracy']:.3f} accuracy")
print()

print("=" * 60)
print("All sport-specific model examples complete!")
print()
print("Key Takeaways:")
print("  - Each sport has pre-configured models")
print("  - Models are tuned for sport-specific characteristics")
print("  - Use get_sport_model() for easy access")
print("  - Customize templates by chaining more methods")
print("  - Feature sets are documented in each model")
