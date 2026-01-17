"""
SQLite storage backend for SportsBetLang.

Provides better performance for large datasets compared to CSV.
"""

import sqlite3
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from sportsbetlang.data.storage import StorageBackend


class SQLiteStorage(StorageBackend):
    """SQLite-based storage implementation"""

    def __init__(self, db_path: Path):
        """
        Initialize SQLite storage

        Args:
            db_path: Path to SQLite database file
        """
        if isinstance(db_path, str):
            db_path = Path(db_path)

        # Ensure directory exists
        db_path.parent.mkdir(parents=True, exist_ok=True)

        self.db_path = db_path
        self.conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Return dict-like rows

        self._create_tables()

    def _create_tables(self):
        """Create database schema if it doesn't exist"""
        cursor = self.conn.cursor()

        # Bets table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bets (
                id TEXT PRIMARY KEY,
                date TEXT NOT NULL,
                sport TEXT,
                description TEXT,
                odds REAL,
                stake REAL,
                result TEXT,
                profit REAL,
                clv REAL,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Line movements table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS line_movements (
                id TEXT PRIMARY KEY,
                game_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                sportsbook TEXT,
                bet_type TEXT,
                line REAL,
                odds REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indexes for performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_bets_date ON bets(date)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_bets_sport ON bets(sport)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_bets_result ON bets(result)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_lines_game ON line_movements(game_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_lines_timestamp ON line_movements(timestamp)
        """)

        self.conn.commit()

    def save_bet(self, bet: Dict[str, Any]) -> str:
        """Save bet and return ID"""
        bet_id = str(uuid.uuid4())

        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO bets
            (id, date, sport, description, odds, stake, result, profit, clv, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            bet_id,
            bet.get('date'),
            bet.get('sport'),
            bet.get('description'),
            bet.get('odds'),
            bet.get('stake'),
            bet.get('result'),
            bet.get('profit'),
            bet.get('clv'),
            bet.get('notes')
        ))

        self.conn.commit()
        return bet_id

    def get_bet(self, bet_id: str) -> Optional[Dict[str, Any]]:
        """Get bet by ID"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM bets WHERE id = ?", (bet_id,))

        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

    def update_bet(self, bet_id: str, updates: Dict[str, Any]) -> bool:
        """Update bet with new data"""
        if not updates:
            return False

        # Build SET clause
        set_clause = ', '.join(f"{key} = ?" for key in updates.keys())
        values = list(updates.values())
        values.append(bet_id)

        cursor = self.conn.cursor()
        cursor.execute(
            f"UPDATE bets SET {set_clause} WHERE id = ?",
            values
        )

        self.conn.commit()
        return cursor.rowcount > 0

    def list_bets(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List bets with optional filters"""
        query = "SELECT * FROM bets"
        params = []

        # Build WHERE clause
        if filters:
            where_clauses = []
            for key, value in filters.items():
                where_clauses.append(f"{key} = ?")
                params.append(value)

            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)

        # Add ORDER BY
        query += " ORDER BY date DESC, created_at DESC"

        # Add LIMIT and OFFSET
        if limit:
            query += f" LIMIT {limit}"
        if offset:
            query += f" OFFSET {offset}"

        cursor = self.conn.cursor()
        cursor.execute(query, params)

        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def delete_bet(self, bet_id: str) -> bool:
        """Delete bet"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM bets WHERE id = ?", (bet_id,))

        self.conn.commit()
        return cursor.rowcount > 0

    def save_line_movement(self, line: Dict[str, Any]) -> str:
        """Save line movement data"""
        line_id = str(uuid.uuid4())

        timestamp = line.get('timestamp', datetime.now().isoformat())

        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO line_movements
            (id, game_id, timestamp, sportsbook, bet_type, line, odds)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            line_id,
            line.get('game_id'),
            timestamp,
            line.get('sportsbook'),
            line.get('bet_type'),
            line.get('line'),
            line.get('odds')
        ))

        self.conn.commit()
        return line_id

    def get_line_history(
        self,
        game_id: str,
        sportsbook: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get line movement history for a game"""
        query = "SELECT * FROM line_movements WHERE game_id = ?"
        params = [game_id]

        if sportsbook:
            query += " AND sportsbook = ?"
            params.append(sportsbook)

        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time.isoformat())

        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time.isoformat())

        query += " ORDER BY timestamp ASC"

        cursor = self.conn.cursor()
        cursor.execute(query, params)

        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_stats(
        self,
        sport: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get betting statistics"""
        # Build WHERE clause
        where_clauses = []
        params = []

        if sport:
            where_clauses.append("sport = ?")
            params.append(sport)

        if start_date:
            where_clauses.append("date >= ?")
            params.append(start_date)

        if end_date:
            where_clauses.append("date <= ?")
            params.append(end_date)

        where_clause = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""

        cursor = self.conn.cursor()

        # Total bets
        cursor.execute(f"SELECT COUNT(*) FROM bets{where_clause}", params)
        total_bets = cursor.fetchone()[0]

        # Settled bets
        settled_where = where_clause + (" AND " if where_clause else " WHERE ") + "result IS NOT NULL AND result != ''"
        cursor.execute(f"SELECT COUNT(*) FROM bets{settled_where}", params)
        settled = cursor.fetchone()[0]

        # Win/Loss/Push counts
        cursor.execute(f"SELECT COUNT(*) FROM bets{settled_where} AND result = 'win'", params)
        wins = cursor.fetchone()[0]

        cursor.execute(f"SELECT COUNT(*) FROM bets{settled_where} AND result = 'loss'", params)
        losses = cursor.fetchone()[0]

        cursor.execute(f"SELECT COUNT(*) FROM bets{settled_where} AND result = 'push'", params)
        pushes = cursor.fetchone()[0]

        # Financial stats
        cursor.execute(f"SELECT SUM(profit), SUM(stake) FROM bets{settled_where}", params)
        row = cursor.fetchone()
        total_profit = row[0] or 0
        total_staked = row[1] or 0

        # CLV stats
        cursor.execute(
            f"SELECT AVG(clv) FROM bets{settled_where} AND clv IS NOT NULL",
            params
        )
        avg_clv = cursor.fetchone()[0] or 0

        # Calculate derived stats
        roi = (total_profit / total_staked * 100) if total_staked > 0 else 0
        win_rate = (wins / settled * 100) if settled > 0 else 0

        return {
            'total_bets': total_bets,
            'settled': settled,
            'pending': total_bets - settled,
            'wins': wins,
            'losses': losses,
            'pushes': pushes,
            'win_rate': win_rate,
            'total_profit': total_profit,
            'total_staked': total_staked,
            'roi': roi,
            'avg_clv': avg_clv,
            'sport': sport,
            'start_date': start_date,
            'end_date': end_date
        }

    def clear_all_data(self) -> bool:
        """Clear all data (USE WITH CAUTION!)"""
        cursor = self.conn.cursor()

        cursor.execute("DELETE FROM bets")
        cursor.execute("DELETE FROM line_movements")

        self.conn.commit()
        return True

    def close(self):
        """Close database connection"""
        self.conn.close()

    def __del__(self):
        """Ensure connection is closed"""
        try:
            self.conn.close()
        except:
            pass
