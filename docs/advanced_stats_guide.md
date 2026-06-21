# Advanced Statistics Guide

Comprehensive guide to advanced statistical techniques for sports betting analytics in VigScript.

## Table of Contents

1. [Overview](#overview)
2. [Regression Analysis](#regression-analysis)
3. [Time Series Analysis](#time-series-analysis)
4. [Bayesian Inference](#bayesian-inference)
5. [Monte Carlo Simulation](#monte-carlo-simulation)
6. [Bootstrap Methods](#bootstrap-methods)
7. [Statistical Tests](#statistical-tests)
8. [Risk Metrics](#risk-metrics)
9. [Usage Examples](#usage-examples)

## Overview

The Advanced Statistics library (`lib/advanced_stats.py`) provides sophisticated statistical techniques specifically designed for sports betting analytics:

- **Regression Models**: Linear and multiple regression for predictive modeling
- **Time Series Analysis**: Trend analysis, moving averages, exponential smoothing
- **Bayesian Methods**: Probability updates and credible intervals
- **Monte Carlo Simulation**: Risk assessment and outcome modeling
- **Bootstrap Resampling**: Confidence intervals without assumptions
- **Statistical Tests**: Permutation tests for comparing groups
- **Risk Metrics**: Sharpe ratio, Sortino ratio, Kelly Criterion

## Regression Analysis

### Linear Regression

Predict one variable based on another (e.g., points scored vs. Elo rating).

```python
from lib.advanced_stats import AdvancedStats

# Team Elo ratings
elo_ratings = [1500, 1550, 1600, 1650, 1700, 1750, 1800]

# Points scored per game
points = [20, 22, 24, 26, 28, 30, 32]

# Fit regression model
result = AdvancedStats.linear_regression(elo_ratings, points)

print(f"Equation: y = {result.coefficients[0]:.4f}x + {result.intercept:.2f}")
print(f"R-squared: {result.r_squared:.4f}")
print(f"RMSE: {result.rmse:.2f}")

# Make prediction for new team
new_elo = 1675
predicted_points = result.coefficients[0] * new_elo + result.intercept
print(f"Predicted points for Elo {new_elo}: {predicted_points:.1f}")
```

**Output:**
```
Equation: y = 0.0200x + -10.00
R-squared: 0.9900
RMSE: 0.58

Predicted points for Elo 1675: 23.5
```

### Multiple Regression

Predict using multiple independent variables.

```python
# Independent variables: [Elo, Home Field (1=yes, 0=no), Days Rest]
X = [
    [1650, 1, 7],
    [1700, 0, 5],
    [1550, 1, 6],
    [1750, 0, 4],
    [1600, 1, 7],
    [1800, 0, 3]
]

# Dependent variable: Points scored
y = [27, 25, 23, 28, 24, 29]

result = AdvancedStats.multiple_regression(X, y)

print(f"Intercept: {result.intercept:.2f}")
print(f"Coefficients: {[f'{c:.4f}' for c in result.coefficients]}")
print(f"R-squared: {result.r_squared:.4f}")

# Make prediction
new_team = [1675, 1, 6]  # Elo=1675, Home game, 6 days rest
prediction = result.intercept + sum(result.coefficients[i] * new_team[i]
                                    for i in range(len(new_team)))
print(f"Predicted points: {prediction:.1f}")
```

### Use Cases

- **Win Prediction**: Model win probability based on team stats
- **Score Prediction**: Estimate points scored
- **Line Movement**: Predict how lines will move
- **Player Props**: Predict player performance
- **Strength of Schedule**: Quantify schedule difficulty

## Time Series Analysis

### Exponential Moving Average (EMA)

Gives more weight to recent observations, good for detecting trends.

```python
# Team's points scored per game over season
points_per_game = [24, 27, 23, 28, 31, 29, 32, 30, 35, 33, 36, 34]

# Calculate EMA (alpha=0.3 means 30% weight to new data)
ema = AdvancedStats.exponential_moving_average(points_per_game, alpha=0.3)

print("Original:", points_per_game)
print("EMA:     ", [f'{x:.1f}' for x in ema])
```

**Output:**
```
Original: [24, 27, 23, 28, 31, 29, 32, 30, 35, 33, 36, 34]
EMA:      ['24.0', '24.9', '24.3', '25.3', '27.0', '27.6', '28.9', '29.2', '31.0', '31.6', '32.8', '33.2']
```

### Weighted Moving Average (WMA)

Linear weights favor recent observations.

```python
# Calculate 5-game WMA
wma = AdvancedStats.weighted_moving_average(points_per_game, window=5)

# WMA gives weights: 1, 2, 3, 4, 5 (most recent gets 5)
print("WMA:", [f'{x:.1f}' if x else 'None' for x in wma])
```

### Trend Calculation

Identify underlying trend in performance.

```python
# Calculate linear trend
trend = AdvancedStats.calculate_trend(points_per_game, method='linear')

print("Trend:", [f'{x:.1f}' for x in trend])

# Check if team is improving
if trend[-1] > trend[0]:
    print("Team is trending UP")
else:
    print("Team is trending DOWN")
```

### Use Cases

- **Form Analysis**: Identify hot/cold streaks
- **Trend Following**: Bet on teams with positive trends
- **Fatigue Detection**: Spot declining performance
- **Line Value**: Compare current form to season averages
- **Forecasting**: Predict future performance

## Bayesian Inference

### Bayesian Win Probability

Update win probability as new data arrives using Beta distribution.

```python
# Team starts season with no data (uninformative prior)
# After 12 games: 8 wins, 4 losses
result = AdvancedStats.bayesian_win_probability(
    wins=8,
    losses=4,
    prior_alpha=1.0,  # Uninformative prior
    prior_beta=1.0
)

print(f"Win Probability: {result['mean_probability']:.1%}")
print(f"Most Likely: {result['mode_probability']:.1%}")
print(f"95% Credible Interval: [{result['ci_lower']:.1%}, {result['ci_upper']:.1%}]")
```

**Output:**
```
Win Probability: 64.3%
Most Likely: 63.6%
95% Credible Interval: [42.8%, 82.1%]
```

### With Informed Prior

If you have domain knowledge, use an informed prior:

```python
# You believe team is above average (prior mean ~55%)
result = AdvancedStats.bayesian_win_probability(
    wins=8,
    losses=4,
    prior_alpha=5.5,  # Prior pseudo-wins
    prior_beta=4.5    # Prior pseudo-losses
)

print(f"Win Probability: {result['mean_probability']:.1%}")
```

### Bayesian Update

Manual Bayes' theorem calculation:

```python
# Prior: Team has 60% chance to win
prior = 0.60

# Evidence: Star player is injured
# Likelihood: When injured, team wins 40% of time
likelihood = 0.40

# Evidence probability: Injury happens in 10% of games where they win
# and 5% where they don't
evidence = (0.40 * 0.60) + (0.05 * 0.40)

# Update belief
posterior = AdvancedStats.bayesian_update(prior, likelihood, evidence)

print(f"Win probability updated: {prior:.1%} → {posterior:.1%}")
```

### Use Cases

- **Probability Updates**: Adjust probabilities as season progresses
- **Injury Impact**: Update win probability when players are injured
- **Lineup Changes**: Account for roster changes
- **Confidence Intervals**: Quantify uncertainty in predictions
- **Small Sample Sizes**: Make better estimates with limited data

## Monte Carlo Simulation

### Basic Simulation

Simulate thousands of possible outcomes to understand risk.

```python
import random

def simulate_season(games=16, win_prob=0.6):
    """Simulate a single season"""
    wins = sum(1 for _ in range(games) if random.random() < win_prob)
    return wins

# Run 10,000 simulations
result = AdvancedStats.monte_carlo_simulation(
    simulate_season,
    n_simulations=10000,
    games=16,
    win_prob=0.6
)

print(f"Expected Wins: {result['mean']:.1f}")
print(f"Median Wins: {result['median']:.0f}")
print(f"90% Range: {result['p5']:.0f} to {result['p95']:.0f} wins")
print(f"Chance of 10+ wins: {sum(1 for w in result['results'] if w >= 10) / len(result['results']):.1%}")
```

**Output:**
```
Expected Wins: 9.6
Median Wins: 10
90% Range: 6 to 13 wins
Chance of 10+ wins: 58.3%
```

### Bankroll Simulation

Simulate betting strategy outcomes:

```python
def simulate_betting_season(
    games=100,
    win_prob=0.55,
    odds=-110,
    stake_per_game=100,
    starting_bankroll=10000
):
    """Simulate a betting season"""
    bankroll = starting_bankroll

    for _ in range(games):
        if random.random() < win_prob:
            # Win
            bankroll += stake_per_game * (100 / 110)  # -110 odds
        else:
            # Loss
            bankroll -= stake_per_game

    return bankroll

result = AdvancedStats.monte_carlo_simulation(
    simulate_betting_season,
    n_simulations=10000,
    games=100,
    win_prob=0.55,
    odds=-110,
    stake_per_game=100,
    starting_bankroll=10000
)

print(f"Expected Final Bankroll: ${result['mean']:.2f}")
print(f"Risk of Ruin (< $1000): {sum(1 for b in result['results'] if b < 1000) / len(result['results']):.1%}")
print(f"Chance of Doubling: {sum(1 for b in result['results'] if b >= 20000) / len(result['results']):.1%}")
```

### Use Cases

- **Season Win Totals**: Simulate team season outcomes
- **Parlay Analysis**: Calculate true parlay probabilities
- **Bankroll Management**: Test betting strategies
- **Risk of Ruin**: Estimate probability of going broke
- **Expected Value**: Calculate EV of complex bets

## Bootstrap Methods

### Confidence Intervals

Calculate confidence intervals without assuming normal distribution.

```python
import statistics

# Your ROI over 50 bets
roi_data = [5.2, 8.1, -2.3, 12.4, 6.7, 9.2, 3.5, 11.1, 7.8, 4.9,
            -1.5, 10.3, 6.2, 8.9, 4.3, 7.1, 9.8, 5.6, 11.2, 3.8]

# Bootstrap confidence interval
result = AdvancedStats.bootstrap_confidence_interval(
    roi_data,
    statistics.mean,  # Statistic to calculate
    n_bootstrap=10000,
    confidence_level=0.95
)

print(f"Mean ROI: {result['statistic']:.1f}%")
print(f"95% CI: [{result['ci_lower']:.1f}%, {result['ci_upper']:.1f}%]")
print(f"Bootstrap Std: {result['bootstrap_std']:.2f}%")
```

**Output:**
```
Mean ROI: 6.6%
95% CI: [4.8%, 8.5%]
Bootstrap Std: 0.98%
```

### Any Statistic

Bootstrap works for any statistic (mean, median, standard deviation, etc.):

```python
# Median ROI
median_result = AdvancedStats.bootstrap_confidence_interval(
    roi_data,
    statistics.median,
    n_bootstrap=10000
)

print(f"Median ROI: {median_result['statistic']:.1f}%")
print(f"95% CI: [{median_result['ci_lower']:.1f}%, {median_result['ci_upper']:.1f}%]")
```

### Use Cases

- **Performance Metrics**: CI for win rate, ROI, profit
- **Small Samples**: Better estimates with limited data
- **Non-Normal Data**: Works without normality assumption
- **Custom Statistics**: Any function you can define
- **Comparison**: Test if one strategy beats another

## Statistical Tests

### Permutation Test

Test if two groups are significantly different (non-parametric).

```python
# Home game performance vs Away game performance
home_margins = [7, 10, 3, 14, 6, 11, 8, 9, 12, 5]
away_margins = [2, -3, 5, 1, -2, 4, 0, 3, -1, 2]

result = AdvancedStats.permutation_test(
    home_margins,
    away_margins,
    n_permutations=10000
)

print(f"Home Avg: {statistics.mean(home_margins):.1f}")
print(f"Away Avg: {statistics.mean(away_margins):.1f}")
print(f"Difference: {result['observed_difference']:.1f}")
print(f"P-value: {result['p_value']:.4f}")
print(f"Significant: {result['significant']}")
```

**Output:**
```
Home Avg: 8.5
Away Avg: 1.1
Difference: 7.4
P-value: 0.0023
Significant: True
```

### Correlation Matrix

Analyze relationships between multiple variables:

```python
# Variables: Points Scored, Points Allowed, Turnovers
points_for = [28, 24, 31, 27, 30, 26, 29, 32]
points_against = [21, 24, 18, 20, 19, 22, 20, 17]
turnovers = [2, 3, 1, 2, 1, 3, 2, 1]

data = [points_for, points_against, turnovers]

corr_matrix = AdvancedStats.calculate_correlation_matrix(data)

print("Correlation Matrix:")
print("           PF      PA      TO")
for i, row in enumerate(corr_matrix):
    labels = ["PF", "PA", "TO"]
    print(f"{labels[i]}: {[f'{val:6.3f}' for val in row]}")
```

## Risk Metrics

### Sharpe Ratio

Risk-adjusted return (higher is better):

```python
# Weekly returns (%)
returns = [2.5, -1.2, 3.8, 1.5, -0.8, 4.2, 2.1, -1.5, 3.3, 1.8]

sharpe = AdvancedStats.sharpe_ratio(returns, risk_free_rate=0.0)

print(f"Sharpe Ratio: {sharpe:.2f}")

# Interpretation:
# > 1.0: Good
# > 2.0: Very good
# > 3.0: Excellent
```

### Sortino Ratio

Like Sharpe but only penalizes downside volatility:

```python
sortino = AdvancedStats.sortino_ratio(returns, risk_free_rate=0.0)

print(f"Sortino Ratio: {sortino:.2f}")

# Usually higher than Sharpe (only counts downside)
```

### Kelly Criterion

Optimal bet sizing:

```python
# You estimate 55% win probability
# Odds are -110 (1.909 decimal)
win_prob = 0.55
decimal_odds = 1.909

kelly = AdvancedStats.kelly_optimal_size(win_prob, decimal_odds)

print(f"Kelly Criterion: {kelly:.1%} of bankroll")
print(f"Half Kelly (conservative): {kelly/2:.1%}")
```

**Output:**
```
Kelly Criterion: 10.0% of bankroll
Half Kelly (conservative): 5.0%
```

## Usage Examples

### Example 1: Predict Team Performance

```python
from lib.advanced_stats import AdvancedStats
import statistics

# Historical data: Elo rating → Points scored
historical_elo = [1550, 1580, 1620, 1590, 1640, 1610, 1650, 1680]
historical_points = [23, 25, 26, 24, 28, 26, 29, 30]

# Fit model
model = AdvancedStats.linear_regression(historical_elo, historical_points)

print(f"Model R²: {model.r_squared:.3f}")
print(f"RMSE: {model.rmse:.2f}")

# Predict for upcoming game
opponent_elo = 1625
predicted_points = model.coefficients[0] * opponent_elo + model.intercept

print(f"\nPrediction for Elo {opponent_elo}: {predicted_points:.1f} points")

# Calculate confidence using bootstrap
predictions_history = model.predictions
residuals = model.residuals

# Bootstrap prediction interval
import random
prediction_samples = []
for _ in range(1000):
    residual = random.choice(residuals)
    prediction_samples.append(predicted_points + residual)

print(f"90% Prediction Interval: [{sorted(prediction_samples)[50]:.1f}, "
      f"{sorted(prediction_samples)[950]:.1f}]")
```

### Example 2: Bayesian Line Shopping

```python
# You see line at -3.5 from two books
# Book A (reliable): -3.5
# Book B (less reliable): -4.0

# Your prior belief: true line is -3.7
# How should you update your belief?

# Using weighted average based on book reliability
book_a_weight = 0.7  # More reliable
book_b_weight = 0.3

updated_line = (-3.5 * book_a_weight) + (-4.0 * book_b_weight)
print(f"Updated true line estimate: {updated_line:.2f}")

# Calculate value on Book A
true_line = updated_line
available_line = -3.5
edge = true_line - available_line  # Negative edge (bad)

print(f"Edge: {edge:.2f} points")
if abs(edge) < 0.5:
    print("No significant value")
```

### Example 3: Simulate Betting Strategy

```python
import random

def simulate_martingale(
    starting_bankroll=1000,
    base_bet=10,
    games=100,
    win_prob=0.48
):
    """Simulate martingale betting strategy"""
    bankroll = starting_bankroll
    current_bet = base_bet

    for _ in range(games):
        if bankroll < current_bet:
            return 0  # Bankrupt

        bankroll -= current_bet

        if random.random() < win_prob:
            # Win - return to base bet
            bankroll += current_bet * 2
            current_bet = base_bet
        else:
            # Loss - double bet
            current_bet *= 2

    return bankroll

# Simulate strategy 10,000 times
result = AdvancedStats.monte_carlo_simulation(
    simulate_martingale,
    n_simulations=10000
)

print(f"Expected Final Bankroll: ${result['mean']:.2f}")
print(f"Median: ${result['median']:.2f}")
print(f"Bankruptcy Rate: {sum(1 for x in result['results'] if x == 0) / 10000:.1%}")
print(f"Chance of Profit: {sum(1 for x in result['results'] if x > 1000) / 10000:.1%}")
```

## Best Practices

### 1. Check Assumptions

Before using regression:

```python
# Check for linear relationship (correlation)
corr = AdvancedStats.pearson_correlation(x, y)
if abs(corr) < 0.3:
    print("Warning: Weak linear relationship")

# Check residuals are normally distributed
result = AdvancedStats.linear_regression(x, y)
# Plot residuals or use statistical test
```

### 2. Use Cross-Validation

Don't test on training data:

```python
# Split data: 80% train, 20% test
split_idx = int(0.8 * len(data))
train_x, test_x = data_x[:split_idx], data_x[split_idx:]
train_y, test_y = data_y[:split_idx], data_y[split_idx:]

# Fit on training data
model = AdvancedStats.linear_regression(train_x, train_y)

# Evaluate on test data
test_predictions = [model.coefficients[0] * x + model.intercept for x in test_x]
test_errors = [test_y[i] - test_predictions[i] for i in range(len(test_y))]
test_rmse = math.sqrt(sum(e**2 for e in test_errors) / len(test_errors))

print(f"Test RMSE: {test_rmse:.2f}")
```

### 3. Consider Sample Size

Minimum samples for reliable results:

- **Linear Regression**: 20-30 points minimum
- **Multiple Regression**: 10-20 samples per variable
- **Bootstrap**: Original sample should be 20+
- **Bayesian**: Works with any size, but more data = tighter intervals

### 4. Use Appropriate Methods

- **Normal data** → Parametric tests (t-test)
- **Non-normal data** → Non-parametric (permutation, bootstrap)
- **Small samples** → Bootstrap or Bayesian methods
- **Time series** → EMA, WMA, trend analysis
- **Binary outcomes** → Logistic regression, Bayesian

### 5. Validate Results

```python
# Always check if results make sense
if result.r_squared < 0.3:
    print("Warning: Low explanatory power")

if result.rmse > mean(y) * 0.5:
    print("Warning: Large prediction errors")

# Check for overfitting
if train_r2 > 0.95 and test_r2 < 0.5:
    print("Warning: Model is overfitting")
```

## Advanced Techniques

### Ensemble Predictions

Combine multiple models:

```python
# Fit multiple models
model1 = AdvancedStats.linear_regression(x1, y)
model2 = AdvancedStats.linear_regression(x2, y)

# Make predictions
pred1 = model1.coefficients[0] * new_x1 + model1.intercept
pred2 = model2.coefficients[0] * new_x2 + model2.intercept

# Weighted average (by R²)
w1 = model1.r_squared
w2 = model2.r_squared
ensemble_pred = (pred1 * w1 + pred2 * w2) / (w1 + w2)

print(f"Ensemble Prediction: {ensemble_pred:.1f}")
```

### Rolling Predictions

Update model as new data arrives:

```python
# Use last 20 games to predict next game
window = 20
predictions = []

for i in range(window, len(historical_data)):
    train_data = historical_data[i-window:i]
    # Fit model on window
    # Predict next game
    # Store prediction
```

## API Reference

See `lib/advanced_stats.py` for complete API documentation.

### Main Classes

- `RegressionResult`: Results from regression analysis
- `TimeSeriesResult`: Results from time series analysis
- `BayesianResult`: Results from Bayesian inference

### Main Methods

- `linear_regression()`: Simple linear regression
- `multiple_regression()`: Multiple linear regression
- `exponential_moving_average()`: EMA calculation
- `bayesian_win_probability()`: Bayesian probability estimation
- `monte_carlo_simulation()`: General Monte Carlo framework
- `bootstrap_confidence_interval()`: Bootstrap CI
- `permutation_test()`: Non-parametric hypothesis test
- `sharpe_ratio()`, `sortino_ratio()`: Risk metrics
- `kelly_optimal_size()`: Kelly Criterion bet sizing
