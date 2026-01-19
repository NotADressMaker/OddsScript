#!/usr/bin/env python3
"""
Data Import/Export Tool

Comprehensive utility for importing and exporting sports betting data
in various formats (CSV, JSON, SQL).
"""

import argparse
import csv
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.sports_data_manager import SportsDataManager, Game, Team, BettingRecord, OddsSnapshot


class DataImportExport:
    """Utility for bulk data import and export operations"""

    def __init__(self, db_path: str = "sportsdata.db"):
        """Initialize with database path"""
        self.manager = SportsDataManager(db_path)

    # CSV Import Functions
    def import_nfl_games_csv(self, csv_path: str) -> int:
        """
        Import NFL games from CSV

        Expected columns: date, home_team, away_team, home_score, away_score,
                         season, week, (optional: spread, total, overtime, playoff)
        """
        count = 0

        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)

            for row in reader:
                game = Game(
                    sport="nfl",
                    league="NFL",
                    date=row['date'],
                    season=row.get('season', ''),
                    week=int(row.get('week', 0)) if row.get('week') else None,
                    home_team=row['home_team'],
                    away_team=row['away_team'],
                    home_score=int(row['home_score']) if row.get('home_score') and row['home_score'] != '' else None,
                    away_score=int(row['away_score']) if row.get('away_score') and row['away_score'] != '' else None,
                    spread=float(row['spread']) if row.get('spread') and row['spread'] != '' else None,
                    total=float(row['total']) if row.get('total') and row['total'] != '' else None,
                    completed=bool(row.get('home_score') and row['home_score'] != ''),
                    overtime=bool(row.get('overtime')) if row.get('overtime') else False,
                    playoff=bool(row.get('playoff')) if row.get('playoff') else False
                )

                self.manager.add_game(game)
                count += 1

        return count

    def import_bets_csv(self, csv_path: str) -> int:
        """
        Import bets from CSV

        Expected columns: date, sport, description, bet_type, selection, odds, stake,
                         (optional: result, profit, sportsbook, notes, game_id)
        """
        count = 0

        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)

            for row in reader:
                bet = BettingRecord(
                    game_id=int(row['game_id']) if row.get('game_id') and row['game_id'] != '' else None,
                    date=row['date'],
                    sport=row['sport'],
                    league=row.get('league', ''),
                    description=row.get('description', ''),
                    bet_type=row['bet_type'],
                    selection=row['selection'],
                    odds=float(row['odds']),
                    stake=float(row['stake']),
                    result=row.get('result') if row.get('result') and row['result'] != '' else None,
                    profit=float(row['profit']) if row.get('profit') and row['profit'] != '' else None,
                    sportsbook=row.get('sportsbook', ''),
                    notes=row.get('notes', '')
                )

                self.manager.add_bet(bet)
                count += 1

        return count

    def import_teams_csv(self, csv_path: str, sport: str) -> int:
        """
        Import teams from CSV

        Expected columns: name, league, (optional: conference, division, elo_rating)
        """
        count = 0

        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)

            for row in reader:
                team = Team(
                    name=row['name'],
                    sport=sport,
                    league=row.get('league', ''),
                    conference=row.get('conference', ''),
                    division=row.get('division', ''),
                    elo_rating=float(row['elo_rating']) if row.get('elo_rating') and row['elo_rating'] != '' else None
                )

                self.manager.add_team(team)
                count += 1

        return count

    # JSON Import Functions
    def import_games_json(self, json_path: str) -> int:
        """
        Import games from JSON file

        Expected format: Array of game objects with same fields as Game model
        """
        with open(json_path, 'r') as f:
            games_data = json.load(f)

        count = 0
        for game_data in games_data:
            game = Game(**game_data)
            self.manager.add_game(game)
            count += 1

        return count

    def import_bets_json(self, json_path: str) -> int:
        """Import bets from JSON file"""
        with open(json_path, 'r') as f:
            bets_data = json.load(f)

        count = 0
        for bet_data in bets_data:
            bet = BettingRecord(**bet_data)
            self.manager.add_bet(bet)
            count += 1

        return count

    # Export Functions
    def export_games_csv(self, output_path: str, sport: Optional[str] = None,
                        start_date: Optional[str] = None, end_date: Optional[str] = None) -> int:
        """Export games to CSV"""
        return self.manager.export_games_to_csv(output_path, sport, start_date, end_date)

    def export_bets_csv(self, output_path: str, sport: Optional[str] = None) -> int:
        """Export bets to CSV"""
        return self.manager.export_bets_to_csv(output_path, sport)

    def export_games_json(self, output_path: str, sport: Optional[str] = None,
                         start_date: Optional[str] = None, end_date: Optional[str] = None) -> int:
        """Export games to JSON"""
        games = self.manager.list_games(sport=sport, start_date=start_date,
                                       end_date=end_date, limit=10000)

        games_data = []
        for game in games:
            game_dict = {
                'id': game.id,
                'sport': game.sport,
                'league': game.league,
                'date': game.date,
                'season': game.season,
                'week': game.week,
                'home_team': game.home_team,
                'away_team': game.away_team,
                'home_score': game.home_score,
                'away_score': game.away_score,
                'home_odds': game.home_odds,
                'away_odds': game.away_odds,
                'spread': game.spread,
                'total': game.total,
                'completed': game.completed,
                'overtime': game.overtime,
                'playoff': game.playoff
            }
            games_data.append(game_dict)

        with open(output_path, 'w') as f:
            json.dump(games_data, f, indent=2)

        return len(games_data)

    def export_stats_json(self, output_path: str) -> Dict:
        """Export comprehensive betting statistics to JSON"""
        # Get stats by sport
        sports = ['nfl', 'nba', 'mlb', 'nhl', 'cfb', 'cbb', 'soccer']

        stats_report = {
            'generated_at': datetime.now().isoformat(),
            'overall': self.manager.get_betting_stats(),
            'by_sport': {},
            'by_bet_type': {}
        }

        for sport in sports:
            stats = self.manager.get_betting_stats(sport=sport)
            if stats['total_bets'] > 0:
                stats_report['by_sport'][sport] = stats

        # Get stats by bet type
        bet_types = ['spread', 'moneyline', 'total', 'prop']
        for bet_type in bet_types:
            stats = self.manager.get_betting_stats(bet_type=bet_type)
            if stats['total_bets'] > 0:
                stats_report['by_bet_type'][bet_type] = stats

        with open(output_path, 'w') as f:
            json.dump(stats_report, f, indent=2)

        return stats_report

    # Bulk Operations
    def bulk_import_directory(self, directory_path: str, file_pattern: str = "*.csv") -> Dict[str, int]:
        """
        Bulk import all matching files from a directory

        Returns counts by filename
        """
        from glob import glob

        directory = Path(directory_path)
        files = glob(str(directory / file_pattern))

        results = {}

        for file_path in files:
            filename = Path(file_path).name
            print(f"Processing {filename}...")

            try:
                # Auto-detect file type by name patterns
                if 'game' in filename.lower():
                    count = self.import_nfl_games_csv(file_path)
                elif 'bet' in filename.lower():
                    count = self.import_bets_csv(file_path)
                elif 'team' in filename.lower():
                    # Try to detect sport from filename
                    sport = 'unknown'
                    for s in ['nfl', 'nba', 'mlb', 'nhl', 'cfb', 'cbb', 'soccer']:
                        if s in filename.lower():
                            sport = s
                            break
                    count = self.import_teams_csv(file_path, sport)
                else:
                    print(f"  Skipped (unknown type)")
                    continue

                results[filename] = count
                print(f"  Imported {count} records")

            except Exception as e:
                print(f"  Error: {e}")
                results[filename] = 0

        return results

    def generate_sample_data(self, num_games: int = 10) -> Dict[str, int]:
        """Generate sample data for testing"""
        from random import randint, choice

        teams = [
            "Kansas City Chiefs", "Buffalo Bills", "Cincinnati Bengals",
            "Dallas Cowboys", "Philadelphia Eagles", "San Francisco 49ers"
        ]

        count = 0
        for i in range(num_games):
            home = choice(teams)
            away = choice([t for t in teams if t != home])

            game = Game(
                sport="nfl",
                league="NFL",
                date=f"2024-01-{15 + i % 15:02d}",
                season="2023",
                week=18,
                home_team=home,
                away_team=away,
                home_score=randint(10, 35),
                away_score=randint(10, 35),
                spread=-3.5,
                total=47.5,
                completed=True
            )

            self.manager.add_game(game)
            count += 1

        return {'games': count}

    def close(self):
        """Close database connection"""
        self.manager.close()


