# Simplified API Guide

The Simplified API makes VigScript incredibly easy to use with clean, intuitive functions.

## Table of Contents

- [Quick Start](#quick-start)
- [SBL Class](#sbl-class-one-liners)
- [Bet Class](#bet-class-fluent-api)
- [Compare Class](#compare-class-compare-bets)
- [Common Workflows](#common-workflows)
- [Examples](#examples)

## Quick Start

```python
from lib.simple_api import SBL, Bet, Compare

# Calculate Kelly bet size
kelly = SBL.kelly(win_prob=0.55, odds=2.0)
print(f"Bet {kelly*100:.1f}% of bankroll")

# Analyze a bet
bet = Bet(100).at_odds(2.1).with_probability(0.58)
bet.print_summary()

# Compare multiple bets
comp = Compare(bankroll=1000)
comp.add("Bet A", prob=0.58, odds=2.1)
comp.add("Bet B", prob=0.52, odds=2.3)
comp.print_comparison()
```

## SBL Class (One-Liners)

The `SBL` class provides quick access to common betting calculations.

### Kelly Criterion

```python
# Full Kelly
kelly = SBL.kelly(win_prob=0.55, odds=2.0)
# Returns: 0.10 (bet 10% of bankroll)

# Half-Kelly (recommended)
half = SBL.half_kelly(win_prob=0.55, odds=2.0)
# Returns: 0.05 (bet 5% of bankroll)

# Quarter-Kelly (conservative)
quarter = SBL.quarter_kelly(win_prob=0.55, odds=2.0)
# Returns: 0.025 (bet 2.5% of bankroll)
```

### Expected Value

```python
# EV in dollars
ev = SBL.ev(win_prob=0.55, odds=2.0, bet_amount=100)
# Returns: 10.0 (expected profit of $10)

# EV as percentage
ev_pct = SBL.ev_percent(win_prob=0.55, odds=2.0)
# Returns: 10.0 (10% EV)
```

### Odds Conversions

```python
# American to Decimal
decimal = SBL.american_to_decimal(-110)
# Returns: 1.909

decimal = SBL.american_to_decimal(150)
# Returns: 2.5

# Decimal to American
american = SBL.decimal_to_american(2.0)
# Returns: 100.0

# Fractional to Decimal
decimal = SBL.fractional_to_decimal(3, 1)  # 3/1
# Returns: 4.0

# Implied probability
implied = SBL.implied_prob(2.0)
# Returns: 0.5 (50%)
```

### Edge and Value

```python
# Calculate edge
edge = SBL.edge(win_prob=0.58, odds=2.1)
# Returns: 10.38 (10.38% edge)

# Remove vig
true_prob1, true_prob2 = SBL.remove_vig(1.91, 1.91)
# Returns: (0.5, 0.5) - true 50/50 without vig

# Closing Line Value
clv = SBL.clv(bet_odds=2.1, closing_odds=1.95)
# Returns: 7.69 (beat closing line by 7.69%)
```

### Bayesian Inference

```python
# Calculate Bayesian win probability
result = SBL.bayes(wins=12, losses=5)
print(f"Win %: {result['mean_probability']*100:.1f}%")
print(f"95% CI: [{result['ci_lower']*100:.1f}%, {result['ci_upper']*100:.1f}%]")
```

### Monte Carlo

```python
import random

# Define simulation
def simulate_season():
    wins = sum(1 for _ in range(16) if random.random() < 0.6)
    return wins

# Run simulation
result = SBL.simulate(simulate_season, n=10000)
print(f"Expected wins: {result['mean']:.1f}")
print(f"90% range: {result['p5']:.0f} to {result['p95']:.0f}")
```

### Quick Decisions

```python
# Should I bet?
should_bet = SBL.should_bet(win_prob=0.58, odds=2.1, min_edge=5)
# Returns: True (edge > 5%)

# Calculate ROI
roi = SBL.roi(total_wagered=1000, total_won=1100)
# Returns: 10.0 (10% ROI)

# Breakeven percentage
breakeven = SBL.breakeven_percentage(odds=2.0)
# Returns: 50.0 (need 50% win rate to break even)
```

### Parlays

```python
# Parlay odds
parlay_odds = SBL.parlay_odds([2.0, 1.5, 1.8])
# Returns: 5.4

# Parlay probability
parlay_prob = SBL.parlay_probability([0.5, 0.65, 0.55])
# Returns: 0.179 (17.9%)
```

### Bankroll Management

```python
# Calculate bet amount
bet = SBL.bet_amount(bankroll=1000, kelly_fraction=0.10, conservatism=0.5)
# Returns: 50.0 (bet $50)

# Units conversion
dollars = SBL.units_to_dollars(units=2.5, unit_size=50)
# Returns: 125.0

units = SBL.dollars_to_units(dollars=125, unit_size=50)
# Returns: 2.5
```

## Bet Class (Fluent API)

The `Bet` class allows method chaining for readable bet analysis.

### Basic Usage

```python
bet = (Bet(100)
       .named("Lakers vs Celtics")
       .at_odds(2.1)
       .with_probability(0.58)
       .from_bankroll(1000))
```

### Methods

```python
# Set bet name
bet.named("My Bet")

# Set odds (decimal)
bet.at_odds(2.1)

# Set odds (American)
bet.at_american(-110)

# Set win probability
bet.with_probability(0.58)

# Set bankroll
bet.from_bankroll(1000)

# Get metrics
edge = bet.edge()           # Edge percentage
ev = bet.ev()               # EV in dollars
ev_pct = bet.ev_percent()   # EV as percentage
kelly = bet.kelly_fraction() # Kelly fraction
kelly_bet = bet.kelly_size() # Kelly bet amount

# Should I bet?
should = bet.should_bet(min_edge=5)  # True/False

# Get summary
summary = bet.summary()  # Dictionary with all metrics

# Print formatted summary
bet.print_summary()
```

### Example Output

```python
bet = Bet(100).at_odds(2.1).with_probability(0.58).from_bankroll(1000)
bet.print_summary()
```

Output:
```
============================================================
BET ANALYSIS: Bet
============================================================
Bet Amount:        $100.00
Odds:              2.10
Your Probability:  58.0%
Implied Prob:      47.6%

EDGE:              10.38%
Expected Value:    $21.80 (21.80%)

Kelly Fraction:    19.82%
Half-Kelly Bet:    $99.09
Quarter-Kelly Bet: $49.55

RECOMMENDATION:    STRONG BET - Excellent edge
============================================================
```

## Compare Class (Compare Bets)

Compare multiple betting opportunities side-by-side.

### Basic Usage

```python
# Create comparison
comp = Compare(bankroll=1000)

# Add bets
comp.add("Bet A", prob=0.58, odds=2.1)
comp.add("Bet B", prob=0.52, odds=2.3)
comp.add("Bet C", prob=0.48, odds=2.5)

# Print comparison
comp.print_comparison()

# Find best bet
best = comp.best(metric='edge')  # 'edge', 'ev', or 'kelly'
print(f"Best bet: {best}")

# Get all summaries
summaries = comp.summary()
```

### Example Output

```
================================================================================
BETTING OPPORTUNITIES COMPARISON
================================================================================
Bet             Prob     Odds     Edge       EV%        Kelly
--------------------------------------------------------------------------------
Bet A            58.0%  2.10      10.38%    21.80%  $   99.09
Bet B            52.0%  2.30       8.48%    19.60%  $   75.65
Bet C            48.0%  2.50       8.00%    20.00%  $   64.00
--------------------------------------------------------------------------------
Best Edge:  Bet A
Best EV:    Bet A
================================================================================
```

## Common Workflows

### Workflow 1: Quick Single Bet Analysis

```python
from lib.simple_api import SBL

# Your inputs
win_prob = 0.58
odds = 2.1
bankroll = 1000

# Quick calculations
edge = SBL.edge(win_prob, odds)
kelly = SBL.kelly(win_prob, odds)
bet_size = bankroll * kelly * 0.5  # Half-Kelly

print(f"Edge: {edge:.2f}%")
print(f"Bet: ${bet_size:.2f}")

if SBL.should_bet(win_prob, odds, min_edge=5):
    print("✓ PLACE BET")
else:
    print("✗ PASS")
```

### Workflow 2: Detailed Bet Analysis

```python
from lib.simple_api import Bet

bet = (Bet(100)
       .named("Lakers ML")
       .at_american(-110)
       .with_probability(0.55)
       .from_bankroll(5000))

bet.print_summary()
```

### Workflow 3: Compare Multiple Games

```python
from lib.simple_api import Compare

# Tonight's games
comp = Compare(bankroll=1000)
comp.add("Lakers ML", prob=0.55, odds=1.91)
comp.add("Celtics -5", prob=0.58, odds=2.10)
comp.add("Warriors O 220", prob=0.52, odds=2.00)

comp.print_comparison()
best = comp.best('edge')
print(f"Best bet tonight: {best}")
```

### Workflow 4: Track Your Record

```python
from lib.simple_api import SBL

# Your betting history
total_wagered = 2500
total_won = 2700

roi = SBL.roi(total_wagered, total_won)
print(f"ROI: {roi:.2f}%")

# Bayesian true skill
wins = 52
losses = 48
result = SBL.bayes(wins, losses)
print(f"True Win %: {result['mean_probability']*100:.1f}%")
```

### Workflow 5: Season Simulation

```python
from lib.simple_api import SBL
import random

def simulate_season():
    points = 75  # Current points
    for _ in range(25):  # 25 games left
        if random.random() < 0.58:
            points += 2
        elif random.random() < 0.25:
            points += 1
    return points

result = SBL.simulate(simulate_season, n=10000)
print(f"Expected points: {result['mean']:.1f}")
print(f"Playoff prob: {sum(1 for p in result['results'] if p >= 95)/10000*100:.1f}%")
```

## Examples

See `examples/quick_start.py` for 12 complete working examples including:

1. Kelly Criterion basics
2. Edge and EV calculations
3. Odds conversions
4. Fluent bet analysis
5. Comparing multiple bets
6. Bayesian inference
7. Quick decision making
8. Parlay analysis
9. ROI calculation
10. Removing vig
11. CLV tracking
12. Units conversion

## Aliases

For even shorter code, use the convenient aliases:

```python
from lib.simple_api import kelly, ev, edge, bayes, simulate

# Now you can use:
k = kelly(0.55, 2.0)
e = ev(0.55, 2.0, 100)
edg = edge(0.55, 2.0)
b = bayes(12, 5)
```

## Error Handling

The simplified API provides clear error messages:

```python
try:
    bet = Bet(100).at_odds(2.1)
    bet.edge()  # Forgot to set probability!
except ValueError as e:
    print(e)
    # "Win probability not set. Use .with_probability()"
```

## Tips

1. **Use Half-Kelly**: Always use `half_kelly()` or multiply `kelly()` by 0.5
2. **Minimum Edge**: Set `min_edge=5` for conservative betting
3. **Chain Methods**: Use fluent API for readable code
4. **Compare Before Betting**: Always compare multiple opportunities
5. **Track CLV**: Use `SBL.clv()` to verify you're beating the market

## Next Steps

- Try the examples in `examples/quick_start.py`
- Read the [Advanced Statistics Guide](advanced_stats_guide.md)
- Explore [Machine Learning Models](ml_models_guide.md)
- Check out [NHL Analytics](nhl_analytics_guide.md)

---

For more information, see the main [README](../README.md).
