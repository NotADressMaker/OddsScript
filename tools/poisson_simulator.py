#!/usr/bin/env python3
"""
Poisson Distribution Simulation Tool

A comprehensive CLI tool for running Monte Carlo simulations using Poisson distribution
for sports betting analysis. Supports match simulations, betting strategy testing,
and season modeling.
"""

import argparse
import sys
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.poisson_calculator import PoissonCalculator


def format_percentage(value, decimals=2):
    """Format a decimal as percentage"""
    return f"{value * 100:.{decimals}f}%"


def format_currency(value, decimals=2):
    """Format value as currency"""
    return f"${value:.{decimals}f}"


def print_separator(char="=", length=70):
    """Print a separator line"""
    print(char * length)


def cmd_simulate_match(args):
    """Simulate a single match or multiple matches"""
    print_separator()
    print(f"POISSON MATCH SIMULATION")
    print_separator()
    print(f"\nTeam Configuration:")
    print(f"  Home Team: λ = {args.home_lambda:.2f} (expected goals/points)")
    print(f"  Away Team: λ = {args.away_lambda:.2f} (expected goals/points)")

    if args.num_simulations == 1:
        # Single match simulation
        print(f"\nSimulating single match...")
        result = PoissonCalculator.simulate_match(
            args.home_lambda,
            args.away_lambda,
            seed=args.seed
        )

        print(f"\nMatch Result:")
        print(f"  Final Score: {result['home_score']} - {result['away_score']}")
        print(f"  Total Goals: {result['total_score']}")
        print(f"  Outcome: {result['result'].replace('_', ' ').title()}")

    else:
        # Monte Carlo simulation
        print(f"\nRunning Monte Carlo simulation with {args.num_simulations:,} matches...")
        results = PoissonCalculator.simulate_matches(
            args.home_lambda,
            args.away_lambda,
            args.num_simulations,
            seed=args.seed
        )

        print(f"\nSimulation Results:")
        print(f"  Simulations: {results['num_simulations']:,}")
        print(f"\nOutcome Probabilities:")
        print(f"  Home Win: {format_percentage(results['home_win_pct'])} ({results['home_wins']:,} matches)")
        print(f"  Draw:     {format_percentage(results['draw_pct'])} ({results['draws']:,} matches)")
        print(f"  Away Win: {format_percentage(results['away_win_pct'])} ({results['away_wins']:,} matches)")
        print(f"\nScoring Statistics:")
        print(f"  Average Total Goals: {results['avg_total']:.2f}")

        # Calculate most common scores
        from collections import Counter
        score_counts = Counter(results['scores'])
        most_common = score_counts.most_common(10)

        print(f"\nMost Common Scores:")
        for i, ((home, away), count) in enumerate(most_common, 1):
            pct = (count / args.num_simulations) * 100
            print(f"  {i:2d}. {home}-{away}: {pct:.2f}% ({count:,} times)")

        # Total goals distribution
        total_counts = Counter(results['total_scores'])
        print(f"\nTotal Goals Distribution:")
        for goals in sorted(set(results['total_scores']))[:10]:
            count = total_counts[goals]
            pct = (count / args.num_simulations) * 100
            bar = "█" * int(pct)
            print(f"  {goals:2d} goals: {pct:5.1f}% {bar}")

        if args.output:
            # Save detailed results to JSON
            output_data = {
                'home_lambda': args.home_lambda,
                'away_lambda': args.away_lambda,
                'num_simulations': args.num_simulations,
                'results': results,
                'score_distribution': dict(score_counts)
            }
            with open(args.output, 'w') as f:
                json.dump(output_data, f, indent=2)
            print(f"\nDetailed results saved to: {args.output}")