def main():
    """Command-line interface"""
    parser = argparse.ArgumentParser(
        description="Sports Betting Data Import/Export Tool"
    )

    parser.add_argument(
        'command',
        choices=['import-games', 'import-bets', 'import-teams',
                'export-games', 'export-bets', 'export-stats',
                'bulk-import', 'generate-sample'],
        help='Import/export command'
    )

    parser.add_argument('--input', '-i', help='Input file path')
    parser.add_argument('--output', '-o', help='Output file path')
    parser.add_argument('--sport', help='Sport filter')
    parser.add_argument('--start-date', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', help='End date (YYYY-MM-DD)')
    parser.add_argument('--format', choices=['csv', 'json'], default='csv', help='File format')
    parser.add_argument('--db', default='sportsdata.db', help='Database path')
    parser.add_argument('--directory', '-d', help='Directory for bulk import')
    parser.add_argument('--num-games', type=int, default=10, help='Number of sample games')

    args = parser.parse_args()

    importer = DataImportExport(args.db)

    try:
        if args.command == 'import-games':
            if not args.input:
                print("Error: --input required")
                return 1

            if args.format == 'csv':
                count = importer.import_nfl_games_csv(args.input)
            else:
                count = importer.import_games_json(args.input)

            print(f"Imported {count} games")

        elif args.command == 'import-bets':
            if not args.input:
                print("Error: --input required")
                return 1

            if args.format == 'csv':
                count = importer.import_bets_csv(args.input)
            else:
                count = importer.import_bets_json(args.input)

            print(f"Imported {count} bets")

        elif args.command == 'import-teams':
            if not args.input or not args.sport:
                print("Error: --input and --sport required")
                return 1

            count = importer.import_teams_csv(args.input, args.sport)
            print(f"Imported {count} teams")

        elif args.command == 'export-games':
            if not args.output:
                print("Error: --output required")
                return 1

            if args.format == 'csv':
                count = importer.export_games_csv(
                    args.output, args.sport, args.start_date, args.end_date
                )
            else:
                count = importer.export_games_json(
                    args.output, args.sport, args.start_date, args.end_date
                )

            print(f"Exported {count} games to {args.output}")

        elif args.command == 'export-bets':
            if not args.output:
                print("Error: --output required")
                return 1

            count = importer.export_bets_csv(args.output, args.sport)
            print(f"Exported {count} bets to {args.output}")

        elif args.command == 'export-stats':
            if not args.output:
                print("Error: --output required")
                return 1

            stats = importer.export_stats_json(args.output)
            print(f"Exported statistics to {args.output}")
            print(f"\nOverall Stats:")
            print(f"  Total Bets: {stats['overall']['total_bets']}")
            print(f"  Win Rate: {stats['overall']['win_rate']:.1f}%")
            print(f"  ROI: {stats['overall']['roi']:.1f}%")

        elif args.command == 'bulk-import':
            if not args.directory:
                print("Error: --directory required")
                return 1

            results = importer.bulk_import_directory(args.directory)
            print(f"\nBulk Import Results:")
            for filename, count in results.items():
                print(f"  {filename}: {count} records")

        elif args.command == 'generate-sample':
            results = importer.generate_sample_data(args.num_games)
            print(f"Generated {results['games']} sample games")

    finally:
        importer.close()

    return 0


if __name__ == '__main__':
    sys.exit(main())
