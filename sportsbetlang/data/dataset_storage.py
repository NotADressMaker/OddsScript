"""
Dataset storage utilities for uploads.

Stores dataset metadata in SQLite and persists files on disk with optional gzip
compression for efficient storage.
"""

import gzip
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class DatasetStorage:
    """Handles saving dataset uploads and metadata."""

    def __init__(self, db_path: Path, storage_dir: Path):
        if isinstance(db_path, str):
            db_path = Path(db_path)
        if isinstance(storage_dir, str):
            storage_dir = Path(storage_dir)

        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path
        self.conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self) -> None:
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS datasets (
                id TEXT PRIMARY KEY,
                name TEXT,
                dataset_type TEXT,
                original_filename TEXT,
                content_type TEXT,
                storage_path TEXT NOT NULL,
                size_bytes INTEGER NOT NULL,
                compressed INTEGER NOT NULL DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_datasets_type ON datasets(dataset_type)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_datasets_created ON datasets(created_at)
        """)
        self.conn.commit()

    def save_upload(
        self,
        upload_file,
        dataset_type: str,
        name: Optional[str] = None,
        compress: bool = True,
        chunk_size: int = 1024 * 1024
    ) -> Dict:
        dataset_id = str(uuid.uuid4())
        original_filename = upload_file.filename or "dataset"
        content_type = getattr(upload_file, "content_type", None)

        ext = Path(original_filename).suffix or ".data"
        file_stem = f"{dataset_id}{ext}"
        storage_path = self.storage_dir / file_stem
        compressed_flag = 0

        should_compress = compress and (content_type or "").startswith("text/")
        if compress:
            if ext.lower() in {".csv", ".json", ".ndjson", ".txt"}:
                should_compress = True

        if should_compress:
            storage_path = storage_path.with_suffix(storage_path.suffix + ".gz")
            compressed_flag = 1

        buffer = bytearray(chunk_size)
        view = memoryview(buffer)
        if should_compress:
            with gzip.open(storage_path, "wb") as output:
                while True:
                    bytes_read = upload_file.file.readinto(view)
                    if not bytes_read:
                        break
                    output.write(view[:bytes_read])
        else:
            with open(storage_path, "wb") as output:
                while True:
                    bytes_read = upload_file.file.readinto(view)
                    if not bytes_read:
                        break
                    output.write(view[:bytes_read])
        size_bytes = storage_path.stat().st_size

        record = {
            "id": dataset_id,
            "name": name or Path(original_filename).stem,
            "dataset_type": dataset_type,
            "original_filename": original_filename,
            "content_type": content_type,
            "storage_path": str(storage_path),
            "size_bytes": size_bytes,
            "compressed": compressed_flag,
            "created_at": datetime.now().isoformat()
        }

        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO datasets
            (id, name, dataset_type, original_filename, content_type, storage_path,
             size_bytes, compressed, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record["id"],
            record["name"],
            record["dataset_type"],
            record["original_filename"],
            record["content_type"],
            record["storage_path"],
            record["size_bytes"],
            record["compressed"],
            record["created_at"]
        ))
        self.conn.commit()

        return record

    def list_datasets(self, dataset_type: Optional[str] = None) -> List[Dict]:
        cursor = self.conn.cursor()
        query = "SELECT * FROM datasets"
        params = []
        if dataset_type:
            query += " WHERE dataset_type = ?"
            params.append(dataset_type)
        query += " ORDER BY created_at DESC"
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def get_dataset(self, dataset_id: str) -> Optional[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM datasets WHERE id = ?", (dataset_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
