#!/usr/bin/env python3
"""
Game Log Manager - CLI Tool for Sports Analytics Pipeline

Manage game logs, calculate team statistics, and generate betting insights
across NFL, NBA, MLB, and NHL.
"""

import argparse
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.game_log_pipeline import GameLogPipeline
from lib.nfl_analytics import NFLAnalytics
from lib.nba_analytics import NBAAnalytics
from lib.mlb_analytics import MLBAnalytics
from lib.nhl_analytics import NHLAnalytics


def print_separator(char="=", length=70):
    """Print separator line"""
    print(char * length)


def cmd_ingest(args):
    """Ingest game logs from file"""
    print_separator()
    print(f"INGESTING GAME LOGS - {args.sport.upper()}")
    print_separator()

    pipeline = GameLogPipeline(args.sport, args.storage)

    # Determine file format
    file_ext = Path(args.file).suffix.lower()

    print(f"\nFile: {args.file}")
    print(f"Format: {file_ext}")
    print(f"Sport: {args.sport.upper()}")

    try:
        if file_ext == '.csv':
            count = pipeline.ingest_csv(args.file)
        elif file_ext == '.json':
            count = pipeline.ingest_json(args.file)
        else:
            print(f"Error: Unsupported file format '{file_ext}'")
            print("Supported formats: .csv, .json")
            return 1

        print(f"\n✓ Successfully ingested {count} games")

        # Calculate statistics
        print("\nCalculating team statistics...")
        pipeline.calculate_team_statistics()

        print("Calculating Elo ratings...")
        pipeline.calculate_elo_ratings(
            k_factor=args.k_factor,
            home_advantage=args.home_advantage
        )

        # Save results
        output_file = args.output or f"data/{args.sport}_team_stats.csv"
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        pipeline.export_team_stats(output_file, format='csv')

        print(f"\n✓ Team statistics saved to: {output_file}")

        # Show summary
        summary = pipeline.get_summary_stats()
        print(f"\nSummary:")
        print(f"  Total Games: {summary['total_games']}")
        print(f"  Total Teams: {summary['total_teams']}")
        print(f"  League Avg PPG: {summary['avg_ppg']:.2f}")
        if summary['date_range']['earliest']:
            print(f"  Date Range: {summary['date_range']['earliest']} to {summary['date_range']['latest']}")

        return 0

    except FileNotFoundError:
        print(f"Error: File not found: {args.file}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


def cmd_stats(args):
    """Show team statistics"""
    print_separator()
    print(f"TEAM STATISTICS - {args.sport.upper()}")
    print_separator()

    pipeline = GameLogPipeline(args.sport, args.storage)

    # Load data
    try:
        if args.file.endswith('.csv'):
            pipeline.ingest_csv(args.file)
        else:
            pipeline.ingest_json(args.file)

        pipeline.calculate_team_statistics()
        pipeline.calculate_elo_ratings()

        # Get rankings
        rankings = pipeline.get_team_rankings(args.sort_by)

        print(f"\nTeam Rankings (by {args.sort_by}):")
        print_separator("-")

        # Print header
        print(f"{'Rank':<5} {'Team':<20} {'W-L':<10} {'PPG':<8} {'PAPG':<8} {'Diff':<8} {'Elo':<8}")
        print_separator("-")

        for i, (team, _) in enumerate(rankings[:args.limit], 1):
            stats = pipeline.team_stats[team]
            record = f"{stats['wins']}-{stats['losses']}"
            if stats['ties'] > 0:
                record += f"-{stats['ties']}"

            print(f"{i:<5} {team:<20} {record:<10} {stats['ppg']:<8.1f} "
                  f"{stats['papg']:<8.1f} {stats['point_diff_per_game']:<8.1f} "
                  f"{stats['elo_rating']:<8.0f}")

        # Detailed view for specific team
        if args.team:
            print(f"\nDetailed Stats for {args.team}:")
            print_separator("-")

            if args.team in pipeline.team_stats:
                stats = pipeline.team_stats[args.team]
                print(f"  Record: {stats['wins']}-{stats['losses']}-{stats['ties']}")
                print(f"  Win Percentage: {stats['win_pct']*100:.1f}%")
                print(f"  Points Per Game: {stats['ppg']:.2f}")
                print(f"  Points Against Per Game: {stats['papg']:.2f}")
                print(f"  Point Differential: {stats['point_diff_per_game']:+.2f} per game")
                print(f"  Elo Rating: {stats['elo_rating']:.0f}")
                print(f"  Home Record: {stats['home_wins']}-{stats['home_games']-stats['home_wins']}")
                print(f"  Away Record: {stats['away_wins']}-{stats['away_games']-stats['away_wins']}")
            else:
                print(f"  Team '{args.team}' not found in dataset")

        return 0

    except Exception as e:
        print(f"Error: {e}")
        return 1


def cmd_predict(args):
    """Predict matchup outcome"""
    print_separator()
    print(f"MATCHUP PREDICTION - {args.sport.upper()}")
    print_separator()

    pipeline = GameLogPipeline(args.sport, args.storage)

    # Load data
    try:
        if args.file.endswith('.csv'):
            pipeline.ingest_csv(args.file)
        else:
            pipeline.ingest_json(args.file)

        pipeline.calculate_team_statistics()
        pipeline.calculate_elo_ratings()

        print(f"\nMatchup: {args.home_team} vs {args.away_team}")
        print(f"Location: {args.home_team} (Home)")

        # Get projection
        projection = pipeline.get_matchup_projection(
            args.home_team,
            args.away_team,
            use_elo=not args.no_elo
        )

        print(f"\nProjection Method: {projection['method'].upper()}")
        print_separator("-")

        if projection['method'] == 'elo':
            print(f"  {args.home_team} Elo: {projection['home_elo']:.0f}")
            print(f"  {args.away_team} Elo: {projection['away_elo']:.0f}")
            print(f"\n  Win Probability:")
            print(f"    {args.home_team}: {projection['home_win_probability']*100:.1f}%")
            print(f"    {args.away_team}: {projection['away_win_probability']*100:.1f}%")
        else:
            print(f"  {args.home_team} Expected: {projection['home_expected_score']:.1f}")
            print(f"  {args.away_team} Expected: {projection['away_expected_score']:.1f}")

        # Use sport-specific analytics for detailed analysis
        print(f"\nSport-Specific Analysis:")
        print_separator("-")

        home_stats = pipeline.team_stats[args.home_team]
        away_stats = pipeline.team_stats[args.away_team]

        if args.sport == 'nfl':
            if args.spread:
                result = NFLAnalytics.calculate_spread_probability(
                    home_stats['ppg'],
                    away_stats['ppg'],
                    args.spread,
                    is_home=True
                )
                print(f"  Spread: {args.spread:+.1f}")
                print(f"  Cover Probability: {result['cover_probability']*100:.1f}%")
                print(f"  Expected Margin: {result['expected_margin']:+.1f}")

        elif args.sport == 'nba':
            total_result = NBAAnalytics.calculate_total_probability(
                home_stats['ppg'],
                away_stats['ppg'],
                home_stats['ppg'] + away_stats['ppg']
            )
            print(f"  Expected Total: {total_result['expected_total']:.1f}")

        elif args.sport == 'mlb':
            ml_result = MLBAnalytics.calculate_moneyline_probability(
                home_stats['ppg'],
                away_stats['ppg'],
                is_home=True
            )
            print(f"  Moneyline Win Probability: {ml_result['win_probability']*100:.1f}%")

        elif args.sport == 'nhl':
            ml_result = NHLAnalytics.calculate_moneyline_probability(
                home_stats['ppg'],
                away_stats['ppg'],
                is_home=True
            )
            print(f"  Moneyline Win Probability: {ml_result['win_probability']*100:.1f}%")

        return 0

    except ValueError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


def cmd_export(args):
    """Export team statistics"""
    pipeline = GameLogPipeline(args.sport, args.storage)

    try:
        # Load data
        if args.input.endswith('.csv'):
            pipeline.ingest_csv(args.input)
        else:
            pipeline.ingest_json(args.input)

        pipeline.calculate_team_statistics()
        pipeline.calculate_elo_ratings()

        # Export
        file_ext = Path(args.output).suffix.lower()
        format_type = 'json' if file_ext == '.json' else 'csv'

        pipeline.export_team_stats(args.output, format=format_type)

        print(f"✓ Exported team statistics to: {args.output}")
        print(f"  Format: {format_type.upper()}")
        print(f"  Teams: {len(pipeline.team_stats)}")

        return 0

    except Exception as e:
        print(f"Error: {e}")
        return 1


def main():
    parser = argparse.ArgumentParser(
        description="Game Log Manager - Sports Analytics Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Ingest NFL game logs
  %(prog)s ingest nfl games_2024.csv

  # Show team statistics
  %(prog)s stats nfl games_2024.csv --sort-by elo_rating --limit 10

  # Detailed stats for specific team
  %(prog)s stats nfl games_2024.csv --team "Chiefs"

  # Predict matchup
  %(prog)s predict nfl games_2024.csv --home "Chiefs" --away "Bills" --spread -3.0

  # Export statistics
  %(prog)s export nfl games_2024.csv -o team_stats.json
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Ingest command
    ingest_parser = subparsers.add_parser('ingest', help='Ingest game logs')
    ingest_parser.add_argument('sport', choices=['nfl', 'nba', 'mlb', 'nhl'], help='Sport')
    ingest_parser.add_argument('file', help='Game log file (CSV or JSON)')
    ingest_parser.add_argument('-o', '--output', help='Output file for team stats')
    ingest_parser.add_argument('--storage', default='data/game_logs', help='Storage directory')
    ingest_parser.add_argument('--k-factor', type=float, default=32, help='Elo K-factor')
    ingest_parser.add_argument('--home-advantage', type=float, default=100, help='Home advantage (Elo points)')
    ingest_parser.set_defaults(func=cmd_ingest)

    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show team statistics')
    stats_parser.add_argument('sport', choices=['nfl', 'nba', 'mlb', 'nhl'], help='Sport')
    stats_parser.add_argument('file', help='Game log file')
    stats_parser.add_argument('--sort-by', default='elo_rating',
                             choices=['elo_rating', 'win_pct', 'ppg', 'point_diff_per_game'],
                             help='Sort by metric')
    stats_parser.add_argument('--limit', type=int, default=32, help='Number of teams to show')
    stats_parser.add_argument('--team', help='Show detailed stats for specific team')
    stats_parser.add_argument('--storage', default='data/game_logs', help='Storage directory')
    stats_parser.set_defaults(func=cmd_stats)

    # Predict command
    predict_parser = subparsers.add_parser('predict', help='Predict matchup outcome')
    predict_parser.add_argument('sport', choices=['nfl', 'nba', 'mlb', 'nhl'], help='Sport')
    predict_parser.add_argument('file', help='Game log file')
    predict_parser.add_argument('--home', dest='home_team', required=True, help='Home team')
    predict_parser.add_argument('--away', dest='away_team', required=True, help='Away team')
    predict_parser.add_argument('--spread', type=float, help='Point spread (for analysis)')
    predict_parser.add_argument('--no-elo', action='store_true', help='Use power ratings instead of Elo')
    predict_parser.add_argument('--storage', default='data/game_logs', help='Storage directory')
    predict_parser.set_defaults(func=cmd_predict)

    # Export command
    export_parser = subparsers.add_parser('export', help='Export team statistics')
    export_parser.add_argument('sport', choices=['nfl', 'nba', 'mlb', 'nhl'], help='Sport')
    export_parser.add_argument('input', help='Input game log file')
    export_parser.add_argument('-o', '--output', required=True, help='Output file')
    export_parser.add_argument('--storage', default='data/game_logs', help='Storage directory')
    export_parser.set_defaults(func=cmd_export)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    try:
        return args.func(args)
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
