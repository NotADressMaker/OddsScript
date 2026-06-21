# Horse Racing Analytics Guide

Comprehensive guide to using the horse racing analytics library for advanced betting analysis.

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Speed Rating Models](#speed-rating-models)
4. [Post Position Analysis](#post-position-analysis)
5. [Exotic Bet Calculators](#exotic-bet-calculators)
6. [Distance & Surface Models](#distance--surface-models)
7. [Complete Race Analysis](#complete-race-analysis)
8. [Advanced Examples](#advanced-examples)

## Overview

The horse racing analytics library provides professional-grade tools for:

- **Speed Ratings**: Beyer-style speed figures with track adjustments
- **Post Position Bias**: Statistical edge analysis by post position
- **Exotic Bets**: Probability and EV calculations for exactas, trifectas, superfectas
- **Specialization Analysis**: Distance and surface suitability models
- **Jockey/Trainer Stats**: Performance tracking and ROI calculations
- **Complete Race Analysis**: Integrated analysis with betting recommendations

## Quick Start

### Installation

```bash
# The library is ready to use directly
python3 lib/horse_racing_analytics.py --help
```

### Basic Usage

```bash
# Analyze a complete race from JSON file
python3 lib/horse_racing_analytics.py analyze-race --race-file race_data.json

# Calculate speed rating for a performance
python3 lib/horse_racing_analytics.py speed-rating \
  --final-time 96.5 \
  --distance 8.0 \
  --surface dirt \
  --condition fast

# Analyze post position bias
python3 lib/horse_racing_analytics.py post-bias \
  --post 3 \
  --horses 10 \
  --distance 6.0

# Calculate exacta expected value
python3 lib/horse_racing_analytics.py exacta \
  --horse1-odds 300 \
  --horse2-odds 500 \
  --horse1-prob 0.30 \
  --horse2-prob 0.25 \
  --bet 2.0
```

## Speed Rating Models

### Calculating Speed Figures

Speed figures adjust raw race times for track conditions, surface, and distance.

#### Command Line

```bash
# Fast dirt track performance
python3 lib/horse_racing_analytics.py speed-rating \
  --final-time 96.0 \
  --distance 8.0 \
  --surface dirt \
  --condition fast \
  --par-time 96.5

# Output:
# Speed Figure: 102
# Above par performance
```

#### Python API

```python
from horse_racing_analytics import SpeedRatingModel, TrackSurface, TrackCondition

# Calculate speed figure
speed_fig = SpeedRatingModel.calculate_speed_figure(
    final_time=96.0,         # Race time in seconds
    distance_furlongs=8.0,   # 1 mile = 8 furlongs
    track_surface=TrackSurface.DIRT,
    track_condition=TrackCondition.FAST,
    track_variant=0,         # Daily track speed adjustment
    par_time=96.5           # Expected time for this class
)

print(f"Speed Figure: {speed_fig}")
```

### Analyzing Form Trends

```python
from horse_racing_analytics import SpeedRatingModel

# Recent speed figures (most recent first)
recent_figures = [105, 103, 100, 98, 95]

# Calculate average of last 3 races
avg_speed = SpeedRatingModel.calculate_average_speed_figure(
    recent_figures,
    num_races=3
)
print(f"Average Speed Figure: {avg_speed}")  # 102.67

# Determine form trend
trend = SpeedRatingModel.calculate_form_trend(recent_figures)
print(f"Form Trend: {trend}")  # "improving"
```

### Track Surface Adjustments

Different surfaces affect speed ratings:

- **Dirt**: No adjustment (base)
- **Turf**: -2 points (typically slower)
- **Synthetic**: -1 point

### Track Condition Adjustments

Weather and maintenance affect track speed:

- **Fast/Firm**: No adjustment (best conditions)
- **Good**: -2 points
- **Yielding**: -3 points
- **Muddy**: -4 points
- **Sloppy**: -5 points
- **Soft**: -4 points
- **Heavy**: -6 points

## Post Position Analysis

### Post Position Bias

Inside posts have advantages in sprint races on oval tracks.

#### Command Line

```bash
# Analyze post 3 in a 10-horse sprint
python3 lib/horse_racing_analytics.py post-bias \
  --post 3 \
  --horses 10 \
  --distance 6.0

# Output:
# Post Position: 3
# Bias Multiplier: 1.15
# Advantage: +15.0%
# Optimal Post Range: 1-4
```

#### Python API

```python
from horse_racing_analytics import PostPositionAnalysis

# Calculate bias for inside post in sprint
bias = PostPositionAnalysis.calculate_post_bias(
    post_position=2,      # Rail is 1
    num_horses=10,
    distance_furlongs=6.0,  # Sprint
    track_type="oval"
)

print(f"Bias Multiplier: {bias}")  # 1.15 (15% advantage)

# Find optimal post positions
min_post, max_post = PostPositionAnalysis.get_optimal_post_range(
    distance_furlongs=6.0,
    num_horses=10
)

print(f"Optimal Posts: {min_post}-{max_post}")  # 1-4
```

### Post Position by Distance

**Sprint Races (≤7 furlongs):**
- Posts 1-3: +15% advantage
- Posts 4-7: Neutral
- Posts 8+: -15% disadvantage

**Route Races (>9 furlongs):**
- Posts 1-2: +5% advantage
- Posts 3-8: Neutral
- Posts 9+: -5% disadvantage

## Exotic Bet Calculators

### Exacta Analysis

#### Command Line

```bash
# Calculate exacta EV: Horse A to win, Horse B to place
python3 lib/horse_racing_analytics.py exacta \
  --horse1-odds 300 \
  --horse2-odds 500 \
  --horse1-prob 0.30 \
  --horse2-prob 0.25 \
  --bet 2.0

# Output:
# Exacta Bet Analysis
# Probability: 7.50%
# Estimated Payout: $16.80
# Expected Value: -$0.74
# ROI: -37.0%
# ✗ NEGATIVE EXPECTED VALUE - Avoid
```

#### Python API

```python
from horse_racing_analytics import ExoticBetCalculator

# Calculate exacta expected value
result = ExoticBetCalculator.calculate_exacta_expected_value(
    horse1_odds=300,         # Horse 1 American odds
    horse2_odds=500,         # Horse 2 American odds
    horse1_true_prob=0.30,   # Your estimated win probability
    horse2_true_prob=0.25,   # Your estimated place probability
    bet_amount=2.0
)

print(f"Probability: {result['probability']*100:.2f}%")
print(f"Payout: ${result['payout']:.2f}")
print(f"Expected Value: ${result['expected_value']:.2f}")
print(f"ROI: {result['roi']:.1f}%")

if result['expected_value'] > 0:
    print("✓ POSITIVE EXPECTED VALUE - Consider betting")
```

### Trifecta and Superfecta

```python
from horse_racing_analytics import ExoticBetCalculator

# Trifecta probability (1-2-3 in order)
tri_prob = ExoticBetCalculator.calculate_trifecta_probability(
    horse1_prob=0.30,  # Win probability
    horse2_prob=0.25,  # Place probability
    horse3_prob=0.20   # Show probability
)

print(f"Trifecta Probability: {tri_prob*100:.2f}%")  # 1.50%

# Superfecta probability (1-2-3-4 in order)
super_prob = ExoticBetCalculator.calculate_superfecta_probability(
    horse1_prob=0.30,
    horse2_prob=0.25,
    horse3_prob=0.20,
    horse4_prob=0.15
)

print(f"Superfecta Probability: {super_prob*100:.3f}%")  # 0.225%
```

## Distance & Surface Models

### Distance Suitability

```python
from horse_racing_analytics import Horse, DistanceSurfaceModel

# Create horse with distance statistics
horse = Horse(
    name="Speed Demon",
    odds=300,
    post_position=3,
    jockey="J. Smith",
    trainer="T. Jones",
    recent_speed_figures=[105, 103, 100],
    best_speed_figure=105,
    days_since_last_race=14,
    career_starts=20,
    career_wins=6,
    career_places=4,
    career_shows=3,
    distance_starts=8,     # 8 races at this distance
    distance_wins=5        # 5 wins at this distance (62.5%)
)

# Calculate suitability for 8-furlong race
suitability = DistanceSurfaceModel.calculate_distance_suitability(
    horse,
    race_distance_furlongs=8.0
)

print(f"Distance Suitability: {suitability*100:.1f}%")  # ~55%
```

### Surface Preferences

```python
from horse_racing_analytics import TrackSurface

# Horse with turf statistics
horse.surface_starts = 12
horse.surface_wins = 6  # 50% on turf

surface_suit = DistanceSurfaceModel.calculate_surface_suitability(
    horse,
    race_surface=TrackSurface.TURF
)

print(f"Turf Suitability: {surface_suit*100:.1f}%")
```

### Specialist Identification

```python
specialist_type = DistanceSurfaceModel.identify_specialist_type(horse)
print(f"Specialist Type: {specialist_type}")
# Options: "distance_specialist", "surface_specialist", "versatile"
```

## Complete Race Analysis

### Race Data Format

Create a JSON file with race information:

```json
{
  "distance_furlongs": 8.0,
  "surface": "dirt",
  "horses": [
    {
      "name": "Speed Demon",
      "odds": 200,
      "post_position": 3,
      "jockey": "J. Velazquez",
      "trainer": "T. Pletcher",
      "recent_speed_figures": [108, 105, 103],
      "best_speed_figure": 108,
      "days_since_last_race": 21,
      "career_starts": 12,
      "career_wins": 5,
      "career_places": 3,
      "career_shows": 2,
      "distance_starts": 4,
      "distance_wins": 3,
      "surface_starts": 10,
      "surface_wins": 5
    },
    {
      "name": "Steady Runner",
      "odds": 400,
      "post_position": 5,
      "jockey": "I. Ortiz",
      "trainer": "C. McGaughey",
      "recent_speed_figures": [95, 96, 94],
      "best_speed_figure": 97,
      "days_since_last_race": 14,
      "career_starts": 20,
      "career_wins": 6,
      "career_places": 5,
      "career_shows": 4,
      "distance_starts": 8,
      "distance_wins": 3,
      "surface_starts": 18,
      "surface_wins": 6
    }
  ]
}
```

### Command Line Analysis

```bash
python3 lib/horse_racing_analytics.py analyze-race --race-file example_race.json
```

Output:
```
Race Analysis
================================================================================
Distance: 8.0 furlongs (middle)
Surface: dirt
Field Size: 2 horses

Horse Rankings:
--------------------------------------------------------------------------------

1. Speed Demon
   Odds: +200 (Market: 33.3%)
   Adjusted Probability: 45.2%
   Speed: Avg 105, Best 108
   Form: improving
   Post: 3 (bias: 1.00)
   Distance Suit: 68%
   Surface Suit: 56%

2. Steady Runner
   Odds: +400 (Market: 20.0%)
   Adjusted Probability: 22.1%
   Speed: Avg 95, Best 97
   Form: consistent
   Post: 5 (bias: 1.00)
   Distance Suit: 35%
   Surface Suit: 34%


Betting Opportunities
================================================================================

STRONG BET: Speed Demon
   Odds: +200
   Market Prob: 33.3%
   True Prob: 45.2%
   Edge: 11.9% (35.7% of market)
```

### Python API

```python
from horse_racing_analytics import (
    Horse, HorseRacingAnalyzer, TrackSurface
)

# Create horses
horses = [
    Horse(
        name="Speed Demon",
        odds=200,
        post_position=3,
        jockey="J. Velazquez",
        trainer="T. Pletcher",
        recent_speed_figures=[108, 105, 103],
        best_speed_figure=108,
        days_since_last_race=21,
        career_starts=12,
        career_wins=5,
        career_places=3,
        career_shows=2,
        distance_starts=4,
        distance_wins=3,
        surface_starts=10,
        surface_wins=5
    )
    # ... more horses
]

# Analyze race
analyzer = HorseRacingAnalyzer()
analyses = analyzer.analyze_race(
    horses,
    race_distance_furlongs=8.0,
    race_surface=TrackSurface.DIRT
)

# Display rankings
for i, analysis in enumerate(analyses, 1):
    print(f"{i}. {analysis['horse_name']}")
    print(f"   Adjusted Prob: {analysis['adjusted_probability']*100:.1f}%")
    print(f"   Speed: {analysis['average_speed_figure']:.0f}")
    print(f"   Form: {analysis['form_trend']}")

# Find betting opportunities
opportunities = analyzer.find_betting_opportunities(
    analyses,
    min_edge=0.05  # Require 5% edge minimum
)

for opp in opportunities:
    print(f"\n{opp['recommendation']}: {opp['horse_name']}")
    print(f"Edge: {opp['edge']*100:.1f}%")
```

## Advanced Examples

### Jockey and Trainer Statistics

```python
from horse_racing_analytics import JockeyStats, TrainerStats

# Create jockey statistics
jockey = JockeyStats(
    name="J. Velazquez",
    starts=1000,
    wins=250,
    places=200,
    shows=150,
    earnings=5000000
)

print(f"Win Rate: {jockey.win_percentage():.1f}%")  # 25.0%

# Calculate ROI (assuming $2 bets)
roi = jockey.roi(total_bet=2000)
print(f"ROI: {roi:.1f}%")  # 150.0%

# Create trainer statistics
trainer = TrainerStats(
    name="T. Pletcher",
    starts=2000,
    wins=500,
    places=400,
    shows=300,
    earnings=10000000
)

print(f"Trainer Win Rate: {trainer.win_percentage():.1f}%")  # 25.0%
```

### Combining with Multi-Outcome Kelly

After identifying value bets, use Kelly Criterion for optimal stakes:

```python
from sportsbetlang.common.kelly import KellyCriterion

# From race analysis, you identified these opportunities
outcomes = [
    {
        'name': 'Speed Demon',
        'odds': 200,  # +200
        'prob': 0.452  # Adjusted probability
    },
    {
        'name': 'Steady Runner',
        'odds': 400,  # +400
        'prob': 0.221  # Adjusted probability
    }
]

# Calculate Kelly stakes
kelly_result = KellyCriterion.multi_outcome(
    outcomes,
    bankroll=1000,
    kelly_fraction=0.25  # Quarter Kelly for safety
)

print(f"Recommended Stakes:")
for outcome in kelly_result['outcomes']:
    if outcome['kelly_pct'] > 0:
        print(f"  {outcome['name']}: ${outcome['stake']:.2f}")
```

### Integrating with Dutch Betting

Use Dutch betting to guarantee profit across multiple horses:

```bash
# After race analysis, Dutch bet on top 3 horses
python3 tools/dutch_betting.py equal \
  -s 100 \
  --outcome "Speed Demon" +200 \
  --outcome "Steady Runner" +400 \
  --outcome "Late Closer" +800

# Output shows how to split $100 for equal profit
```

### Historical Performance Tracking

```python
from horse_racing_analytics import Horse

# Track a horse's progression
horse = Horse(
    name="Rising Star",
    odds=500,
    post_position=4,
    jockey="M. Smith",
    trainer="B. Baffert",
    recent_speed_figures=[95, 92, 88, 85, 82],  # Improving!
    best_speed_figure=95,
    days_since_last_race=14,
    career_starts=8,
    career_wins=2,
    career_places=2,
    career_shows=1
)

from horse_racing_analytics import SpeedRatingModel

# Analyze form
trend = SpeedRatingModel.calculate_form_trend(horse.recent_speed_figures)
avg_speed = SpeedRatingModel.calculate_average_speed_figure(
    horse.recent_speed_figures,
    num_races=3
)

print(f"Form Trend: {trend}")  # "improving"
print(f"Recent Average: {avg_speed:.0f}")  # 92
print(f"Best Figure: {horse.best_speed_figure}")  # 95

# This horse is improving - possible value bet
```

### Multi-Race Portfolio Optimization

```python
# Analyze multiple races and optimize total bankroll allocation
races = []

# Race 1
race1_horses = [...]  # horses for race 1
race1_analysis = analyzer.analyze_race(
    race1_horses,
    8.0,
    TrackSurface.DIRT
)
race1_opps = analyzer.find_betting_opportunities(race1_analysis)
races.append(race1_opps)

# Race 2
race2_horses = [...]
race2_analysis = analyzer.analyze_race(
    race2_horses,
    6.0,
    TrackSurface.TURF
)
race2_opps = analyzer.find_betting_opportunities(race2_analysis)
races.append(race2_opps)

# Combine all opportunities
all_outcomes = []
for race_opps in races:
    for opp in race_opps:
        all_outcomes.append({
            'name': opp['horse_name'],
            'odds': opp['odds'],
            'prob': opp['true_probability']
        })

# Calculate Kelly across all races
kelly_result = KellyCriterion.multi_outcome(
    all_outcomes,
    bankroll=1000,
    kelly_fraction=0.25
)
```

## Model Interpretation

### Speed Figures
- **100+**: Above par, competitive horse
- **90-100**: Near par, average competitor
- **<90**: Below par, weak contender

### Post Position Bias
- **>1.10**: Significant advantage
- **0.95-1.05**: Neutral position
- **<0.90**: Significant disadvantage

### Edge Requirements
- **>15%**: Strong bet, high confidence
- **10-15%**: Good bet
- **5-10%**: Marginal bet, smaller stakes
- **<5%**: Avoid, insufficient edge

## Best Practices

1. **Use Fractional Kelly**: Always use 1/4 or 1/2 Kelly to reduce variance
2. **Require Minimum Edge**: Set min_edge to at least 5% to account for model error
3. **Track Your Results**: Use bet tracker to validate model performance
4. **Update Probabilities**: Adjust based on late scratches, track conditions
5. **Consider Sample Size**: Weight distance/surface stats by number of starts
6. **Watch Form Trends**: Improving horses often have value
7. **Post Position Matters**: Especially in sprints with large fields
8. **Combine Models**: Use speed, post, distance, and surface together

## Integration with Other Tools

The horse racing library integrates seamlessly with other VigScript tools:

- **Multi-Outcome Kelly** (`lib/multi_outcome_kelly.py`): Optimal bet sizing
- **Dutch Betting** (`tools/dutch_betting.py`): Guaranteed profit strategies
- **Bet Tracker** (`tools/bet_tracker.py`): Performance tracking
- **Variance Calculator** (`lib/variance_calc.py`): Risk management

## Testing

Run the comprehensive test suite:

```bash
python3 tests/test_horse_racing_analytics.py
```

Tests cover:
- Speed rating calculations
- Post position bias
- Exotic bet probabilities
- Distance/surface suitability
- Complete race analysis
- Integration workflows

## Support

For issues, questions, or feature requests:
- GitHub Issues: https://github.com/NotADressMaker/SportsBetLang
- Documentation: `/docs/horse_racing_guide.md`
