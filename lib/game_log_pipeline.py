#!/usr/bin/env python3
"""
Game Log Pipeline

End-to-end analytics pipeline for ingesting, processing, and analyzing game logs
across multiple sports (NFL, NBA, MLB, NHL).
"""

import csv
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict
import math


class GameLogPipeline:
    """Core pipeline for ingesting and processing game logs"""

    def __init__(self, sport: str, storage_path: str = "data/game_logs"):
        """
        Initialize pipeline

        Args:
            sport: Sport type (nfl, nba, mlb, nhl)
            storage_path: Path to store processed data
        """
        self.sport = sport.lower()
        self.storage_path = storage_path
        self.games = []
        self.team_stats = defaultdict(lambda: {
            'games': 0,
            'wins': 0,
            'losses': 0,
            'ties': 0,
            'points_for': 0,
            'points_against': 0,
            'home_games': 0,
            'away_games': 0,
            'home_wins': 0,
            'away_wins': 0,
            'elo_rating': 1500
        })

        # Ensure storage directory exists
        os.makedirs(storage_path, exist_ok=True)

    def ingest_csv(self, filepath: str) -> int:
        """
        Ingest game logs from CSV file

        Expected CSV format:
        date,home_team,away_team,home_score,away_score[,additional_columns]

        Args:
            filepath: Path to CSV file

        Returns:
            Number of games ingested
        """
        games_ingested = 0

        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                game = self._parse_game_row(row)
                if game:
                    self.games.append(game)
                    games_ingested += 1

        return games_ingested

    def ingest_json(self, filepath: str) -> int:
        """
        Ingest game logs from JSON file

        Expected JSON format:
        [
            {
                "date": "2024-01-15",
                "home_team": "Team A",
                "away_team": "Team B",
                "home_score": 24,
                "away_score": 17
            }
        ]

        Args:
            filepath: Path to JSON file

        Returns:
            Number of games ingested
        """
        with open(filepath, 'r') as f:
            data = json.load(f)

        games_ingested = 0
        for row in data:
            game = self._parse_game_row(row)
            if game:
                self.games.append(game)
                games_ingested += 1

        return games_ingested

    def _parse_game_row(self, row: Dict) -> Optional[Dict]:
        """Parse and validate game row"""
        try:
            game = {
                'date': row.get('date', ''),
                'home_team': row['home_team'].strip(),
                'away_team': row['away_team'].strip(),
                'home_score': int(row['home_score']),
                'away_score': int(row['away_score']),
                'sport': self.sport
            }

            # Add optional fields
            for field in ['season', 'week', 'overtime', 'playoffs']:
                if field in row:
                    game[field] = row[field]

            return game

        except (KeyError, ValueError) as e:
            print(f"Warning: Skipping invalid row: {e}")
            return None

    def calculate_team_statistics(self):
        """Calculate comprehensive team statistics from game logs"""
        # Reset stats
        self.team_stats.clear()

        for game in self.games:
            home = game['home_team']
            away = game['away_team']
            home_score = game['home_score']
            away_score = game['away_score']

            # Update games played
            self.team_stats[home]['games'] += 1
            self.team_stats[away]['games'] += 1
            self.team_stats[home]['home_games'] += 1
            self.team_stats[away]['away_games'] += 1

            # Update scores
            self.team_stats[home]['points_for'] += home_score
            self.team_stats[home]['points_against'] += away_score
            self.team_stats[away]['points_for'] += away_score
            self.team_stats[away]['points_against'] += home_score

            # Determine winner
            if home_score > away_score:
                self.team_stats[home]['wins'] += 1
                self.team_stats[home]['home_wins'] += 1
                self.team_stats[away]['losses'] += 1
            elif away_score > home_score:
                self.team_stats[away]['wins'] += 1
                self.team_stats[away]['away_wins'] += 1
                self.team_stats[home]['losses'] += 1
            else:
                self.team_stats[home]['ties'] += 1
                self.team_stats[away]['ties'] += 1

        # Calculate derived statistics
        for team in self.team_stats:
            stats = self.team_stats[team]
            if stats['games'] > 0:
                stats['ppg'] = stats['points_for'] / stats['games']
                stats['papg'] = stats['points_against'] / stats['games']
                stats['point_diff'] = stats['points_for'] - stats['points_against']
                stats['point_diff_per_game'] = stats['point_diff'] / stats['games']
                stats['win_pct'] = (stats['wins'] + 0.5 * stats['ties']) / stats['games']

    def calculate_elo_ratings(self, k_factor: float = 32, home_advantage: float = 100):
        """
        Calculate Elo ratings for all teams based on game results

        Args:
            k_factor: Elo K-factor (sensitivity to new results)
            home_advantage: Elo points advantage for home team
        """
        # Initialize all teams to 1500
        elo_ratings = defaultdict(lambda: 1500)

        # Process games chronologically
        sorted_games = sorted(self.games, key=lambda x: x.get('date', ''))

        for game in sorted_games:
            home = game['home_team']
            away = game['away_team']
            home_score = game['home_score']
            away_score = game['away_score']

            # Get current ratings
            home_elo = elo_ratings[home]
            away_elo = elo_ratings[away]

            # Calculate expected scores (with home advantage)
            home_expected = 1 / (1 + 10 ** ((away_elo - (home_elo + home_advantage)) / 400))
            away_expected = 1 - home_expected

            # Actual scores (1 for win, 0.5 for tie, 0 for loss)
            if home_score > away_score:
                home_actual = 1.0
                away_actual = 0.0
            elif away_score > home_score:
                home_actual = 0.0
                away_actual = 1.0
            else:
                home_actual = 0.5
                away_actual = 0.5

            # Update ratings
            home_new = home_elo + k_factor * (home_actual - home_expected)
            away_new = away_elo + k_factor * (away_actual - away_expected)

            elo_ratings[home] = home_new
            elo_ratings[away] = away_new

        # Store in team stats
        for team in elo_ratings:
            self.team_stats[team]['elo_rating'] = elo_ratings[team]

    def get_team_power_ratings(self) -> Dict[str, float]:
        """
        Get power ratings for all teams

        Returns:
            Dictionary of team names to power ratings (points per game adjusted)
        """
        ratings = {}
        for team, stats in self.team_stats.items():
            if stats['games'] > 0:
                # Power rating = offensive rating - defensive rating
                # Adjusted for league average
                league_avg = self._calculate_league_average_ppg()
                off_rating = stats['ppg']
                def_rating = stats['papg']
                power_rating = (off_rating - league_avg) - (def_rating - league_avg)
                ratings[team] = power_rating + league_avg

        return ratings

    def _calculate_league_average_ppg(self) -> float:
        """Calculate league-wide average points per game"""
        total_points = sum(stats['points_for'] for stats in self.team_stats.values())
        total_games = sum(stats['games'] for stats in self.team_stats.values())

        if total_games == 0:
            # Default averages by sport
            defaults = {'nfl': 22.8, 'nba': 115.0, 'mlb': 4.5, 'nhl': 3.0}
            return defaults.get(self.sport, 20.0)

        return total_points / total_games

    def get_matchup_projection(
        self,
        home_team: str,
        away_team: str,
        use_elo: bool = True
    ) -> Dict:
        """
        Project outcome of a matchup using team statistics

        Args:
            home_team: Home team name
            away_team: Away team name
            use_elo: Use Elo ratings if True, else use power ratings

        Returns:
            Projection dictionary with expected scores and probabilities
        """
        if home_team not in self.team_stats or away_team not in self.team_stats:
            raise ValueError(f"Team not found in database")

        home_stats = self.team_stats[home_team]
        away_stats = self.team_stats[away_team]

        if use_elo:
            # Use Elo ratings
            home_elo = home_stats['elo_rating']
            away_elo = away_stats['elo_rating']
            home_advantage = 65 if self.sport == 'nfl' else 100  # Elo points

            win_prob = 1 / (1 + 10 ** ((away_elo - (home_elo + home_advantage)) / 400))

            return {
                'home_team': home_team,
                'away_team': away_team,
                'home_win_probability': win_prob,
                'away_win_probability': 1 - win_prob,
                'home_elo': home_elo,
                'away_elo': away_elo,
                'method': 'elo'
            }
        else:
            # Use average scoring
            home_advantage_points = {
                'nfl': 2.5,
                'nba': 3.5,
                'mlb': 0.25,
                'nhl': 0.25
            }.get(self.sport, 2.0)

            home_expected = home_stats['ppg'] + home_advantage_points
            away_expected = away_stats['papg']  # Defensive rating

            # Simple projection
            return {
                'home_team': home_team,
                'away_team': away_team,
                'home_expected_score': home_expected,
                'away_expected_score': away_expected,
                'home_ppg': home_stats['ppg'],
                'away_ppg': away_stats['ppg'],
                'method': 'power_rating'
            }

    def export_team_stats(self, filepath: str, format: str = 'csv'):
        """
        Export team statistics to file

        Args:
            filepath: Output file path
            format: 'csv' or 'json'
        """
        # Prepare data
        data = []
        for team, stats in sorted(self.team_stats.items()):
            row = {'team': team}
            row.update(stats)
            data.append(row)

        if format == 'csv':
            if data:
                with open(filepath, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=data[0].keys())
                    writer.writeheader()
                    writer.writerows(data)
        elif format == 'json':
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)

    def get_team_rankings(self, sort_by: str = 'elo_rating') -> List[Tuple[str, float]]:
        """
        Get team rankings sorted by specified metric

        Args:
            sort_by: Metric to sort by (elo_rating, win_pct, ppg, etc.)

        Returns:
            List of (team_name, value) tuples sorted descending
        """
        rankings = []
        for team, stats in self.team_stats.items():
            if sort_by in stats:
                rankings.append((team, stats[sort_by]))

        return sorted(rankings, key=lambda x: x[1], reverse=True)

    def get_summary_stats(self) -> Dict:
        """Get summary statistics for the entire dataset"""
        return {
            'total_games': len(self.games),
            'total_teams': len(self.team_stats),
            'sport': self.sport,
            'avg_ppg': self._calculate_league_average_ppg(),
            'date_range': self._get_date_range(),
            'top_team': self.get_team_rankings('elo_rating')[0] if self.team_stats else None
        }

    def _get_date_range(self) -> Dict:
        """Get date range of games"""
        if not self.games:
            return {'earliest': None, 'latest': None}

        dates = [g['date'] for g in self.games if g.get('date')]
        if not dates:
            return {'earliest': None, 'latest': None}

        return {
            'earliest': min(dates),
            'latest': max(dates)
        }


