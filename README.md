# SportsBetLang - A Programming Language for Sports Betting

SportsBetLang is a domain-specific programming language designed specifically for sports betting analysis, bankroll management, and betting strategy development. It provides built-in functions for common betting calculations and a simple, intuitive syntax for betting operations.

## Features

### Core Language
- **Betting-specific syntax**: Create bets, parlays, and manage bankrolls with dedicated language constructs
- **Built-in betting functions**: Kelly criterion, expected value, odds conversions, vig calculator, and more
- **Odds format support**: American, decimal, and fractional odds
- **Bankroll management**: Tools for position sizing and risk management
- **Full programming language**: Variables, functions, loops, conditionals, arrays, dictionaries
- **Interactive REPL**: Test calculations and strategies interactively

### Packages and Tools
- **Standard Library**: Statistics, backtesting, CLV tracking, variance analysis, Poisson calculator, correlation analysis, regression modeling, multi-outcome Kelly
- **Betting Strategies**: Martingale, Fibonacci, Flat Betting implementations
- **CLI Tools**: 20+ professional tools including odds calculator, bet tracker, portfolio optimizer, line tracker, tax calculator, arbitrage finder, hedge calculator, market maker, and more
- **Testing Framework**: Comprehensive unit tests for all components
- **10 Example Programs**: From basic bets to advanced arbitrage and hedging

📚 **[View Complete Package Documentation](PACKAGES.md)** - 20+ tools and libraries

**Advanced Professional Tools:**
- 🎯 **Portfolio Optimizer** - Optimize bet allocation using Modern Portfolio Theory
- 📈 **Line Tracker** - Detect steam moves and sharp action
- ⚽ **Poisson Calculator** - Goal/point probabilities for totals betting
- 💰 **Tax Calculator** - US gambling tax calculator with 2024 brackets
- 🔍 **Correlation Analysis** - Avoid correlated parlay mistakes
- 📊 **Performance Attribution** - Identify your edge by sport, bet type, etc.
- ⚡ **Arbitrage Calculator** - Find guaranteed profit across multiple books
- 🛡️ **Hedge Calculator** - Optimal hedging for parlays, futures, middles
- 🏢 **Market Maker** - Calculate fair odds, remove vig, find value
- 📉 **Regression Analysis** - Build custom betting models
- 🎲 **Multi-Outcome Kelly** - Kelly criterion for 3+ outcomes (horse racing, golf, etc.)

### Data Ingestion & Feature Pipeline
- **Modular pipeline** in `sportsbetlang/ingestion` with sources, extractors, normalizers, db, features, and pipelines modules.
- **Schema-first** odds snapshots and injury reports with validation utilities.
- **Entity resolution** helpers for stable team/player IDs.
- **CLI workflows** for backfill and live ingestion runs.

Run the CLI (tools must be injected by the host environment):
```bash
python -m sportsbetlang.ingestion.pipelines.cli backfill --sport nba --start 2025-10-01 --end 2025-10-31
python -m sportsbetlang.ingestion.pipelines.cli live --sport nba --start 2025-10-01 --end 2025-10-01 --markets spread,total,moneyline
```

## Installation

SportsBetLang works on **desktop, laptop, Jupyter notebooks, Google Colab, and online Python environments**. Requires Python 3.7 or higher.

### 🖥️ Desktop / Laptop (Recommended)

**Quick Install:**
```bash
pip install git+https://github.com/NotADressMaker/SportsBetLang.git
```

Then use in Python:
```python
from lib import SBL, EasySportModel, quick_nba_prediction

# Calculate Kelly
kelly = SBL.kelly(win_prob=0.55, odds=2.0)

# Quick NBA prediction
prob = quick_nba_prediction(115, 108, 110, 109, home=True)
```

📚 **[Desktop Quick Start Guide](DESKTOP_QUICKSTART.md)** - Complete desktop setup with examples

**Alternative - Clone Repository:**
```bash
# Clone and install
git clone <repository-url>
cd programminglangauage
pip install -e ".[dev]"

# Use the domain-specific language REPL
sportsbetlang
# (or python -m sportsbetlang)

# Or run a script
sportsbetlang examples/01_basic_bet.odds
```

### 🌐 Replit.com (Easiest - Start in 60 Seconds!)

**Perfect for beginners - code in your browser:**

