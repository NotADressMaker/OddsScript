#!/usr/bin/env python3
"""
SportsBetLang Database - Easy betting data storage and tracking

Simple database for storing bets, predictions, games, and performance tracking.
Uses SQLite (no external dependencies) and works everywhere (desktop, Replit, etc.)
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Union


class BettingDatabase:
    """
    Easy-to-use database for sports betting tracking

    Features:
    - Store bets and track results
    - Save predictions and compare to actuals
    - Track historical games and data
    - Performance analytics
    - Bankroll tracking
    - Works on desktop, Replit, anywhere SQLite works

    Example:
        >>> db = BettingDatabase()
        >>> db.save_bet('Lakers vs Celtics', 100, 2.1, 0.58, sport='nba')
        >>> db.save_result(1, won=True)
        >>> stats = db.get_performance()
        >>> print(f"Win rate: {stats['win_rate']:.1%}")
    """

    def __init__(self, db_path: str = "betting.db"):
        """
        Initialize database

        Args:
            db_path: Path to SQLite database file (created if doesn't exist)
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        """Create database tables if they don't exist"""
        cursor = self.conn.cursor()

        # Bets table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                matchup TEXT NOT NULL,
                sport TEXT,
                bet_type TEXT,
                amount REAL NOT NULL,
                odds REAL NOT NULL,
                predicted_probability REAL,
                expected_value REAL,
                kelly_size REAL,
                result TEXT,
                profit REAL,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Predictions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                matchup TEXT NOT NULL,
                sport TEXT,
                prediction_type TEXT,
                predicted_value REAL,
                predicted_probability REAL,
                confidence REAL,
                model_used TEXT,
                features TEXT,
                actual_value REAL,
                correct INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Games table (historical data)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                sport TEXT NOT NULL,
                matchup TEXT NOT NULL,
                home_team TEXT,
                away_team TEXT,
                home_score INTEGER,
                away_score INTEGER,
                result TEXT,
                features TEXT,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Bankroll tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bankroll (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                amount REAL NOT NULL,
                change REAL,
                reason TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Models tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS models (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                sport TEXT NOT NULL,
                model_type TEXT NOT NULL,
                created_date TEXT NOT NULL,
                accuracy REAL,
                performance_metrics TEXT,
                features TEXT,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.conn.commit()

    # ========================================
    # Bet Management
    # ========================================

    def save_bet(self, matchup: str, amount: float, odds: float,
                 predicted_prob: float = None, sport: str = None,
                 bet_type: str = None, notes: str = None,
                 timestamp: str = None) -> int:
        """
        Save a bet to database

        Args:
            matchup: Game matchup (e.g., "Lakers vs Celtics")
            amount: Bet amount in dollars
            odds: Decimal odds
            predicted_prob: Your predicted win probability (0-1)
            sport: Sport name (nba, nfl, etc.)
            bet_type: Type of bet (moneyline, spread, total, etc.)
            notes: Optional notes
            timestamp: Optional timestamp (defaults to now)

        Returns:
            Bet ID

        Example:
            >>> db.save_bet('Lakers vs Celtics', 100, 2.1, 0.58, sport='nba')
            1
        """
        if timestamp is None:
            timestamp = datetime.now().isoformat()

        # Calculate Kelly and EV if probability provided
        kelly_size = None
        expected_value = None
        if predicted_prob is not None:
            from lib.simple_api import SBL
            kelly_size = SBL.kelly(predicted_prob, odds)
            expected_value = SBL.ev(predicted_prob, odds, amount)

        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO bets (timestamp, matchup, sport, bet_type, amount, odds,
                            predicted_probability, expected_value, kelly_size, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (timestamp, matchup, sport, bet_type, amount, odds,
              predicted_prob, expected_value, kelly_size, notes))

        self.conn.commit()
        return cursor.lastrowid

    def save_result(self, bet_id: int, won: bool, actual_odds: float = None):
        """
        Save bet result

        Args:
            bet_id: Bet ID from save_bet()
            won: True if bet won, False if lost
            actual_odds: Actual closing odds (if different)

        Example:
            >>> db.save_result(1, won=True)
        """
        cursor = self.conn.cursor()

        # Get bet details
        cursor.execute("SELECT amount, odds FROM bets WHERE id = ?", (bet_id,))
        row = cursor.fetchone()

        if row is None:
            raise ValueError(f"Bet ID {bet_id} not found")

        amount = row['amount']
        odds = actual_odds if actual_odds is not None else row['odds']

        # Calculate profit
        if won:
            profit = amount * (odds - 1)
            result = 'won'
        else:
            profit = -amount
            result = 'lost'

        # Update bet
        cursor.execute("""
            UPDATE bets
            SET result = ?, profit = ?
            WHERE id = ?
        """, (result, profit, bet_id))

        self.conn.commit()

    def get_bets(self, sport: str = None, result: str = None,
                 limit: int = None) -> List[Dict]:
        """
        Get bets from database

        Args:
            sport: Filter by sport
            result: Filter by result ('won', 'lost', 'pending')
            limit: Maximum number to return

        Returns:
            List of bet dictionaries

        Example:
            >>> bets = db.get_bets(sport='nba', result='won')
            >>> for bet in bets:
            ...     print(f"{bet['matchup']}: ${bet['profit']:.2f}")
        """
        query = "SELECT * FROM bets WHERE 1=1"
        params = []

        if sport is not None:
            query += " AND sport = ?"
            params.append(sport)

        if result is not None:
            if result == 'pending':
                query += " AND result IS NULL"
            else:
                query += " AND result = ?"
                params.append(result)

        query += " ORDER BY timestamp DESC"

        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)

        cursor = self.conn.cursor()
        cursor.execute(query, params)

        return [dict(row) for row in cursor.fetchall()]

    # ========================================
    # Predictions
    # ========================================

    def save_prediction(self, matchup: str, predicted_value: Union[int, float],
                       predicted_prob: float = None, sport: str = None,
                       prediction_type: str = None, model_used: str = None,
                       confidence: float = None, features: Dict = None,
                       timestamp: str = None) -> int:
        """
        Save a prediction

        Args:
            matchup: Game matchup
            predicted_value: Predicted outcome (1/0 for winner, number for total, etc.)
            predicted_prob: Probability of prediction
            sport: Sport name
            prediction_type: Type (game_winner, spread, total, etc.)
            model_used: Model name used for prediction
            confidence: Confidence level (0-1)
            features: Feature dict used for prediction
            timestamp: Optional timestamp

        Returns:
            Prediction ID

        Example:
            >>> db.save_prediction('Lakers vs Celtics', 1, 0.65, sport='nba',
            ...                    prediction_type='game_winner', model_used='NBA ML Model')
            1
        """
        if timestamp is None:
            timestamp = datetime.now().isoformat()

        features_json = json.dumps(features) if features else None

        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO predictions (timestamp, matchup, sport, prediction_type,
                                   predicted_value, predicted_probability, confidence,
                                   model_used, features)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (timestamp, matchup, sport, prediction_type, predicted_value,
              predicted_prob, confidence, model_used, features_json))

        self.conn.commit()
        return cursor.lastrowid

    def save_prediction_result(self, prediction_id: int, actual_value: Union[int, float]):
        """
        Save actual result for a prediction

        Args:
            prediction_id: Prediction ID
            actual_value: Actual outcome

        Example:
            >>> db.save_prediction_result(1, actual_value=1)  # Lakers won
        """
        cursor = self.conn.cursor()

        # Get prediction
        cursor.execute("""
            SELECT predicted_value, prediction_type
            FROM predictions WHERE id = ?
        """, (prediction_id,))
        row = cursor.fetchone()

        if row is None:
            raise ValueError(f"Prediction ID {prediction_id} not found")

        predicted_value = row['predicted_value']

        # Determine if correct
        correct = 1 if predicted_value == actual_value else 0

        # Update prediction
        cursor.execute("""
            UPDATE predictions
            SET actual_value = ?, correct = ?
            WHERE id = ?
        """, (actual_value, correct, prediction_id))

        self.conn.commit()

    def get_predictions(self, sport: str = None, model: str = None,
                       limit: int = None) -> List[Dict]:
        """Get predictions from database"""
        query = "SELECT * FROM predictions WHERE 1=1"
        params = []

        if sport is not None:
            query += " AND sport = ?"
            params.append(sport)

        if model is not None:
            query += " AND model_used = ?"
            params.append(model)

        query += " ORDER BY timestamp DESC"

        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)

        cursor = self.conn.cursor()
        cursor.execute(query, params)

        results = []
        for row in cursor.fetchall():
            pred = dict(row)
            # Parse features JSON
            if pred['features']:
                pred['features'] = json.loads(pred['features'])
            results.append(pred)

        return results

    # ========================================
    # Historical Games
    # ========================================

    def save_game(self, date: str, sport: str, matchup: str,
                  home_team: str = None, away_team: str = None,
                  home_score: int = None, away_score: int = None,
                  features: Dict = None, notes: str = None) -> int:
        """
        Save historical game data

        Args:
            date: Game date
            sport: Sport name
            matchup: Matchup description
            home_team: Home team name
            away_team: Away team name
            home_score: Home team score
            away_score: Away team score
            features: Game features/stats dict
            notes: Optional notes

        Returns:
            Game ID
        """
        # Determine result
        result = None
        if home_score is not None and away_score is not None:
            if home_score > away_score:
                result = 'home_win'
            elif away_score > home_score:
                result = 'away_win'
            else:
                result = 'tie'

        features_json = json.dumps(features) if features else None

        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO games (date, sport, matchup, home_team, away_team,
                             home_score, away_score, result, features, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (date, sport, matchup, home_team, away_team, home_score,
              away_score, result, features_json, notes))

        self.conn.commit()
        return cursor.lastrowid

    def get_games(self, sport: str = None, date_from: str = None,
                  date_to: str = None, limit: int = None) -> List[Dict]:
        """Get historical games"""
        query = "SELECT * FROM games WHERE 1=1"
        params = []

        if sport is not None:
            query += " AND sport = ?"
            params.append(sport)

        if date_from is not None:
            query += " AND date >= ?"
            params.append(date_from)

        if date_to is not None:
            query += " AND date <= ?"
            params.append(date_to)

        query += " ORDER BY date DESC"

        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)

        cursor = self.conn.cursor()
        cursor.execute(query, params)

        results = []
        for row in cursor.fetchall():
            game = dict(row)
            if game['features']:
                game['features'] = json.loads(game['features'])
            results.append(game)

        return results

    # ========================================
    # Bankroll Tracking
    # ========================================

    def update_bankroll(self, amount: float, change: float = None,
                       reason: str = None, timestamp: str = None):
        """
        Update bankroll

        Args:
            amount: New bankroll amount
            change: Change from previous (optional, calculated if not provided)
            reason: Reason for change
            timestamp: Optional timestamp
        """
        if timestamp is None:
            timestamp = datetime.now().isoformat()

        # Get previous bankroll
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT amount FROM bankroll
            ORDER BY timestamp DESC LIMIT 1
        """)
        row = cursor.fetchone()

        if change is None and row is not None:
            change = amount - row['amount']

        cursor.execute("""
            INSERT INTO bankroll (timestamp, amount, change, reason)
            VALUES (?, ?, ?, ?)
        """, (timestamp, amount, change, reason))

        self.conn.commit()

    def get_bankroll(self) -> Optional[float]:
        """Get current bankroll"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT amount FROM bankroll
            ORDER BY timestamp DESC LIMIT 1
        """)
        row = cursor.fetchone()
        return row['amount'] if row else None

    def get_bankroll_history(self, limit: int = None) -> List[Dict]:
        """Get bankroll history"""
        query = "SELECT * FROM bankroll ORDER BY timestamp DESC"

        if limit is not None:
            query += f" LIMIT {limit}"

        cursor = self.conn.cursor()
        cursor.execute(query)

        return [dict(row) for row in cursor.fetchall()]

    # ========================================
    # Performance Analytics
    # ========================================

    def get_performance(self, sport: str = None, days: int = None) -> Dict:
        """
        Get betting performance statistics

        Args:
            sport: Filter by sport
            days: Filter by last N days

        Returns:
            Dictionary with performance metrics

        Example:
            >>> stats = db.get_performance(sport='nba')
            >>> print(f"Win rate: {stats['win_rate']:.1%}")
            >>> print(f"ROI: {stats['roi']:.2%}")
            >>> print(f"Profit: ${stats['total_profit']:.2f}")
        """
        query = """
            SELECT
                COUNT(*) as total_bets,
                SUM(CASE WHEN result = 'won' THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN result = 'lost' THEN 1 ELSE 0 END) as losses,
                SUM(amount) as total_wagered,
                SUM(COALESCE(profit, 0)) as total_profit,
                AVG(CASE WHEN result = 'won' THEN odds ELSE NULL END) as avg_winning_odds,
                MAX(profit) as biggest_win,
                MIN(profit) as biggest_loss
            FROM bets
            WHERE result IS NOT NULL
        """
        params = []

        if sport is not None:
            query += " AND sport = ?"
            params.append(sport)

        if days is not None:
            query += " AND timestamp >= datetime('now', ? || ' days')"
            params.append(f'-{days}')

        cursor = self.conn.cursor()
        cursor.execute(query, params)
        row = cursor.fetchone()

        if row['total_bets'] == 0:
            return {
                'total_bets': 0,
                'wins': 0,
                'losses': 0,
                'win_rate': 0.0,
                'total_wagered': 0.0,
                'total_profit': 0.0,
                'roi': 0.0,
                'avg_winning_odds': 0.0,
                'biggest_win': 0.0,
                'biggest_loss': 0.0
            }

        total_bets = row['total_bets']
        wins = row['wins'] or 0
        total_wagered = row['total_wagered'] or 0
        total_profit = row['total_profit'] or 0

        win_rate = wins / total_bets if total_bets > 0 else 0
        roi = (total_profit / total_wagered) if total_wagered > 0 else 0

        return {
            'total_bets': total_bets,
            'wins': wins,
            'losses': row['losses'] or 0,
            'win_rate': win_rate,
            'total_wagered': total_wagered,
            'total_profit': total_profit,
            'roi': roi,
            'avg_winning_odds': row['avg_winning_odds'] or 0,
            'biggest_win': row['biggest_win'] or 0,
            'biggest_loss': row['biggest_loss'] or 0
        }

    def get_prediction_accuracy(self, sport: str = None, model: str = None) -> Dict:
        """
        Get prediction accuracy statistics

        Returns:
            Dictionary with accuracy metrics
        """
        query = """
            SELECT
                COUNT(*) as total_predictions,
                SUM(CASE WHEN correct = 1 THEN 1 ELSE 0 END) as correct_predictions,
                AVG(confidence) as avg_confidence
            FROM predictions
            WHERE actual_value IS NOT NULL
        """
        params = []

        if sport is not None:
            query += " AND sport = ?"
            params.append(sport)

        if model is not None:
            query += " AND model_used = ?"
            params.append(model)

        cursor = self.conn.cursor()
        cursor.execute(query, params)
        row = cursor.fetchone()

        total = row['total_predictions'] or 0
        correct = row['correct_predictions'] or 0

        accuracy = correct / total if total > 0 else 0

        return {
            'total_predictions': total,
            'correct_predictions': correct,
            'accuracy': accuracy,
            'avg_confidence': row['avg_confidence'] or 0
        }

    def print_performance(self, sport: str = None):
        """Print formatted performance report"""
        stats = self.get_performance(sport=sport)

        print("=" * 60)
        print("BETTING PERFORMANCE")
        if sport:
            print(f"Sport: {sport.upper()}")
        print("=" * 60)
        print()
        print(f"Total Bets:     {stats['total_bets']}")
        print(f"Wins:           {stats['wins']}")
        print(f"Losses:         {stats['losses']}")
        print(f"Win Rate:       {stats['win_rate']:.1%}")
        print()
        print(f"Total Wagered:  ${stats['total_wagered']:.2f}")
        print(f"Total Profit:   ${stats['total_profit']:.2f}")
        print(f"ROI:            {stats['roi']:.2%}")
        print()
        print(f"Biggest Win:    ${stats['biggest_win']:.2f}")
        print(f"Biggest Loss:   ${stats['biggest_loss']:.2f}")
        print(f"Avg Win Odds:   {stats['avg_winning_odds']:.2f}")
        print("=" * 60)

    def close(self):
        """Close database connection"""
        self.conn.close()


# Convenience function
def create_database(path: str = "betting.db") -> BettingDatabase:
    """
    Create a new betting database

    Args:
        path: Database file path

    Returns:
        BettingDatabase instance

    Example:
        >>> db = create_database()
        >>> db.save_bet('Lakers vs Celtics', 100, 2.1, 0.58)
    """
    return BettingDatabase(path)
