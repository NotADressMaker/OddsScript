# Database Guide

Track all your betting activity, predictions, and performance with the built-in database.

## Why Use the Database?

- **Track every bet** - Store bets, results, and profits
- **Monitor predictions** - Save predictions and track accuracy
- **Historical data** - Store games for ML model training
- **Bankroll tracking** - Track bankroll changes over time
- **Performance analytics** - ROI, win rate, profit/loss
- **Works everywhere** - Desktop, Replit, anywhere SQLite works
- **No external dependencies** - Built-in SQLite

## Quick Start

```python
from lib.database import BettingDatabase

# Create database
db = BettingDatabase()

# Save a bet
bet_id = db.save_bet(
    matchup="Lakers vs Celtics",
    amount=100,
    odds=2.1,
    predicted_prob=0.58,
    sport='nba'
)

# Save result
db.save_result(bet_id, won=True)

# View performance
db.print_performance()
```

## Creating a Database

```python
from lib.database import BettingDatabase, create_database

# Option 1: Default database (betting.db)
db = BettingDatabase()

# Option 2: Custom path
db = BettingDatabase("my_bets.db")

# Option 3: Convenience function
db = create_database("my_bets.db")
```

The database file is created automatically if it doesn't exist.

## Tracking Bets

### Save a Bet

```python
bet_id = db.save_bet(
    matchup="Lakers vs Celtics",
    amount=100,              # Bet amount in dollars
    odds=2.1,                # Decimal odds
    predicted_prob=0.58,     # Your predicted win probability
    sport='nba',             # Sport name
    bet_type='moneyline',    # Bet type
    notes="Lakers at home"   # Optional notes
)

print(f"Saved bet #{bet_id}")
```

**Automatic Calculations:**
When you provide `predicted_prob`, the database automatically calculates:
- Kelly Criterion size
- Expected Value

### Save Bet Result

```python
# Bet won
db.save_result(bet_id, won=True)

# Bet lost
db.save_result(bet_id, won=False)

# Bet won with different closing odds
db.save_result(bet_id, won=True, actual_odds=2.15)
```

The database automatically calculates profit/loss.

### Get Bets

```python
# Get all bets
all_bets = db.get_bets()

# Get last 10 bets
recent_bets = db.get_bets(limit=10)

# Get NBA bets only
nba_bets = db.get_bets(sport='nba')

# Get winning bets
winning_bets = db.get_bets(result='won')

# Get losing bets
losing_bets = db.get_bets(result='lost')

# Get pending bets (no result yet)
pending_bets = db.get_bets(result='pending')

# Combine filters
nba_wins = db.get_bets(sport='nba', result='won', limit=20)
```

**Bet Dictionary:**
```python
{
    'id': 1,
    'timestamp': '2024-01-15T18:30:00',
    'matchup': 'Lakers vs Celtics',
    'sport': 'nba',
    'bet_type': 'moneyline',
    'amount': 100.0,
    'odds': 2.1,
    'predicted_probability': 0.58,
    'expected_value': 12.0,
    'kelly_size': 0.15,
    'result': 'won',
    'profit': 110.0,
    'notes': 'Lakers at home'
}
```

## Tracking Predictions

### Save a Prediction

```python
pred_id = db.save_prediction(
    matchup="Warriors vs Nets",
    predicted_value=1,           # 1 = Warriors win, 0 = Warriors lose
    predicted_prob=0.65,         # Probability
    sport='nba',
    prediction_type='game_winner',
    model_used='NBA ML Model v1',
    confidence=0.70,             # Model confidence
    features={                   # Features used
        'team_off_rtg': 115,
        'team_def_rtg': 108,
        # ... more features
    }
)
```

### Save Prediction Result

```python
# Warriors won!
db.save_prediction_result(pred_id, actual_value=1)

# Warriors lost
db.save_prediction_result(pred_id, actual_value=0)
```

The database automatically marks if prediction was correct.

### Get Predictions

