# Easy Sport Models Guide

The simplest way to build sport-specific ML models. No feature engineering needed!

## Why Easy Sport Models?

The standard sport models require you to:
1. Know the exact feature names and order
2. Manually create feature arrays
3. Handle train/test splitting
4. Convert dictionaries to arrays

**Easy Sport Models do all of this for you!**

## Quick Start

```python
from lib.easy_sport_models import EasySportModel

# Create model
model = EasySportModel('nba', 'game_winner')

# Train with dict data (no arrays needed!)
games = [
    {
        'team_offensive_rating': 115.0,
        'team_defensive_rating': 107.5,
        'opponent_offensive_rating': 110.2,
        'opponent_defensive_rating': 109.8,
        'home_court': 1,
        'rest_days_team': 2,
        'rest_days_opponent': 1,
        'pace': 100.5,
        'result': 1  # Win
    },
    # ... more games
]

model.fit(games)

# Predict with dict (no arrays needed!)
new_game = {
    'team_offensive_rating': 116.0,
    'team_defensive_rating': 108.0,
    'opponent_offensive_rating': 111.0,
    'opponent_defensive_rating': 110.0,
    'home_court': 1,
    'rest_days_team': 2,
    'rest_days_opponent': 2,
    'pace': 101.0
}

prediction = model.predict(new_game)  # 1 or 0
probability = model.predict_proba(new_game)  # 0.0 to 1.0

print(f"Win probability: {probability:.1%}")
```

## Core Features

### 1. EasySportModel Class

Train and predict with dictionaries instead of arrays.

```python
# Create model for any sport
nba_model = EasySportModel('nba', 'game_winner')
nfl_model = EasySportModel('nfl', 'spread')
soccer_model = EasySportModel('soccer', 'btts')

# Train
model.fit(games_data)

# Predict
prediction = model.predict(game_dict)
probability = model.predict_proba(game_dict)

# Evaluate
metrics = model.evaluate()
model.summary()  # Print formatted report

# Check requirements
features = model.required_features()
```

### 2. Quick Prediction Functions

Get instant predictions without training models.

```python
from lib.easy_sport_models import (
    quick_nba_prediction,
    quick_nfl_prediction,
    quick_soccer_btts
)

# NBA
win_prob = quick_nba_prediction(
    team_off_rtg=115.0,
    team_def_rtg=107.5,
    opp_off_rtg=110.2,
    opp_def_rtg=109.8,
    home=True
)

# NFL (with weather)
win_prob = quick_nfl_prediction(
    team_dvoa=15.0,
    opp_dvoa=5.0,
    home=True,
    temperature=35,
    wind_speed=20
)

# Soccer BTTS
btts_prob = quick_soccer_btts(
    team_goals_avg=1.8,
    opp_goals_avg=1.5
)
```

### 3. AutoFeatures Helper

Automatically create required features from basic stats.

```python
from lib.easy_sport_models import AutoFeatures

# NBA - provide basic stats, get all required features
team_stats = {'off_rtg': 115, 'def_rtg': 107.5, 'pace': 102, 'rest_days': 2}
opp_stats = {'off_rtg': 110, 'def_rtg': 109, 'pace': 99, 'rest_days': 1}
game_info = {'home': True}

features = AutoFeatures.nba_game_features(team_stats, opp_stats, game_info)
# Returns all 8 required features automatically!

# NFL with weather
nfl_features = AutoFeatures.nfl_game_features(
    {'off_dvoa': 15, 'def_dvoa': -8},
    {'off_dvoa': 5, 'def_dvoa': -3},
    {'home': True, 'temp': 35, 'wind': 15}
)

# Soccer
soccer_features = AutoFeatures.soccer_game_features(
    {'gf_avg': 1.8, 'ga_avg': 1.2, 'clean_sheet_pct': 0.35},
    {'gf_avg': 1.5, 'ga_avg': 1.3, 'clean_sheet_pct': 0.40},
    {'home': True, 'league': 'epl'},
    model_type='btts'
)
```

### 4. Data Validation

Check if your data is valid before training.

```python
from lib.easy_sport_models import validate_nba_data, validate_sport_data

# NBA validation
valid, errors = validate_nba_data(games)
if not valid:
    print("Errors:", errors)

# Any sport validation
valid, errors = validate_sport_data('nfl', 'spread', games)
```

### 5. End-to-End Workflow

Complete workflow in one function call.

