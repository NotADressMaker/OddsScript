# Installation Guide for SportsBetLang

## Quick Start for Replit.com (Easiest!)

### Using Replit (Recommended for Beginners)

[Replit.com](https://replit.com/) is the easiest way to start - no installation needed, just your browser!

#### Steps:

1. **Go to [replit.com](https://replit.com/)**
2. **Create Python Repl** (click "+ Create Repl", choose Python)
3. **Install SportsBetLang** - In Shell tab at bottom:
   ```bash
   pip install git+https://github.com/NotADressMaker/SportsBetLang.git
   ```
4. **Start Coding** - In `main.py`:
   ```python
   from lib import SBL, quick_nba_prediction

   # Calculate Kelly
   kelly = SBL.kelly(0.55, 2.0)
   print(f"Kelly: {kelly:.2%}")

   # Quick prediction
   prob = quick_nba_prediction(115, 108, 110, 109, home=True)
   print(f"Win probability: {prob:.1%}")
   ```
5. **Click Run** ▶️

📚 **[Complete Replit Guide](REPLIT_GUIDE.md)** - Full guide with examples, workflows, and tips

## Quick Start for Other Online Python Environments

### Using pythononline.net or Similar Platforms

#### Method 1: Install from GitHub (Recommended)

```python
# Install directly from GitHub
!pip install git+https://github.com/NotADressMaker/SportsBetLang.git

# Import and use
from lib.nhl_analytics import NHLAdvancedAnalytics, ShotQuality
from lib.advanced_stats import AdvancedStats
from lib.ml_models import RandomForest, FeatureEngineering

# Example: Calculate Expected Goals
xg = NHLAdvancedAnalytics.calculate_expected_goals(
    shot_distance=15,
    shot_angle=20,
    shot_type='wrist',
    shot_quality=ShotQuality.HIGH_DANGER,
    rebound=True
)
print(f"Expected Goals: {xg:.3f}")
```

#### Method 2: Download Individual Modules

For quick testing without full installation:

```python
import urllib.request
import sys

# Download the advanced stats module
url = "https://raw.githubusercontent.com/NotADressMaker/SportsBetLang/main/lib/advanced_stats.py"
code = urllib.request.urlopen(url).read().decode('utf-8')

# Save to a temporary file
with open('advanced_stats.py', 'w') as f:
    f.write(code)

# Import and use
from advanced_stats import AdvancedStats

# Calculate Kelly Criterion
kelly = AdvancedStats.kelly_optimal_size(win_prob=0.55, odds=2.0)
print(f"Optimal bet size: {kelly:.2%}")
```

#### Method 3: Clone Repository

If the online environment supports git:

```bash
git clone https://github.com/NotADressMaker/SportsBetLang.git
cd SportsBetLang
python3 -m pip install -e .
```

Then in Python:
```python
from lib.nhl_analytics import NHLAdvancedAnalytics
from lib.ml_models import RandomForest
```

## Local Installation

### Standard Installation

```bash
# Clone repository
git clone https://github.com/NotADressMaker/SportsBetLang.git
cd SportsBetLang

# Install package
pip install -e .

# Or install from GitHub directly
pip install git+https://github.com/NotADressMaker/SportsBetLang.git
```

### Development Installation

```bash
# Clone repository
git clone https://github.com/NotADressMaker/SportsBetLang.git
cd SportsBetLang

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Run tests
python -m unittest discover tests
```

## Verification

After installation, verify it works:

```python
# Test basic import
from lib.advanced_stats import AdvancedStats
from lib.ml_models import RandomForest
from lib.nhl_analytics import NHLAdvancedAnalytics

# Test advanced stats
import random

def simulate_season():
    wins = sum(1 for _ in range(16) if random.random() < 0.6)
    return wins

mc_result = AdvancedStats.monte_carlo_simulation(
    simulate_season,
    n_simulations=1000
)
print(f"✓ Advanced Stats working - Expected wins: {mc_result['mean']:.1f}")

# Test ML models
X = [[1, 2], [3, 4], [5, 6]]
y = [0, 1, 1]
rf = RandomForest(n_trees=10, max_depth=5)
rf.fit(X, y)
print(f"✓ ML Models working - Predictions: {rf.predict(X)}")

# Test NHL analytics
xg = NHLAdvancedAnalytics.calculate_expected_goals(
    shot_distance=15,
    shot_angle=20,
    shot_type='wrist',
    shot_quality=ShotQuality.HIGH_DANGER
)
print(f"✓ NHL Analytics working - xG: {xg:.3f}")

print("\n✅ All modules working correctly!")
```

## Usage in Different Environments

### Jupyter Notebook / Google Colab

```python
# Install
!pip install git+https://github.com/NotADressMaker/SportsBetLang.git

# Import
from lib.nhl_analytics import NHLAdvancedAnalytics
from lib.advanced_stats import AdvancedStats

# Use
edge = NHLAdvancedAnalytics.analyze_betting_edge(
    predicted_probability=0.58,
    offered_odds=2.1,
    confidence_interval=(0.53, 0.63),
    bankroll=1000
)
print(f"Betting edge: {edge['edge_percentage']:.2f}%")
```

### Python REPL / IPython

```python
# If installed via pip
from lib.nhl_analytics import NHLAdvancedAnalytics

# Or if cloned locally
import sys
sys.path.insert(0, '/path/to/SportsBetLang')
from lib.nhl_analytics import NHLAdvancedAnalytics
```

### Python Script

```python
#!/usr/bin/env python3
"""
Example script using SportsBetLang
"""

from lib.nhl_analytics import NHLAdvancedAnalytics, TeamMetrics, GoaltenderStats
from lib.advanced_stats import AdvancedStats

def main():
    # Team metrics
    home_team = TeamMetrics(
        goals_for=3.2,
        goals_against=2.5,
        shots_for=32,
        shots_against=28,
        corsi_for=55,
        corsi_against=45,
        fenwick_for=52,
        fenwick_against=48,
        save_percentage=0.915,
        shooting_percentage=0.10,
        pdo=101.5,
        power_play_pct=0.22,
        penalty_kill_pct=0.82,
        faceoff_win_pct=0.52
    )

    # Goalie stats
    home_goalie = GoaltenderStats(
        save_percentage=0.915,
        goals_against_average=2.5,
        high_danger_save_pct=0.85,
        games_started=20,
        quality_starts=15,
        games_saved_above_expected=3.5
    )

    # Similar for away team...

    # Predict game
    prediction = NHLAdvancedAnalytics.predict_game_ml(
        home_team, away_team, home_goalie, away_goalie
    )

    print(f"Home win probability: {prediction['home_win_probability']:.3f}")
    print(f"Expected total goals: {prediction['expected_total']:.2f}")

if __name__ == '__main__':
    main()
```

## Troubleshooting

### Import Errors

If you get import errors:

```python
# Add SportsBetLang to Python path
import sys
sys.path.insert(0, '/path/to/SportsBetLang')

# Then import normally
from lib.advanced_stats import AdvancedStats
```

### Module Not Found

Make sure you're in the correct directory or have installed the package:

```bash
# Check if installed
pip list | grep sportsbetlang

# If not, install it
pip install git+https://github.com/NotADressMaker/SportsBetLang.git
```

### Online Environment Issues

Some online environments have restricted network access. In that case:

1. Download the library as a zip file from GitHub
2. Upload to the online environment
3. Extract and add to path:

```python
import sys
sys.path.insert(0, '/path/to/extracted/SportsBetLang')
```

## Requirements

- **Python**: 3.7 or higher
- **Dependencies**: None (uses only Python standard library)
- **Optional**: pytest for running tests

## Next Steps

- Read the [README](README.md) for feature overview
- Check [documentation](docs/) for detailed guides
- See [examples](examples/) for working code
- Run tests with `python -m unittest discover tests`

## Support

For issues or questions:
- Open an issue on GitHub
- Check existing documentation in `docs/`
- Review example code in `examples/`
