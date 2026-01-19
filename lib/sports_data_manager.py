#!/usr/bin/env python3
"""
Enhanced Sports Data Manager

Comprehensive data storage and retrieval system for sports betting analytics.
Builds on existing storage backends with enhanced schemas and unified interface.
"""

import sqlite3
import json
import csv
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum


class Sport(Enum):
    """Supported sports"""
    NFL = "nfl"
    NBA = "nba"
    MLB = "mlb"
    NHL = "nhl"
    CFB = "cfb"
    CBB = "cbb"
    SOCCER = "soccer"
    HORSE_RACING = "horse_racing"


@dataclass
class Team:
    """Team data model"""
    id: Optional[int] = None
    name: str = ""
    sport: str = ""
    league: str = ""
    conference: str = ""
    division: str = ""
    elo_rating: Optional[float] = None
    home_record: str = "0-0"
    away_record: str = "0-0"
    created_at: Optional[str] = None


@dataclass
class Game:
    """Game data model"""
    id: Optional[int] = None
    sport: str = ""
    league: str = ""
    date: str = ""
    season: str = ""
    week: Optional[int] = None
    home_team: str = ""
    away_team: str = ""
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    home_odds: Optional[float] = None
    away_odds: Optional[float] = None
    spread: Optional[float] = None
    total: Optional[float] = None
    completed: bool = False
    overtime: bool = False
    playoff: bool = False
    created_at: Optional[str] = None


@dataclass
class OddsSnapshot:
    """Historical odds snapshot"""
    id: Optional[int] = None
    game_id: int = 0
    sportsbook: str = ""
    timestamp: str = ""
    home_moneyline: Optional[float] = None
    away_moneyline: Optional[float] = None
    spread_line: Optional[float] = None
    spread_odds_home: Optional[float] = None
    spread_odds_away: Optional[float] = None
    total_line: Optional[float] = None
    over_odds: Optional[float] = None
    under_odds: Optional[float] = None
    created_at: Optional[str] = None


@dataclass
class BettingRecord:
    """Enhanced betting record"""
    id: Optional[int] = None
    game_id: Optional[int] = None
    date: str = ""
    sport: str = ""
    league: str = ""
    description: str = ""
    bet_type: str = ""  # spread, moneyline, total, prop
    selection: str = ""  # team or over/under
    odds: float = 0.0
    stake: float = 0.0
    opening_odds: Optional[float] = None
    closing_odds: Optional[float] = None
    clv: Optional[float] = None  # Closing line value
    result: Optional[str] = None  # win, loss, push
    profit: Optional[float] = None
    units: Optional[float] = None
    sportsbook: str = ""
    notes: str = ""
    created_at: Optional[str] = None
    settled_at: Optional[str] = None