```python
# All predictions
predictions = db.get_predictions()

# Filter by sport
nba_predictions = db.get_predictions(sport='nba')

# Filter by model
model_predictions = db.get_predictions(model='NBA ML Model v1')

# Combine
recent_nba = db.get_predictions(sport='nba', limit=20)
```

### Check Prediction Accuracy

```python
accuracy = db.get_prediction_accuracy(model='NBA ML Model v1')

print(f"Total predictions: {accuracy['total_predictions']}")
print(f"Correct: {accuracy['correct_predictions']}")
print(f"Accuracy: {accuracy['accuracy']:.1%}")
print(f"Avg confidence: {accuracy['avg_confidence']:.1%}")
```

## Storing Historical Games

Store game data for future ML model training:

```python
game_id = db.save_game(
    date="2024-01-15",
    sport="nba",
    matchup="Lakers vs Celtics",
    home_team="Lakers",
    away_team="Celtics",
    home_score=118,
    away_score=112,
    features={
        'team_offensive_rating': 115.0,
        'team_defensive_rating': 107.5,
        'opponent_offensive_rating': 112.2,
        'opponent_defensive_rating': 108.3,
        'home_court': 1,
        'rest_days_team': 2,
        'rest_days_opponent': 1,
        'pace': 101.5
    },
    notes="Strong defensive game"
)
```

### Get Historical Games

```python
# All games
games = db.get_games()

# Filter by sport
nba_games = db.get_games(sport='nba')

# Filter by date range
recent_games = db.get_games(
    sport='nba',
    date_from='2024-01-01',
    date_to='2024-01-31'
)

# Limit results
last_100 = db.get_games(sport='nba', limit=100)
```

### Train Models from Historical Data

```python
from lib import EasySportModel

# Get historical games
games = db.get_games(sport='nba', limit=200)

# Convert to training data
training_data = []
for game in games:
    if game['features'] and game['result']:
        features = game['features']
        features['result'] = 1 if game['result'] == 'home_win' else 0
        training_data.append(features)

# Train model
model = EasySportModel('nba', 'game_winner')
model.fit(training_data)

# Make predictions
new_prediction = model.predict(new_game_features)
```

## Bankroll Tracking

### Update Bankroll

```python
# Initial deposit
db.update_bankroll(1000, reason="Initial deposit")

# After winning bet
db.update_bankroll(1110, change=110, reason="Lakers ML win")

# After losing bet
db.update_bankroll(960, change=-150, reason="Chiefs ML loss")

# The change is calculated automatically if not provided
db.update_bankroll(1000)  # Change calculated from previous
```

### Get Current Bankroll

```python
bankroll = db.get_bankroll()
print(f"Current bankroll: ${bankroll:.2f}")
```

### View Bankroll History

```python
# All history
history = db.get_bankroll_history()

# Last 30 entries
recent = db.get_bankroll_history(limit=30)

# Display
for entry in recent:
    print(f"{entry['timestamp']}: ${entry['amount']:.2f} ({entry['change']:+.2f})")
```

## Performance Analytics

### Get Performance Stats

```python
stats = db.get_performance()

print(f"Total bets: {stats['total_bets']}")
print(f"Wins: {stats['wins']}")
print(f"Losses: {stats['losses']}")
print(f"Win rate: {stats['win_rate']:.1%}")
print(f"Total wagered: ${stats['total_wagered']:.2f}")
print(f"Total profit: ${stats['total_profit']:.2f}")
print(f"ROI: {stats['roi']:.2%}")
print(f"Biggest win: ${stats['biggest_win']:.2f}")
print(f"Biggest loss: ${stats['biggest_loss']:.2f}")
print(f"Avg winning odds: {stats['avg_winning_odds']:.2f}")
```

### Filter Performance

```python
# NBA only
nba_stats = db.get_performance(sport='nba')

# Last 30 days
recent_stats = db.get_performance(days=30)

# Combine
nba_month = db.get_performance(sport='nba', days=30)
```

### Print Formatted Report

```python
# Full report
db.print_performance()

# Sport-specific
db.print_performance(sport='nba')
```

