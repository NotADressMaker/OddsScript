# OddsScript Packages and Tools

This document describes all the packages, libraries, and utilities available for OddsScript.

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