class SportsDataManager:
    """
    Comprehensive sports data manager with enhanced storage capabilities

    Features:
    - Multi-sport data storage
    - Historical odds tracking
    - Team and game management
    - Betting record management
    - Data import/export
    - Advanced querying and aggregation
    """

    def __init__(self, db_path: str = "sportsdata.db"):
        """
        Initialize data manager

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn = None
        self._init_database()

    def _init_database(self):
        """Initialize database with enhanced schema"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

        cursor = self.conn.cursor()

        # Teams table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS teams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                sport TEXT NOT NULL,
                league TEXT,
                conference TEXT,
                division TEXT,
                elo_rating REAL,
                home_record TEXT DEFAULT '0-0',
                away_record TEXT DEFAULT '0-0',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(name, sport, league)
            )
        ''')

        # Games table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sport TEXT NOT NULL,
                league TEXT,
                date TEXT NOT NULL,
                season TEXT,
                week INTEGER,
                home_team TEXT NOT NULL,
                away_team TEXT NOT NULL,
                home_score INTEGER,
                away_score INTEGER,
                home_odds REAL,
                away_odds REAL,
                spread REAL,
                total REAL,
                completed BOOLEAN DEFAULT 0,
                overtime BOOLEAN DEFAULT 0,
                playoff BOOLEAN DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Odds snapshots table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS odds_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id INTEGER NOT NULL,
                sportsbook TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                home_moneyline REAL,
                away_moneyline REAL,
                spread_line REAL,
                spread_odds_home REAL,
                spread_odds_away REAL,
                total_line REAL,
                over_odds REAL,
                under_odds REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (game_id) REFERENCES games(id)
            )
        ''')

        # Enhanced bets table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id INTEGER,
                date TEXT NOT NULL,
                sport TEXT NOT NULL,
                league TEXT,
                description TEXT,
                bet_type TEXT NOT NULL,
                selection TEXT NOT NULL,
                odds REAL NOT NULL,
                stake REAL NOT NULL,
                opening_odds REAL,
                closing_odds REAL,
                clv REAL,
                result TEXT,
                profit REAL,
                units REAL,
                sportsbook TEXT,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                settled_at TEXT,
                FOREIGN KEY (game_id) REFERENCES games(id)
            )
        ''')

        # Team statistics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS team_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id INTEGER NOT NULL,
                season TEXT NOT NULL,
                games_played INTEGER DEFAULT 0,
                wins INTEGER DEFAULT 0,
                losses INTEGER DEFAULT 0,
                ties INTEGER DEFAULT 0,
                points_for REAL DEFAULT 0,
                points_against REAL DEFAULT 0,
                home_wins INTEGER DEFAULT 0,
                home_losses INTEGER DEFAULT 0,
                away_wins INTEGER DEFAULT 0,
                away_losses INTEGER DEFAULT 0,
                streak TEXT,
                last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (team_id) REFERENCES teams(id),
                UNIQUE(team_id, season)
            )
        ''')

        # Create indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_games_date ON games(date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_games_sport ON games(sport)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_games_teams ON games(home_team, away_team)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_odds_game ON odds_snapshots(game_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_odds_timestamp ON odds_snapshots(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_bets_date ON bets(date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_bets_sport ON bets(sport)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_bets_result ON bets(result)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_teams_sport ON teams(sport)')

        self.conn.commit()

    # Team Management
    def add_team(self, team: Team) -> int:
        """Add or update a team"""
        cursor = self.conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO teams
            (name, sport, league, conference, division, elo_rating, home_record, away_record)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (team.name, team.sport, team.league, team.conference,
              team.division, team.elo_rating, team.home_record, team.away_record))

        self.conn.commit()
        return cursor.lastrowid

    def get_team(self, name: str, sport: str, league: Optional[str] = None) -> Optional[Team]:
        """Get team by name and sport"""
        cursor = self.conn.cursor()

        if league:
            cursor.execute(
                'SELECT * FROM teams WHERE name = ? AND sport = ? AND league = ?',
                (name, sport, league)
            )
        else:
            cursor.execute(
                'SELECT * FROM teams WHERE name = ? AND sport = ?',
                (name, sport)
            )

        row = cursor.fetchone()
        if row:
            return Team(**dict(row))
        return None

    def list_teams(self, sport: Optional[str] = None, league: Optional[str] = None) -> List[Team]:
        """List teams with optional filters"""
        cursor = self.conn.cursor()

        query = 'SELECT * FROM teams WHERE 1=1'
        params = []

        if sport:
            query += ' AND sport = ?'
            params.append(sport)

        if league:
            query += ' AND league = ?'
            params.append(league)

        query += ' ORDER BY name'

        cursor.execute(query, params)
        return [Team(**dict(row)) for row in cursor.fetchall()]

    # Game Management
    def add_game(self, game: Game) -> int:
        """Add a game"""
        cursor = self.conn.cursor()

        cursor.execute('''
            INSERT INTO games
            (sport, league, date, season, week, home_team, away_team,
             home_score, away_score, home_odds, away_odds, spread, total,
             completed, overtime, playoff)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (game.sport, game.league, game.date, game.season, game.week,
              game.home_team, game.away_team, game.home_score, game.away_score,
              game.home_odds, game.away_odds, game.spread, game.total,
              game.completed, game.overtime, game.playoff))

        self.conn.commit()
        return cursor.lastrowid

    def update_game_result(self, game_id: int, home_score: int, away_score: int,
                          overtime: bool = False):
        """Update game with final score"""
        cursor = self.conn.cursor()

        cursor.execute('''
            UPDATE games
            SET home_score = ?, away_score = ?, completed = 1, overtime = ?
            WHERE id = ?
        ''', (home_score, away_score, overtime, game_id))

        self.conn.commit()

    def get_game(self, game_id: int) -> Optional[Game]:
        """Get game by ID"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM games WHERE id = ?', (game_id,))

        row = cursor.fetchone()
        if row:
            return Game(**dict(row))
        return None

    def list_games(self, sport: Optional[str] = None, start_date: Optional[str] = None,
                   end_date: Optional[str] = None, completed: Optional[bool] = None,
                   limit: int = 100, offset: int = 0) -> List[Game]:
        """List games with filters"""
        cursor = self.conn.cursor()

        query = 'SELECT * FROM games WHERE 1=1'
        params = []

        if sport:
            query += ' AND sport = ?'
            params.append(sport)

        if start_date:
            query += ' AND date >= ?'
            params.append(start_date)

        if end_date:
            query += ' AND date <= ?'
            params.append(end_date)

        if completed is not None:
            query += ' AND completed = ?'
            params.append(completed)

        query += ' ORDER BY date DESC, id DESC LIMIT ? OFFSET ?'
        params.extend([limit, offset])

        cursor.execute(query, params)
        return [Game(**dict(row)) for row in cursor.fetchall()]

    # Odds Management
    def add_odds_snapshot(self, odds: OddsSnapshot) -> int:
        """Add odds snapshot"""
        cursor = self.conn.cursor()

        cursor.execute('''
            INSERT INTO odds_snapshots
            (game_id, sportsbook, timestamp, home_moneyline, away_moneyline,
             spread_line, spread_odds_home, spread_odds_away, total_line,
             over_odds, under_odds)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (odds.game_id, odds.sportsbook, odds.timestamp, odds.home_moneyline,
              odds.away_moneyline, odds.spread_line, odds.spread_odds_home,
              odds.spread_odds_away, odds.total_line, odds.over_odds, odds.under_odds))

        self.conn.commit()
        return cursor.lastrowid

    def get_odds_history(self, game_id: int, sportsbook: Optional[str] = None) -> List[OddsSnapshot]:
        """Get odds history for a game"""
        cursor = self.conn.cursor()

        if sportsbook:
            cursor.execute('''
                SELECT * FROM odds_snapshots
                WHERE game_id = ? AND sportsbook = ?
                ORDER BY timestamp
            ''', (game_id, sportsbook))
        else:
            cursor.execute('''
                SELECT * FROM odds_snapshots
                WHERE game_id = ?
                ORDER BY timestamp
            ''', (game_id,))

        return [OddsSnapshot(**dict(row)) for row in cursor.fetchall()]

    def get_closing_odds(self, game_id: int, sportsbook: Optional[str] = None) -> Optional[OddsSnapshot]:
        """Get closing odds (most recent) for a game"""
        cursor = self.conn.cursor()

        if sportsbook:
            cursor.execute('''
                SELECT * FROM odds_snapshots
                WHERE game_id = ? AND sportsbook = ?
                ORDER BY timestamp DESC LIMIT 1
            ''', (game_id, sportsbook))
        else:
            cursor.execute('''
                SELECT * FROM odds_snapshots
                WHERE game_id = ?
                ORDER BY timestamp DESC LIMIT 1
            ''', (game_id,))

        row = cursor.fetchone()
        if row:
            return OddsSnapshot(**dict(row))
        return None

    # Betting Records
    def add_bet(self, bet: BettingRecord) -> int:
        """Add a betting record"""
        cursor = self.conn.cursor()

        cursor.execute('''
            INSERT INTO bets
            (game_id, date, sport, league, description, bet_type, selection,
             odds, stake, opening_odds, closing_odds, clv, result, profit,
             units, sportsbook, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (bet.game_id, bet.date, bet.sport, bet.league, bet.description,
              bet.bet_type, bet.selection, bet.odds, bet.stake, bet.opening_odds,
              bet.closing_odds, bet.clv, bet.result, bet.profit, bet.units,
              bet.sportsbook, bet.notes))

        self.conn.commit()
        return cursor.lastrowid

    def settle_bet(self, bet_id: int, result: str, profit: float):
        """Settle a bet with result"""
        cursor = self.conn.cursor()

        cursor.execute('''
            UPDATE bets
            SET result = ?, profit = ?, settled_at = ?
            WHERE id = ?
        ''', (result, profit, datetime.now().isoformat(), bet_id))

        self.conn.commit()

    def list_bets(self, sport: Optional[str] = None, result: Optional[str] = None,
                  start_date: Optional[str] = None, end_date: Optional[str] = None,
                  limit: int = 100, offset: int = 0) -> List[BettingRecord]:
        """List betting records with filters"""
        cursor = self.conn.cursor()

        query = 'SELECT * FROM bets WHERE 1=1'
        params = []

        if sport:
            query += ' AND sport = ?'
            params.append(sport)

        if result:
            query += ' AND result = ?'
            params.append(result)

        if start_date:
            query += ' AND date >= ?'
            params.append(start_date)

        if end_date:
            query += ' AND date <= ?'
            params.append(end_date)

        query += ' ORDER BY date DESC, id DESC LIMIT ? OFFSET ?'
        params.extend([limit, offset])

        cursor.execute(query, params)
        return [BettingRecord(**dict(row)) for row in cursor.fetchall()]

    def get_betting_stats(self, sport: Optional[str] = None,
                         bet_type: Optional[str] = None) -> Dict:
        """Get betting statistics"""
        cursor = self.conn.cursor()

        query = 'SELECT * FROM bets WHERE result IS NOT NULL'
        params = []

        if sport:
            query += ' AND sport = ?'
            params.append(sport)

        if bet_type:
            query += ' AND bet_type = ?'
            params.append(bet_type)

        cursor.execute(query, params)
        bets = cursor.fetchall()

        if not bets:
            return {
                'total_bets': 0,
                'wins': 0,
                'losses': 0,
                'pushes': 0,
                'win_rate': 0.0,
                'total_staked': 0.0,
                'total_profit': 0.0,
                'roi': 0.0,
                'units_won': 0.0
            }

        total_bets = len(bets)
        wins = sum(1 for bet in bets if bet['result'] == 'win')
        losses = sum(1 for bet in bets if bet['result'] == 'loss')
        pushes = sum(1 for bet in bets if bet['result'] == 'push')
        total_staked = sum(bet['stake'] for bet in bets)
        total_profit = sum(bet['profit'] or 0 for bet in bets)
        units_won = sum(bet['units'] or 0 for bet in bets)

        win_rate = (wins / (wins + losses)) * 100 if (wins + losses) > 0 else 0.0
        roi = (total_profit / total_staked) * 100 if total_staked > 0 else 0.0

        return {
            'total_bets': total_bets,
            'wins': wins,
            'losses': losses,
            'pushes': pushes,
            'win_rate': win_rate,
            'total_staked': total_staked,
            'total_profit': total_profit,
            'roi': roi,
            'units_won': units_won
        }

    # Data Import/Export
    def import_games_from_csv(self, csv_path: str, sport: str,
                             league: Optional[str] = None) -> int:
        """Import games from CSV file"""
        count = 0

        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)

            for row in reader:
                game = Game(
                    sport=sport,
                    league=league or row.get('league', ''),
                    date=row['date'],
                    season=row.get('season', ''),
                    week=int(row['week']) if row.get('week') else None,
                    home_team=row['home_team'],
                    away_team=row['away_team'],
                    home_score=int(row['home_score']) if row.get('home_score') else None,
                    away_score=int(row['away_score']) if row.get('away_score') else None,
                    completed=bool(row.get('home_score'))
                )

                self.add_game(game)
                count += 1

        return count

    def export_games_to_csv(self, csv_path: str, sport: Optional[str] = None,
                           start_date: Optional[str] = None,
                           end_date: Optional[str] = None):
        """Export games to CSV file"""
        games = self.list_games(sport=sport, start_date=start_date,
                               end_date=end_date, limit=10000)

        if not games:
            return 0

        with open(csv_path, 'w', newline='') as f:
            fieldnames = ['id', 'sport', 'league', 'date', 'season', 'week',
                         'home_team', 'away_team', 'home_score', 'away_score',
                         'home_odds', 'away_odds', 'spread', 'total',
                         'completed', 'overtime', 'playoff']

            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for game in games:
                writer.writerow(asdict(game))

        return len(games)

    def export_bets_to_csv(self, csv_path: str, sport: Optional[str] = None):
        """Export bets to CSV file"""
        bets = self.list_bets(sport=sport, limit=10000)

        if not bets:
            return 0

        with open(csv_path, 'w', newline='') as f:
            fieldnames = ['id', 'game_id', 'date', 'sport', 'league',
                         'description', 'bet_type', 'selection', 'odds', 'stake',
                         'opening_odds', 'closing_odds', 'clv', 'result',
                         'profit', 'units', 'sportsbook', 'notes']

            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for bet in bets:
                writer.writerow(asdict(bet))

        return len(bets)

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

    def __del__(self):
        """Cleanup on deletion"""
        self.close()


if __name__ == '__main__':
    # Example usage
    print("Sports Data Manager - Enhanced Storage System")
    print("=" * 70)

    # Initialize manager
    manager = SportsDataManager("test_sportsdata.db")

    # Add teams
    print("\n1. Adding Teams...")
    chiefs = Team(
        name="Kansas City Chiefs",
        sport="nfl",
        league="NFL",
        conference="AFC",
        division="West",
        elo_rating=1650.0
    )
    manager.add_team(chiefs)
    print(f"Added: {chiefs.name}")

    # Add game
    print("\n2. Adding Game...")
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
    game_id = manager.add_game(game)
    print(f"Added game ID: {game_id}")

    # Add odds snapshot
    print("\n3. Adding Odds Snapshot...")
    odds = OddsSnapshot(
        game_id=game_id,
        sportsbook="DraftKings",
        timestamp=datetime.now().isoformat(),
        home_moneyline=-175,
        away_moneyline=+150,
        spread_line=-3.5,
        spread_odds_home=-110,
        spread_odds_away=-110,
        total_line=47.5,
        over_odds=-110,
        under_odds=-110
    )
    manager.add_odds_snapshot(odds)
    print("Added odds snapshot")

    # Add bet
    print("\n4. Adding Bet...")
    bet = BettingRecord(
        game_id=game_id,
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
    bet_id = manager.add_bet(bet)
    print(f"Added bet ID: {bet_id}")

    # List games
    print("\n5. Listing Games...")
    games = manager.list_games(sport="nfl", limit=5)
    print(f"Found {len(games)} NFL games")

    # Get stats
    print("\n6. Betting Statistics...")
    stats = manager.get_betting_stats(sport="nfl")
    print(f"Total Bets: {stats['total_bets']}")
    print(f"Win Rate: {stats['win_rate']:.1f}%")
    print(f"ROI: {stats['roi']:.1f}%")

    manager.close()
    print("\nDatabase closed.")
