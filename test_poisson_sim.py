#!/usr/bin/env python3
"""
Quick test to verify Poisson simulation functions work correctly
"""

from lib.poisson_calculator import PoissonCalculator

print("Testing Poisson Simulation Functions")
print("=" * 50)

# Test 1: Simulate single event
print("\n1. Testing simulate_poisson_event:")
lambda_param = 1.5
event = PoissonCalculator.simulate_poisson_event(lambda_param, seed=42)
print(f"   Lambda: {lambda_param}, Simulated events: {event}")
assert isinstance(event, int), "Should return integer"
assert event >= 0, "Should return non-negative value"
print("   ✓ PASSED")

# Test 2: Simulate single match
print("\n2. Testing simulate_match:")
home_lambda = 1.8
away_lambda = 1.2
match = PoissonCalculator.simulate_match(home_lambda, away_lambda, seed=42)
print(f"   Home: {home_lambda}, Away: {away_lambda}")
print(f"   Result: {match['home_score']}-{match['away_score']} ({match['result']})")
assert 'home_score' in match, "Should have home_score"
assert 'away_score' in match, "Should have away_score"
assert 'result' in match, "Should have result"
assert 'total_score' in match, "Should have total_score"
assert match['result'] in ['home_win', 'away_win', 'draw'], "Valid result"
assert match['total_score'] == match['home_score'] + match['away_score'], "Total should match"
print("   ✓ PASSED")

# Test 3: Simulate multiple matches
print("\n3. Testing simulate_matches (Monte Carlo):")
num_sims = 1000
results = PoissonCalculator.simulate_matches(home_lambda, away_lambda, num_sims, seed=42)
print(f"   Simulations: {num_sims}")
print(f"   Home wins: {results['home_win_pct']*100:.1f}%")
print(f"   Away wins: {results['away_win_pct']*100:.1f}%")
print(f"   Draws: {results['draw_pct']*100:.1f}%")
print(f"   Avg total: {results['avg_total']:.2f}")

# Verify probabilities sum to 1
total_prob = results['home_win_pct'] + results['away_win_pct'] + results['draw_pct']
assert abs(total_prob - 1.0) < 0.001, "Probabilities should sum to 1"
assert results['num_simulations'] == num_sims, "Should track simulation count"
assert len(results['scores']) == num_sims, "Should have all scores"
assert len(results['total_scores']) == num_sims, "Should have all totals"
print("   ✓ PASSED")

# Test 4: Test betting strategy simulation
print("\n4. Testing simulate_betting_strategy:")
bet_results = PoissonCalculator.simulate_betting_strategy(
    home_lambda=1.8,
    away_lambda=1.2,
    bet_type='over',
    bet_target=2.5,
    odds=1.91,
    stake=10,
    num_simulations=1000,
    seed=42
)
print(f"   Bet: Over 2.5 @ 1.91 odds")
print(f"   Win rate: {bet_results['win_rate']*100:.1f}%")
print(f"   ROI: {bet_results['roi']:.2f}%")
print(f"   Total profit: ${bet_results['total_profit']:.2f}")
assert bet_results['wins'] + bet_results['losses'] == 1000, "All bets resolved"
assert 'std_dev' in bet_results, "Should calculate std dev"
print("   ✓ PASSED")

# Test 5: Test season simulation
print("\n5. Testing simulate_season:")
teams = {
    'Team A': 2.0,
    'Team B': 1.5,
    'Team C': 1.0
}
season = PoissonCalculator.simulate_season(teams, num_matches=10, seed=42)
print(f"   Teams: {len(teams)}")
print(f"   Matches: {season['num_matches']}")
assert len(season['matches']) == 10, "Should have 10 matches"
assert 'standings' in season, "Should have standings"
print("   Standings:")
for team, stats in list(season['standings'].items())[:3]:
    print(f"   {team}: {stats['pts']} pts ({stats['wins']}W {stats['draws']}D {stats['losses']}L)")
print("   ✓ PASSED")

# Test 6: Verify reproducibility with seed
print("\n6. Testing reproducibility with seed:")
match1 = PoissonCalculator.simulate_match(1.5, 1.5, seed=123)
match2 = PoissonCalculator.simulate_match(1.5, 1.5, seed=123)
assert match1['home_score'] == match2['home_score'], "Same seed should give same result"
assert match1['away_score'] == match2['away_score'], "Same seed should give same result"
print(f"   Both matches: {match1['home_score']}-{match1['away_score']}")
print("   ✓ PASSED")

print("\n" + "=" * 50)
print("All tests passed! ✓")
print("=" * 50)
