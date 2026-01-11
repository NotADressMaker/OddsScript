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
