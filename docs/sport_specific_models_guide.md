

# Sport-Specific ML Models Guide

Build machine learning models optimized for each sport with pre-configured templates and sport-specific feature engineering.

## Table of Contents

- [Quick Start](#quick-start)
- [NBA Models](#nba-models)
- [NFL Models](#nfl-models)
- [NHL Models](#nhl-models)
- [MLB Models](#mlb-models)
- [College Football Models](#college-football-models)
- [College Basketball Models](#college-basketball-models)
- [Soccer Models](#soccer-models)
- [Horse Racing Models](#horse-racing-models)
- [Sport-Specific Features](#sport-specific-features)
- [Complete Examples](#complete-examples)

## Quick Start

```python
from lib.sport_models import NBAModels, get_sport_model
from lib.model_builder import split_data

# Option 1: Use sport-specific model class
nba_model = NBAModels.game_winner_model()

# Option 2: Use helper function
nba_model = get_sport_model('nba', 'game_winner')

# Train and evaluate
X_train, X_test, y_train, y_test = split_data(X, y)
nba_model.train(X_train, y_train)
nba_model.print_performance(X_test, y_test)
```

## NBA Models

### Game Winner Model

Predict NBA game winners with team efficiency metrics.

```python
from lib.sport_models import NBAModels

model = NBAModels.game_winner_model()
```

**Expected Features (in order):**
1. `team_offensive_rating` - Points per 100 possessions
2. `team_defensive_rating` - Opponent points per 100 possessions
3. `opponent_offensive_rating`
4. `opponent_defensive_rating`
5. `home_court` - 1 if home, 0 if away
6. `rest_days_team` - Days since last game
7. `rest_days_opponent`
8. `pace` - Possessions per game

**Configuration:**
- Random Forest: 150 trees, depth 12
- Standard normalization
- Classification task

**Example:**
```python
# Your data: [team_off, team_def, opp_off, opp_def, home, rest_team, rest_opp, pace]
X = [[112.5, 108.2, 110.1, 109.5, 1, 2, 1, 100.5], ...]
y = [1, 0, 1, 1, ...]  # 1=win, 0=loss

model = NBAModels.game_winner_model()
model.train(X_train, y_train)
predictions = model.predict(X_test)
```

### Spread Model

Predict if team covers the spread.

```python
model = NBAModels.spread_model()
```

**Expected Features:**
1. `rating_differential` - (team - opponent) net rating
2. `spread` - Point spread
3. `home_court` - 1/0
4. `rest_advantage` - (team_rest - opp_rest)
5. `pace_differential` - Difference in preferred pace

**Configuration:**
- Random Forest: 200 trees, depth 15
- Standard normalization

### Total Points Model

Predict total points in the game.

```python
model = NBAModels.total_points_model()
```

**Expected Features:**
1. `team_ppg` - Team points per game
2. `opponent_ppg` - Opponent points per game
3. `pace` - Expected pace
4. `defensive_efficiency_combined` - Combined defensive rating
5. `offensive_efficiency_combined` - Combined offensive rating

**Configuration:**
- Random Forest: 150 trees, depth 18
- Regression task

### Player Points Model

Predict individual player points.

```python
model = NBAModels.player_points_model()
```

**Expected Features:**
1. `player_ppg` - Player's points per game average
2. `minutes_avg` - Average minutes played
3. `usage_rate` - Player's usage rate
4. `matchup_defensive_rating` - Opponent's defensive rating
5. `home_court` - 1/0

**Configuration:**
- Random Forest: 100 trees, depth 15
- Min-max normalization
- Regression task

## NFL Models

### Game Winner Model

```python
from lib.sport_models import NFLModels

model = NFLModels.game_winner_model()
```

**Expected Features:**
1. `team_offensive_dvoa` - Offensive DVOA
2. `team_defensive_dvoa` - Defensive DVOA
3. `opponent_offensive_dvoa`
4. `opponent_defensive_dvoa`
5. `home_field` - 1/0
6. `weather_factor` - 0-1 (0=ideal, 1=terrible)
7. `rest_days_team`
8. `rest_days_opponent`

**Configuration:**
- Random Forest: 180 trees, depth 14

### Spread Model

```python
model = NFLModels.spread_model()
```

**Expected Features:**
1. `dvoa_differential` - Total DVOA difference
2. `spread` - Point spread
3. `home_field` - 1/0
4. `weather_factor` - 0-1
5. `rest_advantage` - Rest days differential

**Configuration:**
- Random Forest: 200 trees, depth 16

### Total Points Model

```python
model = NFLModels.total_points_model()
```

**Expected Features:**
1. `team_ppg`
2. `opponent_ppg`
3. `team_yards_per_play`
4. `opponent_yards_per_play`
5. `weather_factor`
6. `pace`

## NHL Models

### Game Winner Model

```python
from lib.sport_models import NHLModels

model = NHLModels.game_winner_model()
```

**Expected Features:**
1. `team_goals_for_avg`
2. `team_goals_against_avg`
3. `opponent_goals_for_avg`
4. `opponent_goals_against_avg`
5. `team_corsi_for_pct` - Possession metric
6. `opponent_corsi_for_pct`
7. `team_save_pct` - Goaltender save percentage
8. `opponent_save_pct`
9. `home_ice` - 1/0

**Configuration:**
- Random Forest: 150 trees, depth 12

### Puck Line Model

Predict 1.5 goal spread coverage.

```python
model = NHLModels.puck_line_model()
```

**Expected Features:**
1. `expected_goals_differential` - xG difference
2. `puck_line` - Usually -1.5 or +1.5
3. `home_ice` - 1/0
4. `goalie_gsax_team` - Goals Saved Above Expected
5. `goalie_gsax_opponent`

**Configuration:**
- Random Forest: 180 trees, depth 14

### Total Goals Model

```python
model = NHLModels.total_goals_model()
```

**Expected Features:**
1. `team_goals_for_avg`
2. `opponent_goals_for_avg`
3. `team_expected_goals_avg`
4. `opponent_expected_goals_avg`
5. `team_save_pct`
6. `opponent_save_pct`

## MLB Models

### Game Winner Model

```python
from lib.sport_models import MLBModels

model = MLBModels.game_winner_model()
```

**Expected Features:**
1. `team_runs_per_game`
2. `opponent_runs_per_game`
3. `pitcher_era` - Starting pitcher ERA
4. `opponent_pitcher_era`
5. `pitcher_whip` - Walks + hits per inning
6. `opponent_pitcher_whip`
7. `team_batting_avg`
8. `opponent_batting_avg`
9. `home_field` - 1/0
10. `park_factor` - Ballpark run factor

**Configuration:**
- Random Forest: 160 trees, depth 13

### Run Line Model

Predict 1.5 run spread coverage.

```python
model = MLBModels.run_line_model()
```

**Expected Features:**
1. `run_differential` - Team - opponent run differential
2. `run_line` - Usually -1.5 or +1.5
3. `pitcher_quality_differential`
4. `home_field` - 1/0
5. `park_factor`

### Total Runs Model

```python
model = MLBModels.total_runs_model()
```

**Expected Features:**
1. `team_runs_per_game`
2. `opponent_runs_per_game`
3. `pitcher_era`
4. `opponent_pitcher_era`
5. `park_factor`
6. `weather_factor`

## College Football Models

### Game Winner Model

```python
from lib.sport_models import CollegeFootballModels

model = CollegeFootballModels.game_winner_model()
```

**Expected Features:**
1. `team_sp_plus_rating` - SP+ rating
2. `opponent_sp_plus_rating`
3. `conference_strength_team` - 1-5 scale
4. `conference_strength_opponent`
5. `home_field` - 1/0
6. `rivalry_game` - 1/0

**Configuration:**
- Random Forest: 180 trees, depth 14

### Spread Model

```python
model = CollegeFootballModels.spread_model()
```

**Expected Features:**
1. `rating_differential`
2. `spread`
3. `conference_matchup_factor` - P5 vs G5 adjustment
4. `home_field` - 1/0
5. `rivalry_game` - 1/0 (compresses spreads)

### Total Points Model

```python
model = CollegeFootballModels.total_points_model()
```

**Expected Features:**
1. `team_ppg`
2. `opponent_ppg`
3. `pace_factor`
4. `defensive_efficiency_combined`

## College Basketball Models

### Game Winner Model

```python
from lib.sport_models import CollegeBasketballModels

model = CollegeBasketballModels.game_winner_model()
```

**Expected Features:**
1. `team_kenpom_rating` - KenPom rating
2. `opponent_kenpom_rating`
3. `team_offensive_efficiency` - Points per 100 possessions
4. `team_defensive_efficiency`
5. `opponent_offensive_efficiency`
6. `opponent_defensive_efficiency`
7. `home_court` - 1/0
8. `conference_strength_team`
9. `conference_strength_opponent`

**Configuration:**
- Random Forest: 170 trees, depth 13

### Spread Model

```python
model = CollegeBasketballModels.spread_model()
```

**Expected Features:**
1. `efficiency_margin` - Offensive - defensive efficiency
2. `spread`
3. `home_court` - 1/0
4. `tempo_differential` - Pace difference

### March Madness Upset Model

Special model for tournament upsets.

```python
model = CollegeBasketballModels.march_madness_upset_model()
```

**Expected Features:**
1. `seed_differential` - (lower seed - higher seed)
2. `kenpom_rating_differential`
3. `tournament_experience_team` - Prior tournament games
4. `tournament_experience_opponent`
5. `pace_differential`

**Configuration:**
- Random Forest: 200 trees, depth 14
- Optimized for upset detection

## Soccer Models

### Three-Way Result Model

Predict home/draw/away outcome.

```python
from lib.sport_models import SoccerModels

model = SoccerModels.three_way_result_model()
```

**Expected Features:**
1. `team_expected_goals_avg` - xG per game
2. `opponent_expected_goals_avg`
3. `team_goals_for_avg`
4. `team_goals_against_avg`
5. `opponent_goals_for_avg`
6. `opponent_goals_against_avg`
7. `home_advantage` - 1/0
8. `league_home_draw_away_factor` - League characteristics

**Output:** 0=away win, 1=draw, 2=home win

**Configuration:**
- Neural Network: [15, 10] hidden layers
- Standard normalization (required for NN)

### BTTS Model

Predict Both Teams To Score.

```python
model = SoccerModels.btts_model()
```

**Expected Features:**
1. `team_goals_for_avg`
2. `opponent_goals_for_avg`
3. `team_clean_sheet_pct` - Clean sheet percentage
4. `opponent_clean_sheet_pct`
5. `league_btts_frequency` - League BTTS rate

### Total Goals Model

```python
model = SoccerModels.total_goals_model()
```

**Expected Features:**
1. `team_goals_for_avg`
2. `opponent_goals_for_avg`
3. `team_expected_goals_avg`
4. `opponent_expected_goals_avg`
5. `league_avg_goals` - League average total goals

## Horse Racing Models

### Win Probability Model

```python
from lib.sport_models import HorseRacingModels

model = HorseRacingModels.win_probability_model()
```

**Expected Features:**
1. `speed_figure` - Beyer speed figure or equivalent
2. `post_position` - Starting position
3. `jockey_win_pct` - Jockey win percentage
4. `trainer_win_pct` - Trainer win percentage
5. `track_condition_factor` - Track condition rating
6. `class_level` - Class of race
7. `days_since_last_race`
8. `career_earnings`

**Configuration:**
- Random Forest: 200 trees, depth 16
- Min-max normalization

### Exacta Model

Predict top 2 finishers.

```python
model = HorseRacingModels.exacta_model()
```

**Expected Features:**
1. `horse1_speed_figure`
2. `horse2_speed_figure`
3. `horse1_post_position`
4. `horse2_post_position`
5. `horse1_jockey_win_pct`
6. `horse2_jockey_win_pct`
7. `distance_suitability_horse1`
8. `distance_suitability_horse2`

### Speed Rating Predictor

Predict horse's speed rating for this race.

```python
model = HorseRacingModels.speed_rating_predictor()
```

**Expected Features:**
1. `last_speed_figure` - Most recent race
2. `avg_speed_figure_l3` - Last 3 races average
3. `track_surface_performance` - Performance on this surface
4. `distance_performance` - Performance at this distance
5. `jockey_trainer_combo_factor` - Jockey-trainer combination stat

## Sport-Specific Features

Create sport-specific features with helper functions.

### NBA Features

```python
from lib.sport_features import NBAFeatures

# Rating differential
rating_diff = NBAFeatures.create_rating_differential(
    team_off_rtg=112.5,
    team_def_rtg=108.2,
    opp_off_rtg=110.1,
    opp_def_rtg=109.5
)

# Rest advantage
rest_adv = NBAFeatures.create_rest_advantage(
    team_days_rest=2,
    opp_days_rest=1
)

# Four Factors score
four_factors = NBAFeatures.create_four_factors_score(
    efg_pct=0.54,
    tov_pct=0.12,
    orb_pct=0.28,
    ftr=0.25
)
```

### NFL Features

```python
from lib.sport_features import NFLFeatures

# DVOA differential
dvoa_diff = NFLFeatures.create_dvoa_differential(
    team_off_dvoa=12.5,
    team_def_dvoa=-8.2,
    opp_off_dvoa=5.1,
    opp_def_dvoa=-3.5
)

# Weather factor
weather = NFLFeatures.create_weather_factor(
    temperature=28,      # Fahrenheit
    wind_speed=18,       # mph
    precipitation=0.3    # 0-1 scale
)
```

### NHL Features

```python
from lib.sport_features import NHLFeatures

# Expected goals differential
xg_diff = NHLFeatures.create_expected_goals_differential(
    team_xgf_avg=3.2,
    team_xga_avg=2.5,
    opp_xgf_avg=2.8,
    opp_xga_avg=2.9
)

# Goalie advantage
goalie_adv = NHLFeatures.create_goalie_advantage(
    team_gsax=5.2,
    opp_gsax=-2.1
)
```

### MLB Features

```python
from lib.sport_features import MLBFeatures

# Pitcher quality differential
pitcher_diff = MLBFeatures.create_pitcher_quality_differential(
    team_pitcher_era=3.20,
    team_pitcher_whip=1.15,
    opp_pitcher_era=4.50,
    opp_pitcher_whip=1.35
)

# Park-adjusted runs
park_runs = MLBFeatures.create_park_adjusted_runs(
    team_runs=4.8,
    park_factor=1.12  # Hitter-friendly park
)
```

### College Football Features

```python
from lib.sport_features import CollegeFootballFeatures

# Rivalry factor (compresses spreads)
adjusted_diff = CollegeFootballFeatures.create_rivalry_factor(
    is_rivalry=True,
    rating_differential=21.0
)  # Returns 12.6 (compressed by 40%)

# Conference matchup factor
matchup = CollegeFootballFeatures.create_matchup_factor(
    team_conference='SEC',
    opp_conference='Sun Belt',
    power_five_conferences=['SEC', 'Big Ten', 'ACC', 'Big 12', 'Pac-12']
)  # Returns 1.2 (P5 vs G5 advantage)
```

### Soccer Features

```python
from lib.sport_features import SoccerFeatures

# BTTS probability
btts_prob = SoccerFeatures.create_btts_probability(
    team_gf_avg=1.8,
    team_ga_avg=1.2,
    opp_gf_avg=1.5,
    opp_ga_avg=1.3,
    team_clean_sheet_pct=0.35,
    opp_clean_sheet_pct=0.40
)

# League adjustment
adjusted_goals = SoccerFeatures.create_league_adjustment(
    base_value=2.6,
    league='bundesliga'  # Higher scoring league
)  # Returns 2.99
```

### Horse Racing Features

```python
from lib.sport_features import HorseRacingFeatures

# Speed figure trend
trend = HorseRacingFeatures.create_speed_figure_trend(
    last_3_figures=[92, 88, 84]  # Most recent first
)  # Returns +4.0 (improving)

# Post position factor
post_factor = HorseRacingFeatures.create_post_position_factor(
    post_position=1,
    field_size=10,
    distance_furlongs=6
)  # Returns 1.1 (inside post advantage in sprint)
```

## Complete Examples

### Example 1: NBA Game Prediction

```python
from lib.sport_models import NBAModels
from lib.sport_features import NBAFeatures
from lib.model_builder import split_data

# Prepare features using helper functions
def prepare_nba_features(team_data, opp_data, game_data):
    features = []

    # Create rating differential
    rating_diff = NBAFeatures.create_rating_differential(
        team_data['off_rtg'], team_data['def_rtg'],
        opp_data['off_rtg'], opp_data['def_rtg']
    )

    # Create rest advantage
    rest_adv = NBAFeatures.create_rest_advantage(
        team_data['rest_days'], opp_data['rest_days']
    )

    features = [
        team_data['off_rtg'],
        team_data['def_rtg'],
        opp_data['off_rtg'],
        opp_data['def_rtg'],
        game_data['home'],
        team_data['rest_days'],
        opp_data['rest_days'],
        NBAFeatures.create_pace_factor(team_data['pace'], opp_data['pace'])
    ]

    return features

# Build and train model
model = NBAModels.game_winner_model()
X_train, X_test, y_train, y_test = split_data(X, y)
model.train(X_train, y_train)
model.print_performance(X_test, y_test)
```

### Example 2: NFL with Weather

```python
from lib.sport_models import NFLModels
from lib.sport_features import NFLFeatures

# Create weather factor
weather_factor = NFLFeatures.create_weather_factor(
    temperature=25,
    wind_speed=22,
    precipitation=0.4
)

# Prepare NFL spread features
features = [
    dvoa_diff,
    spread,
    1,  # home
    weather_factor,
    rest_advantage
]

model = NFLModels.spread_model()
model.train(X_train, y_train)
```

### Example 3: March Madness Upsets

```python
from lib.sport_models import CollegeBasketballModels
from lib.sport_features import CollegeBasketballFeatures

# Calculate tournament experience
team_exp = CollegeBasketballFeatures.create_tournament_experience_factor(
    games_played=8,
    final_four_appearances=2,
    championship_appearances=1
)

# Build upset model
model = CollegeBasketballModels.march_madness_upset_model()
model.train(X_train, y_train)
```

## get_sport_model() Helper

Easy access to any sport model:

```python
from lib.sport_models import get_sport_model

# Get model by sport and type
model = get_sport_model('nba', 'spread_model')
model = get_sport_model('nfl', 'total_points')  # _model suffix optional
model = get_sport_model('soccer', 'btts')

# Available sports
sports = ['nba', 'nfl', 'nhl', 'mlb', 'cfb', 'cbb', 'soccer', 'horse_racing']
```

## Best Practices

1. **Use Sport-Specific Models** - They're pre-tuned for each sport's characteristics
2. **Feature Engineering Matters** - Use sport feature helpers for better results
3. **Understand Your Features** - Each model documents expected feature order
4. **Normalization is Included** - Models automatically normalize features
5. **Conference/League Adjustments** - CFB, CBB, and Soccer models account for league differences
6. **Weather Matters** - NFL and MLB models include weather factors
7. **Rivalry Games** - CFB model compresses spreads for rivalries
8. **Tournament Context** - March Madness model uses seed and experience

## See Also

- [ML Model Builder Guide](ml_model_builder_guide.md) - General model building
- [Simple API Guide](simple_api_guide.md) - For Kelly, EV calculations
- [Examples](../examples/sport_specific_models.py) - 12 working examples

---

For more information, see the main [README](../README.md).
