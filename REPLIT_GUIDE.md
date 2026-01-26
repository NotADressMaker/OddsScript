# Using SportsBetLang on Replit

Complete guide for using SportsBetLang on [Replit.com](https://replit.com/) - the easiest way to get started online!

## Quick Start (3 Steps)

### Step 1: Create a Replit

1. Go to [replit.com](https://replit.com/)
2. Click **"+ Create Repl"**
3. Choose **"Python"** as the template
4. Name it (e.g., "SportsBetting")
5. Click **"Create Repl"**

### Step 2: Install SportsBetLang

In the **Shell** tab (bottom of screen), run:

```bash
pip install git+https://github.com/NotADressMaker/SportsBetLang.git
```

Or add to `pyproject.toml`:
```toml
[tool.poetry.dependencies]
python = "^3.10"
sportsbetlang = {git = "https://github.com/NotADressMaker/SportsBetLang.git"}
```

Then click **"Install packages"** button.

### Step 3: Start Coding!

In `main.py`:

```python
from lib import SBL, EasySportModel, quick_nba_prediction

# Calculate Kelly Criterion
kelly = SBL.kelly(win_prob=0.55, odds=2.0)
print(f"Kelly bet size: {kelly:.2%}")

# Quick NBA prediction
prob = quick_nba_prediction(
    team_off_rtg=115.0,
    team_def_rtg=107.5,
    opp_off_rtg=110.2,
    opp_def_rtg=109.8,
    home=True
)
print(f"Win probability: {prob:.1%}")

print("\n✅ SportsBetLang working on Replit!")
```

Click **"Run"** ▶️ and you're done!

## Complete Examples for Replit

### Example 1: Bet Analysis Dashboard

Create a simple betting analysis tool:

```python
"""
SportsBetLang Betting Analysis
Run this on Replit!
"""

from lib import SBL, Bet, Compare

def main():
    print("=" * 60)
    print("SPORTSBETLANG - BETTING ANALYSIS")
    print("=" * 60)
    print()

    # Analyze multiple bets
    print("📊 BET ANALYSIS")
    print("-" * 60)

    bets = [
        {'name': 'Lakers vs Celtics', 'prob': 0.58, 'odds': 2.1},
        {'name': 'Chiefs vs Bills', 'prob': 0.52, 'odds': 2.3},
        {'name': 'Warriors vs Nets', 'prob': 0.61, 'odds': 1.9},
    ]

    for bet in bets:
        kelly = SBL.kelly(bet['prob'], bet['odds'])
        ev = SBL.ev(bet['prob'], bet['odds'], 100)
        edge = SBL.edge(bet['prob'], bet['odds'])

        print(f"\n{bet['name']}:")
        print(f"  Win Probability: {bet['prob']:.1%}")
        print(f"  Odds: {bet['odds']}")
        print(f"  Kelly Size: {kelly:.2%}")
        print(f"  Expected Value: ${ev:.2f}")
        print(f"  Edge: {edge:.2%}")

    # Compare bets
    print("\n\n🏆 BEST BET COMPARISON")
    print("-" * 60)

    comp = Compare(bankroll=1000)
    for bet in bets:
        comp.add(bet['name'], prob=bet['prob'], odds=bet['odds'])

    comp.print_comparison()

if __name__ == '__main__':
    main()
```

### Example 2: Quick Predictions

```python
"""
Quick Sport Predictions
No training needed!
"""

from lib import quick_nba_prediction, quick_nfl_prediction, quick_soccer_btts

print("🏀 NBA PREDICTIONS")
print("-" * 60)

nba_prob = quick_nba_prediction(
    team_off_rtg=115.0,
    team_def_rtg=107.5,
    opp_off_rtg=110.2,
    opp_def_rtg=109.8,
    home=True,
    rest_team=2,
    rest_opp=1
)
print(f"Lakers vs Celtics: {nba_prob:.1%} win probability")

print("\n🏈 NFL PREDICTIONS")
print("-" * 60)

nfl_prob = quick_nfl_prediction(
    team_dvoa=15.0,
    opp_dvoa=5.0,
    home=True,
    temperature=35,  # Cold weather
    wind_speed=20    # Windy
)
print(f"Chiefs vs Bills (cold & windy): {nfl_prob:.1%} win probability")

print("\n⚽ SOCCER PREDICTIONS")
print("-" * 60)

btts_prob = quick_soccer_btts(
    team_goals_avg=1.8,
    opp_goals_avg=1.5,
    team_clean_sheets=0.30,
    opp_clean_sheets=0.35
)
print(f"Both Teams To Score: {btts_prob:.1%} probability")
```

### Example 3: Build ML Model (Easy Way)

```python
"""
Build ML Model on Replit
Uses dictionary data - super easy!
"""

from lib import EasySportModel
import random

print("🤖 BUILDING NBA PREDICTION MODEL")
print("=" * 60)

# Generate sample training data
print("\n1. Generating training data...")
random.seed(42)
games = []

for i in range(200):
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

    # Simulate result
    team_net = game['team_offensive_rating'] - game['team_defensive_rating']
    opp_net = game['opponent_offensive_rating'] - game['opponent_defensive_rating']
    diff = team_net - opp_net + (3 if game['home_court'] else 0)
    win_prob = 1 / (1 + 10 ** (-diff / 15))
    game['result'] = 1 if random.random() < win_prob else 0

    games.append(game)

print(f"   ✓ Generated {len(games)} games")

# Train model
print("\n2. Training model...")
model = EasySportModel('nba', 'game_winner')
model.fit(games)
print("   ✓ Model trained!")

# Evaluate
print("\n3. Model Performance:")
model.summary()

# Predict
print("\n4. Making Predictions:")
test_games = [
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
    }
]

for i, game in enumerate(test_games, 1):
    pred = model.predict(game)
    prob = model.predict_proba(game)
    home_status = "Home" if game['home_court'] == 1 else "Away"
    result = "WIN" if pred == 1 else "LOSS"
    print(f"   Game {i} ({home_status}): {result} - {prob:.1%} confidence")

print("\n✅ Model ready to use!")
```

### Example 4: Interactive Bet Calculator

```python
"""
Interactive Betting Calculator
"""

from lib import SBL, Bet

def calculate_bet():
    print("=" * 60)
    print("BETTING CALCULATOR")
    print("=" * 60)

    # Get user input
    win_prob = float(input("\nEnter win probability (0-1, e.g., 0.55): "))
    odds = float(input("Enter odds (decimal, e.g., 2.0): "))
    bet_amount = float(input("Enter bet amount ($): "))
    bankroll = float(input("Enter bankroll ($): "))

    # Calculate metrics
    kelly = SBL.kelly(win_prob, odds)
    ev = SBL.ev(win_prob, odds, bet_amount)
    edge = SBL.edge(win_prob, odds)
    roi = SBL.roi(win_prob, odds)

    # Display results
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"Kelly Criterion: {kelly:.2%} of bankroll")
    print(f"Expected Value: ${ev:.2f}")
    print(f"Edge: {edge:.2%}")
    print(f"ROI: {roi:.2%}")
    print(f"Recommended bet: ${bankroll * kelly:.2f}")

    # Detailed analysis
    print("\n" + "-" * 60)
    bet = (Bet(bet_amount)
           .at_odds(odds)
           .with_probability(win_prob)
           .from_bankroll(bankroll))
    bet.print_summary()

if __name__ == '__main__':
    calculate_bet()
```

## Replit-Specific Features

### File Structure

Organize your Replit project:

```
your-repl/
├── main.py           # Your main code
├── utils.py          # Helper functions
├── data/
│   ├── games.json    # Your data
│   └── predictions.json
├── .replit           # Replit config
└── pyproject.toml    # Dependencies
```

### .replit Configuration

Create `.replit` file:

```toml
run = "python main.py"
language = "python3"

[nix]
channel = "stable-22_11"

[deployment]
run = ["python", "main.py"]
```

### Using Replit Database

Store data in Replit's built-in database:

```python
from lib import EasySportModel
from replit import db
import json

# Train model
model = EasySportModel('nba', 'game_winner')
model.fit(games)

# Save predictions to Replit DB
predictions = []
for game in upcoming_games:
    pred = model.predict(game)
    predictions.append({
        'matchup': game.get('matchup', 'Unknown'),
        'prediction': int(pred),
        'probability': float(model.predict_proba(game))
    })

db['predictions'] = json.dumps(predictions)
print("✓ Predictions saved to Replit DB")

# Retrieve later
saved_predictions = json.loads(db['predictions'])
```

### Creating a Web Interface

Make a simple web app with Flask:

```python
from flask import Flask, render_template, request, jsonify
from lib import SBL, quick_nba_prediction

app = Flask(__name__)

@app.route('/')
def home():
    return '''
    <html>
        <head><title>SportsBetLang Calculator</title></head>
        <body>
            <h1>Betting Calculator</h1>
            <form action="/calculate" method="post">
                Win Probability: <input type="number" step="0.01" name="prob"><br>
                Odds: <input type="number" step="0.1" name="odds"><br>
                <button type="submit">Calculate</button>
            </form>
        </body>
    </html>
    '''

@app.route('/calculate', methods=['POST'])
def calculate():
    prob = float(request.form['prob'])
    odds = float(request.form['odds'])

    kelly = SBL.kelly(prob, odds)
    ev = SBL.ev(prob, odds, 100)

    return f'''
    <html>
        <body>
            <h2>Results</h2>
            <p>Kelly: {kelly:.2%}</p>
            <p>Expected Value: ${ev:.2f}</p>
            <a href="/">Back</a>
        </body>
    </html>
    '''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
```

Update `.replit`:
```toml
run = "python main.py"
```

## Sharing Your Replit

1. Click **"Share"** button (top right)
2. Get shareable link
3. Others can **fork** and use your code
4. Or make it public in Replit community

## Common Workflows on Replit

### Workflow 1: Daily Bet Analysis

```python
"""Run this daily to analyze tonight's games"""

from lib import Compare, quick_nba_prediction

# Tonight's games (update these daily)
games = [
    {'name': 'Lakers vs Celtics', 'team_off': 115, 'team_def': 108,
     'opp_off': 112, 'opp_def': 107, 'home': True, 'odds': 1.95},
    {'name': 'Warriors vs Nets', 'team_off': 118, 'team_def': 110,
     'opp_off': 109, 'opp_def': 111, 'home': True, 'odds': 1.75},
]

comp = Compare(bankroll=1000)

for game in games:
    prob = quick_nba_prediction(
        game['team_off'], game['team_def'],
        game['opp_off'], game['opp_def'],
        game['home']
    )
    comp.add(game['name'], prob=prob, odds=game['odds'])

comp.print_comparison()
```

### Workflow 2: Model Training Pipeline

```python
"""Train models and save predictions"""

from lib import train_and_predict
import json

# Load your data (from files or Replit DB)
with open('data/historical_games.json', 'r') as f:
    historical = json.load(f)

with open('data/upcoming_games.json', 'r') as f:
    upcoming = json.load(f)

# Train and predict
predictions = train_and_predict(
    sport='nba',
    model_type='game_winner',
    historical_games=historical,
    new_games=upcoming,
    show_performance=True
)

# Save predictions
with open('data/predictions.json', 'w') as f:
    json.dump(predictions, f)

print(f"✓ Predictions saved! Analyzed {len(upcoming)} games")
```

### Workflow 3: Scheduled Analysis

Use Replit's "Always On" feature to run code periodically:

```python
"""Scheduled betting analysis"""

import schedule
import time
from lib import Compare
from datetime import datetime

def analyze_games():
    print(f"\n{datetime.now()}: Running analysis...")
    # Your analysis code here
    print("✓ Analysis complete")

# Run every day at 6 PM
schedule.every().day.at("18:00").do(analyze_games)

print("Scheduler started. Will analyze games daily at 6 PM.")

while True:
    schedule.run_pending()
    time.sleep(60)
```

## Tips for Replit

### 1. Use Secrets for API Keys

If you use external APIs:
- Click 🔒 **"Secrets"** in sidebar
- Add keys (they won't be visible in code)
- Access in Python:

```python
import os
api_key = os.environ['API_KEY']
```

### 2. Keep It Running

- Enable **"Always On"** for scheduled tasks
- Free tier stops after inactivity
- Paid tier keeps running 24/7

### 3. Version Control

Replit has built-in Git:
- Click version control icon
- Commit changes
- Push to GitHub

### 4. Collaborate

- Add collaborators via Share menu
- Real-time collaborative coding
- Comments and discussions

### 5. Mobile Friendly

Replit works on mobile:
- Code on phone/tablet
- Run Python anywhere
- Full IDE in browser

## Example Repls to Fork

Create these popular Repls:

### 1. Bet Calculator
Simple calculator for Kelly, EV, odds

### 2. ML Model Trainer
Train models on your data

### 3. Daily Analysis Dashboard
Analyze today's games

### 4. Portfolio Optimizer
Optimize bet allocation

### 5. Quick Predictions
Get instant predictions

## Troubleshooting on Replit

### Installation Issues

If `pip install` fails:
```bash
# Try adding to pyproject.toml instead
poetry add git+https://github.com/NotADressMaker/SportsBetLang.git
```

### Import Errors

```python
# Make sure installed
import subprocess
subprocess.run(['pip', 'list'], check=True)

# Should see sportsbetlang in list
```

### Memory Issues

Free tier has limited memory:
- Use smaller datasets
- Reduce n_trees in models
- Process in batches

### Slow Performance

- Free tier is slower
- Consider Hacker plan for better performance
- Optimize code (fewer iterations)

## Resources

- **Replit Docs**: [docs.replit.com](https://docs.replit.com)
- **SportsBetLang Docs**: Check `docs/` folder
- **Examples**: See `examples/` folder
- **Community**: Replit Discord and forums

## Quick Links

- 🏠 [Replit Home](https://replit.com)
- 📚 [SportsBetLang Docs](https://github.com/NotADressMaker/SportsBetLang)
- 💬 [Get Help](https://github.com/NotADressMaker/SportsBetLang/issues)

---

## Ready to Start?

1. Go to [replit.com](https://replit.com/)
2. Create Python Repl
3. Run: `pip install git+https://github.com/NotADressMaker/SportsBetLang.git`
4. Start coding with examples above!

**Happy coding on Replit! 🎉**