```python
from lib.easy_sport_models import train_and_predict

predictions = train_and_predict(
    sport='nba',
    model_type='game_winner',
    historical_games=past_games,
    new_games=upcoming_games,
    show_performance=True  # Prints metrics
)
```

## Complete Examples

### Example 1: NBA Game Predictions

```python
from lib.easy_sport_models import EasySportModel

# Historical games (dict format - easy!)
historical = [
    {
        'team_offensive_rating': 115.0,
        'team_defensive_rating': 107.5,
        'opponent_offensive_rating': 110.2,
        'opponent_defensive_rating': 109.8,
        'home_court': 1,
        'rest_days_team': 2,
        'rest_days_opponent': 1,
        'pace': 100.5,
        'result': 1
    },
    # ... 100+ more games
]

# Train
model = EasySportModel('nba', 'game_winner')
model.fit(historical)

# Show performance
model.summary()

# Predict tonight's games
lakers_celtics = {
    'team_offensive_rating': 116.0,
    'team_defensive_rating': 108.0,
    'opponent_offensive_rating': 115.5,
    'opponent_defensive_rating': 107.2,
    'home_court': 1,
    'rest_days_team': 2,
    'rest_days_opponent': 1,
    'pace': 101.5
}

prediction = model.predict(lakers_celtics)
probability = model.predict_proba(lakers_celtics)

print(f"Lakers to beat Celtics: {probability:.1%}")
```

### Example 2: NFL with AutoFeatures

```python
from lib.easy_sport_models import EasySportModel, AutoFeatures

# Use AutoFeatures to prepare data easily
chiefs_stats = {'off_dvoa': 18.5, 'def_dvoa': -12.0}
bills_stats = {'off_dvoa': 15.2, 'def_dvoa': -8.5}
game_info = {
    'home': True,
    'temp': 28,      # Cold playoff game
    'wind': 20,      # Windy
    'rest_team': 7,
    'rest_opp': 7
}

# AutoFeatures creates all required features
game_features = AutoFeatures.nfl_game_features(
    chiefs_stats, bills_stats, game_info
)

# Train model on historical data (prepared the same way)
nfl_model = EasySportModel('nfl', 'game_winner')
nfl_model.fit(historical_nfl_games)

# Predict
prediction = nfl_model.predict(game_features)
probability = nfl_model.predict_proba(game_features)

print(f"Chiefs to beat Bills: {probability:.1%}")
print(f"Weather impact included: {game_features['weather_factor']:.2f}")
```

### Example 3: Quick Predictions (No Training)

```python
from lib.easy_sport_models import (
    quick_nba_prediction,
    quick_nfl_prediction,
    quick_soccer_btts
)

# NBA - instant prediction
prob = quick_nba_prediction(
    team_off_rtg=115.0,
    team_def_rtg=107.5,
    opp_off_rtg=110.2,
    opp_def_rtg=109.8,
    home=True,
    rest_team=2,
    rest_opp=1
)
print(f"NBA win probability: {prob:.1%}")

# NFL - instant with weather
prob = quick_nfl_prediction(
    team_dvoa=15.0,
    opp_dvoa=5.0,
    home=True,
    temperature=35,
    wind_speed=18
)
print(f"NFL win probability: {prob:.1%}")

# Soccer BTTS - instant
prob = quick_soccer_btts(
    team_goals_avg=1.8,
    opp_goals_avg=1.5,
    team_clean_sheets=0.30,
    opp_clean_sheets=0.35
)
print(f"BTTS probability: {prob:.1%}")
```

### Example 4: End-to-End Workflow

```python
from lib.easy_sport_models import train_and_predict

# Complete workflow: train + predict + evaluate
predictions = train_and_predict(
    sport='nba',
    model_type='game_winner',
    historical_games=past_200_games,  # List of dicts
    new_games=tonights_10_games,      # List of dicts
    show_performance=True             # Prints metrics
)

# Output:
# NBA game_winner Model Performance:
# ============================================================
# Accuracy:  0.875
# Precision: 0.863
# Recall:    0.891
# ============================================================
#
# Returns: [1, 0, 1, 1, 0, 1, 1, 0, 1, 1]
```

### Example 5: Data Validation