1. Go to [replit.com](https://replit.com/) → Create Python Repl
2. In Shell: `pip install git+https://github.com/NotADressMaker/SportsBetLang.git`
3. Start coding!

```python
from lib import SBL, quick_nba_prediction

# Calculate Kelly
kelly = SBL.kelly(0.55, 2.0)

# Quick prediction
prob = quick_nba_prediction(115, 108, 110, 109, home=True)
```

📚 **[Replit Guide](REPLIT_GUIDE.md)** - Complete Replit guide with examples
🚀 **[Try replit_example.py](replit_example.py)** - Ready-to-run examples

### 🌐 Other Online Environments

**pythononline.net, Google Colab, Jupyter:**
```python
!pip install git+https://github.com/NotADressMaker/SportsBetLang.git

from lib import SBL, EasySportModel
```

📚 **[Installation Guide](INSTALL.md)** - All installation methods
📘 **[Language Specification](docs/LANGUAGE_SPEC.md)** - Grammar, semantics, and LLM/automation-friendly conventions

## Quick Start

### Basic Syntax

```sportsbetlang
# Variables
let bankroll = 1000
const unit_size = 10

# Print output
print("Bankroll: $" + bankroll)

# Arithmetic
let profit = 100 * 1.5
let total = bankroll + profit
```

### Creating Bets

```sportsbetlang
# Moneyline bet
bet "Lakers" odds -110 stake 100

# Spread bet
bet spread "Chiefs" odds -110 stake 50

# Parlay
parlay [bet1, bet2, bet3] stake 100
```

### Odds Calculations

```sportsbetlang
# Convert American odds to decimal
let decimal_odds = american_to_decimal(-110)  # Returns 1.909

# Calculate implied probability
let prob = implied_probability(-110)  # Returns 0.524 (52.4%)

# Calculate expected value
let ev = calculate_ev(0.55, -110, 100)  # true_prob, odds, stake

# Kelly criterion for bet sizing
let kelly = kelly_criterion(0.55, -110)
```

### Control Flow

```sportsbetlang
# Conditionals
if ev > 0 {
    print("Positive EV - place the bet!")
} else {
    print("Negative EV - skip it")
}

# Loops
for game in games {
    print(game)
}

while bankroll > 0 {
    # Betting logic
}
```

### Functions

```sportsbetlang
func analyze_bet(true_prob, odds, stake) {
    let ev = calculate_ev(true_prob, odds, stake)
    let kelly = kelly_criterion(true_prob, odds)

    if ev > 0 {
        print("Value bet! Kelly: " + kelly)
        return kelly
    }
    return 0
}

let bet_size = analyze_bet(0.60, -110, 100)
```

### Modules and Imports

```sportsbetlang
# Import a module namespace
import betting
import stats as s
import web as http

# Or import specific functions
from betting import kelly_criterion as kelly

let kelly_size = betting.kelly_criterion(0.60, -110)
let sim = s.poisson_simulate_match(1.4, 1.1)
let direct = kelly(0.60, -110)
let homepage = http.get("https://example.com")
let data = http.get_json("https://example.com/data.json")
```

## CLI Usage

Run the REPL:
```bash
sportsbetlang
```

Run a program:
```bash
sportsbetlang examples/01_basic_bet.odds
```

Limit execution steps for untrusted scripts:
```bash
sportsbetlang --max-steps 100000 examples/01_basic_bet.odds
```

## Development + Tests

Install dev dependencies and run tests:
```bash
pip install -e ".[dev]"
pytest
```

## Built-in Functions

Core utilities (`abs`, `min`, `max`, `sqrt`, `pow`, `len`, `range`, `sum`) are available by default. Betting, stats, and web helpers live in modules and must be imported (e.g., `import betting`, `import stats as s`, `import web as http`).

### Odds Conversion

- `american_to_decimal(odds)` - Convert American odds to decimal format
- `decimal_to_american(odds)` - Convert decimal odds to American format
- `implied_probability(odds)` - Calculate implied probability from American odds

### Betting Analysis

- `calculate_ev(true_prob, odds, stake)` - Calculate expected value of a bet
- `kelly_criterion(true_prob, odds)` - Optimal bet sizing using Kelly criterion
- `break_even_percentage(odds)` - Required win rate to break even

### Parlay Functions

- `parlay_odds(odds1, odds2, ...)` - Calculate combined parlay odds
- `parlay_probability(prob1, prob2, ...)` - Probability of hitting all legs
- `round_robin(bets_count, parlay_size)` - Calculate round robin combinations

### Market Analysis

- `vig_calculator(odds1, odds2)` - Calculate bookmaker's vig from a two-way market
- `true_odds_from_vig(odds, total_vig)` - Remove vig to find true odds
- `units_to_risk(odds, units_to_win)` - Calculate units needed to risk

### Utility Functions

- `roi_calculator(wins, losses, avg_odds)` - Calculate ROI from betting record
- Standard math: `abs()`, `min()`, `max()`, `sqrt()`, `pow()`
- Array functions: `len()`, `sum()`, `range()`

### Web Utilities

- `web.get(url, timeout=10, headers=null)` - Fetch a URL and return response text
- `web.get_json(url, timeout=10, headers=null)` - Fetch a URL and parse JSON
- `web.get_table(url, table_index=0, timeout=10, headers=null)` - Fetch a URL and extract an HTML table
- `web.get_table_dicts(url, table_index=0, timeout=10, headers=null)` - Fetch a URL and extract an HTML table as dictionaries (first row as headers)
- `web.get_text(url, timeout=10, headers=null)` - Fetch a URL and extract visible text
- `web.get_links(url, timeout=10, headers=null)` - Fetch a URL and extract links (href + text)
- `web.get_tables(url, timeout=10, headers=null)` - Fetch a URL and extract all HTML tables
- `web.get_tables_dicts(url, timeout=10, headers=null)` - Fetch a URL and extract all HTML tables as dictionaries
- `web.get_csv(url, timeout=10, headers=null)` - Fetch a URL and parse CSV into dictionaries

## Examples

The `examples/` directory contains comprehensive examples:

### Basic Examples
1. **01_basic_bet.odds** - Basic betting operations and calculations
2. **02_kelly_criterion.odds** - Optimal bet sizing using Kelly criterion
3. **03_parlay.odds** - Parlay betting and analysis
4. **04_vig_calculator.odds** - Understanding bookmaker's vig
5. **05_bankroll_management.odds** - Bankroll management simulation
6. **06_odds_conversion.odds** - Converting between odds formats
7. **07_advanced_strategy.odds** - Advanced betting strategy with EV analysis

### Advanced Examples
8. **08_arbitrage_betting.odds** - Arbitrage opportunity detection
9. **09_monte_carlo_simulation.odds** - Monte Carlo bankroll simulation
10. **10_hedging_calculator.odds** - Hedging strategies and middle opportunities

### Running Examples

```bash
# Run an example
./sportsbetlang.py examples/02_kelly_criterion.odds

# Or using Python directly
python3 sportsbetlang.py examples/02_kelly_criterion.odds
```

### Generate Python, R, or Julia Code

SportsBetLang can emit source code for integration in quantitative pipelines:

```python
from sportsbetlang import generate_code

source = \"\"\"
let odds = -110
let stake = 100
calculate_ev(0.55, odds, stake)
\"\"\"

python_code = generate_code(source, language=\"python\")
r_code = generate_code(source, language=\"r\")
julia_code = generate_code(source, language=\"julia\")
```

## Language Reference

### Data Types

- **Numbers**: `42`, `3.14`, `-110`
- **Strings**: `"Lakers"`, `'Chiefs'`
- **Booleans**: `true`, `false`
- **Arrays**: `[1, 2, 3]`, `["Lakers", "Celtics"]`
- **Dictionaries**: `{"team": "Lakers", "odds": -110}`

### Operators

- **Arithmetic**: `+`, `-`, `*`, `/`, `%`
- **Comparison**: `==`, `!=`, `<`, `>`, `<=`, `>=`
- **Logical**: `and`, `or`, `not`
- **Assignment**: `=`

### Keywords

```
bet, bankroll, odds, stake, parlay
let, const, if, else, while, for, in
func, return, print
team, game, over, under, spread, moneyline, total
calculate, kelly, ev, implied, probability
true, false, and, or, not
```

## REPL Mode

Start the interactive REPL:

```bash
./sportsbetlang.py
```

```
SportsBetLang v1.0 - Sports Betting Programming Language
Type 'exit' or 'quit' to exit, 'help' for help

>>> let odds = -110
>>> implied_probability(odds)
0.5238095238095238
>>> calculate_ev(0.55, odds, 100)
2.7272727272727266
```

## Use Cases

### Bankroll Management

```sportsbetlang
let bankroll = 5000
let unit = bankroll * 0.01  # 1% units

func calculate_bet_size(edge, odds) {
    let kelly = kelly_criterion(edge, odds)
    return bankroll * kelly * 0.25  # Quarter Kelly
}
```

### Line Shopping

```sportsbetlang
let book1_odds = -110
let book2_odds = -105
let book3_odds = -108

let best_odds = max(book1_odds, book2_odds, book3_odds)
print("Best odds: " + best_odds)
```

### Expected Value Analysis

```sportsbetlang
func should_bet(team, my_probability, market_odds, min_edge) {
    let market_prob = implied_probability(market_odds)
    let edge = my_probability - market_prob

    if edge >= min_edge {
        let ev = calculate_ev(my_probability, market_odds, 100)
        print(team + " - Edge: " + (edge * 100) + "% | EV: $" + ev)
        return true
    }
    return false
}

should_bet("Lakers", 0.58, -110, 0.05)
```

### Parlay Analysis

```sportsbetlang
# Analyze a 3-leg parlay
let leg1 = -110
let leg2 = -120
let leg3 = +150

let parlay = parlay_odds(leg1, leg2, leg3)
let prob = parlay_probability(0.52, 0.55, 0.40)

print("Parlay odds: " + parlay)
print("Win probability: " + (prob * 100) + "%")
```

## Advanced Features

### Custom Betting Systems

```sportsbetlang
func martingale(base_bet, losses) {
    let multiplier = pow(2, losses)
    return base_bet * multiplier
}

func fibonacci_bet(base_bet, position) {
    if position <= 1 {
        return base_bet
    }
    return fibonacci_bet(base_bet, position - 1) + fibonacci_bet(base_bet, position - 2)
}
```

### Portfolio Management

```sportsbetlang
let bets = [
    {"team": "Lakers", "odds": -110, "stake": 100},
    {"team": "Chiefs", "odds": -120, "stake": 150},
    {"team": "Yankees", "odds": +120, "stake": 75}
]

let total_risk = 0
for bet in bets {
    total_risk = total_risk + bet["stake"]
}

print("Total risk: $" + total_risk)
```

## Best Practices

1. **Use Kelly Criterion wisely**: Consider fractional Kelly (1/4 or 1/2) for reduced variance
2. **Always calculate EV**: Never bet without positive expected value
3. **Account for vig**: Remove bookmaker's margin to find true odds
4. **Manage bankroll**: Never risk more than 1-5% of bankroll on a single bet
5. **Track everything**: Log all bets for performance analysis
6. **Shop for lines**: Always get the best available odds
7. **Avoid parlays**: They're typically -EV unless you have significant edge on each leg

## Contributing

Contributions are welcome! Feel free to submit issues or pull requests.

## License

MIT License - feel free to use and modify as needed.

## Disclaimer

This software is for educational and analytical purposes only. Sports betting involves risk. Always bet responsibly and within your means. Check your local laws regarding sports betting.

## Python Library

SportsBetLang can also be used as a Python library with powerful analytics and machine learning capabilities.

### Simplified API

Quick one-liners for common betting calculations:

```python
from lib.simple_api import SBL, Bet, Compare

# Kelly Criterion
kelly = SBL.kelly(win_prob=0.55, odds=2.0)

# Expected Value
ev = SBL.ev(win_prob=0.55, odds=2.0, bet_amount=100)

# Analyze a bet
bet = (Bet(100)
       .at_odds(2.1)
       .with_probability(0.58)
       .from_bankroll(1000))
bet.print_summary()

# Compare multiple bets
comp = Compare(bankroll=1000)
comp.add("Bet A", prob=0.58, odds=2.1)
comp.add("Bet B", prob=0.52, odds=2.3)
comp.print_comparison()
```

📚 **[Simplified API Guide](docs/simple_api_guide.md)** - Complete guide with 30+ functions

### Database - Track Everything

Store and track all your betting activity:

```python
from lib import BettingDatabase

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

# Track predictions
pred_id = db.save_prediction(
    matchup="Warriors vs Nets",
    predicted_value=1,
    predicted_prob=0.65,
    model_used='NBA ML Model'
)

# View performance
db.print_performance()  # Shows win rate, ROI, profit/loss

# Track bankroll
db.update_bankroll(1110, change=110, reason="Lakers win")

# Get prediction accuracy
accuracy = db.get_prediction_accuracy()
print(f"Model accuracy: {accuracy['accuracy']:.1%}")
```

**Features:**
- Track bets with automatic Kelly/EV calculation
- Save predictions and measure accuracy
- Store historical games for ML training
- Monitor bankroll over time
- Performance analytics (ROI, win rate, profit/loss)
- Works everywhere (desktop, Replit, SQLite-compatible)
- No external dependencies

📚 **[Database Guide](docs/database_guide.md)** - Complete tracking system

### Full-Stack API - Build Web & Mobile Apps

Complete REST API and WebSocket support for building full-stack applications:

```python
# Start the API server
pip install -r requirements-api.txt
uvicorn api:app --reload

# API runs at http://localhost:8000
# Interactive docs at http://localhost:8000/docs
```

**Use from any language or platform:**

```javascript
// JavaScript/React/Node.js
const response = await fetch('http://localhost:8000/analyze/bet', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        amount: 100,
        odds: 2.1,
        win_probability: 0.58,
        bankroll: 1000
    })
});

const data = await response.json();
console.log(data.recommendation);  // "STRONG BET - Positive EV"
console.log(data.expected_value);   // 21.8
```

```python
# Python
import requests

response = requests.post('http://localhost:8000/calculate/kelly', json={
    'win_probability': 0.55,
    'odds': 2.0
})

print(response.json()['kelly_size'])  # 0.1 (bet 10% of bankroll)
```

**Available Endpoints:**

*Core Calculations:*
- `/calculate/kelly` - Kelly Criterion calculation
- `/calculate/ev` - Expected Value
- `/calculate/edge` - Betting edge calculation
- `/analyze/bet` - Complete bet analysis with recommendations

*Quick Predictions (9 Sports):*
- `/predict/nba/quick` - Fast NBA predictions
- `/predict/nfl/quick` - Fast NFL predictions (with weather)
- `/predict/nhl/quick` - Fast NHL predictions (Expected Goals)
- `/predict/mlb/quick` - Fast MLB predictions (park factors)
- `/predict/cbb/quick` - College Basketball (KenPom ratings, March Madness)
- `/predict/cfb/quick` - College Football (SP+ ratings, rivalry games)
- `/predict/wnba/quick` - WNBA predictions (with rest advantage)
- `/predict/soccer/btts` - Soccer BTTS predictions
- `/predict/horse-racing/quick` - Horse racing win probability

*Advanced Features:*
- `/recommendations` - Get personalized bet recommendations based on bankroll & risk
- `/arbitrage/detect` - Find guaranteed profit opportunities across bookmakers
- `/compare` - Compare multiple bets side-by-side
- `/export/bets` - Export betting data (JSON/CSV)
- `/statistics/summary` - Comprehensive performance statistics
- `/statistics/trends` - Betting trends over time

*Database Operations:*
- `/bets` - Save, retrieve, and manage bets
- `/predictions` - Track ML predictions and accuracy
- `/performance` - Get performance statistics (by sport, timeframe)
- `/bankroll` - Track bankroll over time

*Real-time:*
- `/ws` - WebSocket for real-time updates
- `/stream/live` - Server-Sent Events (SSE) stream for live updates

**Real-time WebSocket Updates:**

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = (event) => {
    const update = JSON.parse(event.data);
    console.log('New bet placed:', update);
};
```

**Live SSE Stream:**

```javascript
const stream = new EventSource('http://localhost:8000/stream/live?types=bet_placed,bankroll_update');

stream.addEventListener('bet_placed', (event) => {
    const update = JSON.parse(event.data);
    console.log('New bet placed:', update);
});

stream.addEventListener('bankroll_update', (event) => {
    const update = JSON.parse(event.data);
    console.log('Bankroll updated:', update);
});
```

**Docker Deployment:**

```bash
# Build and run
docker build -t sportsbetlang-api .
docker run -p 8000:8000 sportsbetlang-api

# Or use docker-compose
docker-compose up -d
```

**Serverless Deployment (AWS Lambda / Google Cloud Functions):**

```bash
# Install serverless adapters
pip install -r requirements-api.txt
```

```bash
# AWS Lambda (API Gateway)
# handler: serverless.lambda_handler
```

```bash
# Google Cloud Functions (HTTP)
# entrypoint: serverless.gcf_app
```

**Features:**
- REST API with all betting calculations
- WebSocket support for real-time updates
- Database operations (save bets, track performance)
- Sport-specific predictions (9 sports: NBA, NFL, NHL, MLB, CBB, CFB, WNBA, Soccer, Horse Racing)
- Advanced features (recommendations, arbitrage detection, bet comparison)
- Production-ready with Docker
- Auto-generated API documentation (Swagger/OpenAPI)
- CORS enabled for frontend integration
- Frontend examples (Vanilla JS, React, Advanced Dashboard)

📚 **[Full-Stack Guide](docs/FULLSTACK_GUIDE.md)** - Complete API reference, frontend examples, deployment
📚 **[API Reference](docs/API_REFERENCE.md)** - Quick endpoint reference
📚 **[Deployment Guide](docs/DEPLOYMENT_GUIDE.md)** - Deploy to Railway, Heroku, AWS, DigitalOcean, and more
🎨 **[Frontend Examples](frontend/)** - Vanilla JS, React components, and advanced dashboard
🚀 **[Enhanced Dashboard](frontend/dashboard.html)** - Professional multi-tab interface with 6 tools
🧰 **[Dashboard Builder Guide](docs/DASHBOARD_BUILDER_GUIDE.md)** - Manifest-driven starter for LLMs and developers
🧩 **[Tool Dashboard Starter](frontend/tool-dashboard-starter.html)** - JSON manifest → runnable dashboard

### ML Model Builder

Build custom machine learning models for sports betting:

```python
from lib.model_builder import Model, ModelBuilder, split_data

# Split your data
X_train, X_test, y_train, y_test = split_data(X, y, test_size=0.2)

# Build a custom model
model = (Model()
         .named("NBA Game Predictor")
         .for_classification()
         .using_random_forest(n_trees=100, max_depth=10)
         .with_features(['team_rating', 'opp_rating', 'home'])
         .with_normalization('standard')
         .train(X_train, y_train))

# Evaluate
model.print_performance(X_test, y_test)

# Or use pre-built templates
model = ModelBuilder.game_prediction_model()
model.train(X_train, y_train)
```

**Add-On Models (Simple, Predictable Boost)**

Train a small add-on model that learns the leftover error from an existing model:

```python
# Train a base model first
base_model = ModelBuilder.game_prediction_model()
base_model.train(X_train, y_train)

# Add-on model learns residuals and combines predictions
add_on = base_model.add_on(X_train, y_train)
improved_predictions = add_on.predict(X_test)
```

📚 **[ML Model Builder Guide](docs/ml_model_builder_guide.md)** - Build your own models

### Easy Sport Models (Simplified Interface)

The easiest way to build sport-specific models - use dictionaries instead of arrays:

```python
from lib.easy_sport_models import EasySportModel, quick_nba_prediction

# Train with dictionary data (no arrays needed!)
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

model = EasySportModel('nba', 'game_winner')
model.fit(games)

# Predict with dictionary (no arrays!)
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

# Or use quick prediction functions (no training!)
prob = quick_nba_prediction(
    team_off_rtg=115.0, team_def_rtg=107.5,
    opp_off_rtg=110.2, opp_def_rtg=109.8,
    home=True
)
```

**Features:**
- Use dictionaries instead of arrays (more readable)
- Automatic feature extraction and validation
- Quick prediction functions (no training needed)
- AutoFeatures helper for easy data preparation
- End-to-end workflow in one function call
- Same interface for all sports

📚 **[Easy Sport Models Guide](docs/easy_sport_models_guide.md)** - Simplified interface

### Sport-Specific Models (Advanced)

Pre-configured models optimized for each sport (advanced interface):

```python
from lib.sport_models import NBAModels, NFLModels, get_sport_model
from lib.sport_features import NBAFeatures

# NBA game winner model (pre-tuned)
nba_model = NBAModels.game_winner_model()
nba_model.train(X_train, y_train)

# Or use helper function
nfl_model = get_sport_model('nfl', 'spread_model')

# Create sport-specific features
rating_diff = NBAFeatures.create_rating_differential(
    team_off_rtg=112.5, team_def_rtg=108.2,
    opp_off_rtg=110.1, opp_def_rtg=109.5
)
```

**Available Sport Models:**
- **NBA**: Game winner, spread, totals, player props
- **NFL**: Game winner, spread, totals (with weather)
- **NHL**: Game winner, puck line, totals (with xG)
- **MLB**: Game winner, run line, totals (with park factors)
- **CFB**: Game winner, spread, totals (with conference adjustments)
- **CBB**: Game winner, spread, March Madness upsets
- **Soccer**: 3-way result, BTTS, totals
- **Horse Racing**: Win probability, exacta, speed ratings

📚 **[Sport-Specific Models Guide](docs/sport_specific_models_guide.md)** - Models for every sport

### Advanced Statistics & Machine Learning

Zero-dependency implementations of advanced techniques:

```python
from lib.advanced_stats import AdvancedStats
from lib.ml_models import RandomForest, NeuralNetwork

# Bayesian inference
result = AdvancedStats.bayesian_win_probability(wins=12, losses=5)

# Monte Carlo simulation
def simulate_season():
    return sum(1 for _ in range(16) if random.random() < 0.6)

result = AdvancedStats.monte_carlo_simulation(simulate_season, n=10000)

# Machine learning
model = RandomForest(n_trees=100, max_depth=10)
model.fit(X_train, y_train)
predictions = model.predict(X_test)
```

📚 **[Advanced Stats Guide](docs/advanced_stats_guide.md)** - Statistical methods
📚 **[ML Models Guide](docs/ml_models_guide.md)** - Machine learning details

### Sport-Specific Analytics

Comprehensive analytics packages for all 9 sports:

```python
# Professional Sports
from lib import NBAAnalytics, NFLAnalytics, NHLAnalytics, MLBAnalytics

# College Sports
from lib import CBBAnalytics, CFBAnalytics

# Women's Professional
from lib import WNBAAnalytics

# Other Sports
from lib import SoccerAnalytics, HorseRacingAnalytics

# Example: NHL Expected Goals
from lib.nhl_analytics import NHLAdvancedAnalytics
xg = NHLAdvancedAnalytics.calculate_expected_goals(
    shot_distance=15, shot_angle=20, shot_type='wrist'
)

# Example: NHL Advanced Prediction Models
from lib import NHLDecisionTree, NHLPowerRankings, NHLSimilarGameModel

# Decision Tree for O/U and ATS
tree = NHLDecisionTree()
ou_pred = tree.predict_over_under(
    team1_xgf=3.2, team1_xga=2.8,
    team2_xgf=2.9, team2_xga=3.0,
    line=6.5,
    team1_goalie_sv_pct=0.920,
    team2_goalie_sv_pct=0.905
)
# Returns: {'prediction': 'OVER', 'confidence': 0.70, 'expected_total': 6.2, ...}

ats_pred = tree.predict_ats(
    team_xgf=3.2, team_xga=2.8,
    opp_xgf=2.9, opp_xga=3.0,
    spread=-1.5, is_home=True
)
# Returns: {'prediction': 'COVER', 'confidence': 0.65, 'cover_margin': 0.5, ...}

# Power Rankings (Elo-style)
rankings = NHLPowerRankings()
rankings.set_rating("Tampa Bay", 1650)
rankings.set_rating("Arizona", 1380)
pred = rankings.predict_game("Tampa Bay", "Arizona", team1_home=True)
# Returns: {'team1_win_probability': 0.892, 'expected_goal_differential': 2.7, ...}

# Similar Game Model (Historical Pattern Matching)
sim_model = NHLSimilarGameModel()
# Add historical games...
sim_pred = sim_model.predict_from_similar(
    team1_xgf=3.1, team1_xga=2.9,
    team2_xgf=2.8, team2_xga=3.1,
    line_total=6.5, line_spread=-1.5
)
# Returns O/U and ATS predictions based on similar historical games

# Example: College Basketball March Madness
from lib.cbb_analytics import CBBAnalytics
upset_prob = CBBAnalytics.calculate_march_madness_upset(
    favorite_seed=1, underdog_seed=16
)

# Example: WNBA rest advantage
from lib.wnba_analytics import WNBAAnalytics
rest_impact = WNBAAnalytics.calculate_rest_advantage(
    team_rest_days=3, opponent_rest_days=1
)

# Example: College Football rivalry games
from lib.cfb_analytics import CFBAnalytics
rivalry_adjustment = CFBAnalytics.calculate_rivalry_factor(
    is_rivalry=True, spread=14.0
)
```

**Available Analytics Packages:**
- **NBA** - Advanced stats, pace adjustments, playoff modeling
- **NFL** - DVOA, weather factors, key numbers
- **NHL** - Expected goals (xG), Corsi, Fenwick, **Advanced Models** (Decision Tree, Power Rankings, Similar Game)
- **MLB** - Park factors, pitcher adjustments, run expectancy
- **College Basketball** - KenPom ratings, March Madness, conference strength
- **College Football** - SP+ ratings, recruiting rankings, rivalry games
- **WNBA** - Rest advantage, compressed schedule analysis
- **Soccer** - Poisson modeling, BTTS, 3-way moneylines
- **Horse Racing** - Speed ratings, post position, track conditions

**NHL Advanced Models:**
- **Decision Tree Model** - Multi-factor O/U and ATS predictions with confidence scoring
- **Power Rankings** - Elo-style dynamic ratings system with game predictions
- **Similar Game Model** - Historical pattern matching for O/U and ATS predictions

📚 See `lib/` directory for all sport-specific packages and detailed documentation

### Installation

```bash
# Install from GitHub
pip install git+https://github.com/NotADressMaker/SportsBetLang.git

# Or clone and install locally
git clone <repository-url>
cd programminglangauage
pip install -e .
```

📚 **[Installation Guide](INSTALL.md)** - Detailed installation instructions

## Packages and Utilities

### Standard Library
- **Statistics Module** (`lib/statistics.py`) - Mean, median, std dev, Sharpe ratio, max drawdown, and more
- **Backtesting Framework** (`lib/backtesting.py`) - Test strategies on historical data or Monte Carlo simulations
- **CLV Tracker** (`lib/clv_tracker.py`) - Track Closing Line Value, the #1 indicator of long-term success
- **Variance Calculator** (`lib/variance_calc.py`) - Calculate variance, risk of ruin, required bankroll
- **Poisson Calculator** (`lib/poisson_calculator.py`) - Goal/point probabilities for totals betting
- **Correlation Analysis** (`lib/correlation_analysis.py`) - Detect correlated parlay legs
- **Regression Analysis** (`lib/regression_analysis.py`) - Build betting models with linear/multiple regression
- **Multi-Outcome Kelly** (`lib/multi_outcome_kelly.py`) - Kelly criterion for 3+ outcomes

### Betting Strategies
- **Martingale** (`strategies/martingale.py`) - Classic doubling strategy (high risk)
- **Fibonacci** (`strategies/fibonacci.py`) - Fibonacci sequence progression
- **Flat Betting** (`strategies/flat_betting.py`) - Recommended safe strategy
- **Percentage Betting** (`strategies/percentage_betting.py`) - Bet a fixed percentage of current bankroll

### Command-Line Tools

**Performance & Tracking:**
- **Bet Tracker** (`tools/bet_tracker.py`) - Track and analyze your betting performance
- **Performance Attribution** (`tools/performance_attribution.py`) - Identify edge sources by sport, bet type, book, etc.

**Calculations & Analysis:**
- **Odds Calculator** (`tools/odds_calc.py`) - Quick calculations for Kelly, EV, parlays, vig
- **Teaser Calculator** (`tools/teaser_calc.py`) - NFL/NBA teasers with Wong teaser detection
- **Round Robin Calculator** (`tools/round_robin_calc.py`) - All parlay combinations and scenarios
- **Bonus Calculator** (`tools/bonus_calc.py`) - Optimize sportsbook bonuses and promos
- **Tax Calculator** (`tools/tax_calculator.py`) - US gambling tax calculation (2024 brackets)
- **Arbitrage Calculator** (`tools/arbitrage_calculator.py`) - Find guaranteed profit opportunities across books
- **Hedge Calculator** (`tools/hedge_calculator.py`) - Optimal hedging for parlays, futures, and middles
- **Market Maker** (`tools/market_maker.py`) - Calculate fair odds, remove vig, find value bets

**Advanced Analysis:**
- **Portfolio Optimizer** (`tools/portfolio_optimizer.py`) - Optimize bet allocation using Modern Portfolio Theory
- **Line Tracker** (`tools/line_tracker.py`) - Track line movements and detect steam/sharp action
- **Bankroll Simulator** (`tools/bankroll_sim.py`) - Simulate strategies with ASCII visualization

### Testing
- **Test Suite** (`tests/test_interpreter.py`) - Comprehensive unit tests

📚 **[Complete package documentation and usage examples](PACKAGES.md)**

## Quick Tool Examples

```bash
# Calculate Kelly criterion
python3 tools/odds_calc.py kelly --prob 0.55 --odds -110 --bankroll 1000

# Track a bet
python3 tools/bet_tracker.py add NFL "Chiefs vs Bills" "Chiefs -3" \
    --odds -110 --stake 100

# View your betting stats
python3 tools/bet_tracker.py stats

# Run tests
python3 tests/test_interpreter.py
```

## Future Enhancements

Potential features for future versions:

- [ ] Real-time odds API integration
- [x] ~~Historical data analysis~~ ✓ (Backtesting framework, Performance attribution)
- [ ] Graphical visualizations (ASCII visualization available)
- [x] ~~Betting strategy backtesting~~ ✓ (lib/backtesting.py)
- [x] ~~Multi-sport support with sport-specific functions~~ ✓ (Poisson for soccer/hockey, teaser calc for NFL/NBA)
- [ ] Live betting calculations
- [ ] Web interface
- [x] ~~Line movement tracking~~ ✓ (tools/line_tracker.py)
- [x] ~~Tax calculation~~ ✓ (tools/tax_calculator.py)
- [x] ~~Portfolio optimization~~ ✓ (tools/portfolio_optimizer.py)

## Contact

For questions, issues, or suggestions, please open an issue on GitHub.

---

**Happy betting, and remember: Only bet what you can afford to lose!**
