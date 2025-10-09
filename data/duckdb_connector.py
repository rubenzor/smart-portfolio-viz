from __future__ import annotations
import duckdb
from pathlib import Path
from typing import Optional, Iterable

DB_PATH = Path("data_store/smartviz.duckdb")

class DuckDBConnection:
    """Manejador de conexión simple a una sola base DuckDB."""

    def __init__(self, read_only: bool = False):
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        self.con = duckdb.connect(database=str(DB_PATH), read_only=read_only)

    def execute(self, sql: str, params: Optional[Iterable] = None):
        return self.con.execute(sql, params or [])

    def df(self, sql: str, params: Optional[Iterable] = None):
        return self.execute(sql, params).df()

    def close(self):
        self.con.close()