Output:
```
============================================================
BETTING PERFORMANCE
Sport: NBA
============================================================

Total Bets:     47
Wins:           26
Losses:         21
Win Rate:       55.3%

Total Wagered:  $4,750.00
Total Profit:   $342.50
ROI:            7.21%

Biggest Win:    $185.00
Biggest Loss:   $-150.00
Avg Win Odds:   2.15
============================================================
```

## Complete Workflows

### Workflow 1: Place and Track Bet

```python
from lib import SBL, BettingDatabase

db = BettingDatabase()

# 1. Get current bankroll
bankroll = db.get_bankroll()

# 2. Calculate Kelly
win_prob = 0.57
odds = 2.0
kelly = SBL.kelly(win_prob, odds)

# 3. Place bet
bet_amount = bankroll * kelly * 0.5  # 1/2 Kelly
bet_id = db.save_bet(
    matchup="Bucks vs Heat",
    amount=bet_amount,
    odds=odds,
    predicted_prob=win_prob,
    sport='nba'
)

# 4. After game, save result
db.save_result(bet_id, won=True)

# 5. Update bankroll
profit = bet_amount * (odds - 1)
new_bankroll = bankroll + profit
db.update_bankroll(new_bankroll, change=profit, reason="Bucks win")

# 6. Check performance
db.print_performance(sport='nba')
```

### Workflow 2: Track Model Predictions

```python
from lib import EasySportModel, BettingDatabase

db = BettingDatabase()

# Load historical data
games = db.get_games(sport='nba', limit=200)

# Prepare training data
training_data = []
for game in games:
    if game['features']:
        features = game['features']
        features['result'] = 1 if game['result'] == 'home_win' else 0
        training_data.append(features)

# Train model
model = EasySportModel('nba', 'game_winner')
model.fit(training_data)

# Make prediction for new game
new_game = {
    'team_offensive_rating': 116.0,
    'team_defensive_rating': 108.0,
    # ... other features
}

prediction = model.predict(new_game)
probability = model.predict_proba(new_game)

# Save prediction
pred_id = db.save_prediction(
    matchup="Tonight's Game",
    predicted_value=prediction,
    predicted_prob=probability,
    sport='nba',
    model_used='EasySportModel v1',
    features=new_game
)

# After game, save actual result
db.save_prediction_result(pred_id, actual_value=1)  # Home team won

# Check model accuracy
accuracy = db.get_prediction_accuracy(model='EasySportModel v1')
print(f"Model accuracy: {accuracy['accuracy']:.1%}")
```

### Workflow 3: Daily Betting Routine

```python
from lib import BettingDatabase, quick_nba_prediction

db = BettingDatabase()

# Today's games
games = [
    {'matchup': 'Lakers vs Celtics', 'team_off': 115, 'team_def': 108,
     'opp_off': 112, 'opp_def': 107, 'odds': 2.1},
    {'matchup': 'Warriors vs Nets', 'team_off': 118, 'team_def': 110,
     'opp_off': 109, 'opp_def': 111, 'odds': 1.85},
]

print("Today's Betting Analysis:")
print("-" * 60)

for game in games:
    # Quick prediction
    prob = quick_nba_prediction(
        game['team_off'], game['team_def'],
        game['opp_off'], game['opp_def'],
        home=True
    )

    # Calculate EV
    from lib import SBL
    ev = SBL.ev(prob, game['odds'], 100)
    edge = SBL.edge(prob, game['odds'])

    print(f"\n{game['matchup']}:")
    print(f"  Win probability: {prob:.1%}")
    print(f"  Odds: {game['odds']}")
    print(f"  Edge: {edge:.2%}")
    print(f"  EV per $100: ${ev:.2f}")

    # If positive EV, save bet
    if ev > 0:
        kelly = SBL.kelly(prob, game['odds'])
        bankroll = db.get_bankroll()
        bet_amount = bankroll * kelly * 0.5

        bet_id = db.save_bet(
            matchup=game['matchup'],
            amount=bet_amount,
            odds=game['odds'],
            predicted_prob=prob,
            sport='nba',
            notes=f"EV: ${ev:.2f}, Edge: {edge:.2%}"
        )
        print(f"  → Placed bet: ${bet_amount:.2f} (bet ID {bet_id})")
```

