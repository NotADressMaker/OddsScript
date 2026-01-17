# Poisson Simulator - Tech Stack

A comprehensive Monte Carlo simulation tool for sports betting analysis using Poisson distribution.

## Overview

The Poisson Simulator is a standalone CLI tool that models goal/point-based sports using Poisson probability distribution. It enables bettors to:
- Test betting strategies before risking real money
- Calculate true win probabilities from team statistics
- Estimate expected variance and risk in betting outcomes
- Simulate entire seasons and compare scenarios

## Quick Start

```bash
# Basic match simulation
python3 tools/poisson_simulator.py match 1.8 1.2 -n 1000

# Test a betting strategy
python3 tools/poisson_simulator.py bet 1.8 1.2 over 2.5 -o 1.91 -s 10 -n 1000

# Simulate a season
python3 tools/poisson_simulator.py season -t "Team A:2.0" -t "Team B:1.8" -m 20

# Compare scenarios
python3 tools/poisson_simulator.py compare -n 5000
```

## Commands

### 1. Match Simulation

Simulate single matches or run Monte Carlo simulations.

```bash
# Single match
python3 tools/poisson_simulator.py match 1.8 1.2

# 10,000 simulations
python3 tools/poisson_simulator.py match 1.8 1.2 -n 10000 --seed 42

# Save results to JSON
python3 tools/poisson_simulator.py match 1.8 1.2 -n 5000 -o results.json
```

**Output:**
- Outcome probabilities (home win, draw, away win)
- Most common scores
- Total goals distribution with visual chart
- Detailed statistics

**Parameters:**
- `home_lambda` - Expected home team goals/points
- `away_lambda` - Expected away team goals/points
- `-n, --num-simulations` - Number of simulations (default: 1)
- `--seed` - Random seed for reproducibility
- `-o, --output` - Save to JSON file

### 2. Betting Strategy Test

Test betting strategies with comprehensive ROI analysis.

```bash
# Test Over 2.5 bet
python3 tools/poisson_simulator.py bet 1.8 1.2 over 2.5 -o 1.91 -s 10 -n 1000

# Test home win bet
python3 tools/poisson_simulator.py bet 2.0 1.2 home_win -o 2.10 -s 10 -n 1000

# Test BTTS (Both Teams To Score)
python3 tools/poisson_simulator.py bet 1.8 1.5 btts -o 1.80 -s 20 -n 5000

# Test draw bet
python3 tools/poisson_simulator.py bet 1.5 1.5 draw -o 3.40 -s 10 -n 1000
```

**Output:**
- Win rate and financial results
- Total profit/loss and ROI
- Standard deviation and volatility
- Risk assessment (LOW/MODERATE/HIGH)
- 95% confidence intervals
- Expected value analysis (positive/negative EV)

**Bet Types:**
- `home_win` - Home team to win
- `away_win` - Away team to win
- `draw` - Match ends in draw
- `over` - Total goals over line (requires target)
- `under` - Total goals under line (requires target)
- `btts` - Both teams to score

**Parameters:**
- `home_lambda`, `away_lambda` - Expected goals
- `bet_type` - Type of bet
- `target` - Line for over/under (optional for other bets)
- `-o, --odds` - Decimal odds (required)
- `-s, --stake` - Bet stake (default: 10)
- `-n, --num-simulations` - Number of simulations (default: 1000)
- `--seed` - Random seed
- `--output` - Save to JSON

### 3. Season Simulation

Simulate a complete season with multiple teams.

```bash
# Premier League top 4
python3 tools/poisson_simulator.py season \
  -t "Liverpool:2.0" \
  -t "Man City:2.2" \
  -t "Arsenal:1.8" \
  -t "Chelsea:1.7" \
  -m 50

# With custom home advantage
python3 tools/poisson_simulator.py season \
  -t "Team A:2.0" \
  -t "Team B:1.5" \
  -t "Team C:1.8" \
  -m 30 \
  -a 0.5 \
  --seed 123
```

**Output:**
- Final standings (position, points, W-D-L, goals)
- Goal difference
- Recent matches
- Complete season statistics

**Parameters:**
- `-t, --teams` - Team in format "Name:Lambda" (repeat for each team)
- `-m, --num-matches` - Number of matches (default: 38)
- `-a, --home-advantage` - Home advantage bonus (default: 0.3)
- `--seed` - Random seed
- `-o, --output` - Save to JSON

### 4. Scenario Comparison

Compare predefined scenarios side-by-side.