if __name__ == '__main__':
    # Example usage
    print("Game Log Pipeline Library")
    print("=" * 70)

    # Create pipeline
    pipeline = GameLogPipeline('nfl')

    # Simulate some data
    sample_games = [
        {'date': '2024-09-08', 'home_team': 'Chiefs', 'away_team': 'Ravens', 'home_score': 27, 'away_score': 20},
        {'date': '2024-09-08', 'home_team': 'Bills', 'away_team': 'Jets', 'home_score': 24, 'away_score': 17},
        {'date': '2024-09-15', 'home_team': 'Ravens', 'away_team': 'Bengals', 'home_score': 31, 'away_score': 28},
    ]

    pipeline.games = sample_games

    # Calculate statistics
    pipeline.calculate_team_statistics()
    pipeline.calculate_elo_ratings()

    # Show results
    print("\nTeam Statistics:")
    for team, stats in sorted(pipeline.team_stats.items()):
        print(f"  {team}: {stats['wins']}-{stats['losses']}, "
              f"PPG: {stats['ppg']:.1f}, Elo: {stats['elo_rating']:.0f}")

    # Get matchup projection
    print("\nMatchup Projection:")
    proj = pipeline.get_matchup_projection('Chiefs', 'Ravens')
    print(f"  {proj['home_team']} vs {proj['away_team']}")
    print(f"  Win Probability: {proj['home_win_probability']*100:.1f}%")
