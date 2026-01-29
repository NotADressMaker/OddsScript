"""
Data storage layer for SportsBetLang.

Provides abstracted storage backends (CSV, SQLite) with a unified interface.
"""

from sportsbetlang.data.storage import (
    StorageBackend,
    create_storage
)

from sportsbetlang.data.csv_adapter import CSVStorage
from sportsbetlang.data.sqlite_adapter import SQLiteStorage
from sportsbetlang.data.dataset_storage import DatasetStorage

__all__ = [
    'StorageBackend',
    'create_storage',
    'CSVStorage',
    'SQLiteStorage',
    'DatasetStorage',
]
