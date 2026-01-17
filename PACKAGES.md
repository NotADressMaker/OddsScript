# SportsBetLang Packages and Tools

This document describes all the packages, libraries, and utilities available for SportsBetLang.

## Table of Contents

1. [Standard Library](#standard-library)
2. [Betting Strategies](#betting-strategies)
3. [Command-Line Tools](#command-line-tools)
4. [Testing](#testing)
5. [Examples](#examples)

---

## Standard Library

### Statistics Module (`lib/statistics.py`)

Comprehensive statistical functions for betting analysis.

Comprehensive statistical functions for betting analysis.

#### Basic Statistics
- `mean(values)` - Calculate average
- `median(values)` - Find median value
- `mode(values)` - Find most common value
- `variance(values, sample=True)` - Calculate variance
- `std_dev(values, sample=True)` - Calculate standard deviation
- `percentile(values, p)` - Find p-th percentile

#### Advanced Statistics
- `correlation(x_values, y_values)` - Pearson correlation
- `z_score(value, values)` - Calculate z-score
- `moving_average(values, window)` - Moving average
- `weighted_average(values, weights)` - Weighted average
- `confidence_interval(values, confidence=0.95)` - Confidence interval

#### Betting-Specific Statistics
- `win_rate(wins, losses)` - Calculate win rate percentage
- `units_won(wins, losses, avg_odds=-110, unit_size=1.0)` - Total units won/lost
- `roi(wins, losses, avg_odds=-110)` - Return on investment
- `sharpe_ratio(returns, risk_free_rate=0.0)` - Sharpe ratio for betting
- `max_drawdown(bankroll_history)` - Maximum drawdown percentage
- `profit_factor(gross_wins, gross_losses)` - Profit factor
- `expectancy(win_rate, avg_win, avg_loss)` - Average profit per bet

**Example:**
```python
from lib.statistics import *

# Basic stats
values = [100, 110, 95, 105, 120]
print(f"Mean: {mean(values)}")
print(f"Std Dev: {std_dev(values)}")

# Betting stats
print(f"Win Rate: {win_rate(55, 45)}%")
print(f"ROI: {roi(55, 45, -110)}%")
```

---

## Betting Strategies

### Martingale Strategy (`strategies/martingale.py`)

Classic doubling strategy. **WARNING: High risk!**

```python
from strategies.martingale import MartingaleStrategy, simulate_martingale

# Create strategy
strategy = MartingaleStrategy(
    base_bet=10,
    max_bet=500,
    bankroll=1000
)

# Or run simulation
result = simulate_martingale(
    base_bet=10,
    bankroll=1000,
    max_bet=500,
    num_bets=100,
    win_probability=0.48
)

print(f"Final Bankroll: ${result['final_bankroll']:.2f}")
print(f"ROI: {result['roi']:.2f}%")
```

**Classes:**
- `MartingaleStrategy` - Double bet after each loss
- `ReverseMartingale` - Double bet after each win (Paroli)

### Fibonacci Strategy (`strategies/fibonacci.py`)

Uses Fibonacci sequence for bet progression.

```python
from strategies.fibonacci import FibonacciStrategy, simulate_fibonacci

strategy = FibonacciStrategy(
    base_unit=10,
    bankroll=1000,
    max_sequence_position=15
)

# Run simulation
result = simulate_fibonacci(
    base_unit=10,
    bankroll=1000,
    num_bets=100,
    win_probability=0.48
)
```

### Flat Betting (`strategies/flat_betting.py`)

**RECOMMENDED**: Safest strategy for long-term success.

```python
from strategies.flat_betting import FlatBetting, PercentageBetting, compare_strategies

# Fixed amount betting
flat = FlatBetting(bet_size=20, bankroll=1000)

# Percentage betting (adjusts with bankroll)
pct = PercentageBetting(percentage=0.02, bankroll=1000)

# Compare strategies
results = compare_strategies(
    starting_bankroll=1000,
    num_bets=100,
    win_probability=0.54
)
```

**Classes:**
- `FlatBetting` - Bet same amount each time
- `PercentageBetting` - Bet fixed percentage of current bankroll

---

## Command-Line Tools

### Odds Calculator (`tools/odds_calc.py`)

Quick calculator for common betting calculations.

**Installation:**
```bash
chmod +x tools/odds_calc.py
# Optional: alias for convenience
alias oddscalc='python3 tools/odds_calc.py'
```

**Commands:**

#### Convert Odds
```bash
python3 tools/odds_calc.py convert -110
python3 tools/odds_calc.py convert +150
```

#### Calculate Payout
```bash
python3 tools/odds_calc.py payout -110 --stake 100
```

#### Kelly Criterion
```bash
python3 tools/odds_calc.py kelly --prob 0.55 --odds -110 --bankroll 1000
```

#### Expected Value
```bash
python3 tools/odds_calc.py ev --prob 0.55 --odds -110 --stake 100
```

#### Parlay Calculator
```bash
python3 tools/odds_calc.py parlay -110 -120 +150 --stake 50
```

#### Vig Calculator
```bash
python3 tools/odds_calc.py vig -110 -110
```

### Bet Tracker (`tools/bet_tracker.py`)

Track and analyze your betting performance.

**Setup:**
```bash
chmod +x tools/bet_tracker.py
```

**Commands:**

#### Add a Bet
```bash
python3 tools/bet_tracker.py add NFL "Chiefs vs Bills" "Chiefs -3" \
    --type spread --odds -110 --stake 100 --notes "Home favorite"
```

#### List Pending Bets
```bash
python3 tools/bet_tracker.py pending
```

#### Settle a Bet
```bash
python3 tools/bet_tracker.py settle 0 won
python3 tools/bet_tracker.py settle 1 lost
python3 tools/bet_tracker.py settle 2 push
```

#### View Statistics
```bash
# Overall stats
python3 tools/bet_tracker.py stats

# Filter by sport
python3 tools/bet_tracker.py stats --sport NFL

# Last 30 days
python3 tools/bet_tracker.py stats --days 30
```

#### Export Data
```bash
python3 tools/bet_tracker.py export --file my_bets.json
```

**Data Storage:**
- Bets are stored in `bets.csv` in the current directory
- CSV format for easy import into Excel or other tools

---

## Testing

### Running Tests

```bash
# Run all tests
python3 tests/test_interpreter.py

# Run with verbose output
python3 -m pytest tests/ -v

# Run specific test class
python3 -m pytest tests/test_interpreter.py::TestInterpreter -v
```

### Test Coverage

The test suite includes:
- **Interpreter Tests**: Arithmetic, variables, functions, control flow
- **Lexer Tests**: Tokenization of numbers, strings, keywords, operators
- **Parser Tests**: AST generation for various constructs
- **Built-in Function Tests**: Odds conversions, Kelly, EV, parlay, vig

### Writing Tests

```python
import unittest
from lexer import Lexer
from parser import Parser
from interpreter import Interpreter

class TestMyFeature(unittest.TestCase):
    def run_code(self, code: str):
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        interpreter = Interpreter()
        return interpreter.interpret(ast)

    def test_my_calculation(self):
        result = self.run_code("calculate_ev(0.55, -110, 100)")
        self.assertGreater(result, 0)  # Should be +EV
```

---

## Examples

### Basic Examples (1-7)

1. **01_basic_bet.odds** - Basic betting calculations
2. **02_kelly_criterion.odds** - Optimal bet sizing
3. **03_parlay.odds** - Parlay betting analysis
4. **04_vig_calculator.odds** - Understanding bookmaker's vig
5. **05_bankroll_management.odds** - Bankroll simulation
6. **06_odds_conversion.odds** - Format conversions
7. **07_advanced_strategy.odds** - EV-based betting strategy

### Advanced Examples (8-10)

8. **08_arbitrage_betting.odds** - Arbitrage opportunity detection
9. **09_monte_carlo_simulation.odds** - Monte Carlo bankroll simulation
10. **10_hedging_calculator.odds** - Hedging strategies and middle opportunities

### Running Examples

```bash
# Run an example
python3 oddsscript.py examples/02_kelly_criterion.odds

# Run all examples
for f in examples/*.odds; do
    echo "Running $f..."
    python3 oddsscript.py "$f"
    echo "---"
done
```

---

## Package Development

### Creating New Modules

1. **Create Python file in appropriate directory:**
   - `lib/` for standard library functions
   - `strategies/` for betting strategies
   - `tools/` for CLI utilities

2. **Follow naming conventions:**
   - Use snake_case for filenames
   - Use descriptive names

3. **Add documentation:**
   - Docstrings for all functions
   - Usage examples
   - Add to this PACKAGES.md file

4. **Write tests:**
   - Add tests in `tests/` directory
   - Test all major functionality

### Example: Creating a New Strategy

```python
# strategies/my_strategy.py
"""
My Custom Betting Strategy
"""

class MyStrategy:
    def __init__(self, param1, param2):
        self.param1 = param1
        self.param2 = param2

    def next_bet(self, won_last: bool) -> float:
        # Calculate next bet size
        pass

    def record_result(self, won: bool):
        # Update strategy state
        pass

def simulate_my_strategy(...):
    # Simulation function
    pass
```

---

## Tips and Best Practices

### Using the Statistics Module

```python
# Track your betting results
from lib.statistics import *

returns = [0.05, -0.02, 0.03, 0.01, -0.01, 0.04]
bankroll_history = [1000, 1050, 1029, 1060, 1070, 1059, 1102]

print(f"Mean Return: {mean(returns):.4f}")
print(f"Sharpe Ratio: {sharpe_ratio(returns):.2f}")
print(f"Max Drawdown: {max_drawdown(bankroll_history):.2f}%")
```

### Strategy Comparison

```python
# Compare different strategies
from strategies.flat_betting import compare_strategies

results = compare_strategies(
    starting_bankroll=1000,
    num_bets=100,
    win_probability=0.54,
    odds=-110
)

for strategy, stats in results.items():
    print(f"{strategy}:")
    print(f"  Final: ${stats['bankroll']:.2f}")
    print(f"  ROI: {stats['roi']:.2f}%")
```

### Quick Calculations

```bash
# Use the calculator for quick checks
alias kelly='python3 tools/odds_calc.py kelly'
alias ev='python3 tools/odds_calc.py ev'
alias parlay='python3 tools/odds_calc.py parlay'

# Then:
kelly --prob 0.55 --odds -110 --bankroll 1000
ev --prob 0.52 --odds -110 --stake 100
parlay -110 -110 +150 --stake 50
```

---

## Integration with OddsScript

While these packages are written in Python, you can use them alongside OddsScript programs:

```bash
# Run OddsScript for analysis
python3 oddsscript.py my_analysis.odds

# Use Python tools for tracking
python3 tools/bet_tracker.py add NBA "Lakers vs Celtics" "Lakers -5" \
    --odds -110 --stake 100

# Check stats
python3 tools/bet_tracker.py stats
```

---

## Contributing

To contribute a new package:

1. Create your module following the structure above
2. Add comprehensive documentation
3. Write unit tests
4. Update this PACKAGES.md file
5. Submit a pull request

---

## License

All packages are released under the MIT License, same as OddsScript.

### Backtesting Framework (`lib/backtesting.py`)

Test betting strategies against historical data or simulations.

**Classes:**
- `BetResult` - Single bet result
- `BacktestResult` - Full backtest results with analytics
- `Backtester` - Run backtests

**Key Methods:**
- `run_historical_backtest()` - Test on historical data
- `run_monte_carlo_backtest()` - Monte Carlo simulation
- `compare_strategies()` - Compare multiple strategies

**Example:**
```python
from lib.backtesting import Backtester, generate_sample_data

# Generate or load historical data
data = generate_sample_data(100, win_rate=0.54)

# Create backtester
bt = Backtester(starting_bankroll=1000)

# Test a strategy
result = bt.run_historical_backtest(
    "My Strategy",
    lambda br, odds: br * 0.02,  # Bet 2% of bankroll
    data
)

result.print_summary()
```

### Variance Calculator (`lib/variance_calc.py`)

Understand variance and risk of ruin for betting strategies.

**Key Functions:**
- `calculate_variance()` - Variance per bet
- `standard_deviation()` - Std dev over N bets
- `confidence_interval()` - Confidence intervals for profit
- `risk_of_ruin()` - Probability of going broke
- `required_bankroll()` - Bankroll needed for risk tolerance
- `kelly_variance()` - Variance when using Kelly

**Example:**
```bash
python3 lib/variance_calc.py -w 0.54 -o -110 -b 1000 -s 20 -n 100
```

### Closing Line Value Tracker (`lib/clv_tracker.py`)

Track whether you're beating the closing line - the #1 indicator of long-term success.

**Key Methods:**
- `add_bet()` - Add bet with your odds
- `update_closing_line()` - Add closing line odds
- `settle_bet()` - Record result
- `get_stats()` - Comprehensive CLV statistics
- `print_stats()` - Formatted CLV analysis

**CLI Usage:**
```bash
# Add a bet
python3 lib/clv_tracker.py add "Lakers vs Celtics" "Lakers -5" -110 -c -108

# Update closing line
python3 lib/clv_tracker.py close 0 -108

# View stats
python3 lib/clv_tracker.py stats
```

---

## Advanced Tools

### Teaser Calculator (`tools/teaser_calc.py`)

Calculate teaser odds and payouts for NFL and NBA.

**Features:**
- NFL teasers: 6, 6.5, 7 points
- NBA teasers: 4, 4.5, 5 points
- Wong teaser detection (crossing key numbers 3 and 7)
- Break-even analysis per leg

**Usage:**
```bash
# NFL 6-point teaser
python3 tools/teaser_calc.py nfl 6 -l "Chiefs" -7 -l "Bills" -3 -s 100

# NBA 4.5-point teaser
python3 tools/teaser_calc.py nba 4.5 -l "Lakers" -5.5 -l "Celtics" -4 -s 50

# List available teasers
python3 tools/teaser_calc.py nfl 6 --list
```

### Round Robin Calculator (`tools/round_robin_calc.py`)

Calculate all parlay combinations for round robin bets.

**Features:**
- Supports any number of selections
- Multiple parlay sizes (2-team, 3-team, etc.)
- Scenario analysis (what if X teams win?)
- Complete payout breakdown

**Usage:**
```bash
# 4-team round robin with 2s and 3s
python3 tools/round_robin_calc.py \
  -l Chiefs -110 -l Bills -120 -l Ravens +150 -l Bengals -105 \
  --sizes 2 3 --stake 10

# 5-team round robin, just 2-teamers
python3 tools/round_robin_calc.py \
  -l T1 -110 -l T2 -110 -l T3 -110 -l T4 -110 -l T5 -110 \
  --sizes 2 --stake 20
```

**Output includes:**
- All parlay combinations
- Total number of parlays
- Total risk
- Scenario payouts (0 wins, 1 win, 2 wins, etc.)

### Bonus Calculator (`tools/bonus_calc.py`)

Optimal strategies for sportsbook bonuses and promotions.

**Bonus Types:**

1. **Risk-Free Bets**
```bash
python3 tools/bonus_calc.py riskfree 100 -110
```

2. **Deposit Match**
```bash
python3 tools/bonus_calc.py deposit 1000 100 5
# $1000 deposit, 100% match, 5x rollover
```

3. **Free Bet Conversion**
```bash
python3 tools/bonus_calc.py freebet 50 +200 --hedge -110
```

4. **Profit Boost**
```bash
python3 tools/bonus_calc.py boost 100 -110 50
# $100 bet at -110 with 50% boost
```

### Bankroll Simulator (`tools/bankroll_sim.py`)

Simulate betting strategies with ASCII visualization.

**Strategies:**
- Flat betting
- Percentage betting
- Kelly criterion
- Martingale

**Features:**
- ASCII chart visualization
- Detailed statistics
- Monte Carlo simulations
- Risk metrics

**Usage:**
```bash
# Single simulation with visualization
python3 tools/bankroll_sim.py -b 1000 -s kelly -w 0.55 -o -110 -n 100

# Multiple simulations (Monte Carlo)
python3 tools/bankroll_sim.py -b 1000 -s percentage -w 0.54 -o -110 -n 100 --sims 1000
```

**Output:**
- Bankroll progression chart
- Win/loss record
- Peak and low values
- Maximum drawdown
- ROI and profit
- Bust rate (for multiple sims)

### Portfolio Optimizer (`tools/portfolio_optimizer.py`)

Optimize bet allocation across multiple opportunities using Modern Portfolio Theory.

**Optimization Methods:**
- Kelly Criterion
- EV-Weighted allocation
- Sharpe Ratio optimization
- Equal allocation (baseline)

**Features:**
- Multi-bet portfolio optimization
- Risk-adjusted returns
- Correlation awareness
- Side-by-side comparison

**Usage:**
```bash
# Optimize 3-bet portfolio
python3 tools/portfolio_optimizer.py -b 1000 \
  --bet "Chiefs ML" -150 0.58 \
  --bet "Lakers spread" -110 0.54 \
  --bet "Over 48.5" +105 0.52 \
  --max-allocation 0.10

# Compare all methods
python3 tools/portfolio_optimizer.py -b 5000 \
  --bet "Bet1" -110 0.55 \
  --bet "Bet2" +120 0.48 \
  --bet "Bet3" -105 0.53 \
  --compare
```

**Output:**
- Optimal allocation per bet
- Expected portfolio return
- Portfolio variance/risk
- Sharpe ratio
- Method comparison table

### Line Movement Tracker (`tools/line_tracker.py`)

Track line movements and detect sharp/steam moves.

**Features:**
- Line movement history tracking
- Steam move detection
- Multi-book comparison
- Reverse Line Movement (RLM) detection
- CLV opportunity calculation

**Usage:**
```bash
# Track single book
python3 tools/line_tracker.py "Chiefs vs Bills" -3 \
  -m -3.5 FanDuel -m -4 DraftKings -m -4.5 BetMGM

# Multi-book comparison
# (Use programmatically)
```

**Key Metrics:**
- Total line movement
- Number of movements
- Movement pattern (upward/downward/stable)
- Volatility
- Steam moves detected
- Potential RLM warnings

### Poisson Calculator (`lib/poisson_calculator.py`)

Calculate probabilities for goal/point-based sports using Poisson distribution.

**Calculations:**
- Match outcome probabilities (win/draw/loss)
- Over/Under totals
- Correct score probabilities
- Both Teams To Score (BTTS)
- Asian Handicap probabilities

**Usage:**
```bash
# Soccer match analysis
python3 lib/poisson_calculator.py match 1.8 1.2 --sport soccer

# Over/Under analysis
python3 lib/poisson_calculator.py over-under 1.8 1.2 2.5

# Correct score
python3 lib/poisson_calculator.py correct-score 1.8 1.2 2 1

# BTTS probability
python3 lib/poisson_calculator.py btts 1.8 1.2
```

**Use Cases:**
- Soccer totals betting
- Hockey goal betting
- Basketball point modeling
- Finding value in goal markets

### Tax Calculator (`tools/tax_calculator.py`)

Calculate US gambling taxes with 2024 tax brackets.

**Features:**
- Federal tax calculation (single & married filing)
- Standard vs. itemized deduction comparison
- Gambling loss deduction (up to winnings)
- Withholding requirement check
- Quarterly estimated payment calculation
- State tax support

**Usage:**
```bash
# Basic calculation
python3 tools/tax_calculator.py -i 75000 -w 25000 -l 18000 --status single

# With state tax
python3 tools/tax_calculator.py -i 100000 -w 50000 -l 35000 \
  --status married --state-tax 0.05
```

**Output:**
- Recommended filing method (standard vs. itemized)
- Total tax owed
- Effective tax rate
- Net gambling profit after tax
- Withholding warnings
- Quarterly payment amounts

### Correlation Analysis (`lib/correlation_analysis.py`)

Analyze correlations between parlay legs to avoid common mistakes.

**Features:**
- Correlation coefficient calculation
- Same-game correlation detection
- Parlay odds adjustment for correlation
- Common scenario examples
- Detailed warnings

**Usage:**
```bash
# Show common correlation examples
python3 lib/correlation_analysis.py --examples

# Analyze a same-game parlay (BAD)
python3 lib/correlation_analysis.py \
  --leg moneyline -150 game1 Chiefs "Chiefs ML" \
  --leg spread -110 game1 Chiefs "Chiefs -7" \
  --leg total_over -110 game1 "" "Over 48.5"

# Analyze multi-game parlay (GOOD)
python3 lib/correlation_analysis.py \
  --leg moneyline -150 game1 "" "Chiefs ML" \
  --leg moneyline +120 game2 "" "Lions ML" \
  --leg spread -110 game3 "" "Eagles -3"
```

**Key Warnings:**
- ⛔ Perfect correlation (DO NOT parlay)
- ⚠️ Strong correlation (not recommended)
- ⚡ Moderate correlation (reduces value)
- ✓ No correlation (acceptable)

### Performance Attribution (`tools/performance_attribution.py`)

Analyze betting performance across multiple dimensions to identify edge sources.

**Dimensions:**
- By sport (NFL, NBA, MLB, etc.)
- By bet type (moneyline, spread, total, prop)
- By sportsbook
- By odds category (short/medium/long)
- By CLV (positive vs negative)

**Features:**
- Top/bottom performer identification
- Sharpe ratio by category
- Comprehensive recommendations
- JSON export for further analysis

**Usage:**
```bash
# Full attribution report
python3 tools/performance_attribution.py bets.csv

# Specific dimension
python3 tools/performance_attribution.py bets.csv --dimension sport

# Export to JSON
python3 tools/performance_attribution.py bets.csv --export report.json
```

**CSV Format:**
```csv
date,sport,bet_type,odds,stake,result,book,clv,description
2024-01-15,nfl,spread,-110,100,win,fanduel,2.5,Chiefs -3
2024-01-16,nba,moneyline,-150,50,loss,draftkings,-1.2,Lakers ML
```

**Output:**
- Overall performance metrics
- Performance by each dimension
- Top 3 performers per dimension
- Bottom 3 performers (areas to improve)
- Actionable recommendations

### Arbitrage Calculator (`tools/arbitrage_calculator.py`)

Find guaranteed profit opportunities across multiple sportsbooks.

**Features:**
- Two-way market arbitrage (over/under, moneyline)
- Three-way market arbitrage (soccer 1X2)
- Multi-book comparison to find best arb
- Custom stake calculations

**Usage:**
```bash
# Two-way arbitrage
python3 tools/arbitrage_calculator.py --two-way -o1 -105 -o2 +100

# Three-way arbitrage (soccer)
python3 tools/arbitrage_calculator.py --three-way -o1 +200 -o2 +250 -o3 -110

# Multi-book comparison
python3 tools/arbitrage_calculator.py --multi-book \
  --book FanDuel over -110 \
  --book DraftKings over -108 \
  --book BetMGM under +105 \
  --book Caesars under +100

# Custom stake
python3 tools/arbitrage_calculator.py --two-way -o1 +105 -o2 -110 --stake 1000
```

**Output:**
- Arbitrage exists (yes/no)
- Profit margin percentage
- Stake distribution
- Guaranteed profit
- Best books for each outcome

### Advanced Hedge Calculator (`tools/hedge_calculator.py`)

Calculate optimal hedges for parlays, futures, and multi-way outcomes.

**Hedge Types:**
1. **Parlay Hedging**
   - Guarantee equal profit
   - Maximize parlay upside
   - Freeroll (get stakes back)

2. **Futures Hedging**
   - Lock in guaranteed profit
   - Account for unrealized P/L

3. **Middle Opportunities**
   - Calculate middle scenarios
   - Analyze best/worst case

**Usage:**
```bash
# Parlay hedge (guarantee profit)
python3 tools/hedge_calculator.py parlay \
  --stake 100 --parlay-odds +800 --hedge-odds -110

# Parlay freeroll
python3 tools/hedge_calculator.py parlay \
  --stake 50 --parlay-odds +500 --hedge-odds -110 --strategy freeroll

# Futures hedge
python3 tools/hedge_calculator.py futures \
  --stake 100 --original-odds +2000 --current-odds +500 --hedge-odds -150

# Middle opportunity
python3 tools/hedge_calculator.py middle \
  --odds1 -110 --odds2 -110 --spread1 -3 --spread2 +3.5 --stake 100
```

**Strategies:**
- **Guarantee**: Equal profit both outcomes
- **Maximize**: Let parlay ride but hedge some
- **Freeroll**: Get original stake back

### Market Maker Tool (`tools/market_maker.py`)

Calculate fair odds, remove vig, and set profitable betting lines.

**Features:**
- Calculate bookmaker's vig/overround
- Remove vig using proportional or power method
- Set odds with target profit margin
- Find value bets by comparing to true probabilities
- Convert moneyline to spread

**Usage:**
```bash
# Calculate vig
python3 tools/market_maker.py vig -110 -110

# Three-way vig (soccer)
python3 tools/market_maker.py vig +180 +220 +150

# Set odds with 5% margin
python3 tools/market_maker.py set-odds --probs 0.55 0.45 --margin 5

# Find value bets
python3 tools/market_maker.py value \
  --market "Team A" +150 --market "Team B" -170 \
  --true-probs 0.45 0.55 --min-edge 0.03

# Calculate spread odds
python3 tools/market_maker.py spread --prob 0.55 --margin 4.55

# Convert moneyline to spread
python3 tools/market_maker.py ml-to-spread -180
```

**Key Calculations:**
- Fair odds (vig-free)
- True probabilities
- Expected value
- Profit margins
- Value identification

### Regression Analysis (`lib/regression_analysis.py`)

Build simple betting models using linear and multiple regression.

**Features:**
- Simple linear regression (one predictor)
- Multiple linear regression (multiple predictors)
- R-squared and adjusted R-squared
- Prediction with new data
- CSV data import

**Usage:**
```bash
# Simple linear regression
python3 lib/regression_analysis.py --simple \
  --x 1 2 3 4 5 --y 2 4 5 4 5

# Multiple regression from CSV
python3 lib/regression_analysis.py --csv training_data.csv

# Predict new values
python3 lib/regression_analysis.py --csv data.csv --predict 3.5 2.1 1.8
```

**CSV Format:**
```csv
offensive_rating,defensive_rating,total_points
110,105,215
115,98,225
105,110,208
```

**Use Cases:**
- Predict team totals from offensive/defensive stats
- Forecast player props from historical data
- Model win probability from power ratings
- Build custom sports betting models

### Multi-Outcome Kelly (`lib/multi_outcome_kelly.py`)

Calculate Kelly Criterion for markets with 3+ outcomes.

**Features:**
- Kelly fractions for multiple simultaneous bets
- Fractional Kelly support
- Expected bankroll growth calculation
- Portfolio optimization

**Usage:**
```bash
# Horse racing (5 horses)
python3 lib/multi_outcome_kelly.py -b 1000 --max-fraction 0.25 \
  --outcome "Horse A" +300 0.35 \
  --outcome "Horse B" +500 0.25 \
  --outcome "Horse C" +800 0.15 \
  --outcome "Horse D" +1200 0.10 \
  --outcome "Horse E" +2000 0.15

# Soccer 1X2
python3 lib/multi_outcome_kelly.py -b 500 --max-fraction 0.20 \
  --outcome "Home Win" -110 0.52 \
  --outcome "Draw" +220 0.28 \
  --outcome "Away Win" +180 0.20

# Golf tournament
python3 lib/multi_outcome_kelly.py -b 2000 --max-fraction 0.10 \
  --outcome "Player 1" +800 0.15 \
  --outcome "Player 2" +1200 0.10 \
  --outcome "Player 3" +1500 0.08
```

**Output:**
- Kelly fraction per outcome
- Stake amounts
- Expected value per bet
- Total portfolio expected growth
- Number of recommended bets

---

## Complete Tool Reference

### Quick Command Examples

```bash
# ===== ODDS CALCULATIONS =====
# Convert odds
python3 tools/odds_calc.py convert -110

# Kelly criterion
python3 tools/odds_calc.py kelly -p 0.55 -o -110 -b 1000

# Expected value
python3 tools/odds_calc.py ev -p 0.55 -o -110 -s 100

# Parlay odds
python3 tools/odds_calc.py parlay -110 -120 +150 -s 50

# Vig calculator
python3 tools/odds_calc.py vig -110 -110

# ===== TEASERS & PARLAYS =====
# NFL teaser
python3 tools/teaser_calc.py nfl 6 -l "Chiefs" -7 -l "Bills" -3 -s 100

# Round robin
python3 tools/round_robin_calc.py -l T1 -110 -l T2 -120 -l T3 +150 --sizes 2 3 -s 10

# ===== PERFORMANCE TRACKING =====
# Add a bet
python3 tools/bet_tracker.py add NFL "Chiefs vs Bills" "Chiefs -3" -o -110 -s 100

# View stats
python3 tools/bet_tracker.py stats --sport NFL --days 30

# Settle bet
python3 tools/bet_tracker.py settle 0 won

# ===== CLV TRACKING =====
# Add bet with CLV
python3 lib/clv_tracker.py add "Game" "Pick" -110 -c -108

# View CLV stats
python3 lib/clv_tracker.py stats

# ===== BONUSES =====
# Risk-free bet hedge
python3 tools/bonus_calc.py riskfree 100 -110

# Free bet conversion
python3 tools/bonus_calc.py freebet 50 +200

# ===== SIMULATION =====
# Bankroll simulation
python3 tools/bankroll_sim.py -b 1000 -s kelly -w 0.55 -o -110 -n 100

# Variance analysis
python3 lib/variance_calc.py -w 0.54 -o -110 -b 1000 -s 20 -n 100

# Backtest a strategy
python3 lib/backtesting.py

# ===== PORTFOLIO OPTIMIZATION =====
# Optimize bet allocation
python3 tools/portfolio_optimizer.py -b 1000 \
  --bet "Bet1" -110 0.55 --bet "Bet2" +120 0.52 --compare

# ===== LINE TRACKING =====
# Track line movements
python3 tools/line_tracker.py "Game" -3 -m -3.5 Book1 -m -4 Book2

# ===== POISSON ANALYSIS =====
# Soccer match probabilities
python3 lib/poisson_calculator.py match 1.8 1.2 --sport soccer

# Over/under analysis
python3 lib/poisson_calculator.py over-under 1.8 1.2 2.5

# ===== TAX CALCULATION =====
# Calculate gambling taxes
python3 tools/tax_calculator.py -i 75000 -w 25000 -l 18000 --status single

# ===== CORRELATION ANALYSIS =====
# Check parlay correlations
python3 lib/correlation_analysis.py --examples

# Analyze specific parlay
python3 lib/correlation_analysis.py \
  --leg moneyline -150 game1 "" "Chiefs ML" \
  --leg spread -110 game2 "" "Lakers -5"

# ===== PERFORMANCE ATTRIBUTION =====
# Analyze betting performance
python3 tools/performance_attribution.py bets.csv

# By specific dimension
python3 tools/performance_attribution.py bets.csv --dimension sport

# ===== ARBITRAGE =====
# Two-way arbitrage
python3 tools/arbitrage_calculator.py --two-way -o1 -105 -o2 +100

# Three-way arbitrage
python3 tools/arbitrage_calculator.py --three-way -o1 +200 -o2 +250 -o3 -110

# ===== HEDGING =====
# Parlay hedge
python3 tools/hedge_calculator.py parlay -s 100 -p +800 -h -110

# Futures hedge
python3 tools/hedge_calculator.py futures -s 100 -o +2000 -c +500 -h -150

# Middle opportunity
python3 tools/hedge_calculator.py middle --odds1 -110 --odds2 -110 --spread1 -3 --spread2 +3.5

# ===== MARKET MAKING =====
# Calculate vig
python3 tools/market_maker.py vig -110 -110

# Find value bets
python3 tools/market_maker.py value --market "Team A" +150 --market "Team B" -170 --true-probs 0.45 0.55

# Set odds with margin
python3 tools/market_maker.py set-odds --probs 0.55 0.45 --margin 5

# ===== MODELING =====
# Build regression model
python3 lib/regression_analysis.py --csv training_data.csv

# Multi-outcome Kelly
python3 lib/multi_outcome_kelly.py -b 1000 --outcome "A" +300 0.35 --outcome "B" +500 0.25
```

---

## Tool Comparison Matrix

| Tool | Purpose | Input | Output |
|------|---------|-------|--------|
| odds_calc | Quick calculations | Odds, probabilities | EV, Kelly, conversions |
| bet_tracker | Performance tracking | Your bets | Stats, analytics |
| clv_tracker | Closing line value | Bet odds, closing odds | CLV analysis |
| teaser_calc | Teaser analysis | Teams, lines, points | Teaser odds, Wong check |
| round_robin_calc | Parlay combinations | Selections, sizes | All combos, scenarios |
| bonus_calc | Bonus optimization | Bonus terms | Optimal strategy |
| bankroll_sim | Strategy simulation | Strategy, parameters | Visualization, stats |
| variance_calc | Risk analysis | Win rate, odds | Variance, risk of ruin |
| backtesting | Strategy testing | Historical data | Performance metrics |
| portfolio_optimizer | Bet allocation | Multiple opportunities | Optimal allocation |
| line_tracker | Line movements | Line history | Steam moves, RLM |
| poisson_calculator | Goal probabilities | Expected goals | Match probabilities |
| tax_calculator | Tax estimation | Income, winnings/losses | Tax owed, filing strategy |
| correlation_analysis | Parlay safety | Parlay legs | Correlation warnings |
| performance_attribution | Edge identification | Bet history | Performance by dimension |
| arbitrage_calculator | Arbitrage finder | Multi-book odds | Guaranteed profit, stakes |
| hedge_calculator | Hedging optimizer | Parlay/futures position | Optimal hedge strategy |
| market_maker | Fair odds calculator | Market odds, true probs | No-vig odds, value bets |
| regression_analysis | Model builder | Historical data | Predictions, R-squared |
| multi_outcome_kelly | Multi-Kelly optimizer | Multiple outcomes | Kelly fractions, EV |

---

## Best Practices

### Daily Workflow

1. **Before Betting:**
```bash
# Calculate Kelly size
python3 tools/odds_calc.py kelly -p 0.55 -o -110 -b 1000

# Check EV
python3 tools/odds_calc.py ev -p 0.55 -o -110 -s 100
```

2. **Place Bet:**
```bash
# Log the bet
python3 tools/bet_tracker.py add NFL "Game" "Pick" -o -110 -s 100

# Track CLV
python3 lib/clv_tracker.py add "Game" "Pick" -110
```

3. **After Game:**
```bash
# Settle bet
python3 tools/bet_tracker.py settle 0 won

# Update closing line
python3 lib/clv_tracker.py close 0 -108
```

4. **Weekly Review:**
```bash
# View stats
python3 tools/bet_tracker.py stats --days 7

# Check CLV
python3 lib/clv_tracker.py stats

# Review variance
python3 lib/variance_calc.py -w 0.54 -o -110 -b 1000 -s 20 -n 100
```

### Strategy Development

1. **Backtest** your strategy:
```python
from lib.backtesting import Backtester
# Test with historical data
```

2. **Analyze variance**:
```bash
python3 lib/variance_calc.py -w 0.54 -o -110 -b 1000 -s 20 -n 100
```

3. **Run simulations**:
```bash
python3 tools/bankroll_sim.py -b 1000 -s kelly -w 0.54 -o -110 -n 1000 --sims 1000
```

4. **Calculate risk of ruin** and adjust bet sizing accordingly

---

## Integration Examples

### Using Multiple Tools Together

**Example: Evaluating a promotional bet**

```bash
# 1. Check base EV
python3 tools/odds_calc.py ev -p 0.52 -o +150 -s 100

# 2. Calculate profit boost value
python3 tools/bonus_calc.py boost 100 +150 50

# 3. Determine optimal hedge for risk-free component
python3 tools/bonus_calc.py riskfree 100 +150

# 4. Log the bet
python3 tools/bet_tracker.py add NBA "Game" "Pick" -o +150 -s 100 -n "50% boost promo"
```

**Example: Analyzing a teaser vs straight bets**

```bash
# 1. Calculate 6-point teaser
python3 tools/teaser_calc.py nfl 6 -l "Team1" -8.5 -l "Team2" -2.5 -s 100

# 2. Compare to 2-team parlay
python3 tools/odds_calc.py parlay -110 -110 -s 100

# 3. Check if Wong teaser (built into teaser_calc)

# 4. Decision based on EV
```

