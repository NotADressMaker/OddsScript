#!/usr/bin/env python3
"""
Sports Analyzer - Unified CLI Tool for Multiple Sports

Comprehensive betting analysis tool supporting NFL, NBA, MLB, and NHL.
Each sport uses appropriate statistical models and provides sport-specific insights.
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.nfl_analytics import NFLAnalytics
from lib.nba_analytics import NBAAnalytics
from lib.mlb_analytics import MLBAnalytics
from lib.nhl_analytics import NHLAnalytics


def print_separator(char="=", length=70):
    """Print separator line"""
    print(char * length)


def format_percentage(value):
    """Format as percentage"""
    return f"{value * 100:.1f}%"


def analyze_nfl(args):
    """Analyze NFL game"""
    print_separator()
    print(f"NFL GAME ANALYSIS")
    print_separator()

    if args.analysis_type == 'spread':
        print(f"\nSpread Analysis:")
        print(f"  Team Rating: {args.team_rating:.1f} pts/game")
        print(f"  Opponent Rating: {args.opponent_rating:.1f} pts/game")
        print(f"  Spread: {args.spread:+.1f}")
        print(f"  Home Team: {'Yes' if args.home else 'No'}")

        result = NFLAnalytics.calculate_spread_probability(
            args.team_rating,
            args.opponent_rating,
            args.spread,
            args.home
        )

        print(f"\nResults:")
        print(f"  Cover Probability: {format_percentage(result['cover_probability'])}")
        print(f"  Push Probability: {format_percentage(result['push_probability'])}")
        print(f"  Lose Probability: {format_percentage(result['lose_probability'])}")
        print(f"  Expected Margin: {result['expected_margin']:+.1f}")
        if result['is_key_number']:
            print(f"  ⚠ KEY NUMBER: {abs(args.spread)} is a critical NFL number!")

        # Key number analysis
        key_analysis = NFLAnalytics.analyze_key_numbers(args.spread)
        print(f"\nKey Number Analysis:")
        print(f"  {key_analysis['advice']}")

    elif args.analysis_type == 'total':
        print(f"\nTotal Analysis:")
        print(f"  Team 1 Avg: {args.team1_avg:.1f} pts/game")
        print(f"  Team 2 Avg: {args.team2_avg:.1f} pts/game")
        print(f"  Total Line: {args.total_line:.1f}")

        result = NFLAnalytics.calculate_total_probability(
            args.team1_avg,
            args.team2_avg,
            args.total_line
        )

        print(f"\nResults:")
        print(f"  Over Probability: {format_percentage(result['over_probability'])}")
        print(f"  Under Probability: {format_percentage(result['under_probability'])}")
        print(f"  Expected Total: {result['expected_total']:.1f}")
        print(f"  Difference from Line: {result['difference']:+.1f}")

    elif args.analysis_type == 'simulate':
        print(f"\nGame Simulation:")
        print(f"  Home Team Rating: {args.home_rating:.1f}")
        print(f"  Away Team Rating: {args.away_rating:.1f}")

        game = NFLAnalytics.simulate_game(args.home_rating, args.away_rating, args.seed)

        print(f"\nFinal Score:")
        print(f"  Home: {game['home_score']}")
        print(f"  Away: {game['away_score']}")
        print(f"  Margin: {game['margin']:+d}")
        print(f"  Total: {game['total']}")
        print(f"  Result: {game['result'].replace('_', ' ').title()}")
        if game['is_key_number']:
            print(f"  Key Number Margin: Yes ({abs(game['margin'])})")


def analyze_nba(args):
    """Analyze NBA game"""
    print_separator()
    print(f"NBA GAME ANALYSIS")
    print_separator()

    if args.analysis_type == 'spread':
        print(f"\nSpread Analysis:")
        print(f"  Team Rating: {args.team_rating:.1f} pts/game")
        print(f"  Opponent Rating: {args.opponent_rating:.1f} pts/game")
        print(f"  Spread: {args.spread:+.1f}")
        print(f"  Home Team: {'Yes' if args.home else 'No'}")

        result = NBAAnalytics.calculate_spread_probability(
            args.team_rating,
            args.opponent_rating,
            args.spread,
            args.home
        )

        print(f"\nResults:")
        print(f"  Cover Probability: {format_percentage(result['cover_probability'])}")
        print(f"  Expected Margin: {result['expected_margin']:+.1f}")
        print(f"  Confidence Level: {result['confidence'].upper()}")

    elif args.analysis_type == 'total':
        print(f"\nTotal Analysis:")
        print(f"  Team 1 Avg: {args.team1_avg:.1f} pts/game")
        print(f"  Team 2 Avg: {args.team2_avg:.1f} pts/game")
        print(f"  Total Line: {args.total_line:.1f}")
        print(f"  Pace Factor: {args.pace_factor:.2f}x")

        result = NBAAnalytics.calculate_total_probability(
            args.team1_avg,
            args.team2_avg,
            args.total_line,
            args.pace_factor
        )

        print(f"\nResults:")
        print(f"  Over Probability: {format_percentage(result['over_probability'])}")
        print(f"  Under Probability: {format_percentage(result['under_probability'])}")
        print(f"  Expected Total: {result['expected_total']:.1f}")
        print(f"  Edge: {result['edge']:.2f} std devs")

    elif args.analysis_type == 'prop':
        print(f"\nPlayer Prop Analysis:")
        print(f"  Player Average: {args.player_avg:.1f}")
        print(f"  Prop Line: {args.prop_line:.1f}")
        print(f"  Usage Adjustment: {args.usage:.2f}x")

        result = NBAAnalytics.calculate_player_prop_probability(
            args.player_avg,
            args.prop_line,
            usage_adjustment=args.usage
        )

        print(f"\nResults:")
        print(f"  Over Probability: {format_percentage(result['over_probability'])}")
        print(f"  Under Probability: {format_percentage(result['under_probability'])}")
        print(f"  Adjusted Average: {result['adjusted_average']:.1f}")
        print(f"  Edge: {result['edge']:+.2f} std devs")

        if result['edge'] > 0.5:
            print(f"\n  ✓ OVER has significant edge")
        elif result['edge'] < -0.5:
            print(f"\n  ✓ UNDER has significant edge")


def analyze_mlb(args):
    """Analyze MLB game"""
    print_separator()
    print(f"MLB GAME ANALYSIS")
    print_separator()

    if args.analysis_type == 'moneyline':
        print(f"\nMoneyline Analysis:")
        print(f"  Team Avg Runs: {args.team_avg:.2f}")
        print(f"  Opponent Avg Runs: {args.opponent_avg:.2f}")
        print(f"  Home Team: {'Yes' if args.home else 'No'}")

        result = MLBAnalytics.calculate_moneyline_probability(
            args.team_avg,
            args.opponent_avg,
            args.home
        )

        print(f"\nResults:")
        print(f"  Win Probability: {format_percentage(result['win_probability'])}")
        print(f"  Tie Probability (Extra Innings): {format_percentage(result['tie_probability'])}")
        print(f"  Loss Probability: {format_percentage(result['loss_probability'])}")
        print(f"  Expected Runs: {result['expected_runs']:.2f}")

    elif args.analysis_type == 'runline':
        print(f"\nRun Line Analysis:")
        print(f"  Team Avg Runs: {args.team_avg:.2f}")
        print(f"  Opponent Avg Runs: {args.opponent_avg:.2f}")
        print(f"  Run Line: {args.runline:+.1f}")

        result = MLBAnalytics.calculate_runline_probability(
            args.team_avg,
            args.opponent_avg,
            args.runline,
            args.home
        )

        print(f"\nResults:")
        print(f"  Cover Probability: {format_percentage(result['cover_probability'])}")
        print(f"  Expected Margin: {result['expected_margin']:+.2f} runs")

    elif args.analysis_type == 'total':
        print(f"\nTotal Analysis:")
        print(f"  Team 1 Avg: {args.team1_avg:.2f} runs")
        print(f"  Team 2 Avg: {args.team2_avg:.2f} runs")
        print(f"  Total Line: {args.total_line:.1f}")
        print(f"  Park Factor: {args.park_factor:.2f}x")

        result = MLBAnalytics.calculate_total_probability(
            args.team1_avg,
            args.team2_avg,
            args.total_line,
            park_factor=args.park_factor
        )

        print(f"\nResults:")
        print(f"  Over Probability: {format_percentage(result['over_probability'])}")
        print(f"  Under Probability: {format_percentage(result['under_probability'])}")
        print(f"  Expected Total: {result['expected_total']:.2f}")


def analyze_nhl(args):
    """Analyze NHL game"""
    print_separator()
    print(f"NHL GAME ANALYSIS")
    print_separator()

    if args.analysis_type == 'moneyline':
        print(f"\nMoneyline Analysis:")
        print(f"  Team Avg Goals: {args.team_avg:.2f}")
        print(f"  Opponent Avg Goals: {args.opponent_avg:.2f}")
        print(f"  Home Team: {'Yes' if args.home else 'No'}")

        result = NHLAnalytics.calculate_moneyline_probability(
            args.team_avg,
            args.opponent_avg,
            args.home
        )

        print(f"\nResults:")
        print(f"  Win Probability (incl. OT/SO): {format_percentage(result['win_probability'])}")
        print(f"  Regulation Win Probability: {format_percentage(result['regulation_win_probability'])}")
        print(f"  Overtime Probability: {format_percentage(result['overtime_probability'])}")

    elif args.analysis_type == 'puckline':
        print(f"\nPuck Line Analysis:")
        print(f"  Team Avg Goals: {args.team_avg:.2f}")
        print(f"  Opponent Avg Goals: {args.opponent_avg:.2f}")
        print(f"  Puck Line: {args.puckline:+.1f}")

        result = NHLAnalytics.calculate_puckline_probability(
            args.team_avg,
            args.opponent_avg,
            args.puckline,
            args.home
        )

        print(f"\nResults:")
        print(f"  Cover Probability: {format_percentage(result['cover_probability'])}")
        print(f"  Expected Margin: {result['expected_margin']:+.2f} goals")

    elif args.analysis_type == 'total':
        print(f"\nTotal Analysis:")
        print(f"  Team 1 Avg: {args.team1_avg:.2f} goals")
        print(f"  Team 2 Avg: {args.team2_avg:.2f} goals")
        print(f"  Total Line: {args.total_line:.1f}")

        result = NHLAnalytics.calculate_total_probability(
            args.team1_avg,
            args.team2_avg,
            args.total_line
        )

        print(f"\nResults:")
        print(f"  Over Probability: {format_percentage(result['over_probability'])}")
        print(f"  Under Probability: {format_percentage(result['under_probability'])}")
        print(f"  Expected Total: {result['expected_total']:.2f}")


def main():
    parser = argparse.ArgumentParser(
        description="Sports Analyzer - Multi-Sport Betting Analysis Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # NFL spread analysis
  %(prog)s nfl spread -t 24.5 -o 20.0 -s -7.5 --home

  # NBA total analysis
  %(prog)s nba total -t1 118.5 -t2 112.3 -l 230.5 --pace 1.05

  # MLB run line
  %(prog)s mlb runline -t 5.2 -o 4.1 -r -1.5 --home

  # NHL puck line
  %(prog)s nhl puckline -t 3.2 -o 2.7 -p -1.5
        """
    )

    subparsers = parser.add_subparsers(dest='sport', help='Sport to analyze')

    # NFL parser
    nfl_parser = subparsers.add_parser('nfl', help='NFL analysis')
    nfl_sub = nfl_parser.add_subparsers(dest='analysis_type')

    nfl_spread = nfl_sub.add_parser('spread', help='Spread analysis')
    nfl_spread.add_argument('-t', '--team-rating', type=float, required=True)
    nfl_spread.add_argument('-o', '--opponent-rating', type=float, required=True)
    nfl_spread.add_argument('-s', '--spread', type=float, required=True)
    nfl_spread.add_argument('--home', action='store_true', help='Team is home')

    nfl_total = nfl_sub.add_parser('total', help='Total analysis')
    nfl_total.add_argument('-t1', '--team1-avg', type=float, required=True)
    nfl_total.add_argument('-t2', '--team2-avg', type=float, required=True)
    nfl_total.add_argument('-l', '--total-line', type=float, required=True)

    nfl_sim = nfl_sub.add_parser('simulate', help='Simulate game')
    nfl_sim.add_argument('--home-rating', type=float, required=True)
    nfl_sim.add_argument('--away-rating', type=float, required=True)
    nfl_sim.add_argument('--seed', type=int)

    # NBA parser
    nba_parser = subparsers.add_parser('nba', help='NBA analysis')
    nba_sub = nba_parser.add_subparsers(dest='analysis_type')

    nba_spread = nba_sub.add_parser('spread', help='Spread analysis')
    nba_spread.add_argument('-t', '--team-rating', type=float, required=True)
    nba_spread.add_argument('-o', '--opponent-rating', type=float, required=True)
    nba_spread.add_argument('-s', '--spread', type=float, required=True)
    nba_spread.add_argument('--home', action='store_true')

    nba_total = nba_sub.add_parser('total', help='Total analysis')
    nba_total.add_argument('-t1', '--team1-avg', type=float, required=True)
    nba_total.add_argument('-t2', '--team2-avg', type=float, required=True)
    nba_total.add_argument('-l', '--total-line', type=float, required=True)
    nba_total.add_argument('--pace-factor', type=float, default=1.0)

    nba_prop = nba_sub.add_parser('prop', help='Player prop analysis')
    nba_prop.add_argument('-p', '--player-avg', type=float, required=True)
    nba_prop.add_argument('-l', '--prop-line', type=float, required=True)
    nba_prop.add_argument('--usage', type=float, default=1.0)

    # MLB parser
    mlb_parser = subparsers.add_parser('mlb', help='MLB analysis')
    mlb_sub = mlb_parser.add_subparsers(dest='analysis_type')

    mlb_ml = mlb_sub.add_parser('moneyline', help='Moneyline analysis')
    mlb_ml.add_argument('-t', '--team-avg', type=float, required=True)
    mlb_ml.add_argument('-o', '--opponent-avg', type=float, required=True)
    mlb_ml.add_argument('--home', action='store_true')

    mlb_rl = mlb_sub.add_parser('runline', help='Run line analysis')
    mlb_rl.add_argument('-t', '--team-avg', type=float, required=True)
    mlb_rl.add_argument('-o', '--opponent-avg', type=float, required=True)
    mlb_rl.add_argument('-r', '--runline', type=float, default=-1.5)
    mlb_rl.add_argument('--home', action='store_true')

    mlb_total = mlb_sub.add_parser('total', help='Total analysis')
    mlb_total.add_argument('-t1', '--team1-avg', type=float, required=True)
    mlb_total.add_argument('-t2', '--team2-avg', type=float, required=True)
    mlb_total.add_argument('-l', '--total-line', type=float, required=True)
    mlb_total.add_argument('--park-factor', type=float, default=1.0)

    # NHL parser
    nhl_parser = subparsers.add_parser('nhl', help='NHL analysis')
    nhl_sub = nhl_parser.add_subparsers(dest='analysis_type')

    nhl_ml = nhl_sub.add_parser('moneyline', help='Moneyline analysis')
    nhl_ml.add_argument('-t', '--team-avg', type=float, required=True)
    nhl_ml.add_argument('-o', '--opponent-avg', type=float, required=True)
    nhl_ml.add_argument('--home', action='store_true')

    nhl_pl = nhl_sub.add_parser('puckline', help='Puck line analysis')
    nhl_pl.add_argument('-t', '--team-avg', type=float, required=True)
    nhl_pl.add_argument('-o', '--opponent-avg', type=float, required=True)
    nhl_pl.add_argument('-p', '--puckline', type=float, default=-1.5)
    nhl_pl.add_argument('--home', action='store_true')

    nhl_total = nhl_sub.add_parser('total', help='Total analysis')
    nhl_total.add_argument('-t1', '--team1-avg', type=float, required=True)
    nhl_total.add_argument('-t2', '--team2-avg', type=float, required=True)
    nhl_total.add_argument('-l', '--total-line', type=float, required=True)

    args = parser.parse_args()

    if not args.sport:
        parser.print_help()
        return 1

    try:
        if args.sport == 'nfl':
            analyze_nfl(args)
        elif args.sport == 'nba':
            analyze_nba(args)
        elif args.sport == 'mlb':
            analyze_mlb(args)
        elif args.sport == 'nhl':
            analyze_nhl(args)

        return 0
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