## Using on Replit

The database works perfectly on Replit:

```python
# In your Replit
from lib.database import BettingDatabase

# Database file stored in your Repl
db = BettingDatabase("my_betting.db")

# Use normally
db.save_bet("Lakers vs Celtics", 100, 2.1, 0.58)
```

The database file persists in your Repl!

## Using on Desktop

```python
from lib.database import BettingDatabase

# Database in your project folder
db = BettingDatabase("./data/betting.db")

# Or absolute path
db = BettingDatabase("/Users/you/sports_betting/bets.db")
```

## Database Tables

The database has 5 tables:

### 1. bets
Stores all bets and results

### 2. predictions
Stores ML model predictions

### 3. games
Stores historical game data

### 4. bankroll
Tracks bankroll over time

### 5. models
Stores model metadata (future feature)

## Best Practices

### 1. Always Track Everything

```python
# Save every bet
bet_id = db.save_bet(...)

# Save every prediction
pred_id = db.save_prediction(...)

# Save every game for training
game_id = db.save_game(...)
```

### 2. Use Consistent Sport Names

```python
# Good: Consistent lowercase
db.save_bet(..., sport='nba')
db.save_bet(..., sport='nfl')

# Avoid: Inconsistent
db.save_bet(..., sport='NBA')  # Don't mix cases
db.save_bet(..., sport='N.B.A.')
```

### 3. Add Notes

```python
db.save_bet(
    ...,
    notes="Lakers on 3-game win streak, Celtics on back-to-back"
)
```

### 4. Update Results Promptly

```python
# As soon as game ends
db.save_result(bet_id, won=True)
db.save_prediction_result(pred_id, actual_value=1)
```

### 5. Track Bankroll

```python
# Update after every bet settles
db.update_bankroll(new_amount, change=profit, reason="Bet result")
```

### 6. Regular Performance Reviews

```python
# Weekly
db.print_performance(days=7)

# Monthly
db.print_performance(days=30)

# By sport
db.print_performance(sport='nba')
```

### 7. Close When Done

```python
# In scripts
db.close()

# Or use context manager (future feature)
```

## Advanced Usage

### Custom Queries

You can execute custom SQL:

```python
cursor = db.conn.cursor()
cursor.execute("""
    SELECT sport, COUNT(*) as count, SUM(profit) as total_profit
    FROM bets
    WHERE result IS NOT NULL
    GROUP BY sport
    ORDER BY total_profit DESC
""")

for row in cursor.fetchall():
    print(f"{row['sport']}: {row['count']} bets, ${row['total_profit']:.2f} profit")
```

### Export Data

```python
import csv

# Export bets to CSV
bets = db.get_bets()

with open('bets.csv', 'w', newline='') as f:
    if bets:
        writer = csv.DictWriter(f, fieldnames=bets[0].keys())
        writer.writeheader()
        writer.writerows(bets)
```

### Backup Database

```python
import shutil
from datetime import datetime

# Backup database file
backup_name = f"betting_backup_{datetime.now():%Y%m%d}.db"
shutil.copy('betting.db', backup_name)
print(f"Backed up to {backup_name}")
```

## Tips

1. **One database per season/year** - Keep databases manageable
2. **Regular backups** - Copy database file regularly
3. **Track everything** - More data = better analysis
4. **Review performance** - Weekly/monthly reviews
5. **Use notes field** - Document your reasoning
6. **Consistent naming** - Use same sport/bet type names
7. **Save features** - Store features with games for ML training

## See Also

- [Simple API Guide](simple_api_guide.md) - Kelly, EV calculations
- [Easy Sport Models Guide](easy_sport_models_guide.md) - ML models
- [Examples](../examples/database_examples.py) - Complete examples

---

For more information, see the main [README](../README.md).
