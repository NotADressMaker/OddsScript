#!/usr/bin/env python3
"""
SportsBetLang - Quick Start Example for Replit
================================================

This example shows the easiest ways to use SportsBetLang on Replit.
Just click Run to see it in action!

To get started on Replit:
1. Install: pip install git+https://github.com/NotADressMaker/SportsBetLang.git
2. Run this file!
"""

print("=" * 70)
print("SPORTSBETLANG - QUICK START ON REPLIT")
print("=" * 70)
print()

# ============================================================================
# EXAMPLE 1: Kelly Criterion and EV Calculations
# ============================================================================
print("📊 EXAMPLE 1: Bet Analysis")
print("-" * 70)

from lib import SBL

# Calculate Kelly Criterion
win_prob = 0.55
odds = 2.0

kelly = SBL.kelly(win_prob, odds)
ev = SBL.ev(win_prob, odds, bet_amount=100)
edge = SBL.edge(win_prob, odds)

print(f"Win Probability: {win_prob:.1%}")
print(f"Odds: {odds}")
print(f"Kelly Criterion: {kelly:.2%} of bankroll")
print(f"Expected Value: ${ev:.2f} per $100 bet")
print(f"Edge: {edge:.2%}")
print()

# ============================================================================
# EXAMPLE 2: Detailed Bet Analysis
# ============================================================================
print("💰 EXAMPLE 2: Full Bet Analysis")
print("-" * 70)

from lib import Bet

bet = (Bet(100)
       .named("Lakers vs Celtics")
       .at_odds(2.1)
       .with_probability(0.58)
       .from_bankroll(1000))

bet.print_summary()
print()

# ============================================================================
# EXAMPLE 3: Compare Multiple Bets
# ============================================================================
print("🏆 EXAMPLE 3: Compare Multiple Bets")
print("-" * 70)

from lib import Compare

comp = Compare(bankroll=1000)
comp.add("Lakers ML", prob=0.58, odds=2.1)
comp.add("Chiefs ML", prob=0.52, odds=2.3)
comp.add("Warriors ML", prob=0.61, odds=1.9)

comp.print_comparison()
print()

# ============================================================================
# EXAMPLE 4: Quick NBA Prediction (No Training!)
# ============================================================================
print("🏀 EXAMPLE 4: Quick NBA Prediction")
print("-" * 70)

from lib import quick_nba_prediction

prob = quick_nba_prediction(
    team_off_rtg=115.0,
    team_def_rtg=107.5,
    opp_off_rtg=110.2,
    opp_def_rtg=109.8,
    home=True,
    rest_team=2,
    rest_opp=1
)

print(f"Lakers (Home) vs Celtics")
print(f"  Team Off Rating: 115.0, Def Rating: 107.5")
print(f"  Opp Off Rating: 110.2, Def Rating: 109.8")
print(f"  Rest: Lakers 2 days, Celtics 1 day")
print(f"\n  Win Probability: {prob:.1%}")
print()

# ============================================================================
# EXAMPLE 5: Quick NFL Prediction (With Weather!)
# ============================================================================
print("🏈 EXAMPLE 5: Quick NFL Prediction (With Weather)")
print("-" * 70)

from lib import quick_nfl_prediction

nfl_prob = quick_nfl_prediction(
    team_dvoa=15.0,
    opp_dvoa=5.0,
    home=True,
    temperature=28,  # Cold playoff game
    wind_speed=20    # Very windy
)

print(f"Chiefs (Home) vs Bills")
print(f"  Chiefs DVOA: 15.0, Bills DVOA: 5.0")
print(f"  Weather: 28°F, Wind 20mph (tough conditions)")
print(f"\n  Win Probability: {nfl_prob:.1%}")
print()

# ============================================================================
# EXAMPLE 6: Build ML Model (Easy Way!)
# ============================================================================
print("🤖 EXAMPLE 6: Build ML Model")
print("-" * 70)

from lib import EasySportModel
import random

print("Creating sample NBA training data...")
random.seed(42)
games = []

