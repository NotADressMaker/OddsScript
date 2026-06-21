#!/usr/bin/env python3
"""
Quick Start Examples for VigScript

Simple examples using the simplified API.
"""

import sys
import os
# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# ========================================
# Import the simplified API
# ========================================
from lib.simple_api import SBL, Bet, Compare

print("VigScript - Quick Start Examples")
print("=" * 60)
print()

# ========================================
# Example 1: Basic Kelly Criterion
# ========================================
print("EXAMPLE 1: Kelly Criterion")
print("-" * 60)

# You think a team has 55% chance to win at 2.0 odds
kelly_size = SBL.kelly(win_prob=0.55, odds=2.0)

print(f"Win Probability: 55%")
print(f"Odds: 2.0")
print(f"Full Kelly: {kelly_size*100:.1f}% of bankroll")
print(f"Half Kelly: {kelly_size*0.5*100:.1f}% of bankroll (recommended)")
print(f"On $1000 bankroll: ${kelly_size*0.5*1000:.2f}")
print()

# ========================================
# Example 2: Calculate Edge and EV
# ========================================
print("EXAMPLE 2: Edge and Expected Value")
print("-" * 60)

edge_pct = SBL.edge(win_prob=0.58, odds=2.1)
ev_dollars = SBL.ev(win_prob=0.58, odds=2.1, bet_amount=100)

print(f"Your Prediction: 58%")
print(f"Offered Odds: 2.1")
print(f"Edge: {edge_pct:.2f}%")
print(f"EV on $100 bet: ${ev_dollars:.2f}")
print()

# ========================================
# Example 3: Odds Conversion
# ========================================
print("EXAMPLE 3: Odds Conversion")
print("-" * 60)

american_odds = -110
decimal = SBL.american_to_decimal(american_odds)
implied = SBL.implied_prob(decimal)

print(f"American Odds: {american_odds}")
print(f"Decimal Odds: {decimal:.3f}")
print(f"Implied Probability: {implied*100:.2f}%")
print()

# ========================================
# Example 4: Fluent Bet Analysis
# ========================================
print("EXAMPLE 4: Fluent Bet Analysis")
print("-" * 60)

bet = (Bet(100)
       .named("Lakers vs Celtics")
       .at_odds(2.1)
       .with_probability(0.58)
       .from_bankroll(1000))

bet.print_summary()

# ========================================
# Example 5: Compare Multiple Bets
# ========================================
print("EXAMPLE 5: Compare Multiple Bets")
print("-" * 60)

comparison = Compare(bankroll=1000)
comparison.add("Bet A", prob=0.58, odds=2.1)
comparison.add("Bet B", prob=0.52, odds=2.3)
comparison.add("Bet C", prob=0.48, odds=2.5)
comparison.print_comparison()

# ========================================
# Example 6: Bayesian Inference
# ========================================
print("EXAMPLE 6: Bayesian Win Probability")
print("-" * 60)

# Team has 12 wins and 5 losses
result = SBL.bayes(wins=12, losses=5)

print(f"Record: 12-5")
print(f"Raw Win %: {12/(12+5)*100:.1f}%")
print(f"Bayesian Win %: {result['mean_probability']*100:.1f}%")
print(f"95% Confidence: [{result['ci_lower']*100:.1f}%, {result['ci_upper']*100:.1f}%]")
print()

# ========================================
# Example 7: Quick Decision
# ========================================
print("EXAMPLE 7: Quick Bet Decision")
print("-" * 60)

should_bet = SBL.should_bet(win_prob=0.58, odds=2.1, min_edge=5)
print(f"Win Prob: 58%, Odds: 2.1")
print(f"Should bet (5% min edge)? {'YES' if should_bet else 'NO'}")
print()

# ========================================
# Example 8: Parlay Calculation
# ========================================
print("EXAMPLE 8: Parlay Analysis")
print("-" * 60)

# Three-leg parlay
individual_odds = [2.0, 1.5, 1.8]
individual_probs = [0.5, 0.65, 0.55]

parlay_odds = SBL.parlay_odds(individual_odds)
parlay_prob = SBL.parlay_probability(individual_probs)

print(f"Individual Odds: {individual_odds}")
print(f"Parlay Odds: {parlay_odds:.2f}")
print(f"Parlay Win Probability: {parlay_prob*100:.1f}%")
print(f"Parlay EV: {SBL.ev(parlay_prob, parlay_odds, 100):.2f}")
print()

# ========================================
# Example 9: ROI Calculation
# ========================================
print("EXAMPLE 9: Calculate ROI")
print("-" * 60)

total_wagered = 2500
total_won = 2700
roi = SBL.roi(total_wagered, total_won)

print(f"Total Wagered: ${total_wagered}")
print(f"Total Won: ${total_won}")
print(f"Profit: ${total_won - total_wagered}")
print(f"ROI: {roi:.2f}%")
print()

# ========================================
# Example 10: Remove Vig
# ========================================
print("EXAMPLE 10: Remove Vig to Find True Odds")
print("-" * 60)

# Sportsbook offers 1.91 on both sides
prob1, prob2 = SBL.remove_vig(1.91, 1.91)

print(f"Sportsbook Odds: 1.91 / 1.91")
print(f"Implied Total: {SBL.implied_prob(1.91)*2*100:.1f}% (vig)")
print(f"True Probabilities: {prob1*100:.1f}% / {prob2*100:.1f}%")
print()

# ========================================
# Example 11: CLV (Closing Line Value)
# ========================================
print("EXAMPLE 11: Closing Line Value")
print("-" * 60)

bet_odds = 2.1
closing_odds = 1.95
clv = SBL.clv(bet_odds, closing_odds)

print(f"Your Bet Odds: {bet_odds}")
print(f"Closing Odds: {closing_odds}")
print(f"CLV: {clv:.2f}%")
print(f"Result: {'Beat the closing line!' if clv > 0 else 'Lost to closing line'}")
print()

# ========================================
# Example 12: Units Conversion
# ========================================
print("EXAMPLE 12: Units to Dollars")
print("-" * 60)

unit_size = 50
units_bet = 2.5

dollars = SBL.units_to_dollars(units_bet, unit_size)
print(f"Unit Size: ${unit_size}")
print(f"Betting 2.5 units = ${dollars}")
print()

print("=" * 60)
print("All examples complete!")
print()
print("Next steps:")
print("  - Try modifying these examples")
print("  - Check out docs/simple_api_guide.md for more")
print("  - Import with: from lib.simple_api import SBL, Bet, Compare")