```bash
python3 tools/poisson_simulator.py compare -n 5000
```

**Scenarios Compared:**
- Strong Favorite (2.5 vs 0.8)
- Moderate Favorite (2.0 vs 1.3)
- Even Match (1.5 vs 1.5)
- Underdog (1.3 vs 2.0)
- High Scoring (3.0 vs 2.8)
- Low Scoring (0.8 vs 0.7)

**Output:**
- Win/draw percentages for each scenario
- Average total goals
- Side-by-side comparison table

## Technical Details

### Poisson Distribution

The Poisson distribution models the probability of a given number of events occurring in a fixed interval. For sports:

```
P(X = k) = (λ^k × e^(-λ)) / k!
```

Where:
- `k` = number of goals/points
- `λ` (lambda) = expected number of goals/points
- `e` = Euler's number (≈2.718)

### Sampling Algorithm

Uses **Knuth's algorithm** for accurate Poisson sampling:
- For λ < 30: Direct simulation using Knuth's method
- For λ ≥ 30: Normal approximation for efficiency

### Statistical Accuracy

- Reproducible results with `--seed` parameter
- 95% confidence intervals for betting results
- Standard deviation and variance calculations
- Risk metrics based on volatility ratios

## Real-World Examples

### Example 1: Soccer Match Analysis

Analyze Liverpool (2.0 xG) vs Brighton (1.2 xG):

```bash
python3 tools/poisson_simulator.py match 2.0 1.2 -n 10000
```

Output shows:
- Liverpool 55% win probability
- Draw 23%
- Brighton 22%
- Most likely scores: 2-1, 1-0, 2-0

### Example 2: Over 2.5 Goals Strategy

Test if Over 2.5 at 1.91 odds is profitable:

```bash
python3 tools/poisson_simulator.py bet 2.0 1.2 over 2.5 -o 1.91 -s 10 -n 10000
```

Output shows:
- Win rate: 57.3%
- ROI: +9.5%
- Risk level: LOW
- ✓ POSITIVE EV BET

### Example 3: Season Simulation

Simulate Premier League with top teams:

```bash
python3 tools/poisson_simulator.py season \
  -t "Man City:2.3" \
  -t "Liverpool:2.1" \
  -t "Arsenal:1.9" \
  -t "Chelsea:1.7" \
  -t "Tottenham:1.8" \
  -m 100
```

### Example 4: Strategy Comparison

Compare home win vs draw bets:

```bash
# Home win at 2.10 odds
python3 tools/poisson_simulator.py bet 2.0 1.2 home_win -o 2.10 -s 10 -n 5000

# Draw at 3.40 odds
python3 tools/poisson_simulator.py bet 2.0 1.2 draw -o 3.40 -s 10 -n 5000
```

## Integration with SportsBetLang

The Poisson Simulator is also available as built-in functions in SportsBetLang:

```sportsbetlang
# In SportsBetLang programs
let results = poisson_simulate_matches(1.8, 1.2, 1000)
let match = poisson_simulate_match(2.0, 1.3)
let prob = poisson_probability(2, 1.8)
```

See `examples/11_poisson_simulations.odds` for detailed examples.

## Performance Notes

- Single simulations: Instant
- 1,000 simulations: < 0.1 seconds
- 10,000 simulations: < 1 second
- 100,000 simulations: < 5 seconds

## Tips for Best Results

1. **Use appropriate lambda values**: Base on xG (expected goals) for soccer, or adjusted team scoring averages
2. **Run enough simulations**: Use 1,000+ for reliable statistics, 10,000+ for precision
3. **Set seeds for reproducibility**: Use `--seed` when comparing strategies
4. **Account for home advantage**: Typically 0.3-0.4 goals in soccer
5. **Consider context**: Adjust lambdas for team form, injuries, motivation

## Error Handling

The tool validates:
- Lambda values must be positive
- Odds must be > 1.0
- Stake must be positive
- Number of simulations must be ≥ 1

## Output Formats

### Terminal Output
- Human-readable formatted output
- Visual charts for distributions
- Color-coded risk levels
- Clear sections and separators

### JSON Output
Use `-o filename.json` to save:
- Complete simulation data
- All statistics and results
- Score distributions
- Ready for further analysis

## Support

For issues or questions:
- Check `PACKAGES.md` for full documentation
- See `examples/11_poisson_simulations.odds` for code examples
- Run `python3 tools/poisson_simulator.py --help` for quick reference

## License

Part of SportsBetLang - MIT License