def cmd_test_bet(args):
    """Test a betting strategy with simulations"""
    print_separator()
    print(f"BETTING STRATEGY SIMULATION")
    print_separator()
    print(f"\nMatch Configuration:")
    print(f"  Home Team: λ = {args.home_lambda:.2f}")
    print(f"  Away Team: λ = {args.away_lambda:.2f}")

    print(f"\nBet Configuration:")
    print(f"  Bet Type: {args.bet_type}")
    if args.bet_type in ['over', 'under']:
        print(f"  Line: {args.target}")
    print(f"  Odds: {args.odds:.2f} (decimal)")
    print(f"  Stake: {format_currency(args.stake)}")
    print(f"  Simulations: {args.num_simulations:,}")

    print(f"\nRunning simulations...")
    results = PoissonCalculator.simulate_betting_strategy(
        args.home_lambda,
        args.away_lambda,
        args.bet_type,
        args.target,
        args.odds,
        args.stake,
        args.num_simulations,
        seed=args.seed
    )

    print(f"\nBetting Results:")
    print_separator("-")
    print(f"  Winning Bets: {results['wins']:,}")
    print(f"  Losing Bets:  {results['losses']:,}")
    print(f"  Win Rate:     {format_percentage(results['win_rate'])}")

    print(f"\nFinancial Results:")
    print_separator("-")
    total_risked = args.stake * args.num_simulations
    print(f"  Total Risked:        {format_currency(total_risked)}")
    print(f"  Total Profit/Loss:   {format_currency(results['total_profit'])}")
    print(f"  Avg Profit Per Bet:  {format_currency(results['avg_profit_per_bet'])}")
    print(f"  ROI:                 {results['roi']:.2f}%")
    print(f"  Standard Deviation:  {format_currency(results['std_dev'])}")

    # Expected value analysis
    print(f"\nExpected Value Analysis:")
    print_separator("-")
    if results['roi'] > 0:
        print(f"  ✓ POSITIVE EV BET (+{results['roi']:.2f}% ROI)")
        print(f"  This bet has an edge and is profitable long-term.")
    elif results['roi'] == 0:
        print(f"  ⚠ BREAK-EVEN BET (0% ROI)")
        print(f"  This bet has no edge.")
    else:
        print(f"  ✗ NEGATIVE EV BET ({results['roi']:.2f}% ROI)")
        print(f"  This bet loses money long-term. Avoid.")

    # Confidence intervals (approximate)
    import math
    z_score = 1.96  # 95% confidence
    margin = z_score * results['std_dev'] / math.sqrt(args.num_simulations)
    lower_bound = results['avg_profit_per_bet'] - margin
    upper_bound = results['avg_profit_per_bet'] + margin

    print(f"\n95% Confidence Interval:")
    print(f"  {format_currency(lower_bound)} to {format_currency(upper_bound)} per bet")

    # Variance and risk
    print(f"\nRisk Assessment:")
    print_separator("-")
    win_amount = args.stake * (args.odds - 1)
    volatility_ratio = results['std_dev'] / args.stake
    print(f"  Win Amount:       {format_currency(win_amount)}")
    print(f"  Loss Amount:      {format_currency(args.stake)}")
    print(f"  Volatility Ratio: {volatility_ratio:.2f}x stake")

    if volatility_ratio < 1.0:
        risk_level = "LOW"
    elif volatility_ratio < 1.5:
        risk_level = "MODERATE"
    else:
        risk_level = "HIGH"
    print(f"  Risk Level:       {risk_level}")

    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nDetailed results saved to: {args.output}")


def cmd_simulate_season(args):
    """Simulate a season with multiple teams"""
    print_separator()
    print(f"SEASON SIMULATION")
    print_separator()

    # Parse teams
    teams = {}
    print(f"\nTeams:")
    for i, team_str in enumerate(args.teams, 1):
        name, lambda_str = team_str.rsplit(':', 1)
        teams[name] = float(lambda_str)
        print(f"  {i}. {name}: λ = {teams[name]:.2f}")

    print(f"\nSeason Configuration:")
    print(f"  Number of Matches: {args.num_matches}")
    print(f"  Home Advantage: +{args.home_advantage:.2f} goals")

    print(f"\nSimulating season...")
    results = PoissonCalculator.simulate_season(
        teams,
        args.num_matches,
        args.home_advantage,
        seed=args.seed
    )

    print(f"\nFinal Standings:")
    print_separator("-")
    print(f"{'Pos':<5} {'Team':<20} {'Pts':<5} {'W':<4} {'D':<4} {'L':<4} {'GF':<4} {'GA':<4} {'GD':<5}")
    print_separator("-")

    for pos, (team, stats) in enumerate(results['standings'].items(), 1):
        gd = stats['gf'] - stats['ga']
        gd_str = f"+{gd}" if gd > 0 else str(gd)
        print(f"{pos:<5} {team:<20} {stats['pts']:<5} {stats['wins']:<4} {stats['draws']:<4} "
              f"{stats['losses']:<4} {stats['gf']:<4} {stats['ga']:<4} {gd_str:<5}")

    print(f"\nRecent Matches:")
    print_separator("-")
    for i, match in enumerate(results['matches'][-10:], 1):
        result_str = f"{match['home_score']}-{match['away_score']}"
        print(f"  {i:2d}. {match['home']:20s} {result_str:^7s} {match['away']:20s}")

    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nDetailed results saved to: {args.output}")


