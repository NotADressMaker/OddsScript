# Desktop Quick Start Guide

Use SportsBetLang on your desktop/laptop with Python installed.

## Installation (Choose One Method)

### Method 1: Install from GitHub (Easiest)

```bash
pip install git+https://github.com/NotADressMaker/SportsBetLang.git
```

### Method 2: Clone and Install

```bash
# Clone repository
git clone https://github.com/NotADressMaker/SportsBetLang.git
cd SportsBetLang

# Install
pip install -e .
```

### Method 3: Development Mode

```bash
# Clone repository
git clone https://github.com/NotADressMaker/SportsBetLang.git
cd SportsBetLang

# Install in editable mode
pip install -e .

# Run tests (optional)
python -m unittest discover tests
```

## Requirements

- **Python 3.7+** (check with `python --version`)
- **pip** (Python package installer)
- **No other dependencies!** (uses only Python standard library)

## Verify Installation

```python
# Test import
from lib import SBL, EasySportModel, AdvancedStats

print("✓ SportsBetLang installed successfully!")
```

## Quick Examples

### Example 1: Kelly Criterion

```python
from lib import SBL

# Calculate optimal bet size
kelly = SBL.kelly(win_prob=0.55, odds=2.0)
print(f"Kelly bet size: {kelly:.2%}")

# Calculate expected value
ev = SBL.ev(win_prob=0.55, odds=2.0, bet_amount=100)
print(f"Expected value: ${ev:.2f}")
```

### Example 2: Analyze a Bet

```python
from lib import Bet

# Create and analyze a bet
bet = (Bet(100)
       .named("Lakers vs Celtics")
       .at_odds(2.1)
       .with_probability(0.58)
       .from_bankroll(1000))

bet.print_summary()
```

### Example 3: NBA Game Prediction (Easy Way)

```python
from lib import EasySportModel

# Historical games (dictionary format)
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
    # ... add 100+ more games for training
]

# Train model
model = EasySportModel('nba', 'game_winner')
model.fit(games)

# Predict new game
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

prediction = model.predict(new_game)
probability = model.predict_proba(new_game)

print(f"Win probability: {probability:.1%}")
```

### Example 4: Quick Predictions (No Training)

```python
from lib import quick_nba_prediction, quick_nfl_prediction

# NBA - instant prediction
nba_prob = quick_nba_prediction(
    team_off_rtg=115.0,
    team_def_rtg=107.5,
    opp_off_rtg=110.2,
    opp_def_rtg=109.8,
    home=True
)
print(f"NBA win probability: {nba_prob:.1%}")

# NFL - with weather
nfl_prob = quick_nfl_prediction(
    team_dvoa=15.0,
    opp_dvoa=5.0,
    home=True,
    temperature=35,
    wind_speed=20
)
print(f"NFL win probability: {nfl_prob:.1%}")
```

### Example 5: Advanced Statistics

```python
from lib import AdvancedStats
import random

# Bayesian inference
result = AdvancedStats.bayesian_win_probability(wins=12, losses=5)
print(f"Win probability: {result['probability']:.3f}")

# Monte Carlo simulation
def simulate_season():
    return sum(1 for _ in range(16) if random.random() < 0.6)

mc_result = AdvancedStats.monte_carlo_simulation(simulate_season, n=10000)
print(f"Expected wins: {mc_result['mean']:.1f}")
print(f"Range: {mc_result['percentile_5']:.1f} - {mc_result['percentile_95']:.1f}")
```

### Example 6: Machine Learning Models

```python
from lib import Model, split_data

# Your training data
X = [[115, 107.5, 110.2, 109.8, 1, 2, 1, 100.5], ...]
y = [1, 0, 1, 1, 0, ...]

# Split data
X_train, X_test, y_train, y_test = split_data(X, y, test_size=0.2)

# Build and train model
model = (Model()
         .named("NBA Game Predictor")
         .for_classification()
         .using_random_forest(n_trees=100, max_depth=10)
         .with_features(['team_off', 'team_def', 'opp_off', 'opp_def',
                        'home', 'rest_team', 'rest_opp', 'pace'])
         .with_normalization('standard')
         .train(X_train, y_train))

# Evaluate
model.print_performance(X_test, y_test)

# Predict
predictions = model.predict(X_test)
```

## Using in Python Scripts

Create a file `my_betting_analysis.py`:

```python
#!/usr/bin/env python3
"""My betting analysis script"""

from lib import SBL, Bet, EasySportModel

def main():
    # Calculate Kelly for multiple bets
    bets = [
        {'name': 'Bet A', 'prob': 0.58, 'odds': 2.1},
        {'name': 'Bet B', 'prob': 0.52, 'odds': 2.3},
        {'name': 'Bet C', 'prob': 0.61, 'odds': 1.9},
    ]

    print("Kelly Criterion Analysis:")
    for bet in bets:
        kelly = SBL.kelly(bet['prob'], bet['odds'])
        ev = SBL.ev(bet['prob'], bet['odds'], 100)
        print(f"{bet['name']}: Kelly {kelly:.2%}, EV ${ev:.2f}")

if __name__ == '__main__':
    main()
```

Run it:
```bash
python my_betting_analysis.py
```

## Using in Jupyter Notebooks

```python
# Cell 1: Install (if needed)
!pip install git+https://github.com/NotADressMaker/SportsBetLang.git

# Cell 2: Import
from lib import SBL, Bet, Compare, EasySportModel
from lib import AdvancedStats, RandomForest

# Cell 3: Use
kelly = SBL.kelly(0.55, 2.0)
print(f"Kelly: {kelly:.2%}")
```

