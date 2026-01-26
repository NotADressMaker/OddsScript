#!/usr/bin/env python3
"""
Test suite for Sports Data Manager
"""

import unittest
import sys
import os
import tempfile
from pathlib import Path

# Add lib directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))

from sports_data_manager import (
    SportsDataManager, Team, Game, OddsSnapshot, BettingRecord
)


class TestSportsDataManager(unittest.TestCase):
    """Test sports data manager functionality"""

    def setUp(self):
        """Create temporary database for testing"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.manager = SportsDataManager(self.temp_db.name)

    def tearDown(self):
        """Clean up temporary database"""
        self.manager.close()
        os.unlink(self.temp_db.name)

    def test_add_and_get_team(self):
        """Test adding and retrieving a team"""
        team = Team(
            name="Kansas City Chiefs",
            sport="nfl",
            league="NFL",
            conference="AFC",
            division="West",
            elo_rating=1650.0
        )

        team_id = self.manager.add_team(team)
        self.assertIsNotNone(team_id)

        # Retrieve team
        retrieved = self.manager.get_team("Kansas City Chiefs", "nfl", "NFL")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "Kansas City Chiefs")
        self.assertEqual(retrieved.elo_rating, 1650.0)

    def test_list_teams(self):
        """Test listing teams with filters"""
        # Add multiple teams
        teams = [
            Team(name="Chiefs", sport="nfl", league="NFL"),
            Team(name="Bills", sport="nfl", league="NFL"),
            Team(name="Lakers", sport="nba", league="NBA")
        ]

        for team in teams:
            self.manager.add_team(team)

        # List all NFL teams
        nfl_teams = self.manager.list_teams(sport="nfl")
        self.assertEqual(len(nfl_teams), 2)

        # List all NBA teams
        nba_teams = self.manager.list_teams(sport="nba")
        self.assertEqual(len(nba_teams), 1)

    def test_add_and_get_game(self):
        """Test adding and retrieving a game"""
        game = Game(
            sport="nfl",
            league="NFL",
            date="2024-01-15",
            season="2023",
            week=18,
            home_team="Kansas City Chiefs",
            away_team="Buffalo Bills",
            spread=-3.5,
            total=47.5
        )

        game_id = self.manager.add_game(game)
        self.assertIsNotNone(game_id)

        # Retrieve game
        retrieved = self.manager.get_game(game_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.home_team, "Kansas City Chiefs")
        self.assertEqual(retrieved.spread, -3.5)

    def test_update_game_result(self):
        """Test updating game with final score"""
        game = Game(
            sport="nfl",
            league="NFL",
            date="2024-01-15",
            season="2023",
            week=18,
            home_team="Kansas City Chiefs",
            away_team="Buffalo Bills"
        )

        game_id = self.manager.add_game(game)

        # Update with result
        self.manager.update_game_result(game_id, 27, 24, overtime=False)

        # Verify update
        updated = self.manager.get_game(game_id)
        self.assertEqual(updated.home_score, 27)
        self.assertEqual(updated.away_score, 24)
        self.assertTrue(updated.completed)

    def test_list_games_with_filters(self):
        """Test listing games with various filters"""
        # Add multiple games
        games = [
            Game(sport="nfl", league="NFL", date="2024-01-15", home_team="Chiefs", away_team="Bills"),
            Game(sport="nfl", league="NFL", date="2024-01-16", home_team="Cowboys", away_team="Eagles"),
            Game(sport="nba", league="NBA", date="2024-01-15", home_team="Lakers", away_team="Warriors")
        ]

        for game in games:
            self.manager.add_game(game)

        # Test sport filter
        nfl_games = self.manager.list_games(sport="nfl")
        self.assertEqual(len(nfl_games), 2)

        # Test date filter
        jan15_games = self.manager.list_games(start_date="2024-01-15", end_date="2024-01-15")
        self.assertEqual(len(jan15_games), 2)

    def test_add_and_get_odds_snapshot(self):
        """Test adding and retrieving odds snapshots"""
        # First add a game
        game = Game(
            sport="nfl",
            league="NFL",
            date="2024-01-15",
            home_team="Chiefs",
            away_team="Bills"
        )
        game_id = self.manager.add_game(game)

        # Add odds snapshot
        odds = OddsSnapshot(
            game_id=game_id,
            sportsbook="DraftKings",
            timestamp="2024-01-15T10:00:00",
            home_moneyline=-175,
            away_moneyline=+150,
            spread_line=-3.5,
            total_line=47.5
        )

        odds_id = self.manager.add_odds_snapshot(odds)
        self.assertIsNotNone(odds_id)

        # Get odds history
        history = self.manager.get_odds_history(game_id)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].sportsbook, "DraftKings")

    def test_get_closing_odds(self):
        """Test getting closing odds (most recent)"""
        game = Game(sport="nfl", league="NFL", date="2024-01-15", home_team="A", away_team="B")
        game_id = self.manager.add_game(game)

        # Add multiple odds snapshots
        for i in range(3):
            odds = OddsSnapshot(
                game_id=game_id,
                sportsbook="DraftKings",
                timestamp=f"2024-01-15T{10+i}:00:00",
                home_moneyline=-150 - (i * 10)
            )
            self.manager.add_odds_snapshot(odds)

        # Get closing odds
        closing = self.manager.get_closing_odds(game_id)
        self.assertIsNotNone(closing)
        self.assertEqual(closing.home_moneyline, -170)  # Last one added

    def test_add_and_settle_bet(self):
        """Test adding and settling a bet"""
        bet = BettingRecord(
            date="2024-01-15",
            sport="nfl",
            league="NFL",
            description="Chiefs -3.5",
            bet_type="spread",
            selection="Kansas City Chiefs",
            odds=-110,
            stake=110.0,
            sportsbook="DraftKings"
        )

        bet_id = self.manager.add_bet(bet)
        self.assertIsNotNone(bet_id)

        # Settle bet as win
        profit = 100.0
        self.manager.settle_bet(bet_id, "win", profit)

        # Verify settlement
        bets = self.manager.list_bets(limit=1)
        self.assertEqual(len(bets), 1)
        self.assertEqual(bets[0].result, "win")
        self.assertEqual(bets[0].profit, 100.0)

    def test_list_bets_with_filters(self):
        """Test listing bets with filters"""
        # Add multiple bets
        bets = [
            BettingRecord(date="2024-01-15", sport="nfl", bet_type="spread",
                         selection="Chiefs", odds=-110, stake=110.0, result="win", profit=100.0),
            BettingRecord(date="2024-01-16", sport="nfl", bet_type="total",
                         selection="Over", odds=-110, stake=110.0, result="loss", profit=-110.0),
            BettingRecord(date="2024-01-17", sport="nba", bet_type="moneyline",
                         selection="Lakers", odds=-150, stake=150.0, result="win", profit=100.0)
        ]

        for bet in bets:
            self.manager.add_bet(bet)

        # Test sport filter
        nfl_bets = self.manager.list_bets(sport="nfl")
        self.assertEqual(len(nfl_bets), 2)

        # Test result filter
        wins = self.manager.list_bets(result="win")
        self.assertEqual(len(wins), 2)

        # Test date filter
        jan15_bets = self.manager.list_bets(start_date="2024-01-15", end_date="2024-01-15")
        self.assertEqual(len(jan15_bets), 1)

    def test_get_betting_stats(self):
        """Test betting statistics calculation"""
        # Add test bets
        bets = [
            BettingRecord(date="2024-01-15", sport="nfl", bet_type="spread",
                         selection="A", odds=-110, stake=110.0, result="win", profit=100.0, units=1.0),
            BettingRecord(date="2024-01-16", sport="nfl", bet_type="spread",
                         selection="B", odds=-110, stake=110.0, result="loss", profit=-110.0, units=-1.0),
            BettingRecord(date="2024-01-17", sport="nfl", bet_type="spread",
                         selection="C", odds=-110, stake=110.0, result="win", profit=100.0, units=1.0),
            BettingRecord(date="2024-01-18", sport="nfl", bet_type="spread",
                         selection="D", odds=-110, stake=110.0, result="push", profit=0.0, units=0.0),
        ]

        for bet in bets:
            self.manager.add_bet(bet)

        # Get overall stats
        stats = self.manager.get_betting_stats(sport="nfl")

        self.assertEqual(stats['total_bets'], 4)
        self.assertEqual(stats['wins'], 2)
        self.assertEqual(stats['losses'], 1)
        self.assertEqual(stats['pushes'], 1)
        self.assertAlmostEqual(stats['win_rate'], 66.67, places=1)  # 2 wins / (2 wins + 1 loss)
        self.assertEqual(stats['total_staked'], 440.0)
        self.assertEqual(stats['total_profit'], 90.0)
        self.assertAlmostEqual(stats['roi'], 20.45, places=1)
        self.assertEqual(stats['units_won'], 1.0)

    def test_get_betting_stats_by_bet_type(self):
        """Test betting statistics by bet type"""
        # Add bets of different types
        bets = [
            BettingRecord(date="2024-01-15", sport="nfl", bet_type="spread",
                         selection="A", odds=-110, stake=110.0, result="win", profit=100.0),
            BettingRecord(date="2024-01-16", sport="nfl", bet_type="moneyline",
                         selection="B", odds=-150, stake=150.0, result="loss", profit=-150.0)
        ]

        for bet in bets:
            self.manager.add_bet(bet)

        # Get spread stats
        spread_stats = self.manager.get_betting_stats(bet_type="spread")
        self.assertEqual(spread_stats['total_bets'], 1)
        self.assertEqual(spread_stats['wins'], 1)

        # Get moneyline stats
        ml_stats = self.manager.get_betting_stats(bet_type="moneyline")
        self.assertEqual(ml_stats['total_bets'], 1)
        self.assertEqual(ml_stats['losses'], 1)


class TestDataModels(unittest.TestCase):
    """Test data model classes"""

    def test_team_model(self):
        """Test Team dataclass"""
        team = Team(
            name="Chiefs",
            sport="nfl",
            league="NFL",
            conference="AFC",
            division="West"
        )

        self.assertEqual(team.name, "Chiefs")
        self.assertEqual(team.sport, "nfl")

    def test_game_model(self):
        """Test Game dataclass"""
        game = Game(
            sport="nfl",
            league="NFL",
            date="2024-01-15",
            home_team="Chiefs",
            away_team="Bills"
        )

        self.assertEqual(game.sport, "nfl")
        self.assertEqual(game.home_team, "Chiefs")
        self.assertFalse(game.completed)

    def test_betting_record_model(self):
        """Test BettingRecord dataclass"""
        bet = BettingRecord(
            date="2024-01-15",
            sport="nfl",
            bet_type="spread",
            selection="Chiefs -3.5",
            odds=-110,
            stake=110.0
        )

        self.assertEqual(bet.sport, "nfl")
        self.assertEqual(bet.stake, 110.0)
        self.assertIsNone(bet.result)


def run_tests():
    """Run all tests"""
    unittest.main()


if __name__ == '__main__':
    run_tests()