def cmd_compare_scenarios(args):
    """Compare different betting scenarios"""
    print_separator()
    print(f"SCENARIO COMPARISON")
    print_separator()

    scenarios = [
        ("Strong Favorite", 2.5, 0.8),
        ("Moderate Favorite", 2.0, 1.3),
        ("Even Match", 1.5, 1.5),
        ("Underdog", 1.3, 2.0),
        ("High Scoring", 3.0, 2.8),
        ("Low Scoring", 0.8, 0.7),
    ]

    print(f"\nComparing {len(scenarios)} scenarios with {args.num_simulations:,} simulations each...")
    print(f"\nScenario Results:")
    print_separator("-")
    print(f"{'Scenario':<20} {'Home λ':<8} {'Away λ':<8} {'Home W%':<10} {'Draw%':<10} {'Away W%':<10} {'Avg Total':<10}")
    print_separator("-")

    for scenario_name, home_lambda, away_lambda in scenarios:
        results = PoissonCalculator.simulate_matches(
            home_lambda,
            away_lambda,
            args.num_simulations,
            seed=args.seed
        )

        print(f"{scenario_name:<20} {home_lambda:<8.2f} {away_lambda:<8.2f} "
              f"{format_percentage(results['home_win_pct'], 1):<10} "
              f"{format_percentage(results['draw_pct'], 1):<10} "
              f"{format_percentage(results['away_win_pct'], 1):<10} "
              f"{results['avg_total']:<10.2f}")


def main():
    parser = argparse.ArgumentParser(
        description="Poisson Distribution Simulation Tool for Sports Betting",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Simulate a single match
  %(prog)s match 1.8 1.2

  # Run 10,000 match simulations
  %(prog)s match 1.8 1.2 -n 10000

  # Test an Over 2.5 bet
  %(prog)s bet 1.8 1.2 over 2.5 -o 1.91 -s 10 -n 1000

  # Test a home win bet
  %(prog)s bet 1.8 1.2 home_win -o 2.10 -s 10 -n 1000

  # Simulate a season
  %(prog)s season -t "Liverpool:2.0" -t "Man City:2.2" -t "Arsenal:1.8" -m 50

  # Compare scenarios
  %(prog)s compare -n 5000
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Match simulation command
    match_parser = subparsers.add_parser('match', help='Simulate match(es)')
    match_parser.add_argument('home_lambda', type=float, help='Home team expected goals/points')
    match_parser.add_argument('away_lambda', type=float, help='Away team expected goals/points')
    match_parser.add_argument('-n', '--num-simulations', type=int, default=1,
                            help='Number of simulations (default: 1)')
    match_parser.add_argument('--seed', type=int, help='Random seed for reproducibility')
    match_parser.add_argument('-o', '--output', help='Save results to JSON file')
    match_parser.set_defaults(func=cmd_simulate_match)

    # Betting strategy test command
    bet_parser = subparsers.add_parser('bet', help='Test betting strategy')
    bet_parser.add_argument('home_lambda', type=float, help='Home team expected goals/points')
    bet_parser.add_argument('away_lambda', type=float, help='Away team expected goals/points')
    bet_parser.add_argument('bet_type', choices=['home_win', 'away_win', 'draw', 'over', 'under', 'btts'],
                           help='Type of bet')
    bet_parser.add_argument('target', type=float, nargs='?', default=0,
                           help='Target value (for over/under)')
    bet_parser.add_argument('-o', '--odds', type=float, required=True,
                           help='Decimal odds')
    bet_parser.add_argument('-s', '--stake', type=float, default=10,
                           help='Bet stake (default: 10)')
    bet_parser.add_argument('-n', '--num-simulations', type=int, default=1000,
                           help='Number of simulations (default: 1000)')
    bet_parser.add_argument('--seed', type=int, help='Random seed for reproducibility')
    bet_parser.add_argument('--output', help='Save results to JSON file')
    bet_parser.set_defaults(func=cmd_test_bet)

    # Season simulation command
    season_parser = subparsers.add_parser('season', help='Simulate a season')
    season_parser.add_argument('-t', '--teams', action='append', required=True,
                              help='Team in format "Name:Lambda" (can specify multiple)')
    season_parser.add_argument('-m', '--num-matches', type=int, default=38,
                              help='Number of matches to simulate (default: 38)')
    season_parser.add_argument('-a', '--home-advantage', type=float, default=0.3,
                              help='Home advantage bonus (default: 0.3)')
    season_parser.add_argument('--seed', type=int, help='Random seed for reproducibility')
    season_parser.add_argument('-o', '--output', help='Save results to JSON file')
    season_parser.set_defaults(func=cmd_simulate_season)

    # Compare scenarios command
    compare_parser = subparsers.add_parser('compare', help='Compare different scenarios')
    compare_parser.add_argument('-n', '--num-simulations', type=int, default=1000,
                               help='Number of simulations per scenario (default: 1000)')
    compare_parser.add_argument('--seed', type=int, help='Random seed for reproducibility')
    compare_parser.set_defaults(func=cmd_compare_scenarios)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    try:
        args.func(args)
        return 0
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