## Using in VS Code / PyCharm / IDE

1. **Install SportsBetLang** (see methods above)

2. **Create Python file** (e.g., `analysis.py`)

3. **Import and use:**
```python
from lib import SBL, EasySportModel, AdvancedStats

# Your code here
```

4. **Run** with your IDE's run button or terminal

## Common Desktop Workflows

### Workflow 1: Quick Bet Analysis

```python
from lib import SBL, Bet

# Quick calculations
kelly = SBL.kelly(0.55, 2.0)
ev = SBL.ev(0.55, 2.0, 100)

print(f"Kelly: {kelly:.2%}")
print(f"EV: ${ev:.2f}")

# Detailed analysis
bet = (Bet(100)
       .at_odds(2.0)
       .with_probability(0.55)
       .from_bankroll(1000))

bet.print_summary()
```

### Workflow 2: Compare Multiple Bets

```python
from lib import Compare

comp = Compare(bankroll=1000)
comp.add("Lakers ML", prob=0.58, odds=2.1)
comp.add("Celtics ML", prob=0.52, odds=2.3)
comp.add("Bucks ML", prob=0.61, odds=1.9)

comp.print_comparison()
```

### Workflow 3: Build ML Model

```python
from lib import EasySportModel

# Load your historical data
games = load_historical_games()  # Your function

# Train
model = EasySportModel('nba', 'game_winner')
model.fit(games)

# Predict tonight's games
tonights_games = load_tonights_games()  # Your function

for game in tonights_games:
    prob = model.predict_proba(game)
    print(f"{game['matchup']}: {prob:.1%} win probability")
```

### Workflow 4: Batch Analysis Script

```python
#!/usr/bin/env python3
from lib import train_and_predict
import json

# Load data from files
with open('historical_games.json', 'r') as f:
    historical = json.load(f)

with open('upcoming_games.json', 'r') as f:
    upcoming = json.load(f)

# Run complete workflow
predictions = train_and_predict(
    sport='nba',
    model_type='game_winner',
    historical_games=historical,
    new_games=upcoming,
    show_performance=True
)

# Save predictions
with open('predictions.json', 'w') as f:
    json.dump(predictions, f)

print(f"✓ Analyzed {len(upcoming)} games")
```

## IDE-Specific Setup

### VS Code

1. Install Python extension
2. Open SportsBetLang folder
3. Select Python interpreter (Python 3.7+)
4. Create `.py` files and code!

### PyCharm

1. Open SportsBetLang as project
2. Configure Python interpreter
3. Mark `lib/` as sources root
4. Create Python files and run

### Jupyter

```bash
# Install Jupyter
pip install jupyter

# Start notebook
jupyter notebook

# Create new notebook, import SportsBetLang
```

## Data Sources

SportsBetLang is a calculation and modeling library. You need to provide your own data from:

- **Stats APIs**: NBA.com, ESPN, Basketball Reference, etc.
- **Betting sites**: Odds data (where legal)
- **CSV files**: Your historical tracking
- **Manual entry**: For small datasets

Example data structure:
```python
games = [
    {
        'team_offensive_rating': 115.0,
        'team_defensive_rating': 107.5,
        # ... other features
        'result': 1  # Actual outcome
    },
]
```

## File Organization

Recommended desktop project structure:

```
my_betting_project/
├── data/
│   ├── historical_games.csv
│   ├── upcoming_games.csv
│   └── predictions.csv
├── models/
│   └── saved_models/
├── scripts/
│   ├── train_models.py
│   ├── make_predictions.py
│   └── analyze_results.py
└── notebooks/
    ├── exploratory_analysis.ipynb
    └── model_evaluation.ipynb
```

## Troubleshooting

### "Module not found"
```bash
# Check if installed
pip list | grep sportsbetlang

# If not, install
pip install git+https://github.com/NotADressMaker/SportsBetLang.git
```

### "Python not found"
```bash
# Check Python version
python --version
# or
python3 --version

# If not installed, download from python.org
```

### Import errors
```python
# Add to Python path (if not installed via pip)
import sys
sys.path.insert(0, '/path/to/SportsBetLang')

from lib import SBL
```

## Next Steps

- **Read guides**: Check `docs/` folder
- **Run examples**: Try files in `examples/` folder
- **Build models**: Start with Easy Sport Models
- **Track performance**: Use SBL and Bet classes
- **Advanced analysis**: Use AdvancedStats for Monte Carlo, Bayesian

## Resources

- [Easy Sport Models Guide](docs/easy_sport_models_guide.md) - Simplest way to build models
- [Sport-Specific Models Guide](docs/sport_specific_models_guide.md) - Models for each sport
- [Simple API Guide](docs/simple_api_guide.md) - Kelly, EV, bet analysis
- [ML Model Builder Guide](docs/ml_model_builder_guide.md) - Custom models
- [Examples](examples/) - Working code examples

## Getting Help

- **Documentation**: Read `docs/` folder
- **Examples**: Check `examples/` folder
- **Issues**: Open issue on GitHub
- **Tests**: Run `python -m unittest discover tests`

---

**Ready to start?** Run this to verify everything works:

```python
from lib import SBL, quick_nba_prediction

# Test 1: Kelly
kelly = SBL.kelly(0.55, 2.0)
print(f"✓ Kelly: {kelly:.2%}")

# Test 2: Quick prediction
prob = quick_nba_prediction(115, 108, 110, 109, home=True)
print(f"✓ NBA prediction: {prob:.1%}")

print("\n✅ SportsBetLang is ready to use!")
```