for i in range(100):  # Using 100 games for quick demo
    game = {
        'team_offensive_rating': random.uniform(105, 118),
        'team_defensive_rating': random.uniform(105, 118),
        'opponent_offensive_rating': random.uniform(105, 118),
        'opponent_defensive_rating': random.uniform(105, 118),
        'home_court': random.choice([0, 1]),
        'rest_days_team': random.randint(0, 4),
        'rest_days_opponent': random.randint(0, 4),
        'pace': random.uniform(95, 105),
    }

    # Simulate realistic outcomes
    team_net = game['team_offensive_rating'] - game['team_defensive_rating']
    opp_net = game['opponent_offensive_rating'] - game['opponent_defensive_rating']
    diff = team_net - opp_net + (3 if game['home_court'] else 0)
    win_prob = 1 / (1 + 10 ** (-diff / 15))
    game['result'] = 1 if random.random() < win_prob else 0

    games.append(game)

print(f"✓ Generated {len(games)} training games")
print("\nTraining NBA Game Winner model...")

model = EasySportModel('nba', 'game_winner')
model.fit(games)

print("✓ Model trained!")

# Make predictions
test_game = {
    'team_offensive_rating': 116.0,
    'team_defensive_rating': 108.0,
    'opponent_offensive_rating': 111.0,
    'opponent_defensive_rating': 110.0,
    'home_court': 1,
    'rest_days_team': 2,
    'rest_days_opponent': 2,
    'pace': 101.0
}

prediction = model.predict(test_game)
probability = model.predict_proba(test_game)

print(f"\nPredicting: Strong Home Team vs Good Away Team")
print(f"  Prediction: {'WIN' if prediction == 1 else 'LOSS'}")
print(f"  Confidence: {probability:.1%}")
print()

# ============================================================================
# EXAMPLE 7: Advanced Statistics
# ============================================================================
print("📈 EXAMPLE 7: Advanced Statistics")
print("-" * 70)

from lib import AdvancedStats

# Bayesian inference
result = AdvancedStats.bayesian_win_probability(wins=12, losses=5)
print(f"Team Record: 12-5")
print(f"  Bayesian Win Probability: {result['probability']:.1%}")
print(f"  95% Credible Interval: {result['ci_lower']:.1%} - {result['ci_upper']:.1%}")

# Monte Carlo simulation
print("\nMonte Carlo Simulation: 16-game season with 60% win rate")

def simulate_season():
    return sum(1 for _ in range(16) if random.random() < 0.6)

mc_result = AdvancedStats.monte_carlo_simulation(simulate_season, n_simulations=1000)
print(f"  Expected wins: {mc_result['mean']:.1f}")
print(f"  5th percentile: {mc_result['percentile_5']:.0f} wins")
print(f"  95th percentile: {mc_result['percentile_95']:.0f} wins")
print()

# ============================================================================
# SUMMARY
# ============================================================================
print("=" * 70)
print("✅ ALL EXAMPLES COMPLETE!")
print("=" * 70)
print()
print("What you just saw:")
print("  1. Kelly Criterion and Expected Value calculations")
print("  2. Detailed bet analysis with recommendations")
print("  3. Compare multiple bets side-by-side")
print("  4. Quick NBA predictions (no training needed!)")
print("  5. Quick NFL predictions with weather factors")
print("  6. Build ML models with dictionary data")
print("  7. Advanced statistical analysis")
print()
print("Next steps:")
print("  • Modify the examples above with your own data")
print("  • Check out REPLIT_GUIDE.md for more examples")
print("  • Read docs/ folder for detailed guides")
print("  • See examples/ folder for more code")
print()
print("📚 Documentation:")
print("  • REPLIT_GUIDE.md - Complete Replit guide")
print("  • DESKTOP_QUICKSTART.md - Desktop usage")
print("  • docs/easy_sport_models_guide.md - Simplified ML models")
print("  • docs/simple_api_guide.md - Bet calculations")
print()
print("Happy betting analysis! 🎉")
print("=" * 70)
