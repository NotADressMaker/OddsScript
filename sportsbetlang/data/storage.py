"""
Storage abstraction layer for SportsBetLang.

Provides a unified interface for different storage backends (CSV, SQLite).
Allows switching between backends without changing code.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path


class StorageBackend(ABC):
    """Abstract storage interface"""

    @abstractmethod
    def save_bet(self, bet: Dict[str, Any]) -> str:
        """
        Save bet and return ID

        Args:
            bet: Bet dictionary with keys: date, sport, description, odds, stake, etc.

        Returns:
            Unique bet ID
        """
        pass

    @abstractmethod
    def get_bet(self, bet_id: str) -> Optional[Dict[str, Any]]:
        """
        Get bet by ID

        Args:
            bet_id: Unique bet identifier

        Returns:
            Bet dictionary or None if not found
        """
        pass

    @abstractmethod
    def update_bet(self, bet_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update bet with new data

        Args:
            bet_id: Unique bet identifier
            updates: Dictionary of fields to update

        Returns:
            True if successful, False if bet not found
        """
        pass

    @abstractmethod
    def list_bets(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List bets with optional filters

        Args:
            filters: Optional filter dict (e.g., {'sport': 'nfl', 'result': 'win'})
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of bet dictionaries
        """
        pass

    @abstractmethod
    def delete_bet(self, bet_id: str) -> bool:
        """
        Delete bet

        Args:
            bet_id: Unique bet identifier

        Returns:
            True if successful, False if not found
        """
        pass

    @abstractmethod
    def save_line_movement(self, line: Dict[str, Any]) -> str:
        """
        Save line movement data

        Args:
            line: Line movement dict with keys: game_id, timestamp, sportsbook, line, odds, etc.

        Returns:
            Unique line movement ID
        """
        pass

    @abstractmethod
    def get_line_history(
        self,
        game_id: str,
        sportsbook: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get line movement history for a game

        Args:
            game_id: Unique game identifier
            sportsbook: Optional sportsbook filter
            start_time: Optional start timestamp
            end_time: Optional end timestamp

        Returns:
            List of line movement dictionaries, sorted by timestamp
        """
        pass

    @abstractmethod
    def get_stats(
        self,
        sport: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get betting statistics

        Args:
            sport: Optional sport filter
            start_date: Optional start date (YYYY-MM-DD)
            end_date: Optional end date (YYYY-MM-DD)

        Returns:
            Dictionary with stats: total_bets, wins, losses, roi, etc.
        """
        pass

    @abstractmethod
    def clear_all_data(self) -> bool:
        """
        Clear all data (USE WITH CAUTION!)

        Returns:
            True if successful
        """
        pass


def create_storage(backend: str = 'csv', **kwargs) -> StorageBackend:
    """
    Factory function to create storage backend

    Args:
        backend: Backend type ('csv' or 'sqlite')
        **kwargs: Backend-specific arguments

    Returns:
        StorageBackend instance

    Examples:
        >>> storage = create_storage('csv')
        >>> storage = create_storage('sqlite', db_path='/path/to/db.sqlite')
    """
    if backend == 'csv':
        from sportsbetlang.data.csv_adapter import CSVStorage
        from sportsbetlang.config import get_config

        data_dir = kwargs.get('data_dir', get_config().data_directory)
        return CSVStorage(data_dir)

    elif backend == 'sqlite':
        from sportsbetlang.data.sqlite_adapter import SQLiteStorage
        from sportsbetlang.config import get_config

        config = get_config()
        db_path = kwargs.get('db_path', config.data_directory / config.db_filename)
        return SQLiteStorage(db_path)

    else:
        raise ValueError(f"Unknown storage backend: {backend}")