```python
from lib.easy_sport_models import validate_sport_data

# Validate before training
games = [
    {'team_offensive_rating': 115, 'team_defensive_rating': 107, ...},
    {'team_offensive_rating': 110, ...}  # Missing some fields
]

valid, errors = validate_sport_data('nba', 'game_winner', games)

if not valid:
    print("Data validation failed:")
    for error in errors:
        print(f"  - {error}")
    # Fix data before training
else:
    # Proceed with training
    model.fit(games)
```

### Example 6: Multiple Sports - Same Interface

```python
from lib.easy_sport_models import EasySportModel

# NBA
nba = EasySportModel('nba', 'game_winner')
nba.fit(nba_games)
nba_pred = nba.predict(new_nba_game)

# NFL
nfl = EasySportModel('nfl', 'spread')
nfl.fit(nfl_games)
nfl_pred = nfl.predict(new_nfl_game)

# NHL
nhl = EasySportModel('nhl', 'total_goals')
nhl.fit(nhl_games)
nhl_pred = nhl.predict(new_nhl_game)

# Soccer
soccer = EasySportModel('soccer', 'btts')
soccer.fit(soccer_games)
soccer_pred = soccer.predict(new_soccer_game)

# Same interface for all sports!
```

## Available Sports & Models

All sport models from the standard interface work with Easy Sport Models:

- **NBA**: `game_winner`, `spread`, `total_points`, `player_points`
- **NFL**: `game_winner`, `spread`, `total_points`
- **NHL**: `game_winner`, `puck_line`, `total_goals`
- **MLB**: `game_winner`, `run_line`, `total_runs`
- **CFB**: `game_winner`, `spread`, `total_points`
- **CBB**: `game_winner`, `spread`, `march_madness_upset`
- **Soccer**: `three_way_result`, `btts`, `total_goals`
- **Horse Racing**: `win_probability`, `exacta`, `speed_rating_predictor`

## Comparison: Standard vs Easy

### Standard Interface (More Control)

```python
from lib.sport_models import NBAModels
from lib.model_builder import split_data

# Must create arrays manually
X = [[115, 107.5, 110.2, 109.8, 1, 2, 1, 100.5], ...]
y = [1, 0, 1, ...]

# Manual train/test split
X_train, X_test, y_train, y_test = split_data(X, y)

# Train
model = NBAModels.game_winner_model()
model.train(X_train, y_train)

# Predict (must create array in exact order)
prediction = model.predict([[116, 108, 111, 110, 1, 2, 2, 101]])
```

### Easy Interface (More Convenient)

```python
from lib.easy_sport_models import EasySportModel

# Use dicts (clear and easy)
games = [
    {
        'team_offensive_rating': 115,
        'team_defensive_rating': 107.5,
        'opponent_offensive_rating': 110.2,
        'opponent_defensive_rating': 109.8,
        'home_court': 1,
        'rest_days_team': 2,
        'rest_days_opponent': 1,
        'pace': 100.5,
        'result': 1
    },
    # ...
]

# Train (automatic split)
model = EasySportModel('nba', 'game_winner')
model.fit(games)

# Predict (dict with feature names)
prediction = model.predict({
    'team_offensive_rating': 116,
    'team_defensive_rating': 108,
    'opponent_offensive_rating': 111,
    'opponent_defensive_rating': 110,
    'home_court': 1,
    'rest_days_team': 2,
    'rest_days_opponent': 2,
    'pace': 101
})
```

## Tips

1. **Use Quick Functions for Instant Results** - No training needed
2. **Use AutoFeatures to Prepare Data** - Handles feature creation
3. **Validate Before Training** - Catch errors early
4. **Use Dicts, Not Arrays** - More readable and less error-prone
5. **Same Interface for All Sports** - Learn once, use everywhere
6. **Check Required Features** - `model.required_features()`
7. **Use train_and_predict() for Complete Workflow** - One function does everything

## When to Use Standard vs Easy

**Use Easy Interface when:**
- You want simplicity and convenience
- You're working with dict data
- You want automatic data validation
- You're prototyping quickly

**Use Standard Interface when:**
- You need maximum control
- You're doing custom feature engineering
- You have existing array-based pipelines
- You need to customize train/test split

Both interfaces use the same underlying models, so performance is identical!

## See Also

- [Sport-Specific Models Guide](sport_specific_models_guide.md) - Standard interface
- [ML Model Builder Guide](ml_model_builder_guide.md) - General model building
- [Examples](../examples/easy_sport_models_examples.py) - 10 complete examples

---

For more information, see the main [README](../README.md).
