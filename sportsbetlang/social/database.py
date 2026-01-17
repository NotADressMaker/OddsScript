"""
Database Models for Social Features

SQLite database schema for user-generated content, predictions, discussions, and social interactions.
"""

import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import contextmanager


class SocialDatabase:
    """Database manager for social features."""

    def __init__(self, db_path: str = "sportsbetlang_social.db"):
        """Initialize database connection."""
        self.db_path = db_path
        self.init_database()

    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def init_database(self):
        """Initialize database tables."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    display_name TEXT,
                    bio TEXT,
                    avatar_url TEXT,
                    is_analyst BOOLEAN DEFAULT 0,
                    analyst_tier TEXT,  -- 'expert', 'pro', 'amateur'
                    verified BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # User stats table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_stats (
                    user_id INTEGER PRIMARY KEY,
                    total_predictions INTEGER DEFAULT 0,
                    correct_predictions INTEGER DEFAULT 0,
                    total_units_wagered REAL DEFAULT 0,
                    total_profit_loss REAL DEFAULT 0,
                    win_rate REAL DEFAULT 0,
                    roi REAL DEFAULT 0,
                    current_streak INTEGER DEFAULT 0,
                    best_streak INTEGER DEFAULT 0,
                    followers_count INTEGER DEFAULT 0,
                    following_count INTEGER DEFAULT 0,
                    reputation_score INTEGER DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)

            # Predictions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    sport TEXT NOT NULL,
                    game_id TEXT,
                    prediction_type TEXT NOT NULL,  -- 'player_prop', 'game_outcome', 'spread', 'total'
                    description TEXT NOT NULL,
                    pick TEXT NOT NULL,
                    odds REAL,
                    stake REAL,
                    confidence INTEGER,  -- 1-5 stars
                    reasoning TEXT,
                    status TEXT DEFAULT 'pending',  -- 'pending', 'won', 'lost', 'void'
                    result REAL,  -- profit/loss
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    game_date TIMESTAMP,
                    settled_at TIMESTAMP,
                    likes_count INTEGER DEFAULT 0,
                    comments_count INTEGER DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)

            # Discussion threads table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS discussions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    category TEXT,  -- 'general', 'strategy', 'picks', 'analysis'
                    sport TEXT,
                    tags TEXT,  -- JSON array of tags
                    is_pinned BOOLEAN DEFAULT 0,
                    is_locked BOOLEAN DEFAULT 0,
                    views_count INTEGER DEFAULT 0,
                    likes_count INTEGER DEFAULT 0,
                    comments_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)

            # Comments table (for both predictions and discussions)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS comments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    parent_type TEXT NOT NULL,  -- 'prediction', 'discussion', 'comment'
                    parent_id INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    likes_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)

            # Follows table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS follows (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    follower_id INTEGER NOT NULL,
                    following_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (follower_id) REFERENCES users(id),
                    FOREIGN KEY (following_id) REFERENCES users(id),
                    UNIQUE(follower_id, following_id)
                )
            """)

            # Likes table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS likes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    target_type TEXT NOT NULL,  -- 'prediction', 'discussion', 'comment'
                    target_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    UNIQUE(user_id, target_type, target_id)
                )
            """)

            # Leaderboard snapshots table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS leaderboard_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    period TEXT NOT NULL,  -- 'daily', 'weekly', 'monthly', 'all_time'
                    sport TEXT,
                    snapshot_date DATE NOT NULL,
                    rankings TEXT NOT NULL,  -- JSON array of user rankings
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Activity feed table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS activities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    activity_type TEXT NOT NULL,  -- 'prediction', 'discussion', 'follow', 'comment'
                    activity_data TEXT,  -- JSON data
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)

            # Create indexes for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_predictions_user ON predictions(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_predictions_status ON predictions(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_predictions_sport ON predictions(sport)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_discussions_user ON discussions(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_discussions_category ON discussions(category)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_comments_parent ON comments(parent_type, parent_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_follows_follower ON follows(follower_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_follows_following ON follows(following_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_activities_user ON activities(user_id)")

            conn.commit()

    def execute_query(self, query: str, params: tuple = ()) -> List[Dict]:
        """Execute a query and return results as list of dicts."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def execute_update(self, query: str, params: tuple = ()) -> int:
        """Execute an update/insert query and return affected rows."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.lastrowid

    def clear_all_data(self):
        """Clear all data from database (for testing)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            tables = ['activities', 'leaderboard_snapshots', 'likes', 'follows',
                     'comments', 'discussions', 'predictions', 'user_stats', 'users']
            for table in tables:
                cursor.execute(f"DELETE FROM {table}")
            conn.commit()


# Singleton instance
_db_instance = None

def get_database(db_path: str = "sportsbetlang_social.db") -> SocialDatabase:
    """Get or create database instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = SocialDatabase(db_path)
    return _db_instance
