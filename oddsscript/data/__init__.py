"""
Data storage layer for OddsScript.

Provides abstracted storage backends (CSV, SQLite) with a unified interface.
"""

from oddsscript.data.storage import (
    StorageBackend,
    create_storage
)

from oddsscript.data.csv_adapter import CSVStorage
from oddsscript.data.sqlite_adapter import SQLiteStorage

__all__ = [
    'StorageBackend',
    'create_storage',
    'CSVStorage',
    'SQLiteStorage',
]
