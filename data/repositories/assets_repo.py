from __future__ import annotations
from typing import Optional, List, Dict, Any
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from data.duckdb_connector import DuckDBConnection


# ────────────────────────────────────────────────────────────────
# Definición de tablas
# ────────────────────────────────────────────────────────────────
DDL_ASSETS = """
CREATE TABLE IF NOT EXISTS assets (
    asset_id INTEGER PRIMARY KEY,
    symbol TEXT UNIQUE NOT NULL,
    name TEXT,
    asset_type TEXT CHECK (asset_type IN ('stock','crypto','bond','etf')),
    currency TEXT DEFAULT 'USD'
);
"""

# ────────────────────────────────────────────────────────────────
# Repositorio de Activos
# ────────────────────────────────────────────────────────────────
class AssetsRepo:
    def __init__(self):
        self.db = DuckDBConnection(read_only=False)
        self.db.execute(DDL_ASSETS)

    def create_asset(self, symbol: str, name: str, asset_type: str = "stock", currency: str = "USD") -> int:
        next_id = self.db.df("SELECT COALESCE(MAX(asset_id),0)+1 AS nid FROM assets;").iloc[0]["nid"]
        self.db.execute(
            "INSERT INTO assets(asset_id, symbol, name, asset_type, currency) VALUES (?, ?, ?, ?, ?);",
            (int(next_id), symbol, name, asset_type, currency)
        )
        return int(next_id)

    def get_asset(self, symbol: str) -> Optional[Dict[str, Any]]:
        df = self.db.df("SELECT * FROM assets WHERE symbol=?;", (symbol,))
        return None if df.empty else df.iloc[0].to_dict()

    def get_all_assets(self) -> List[Dict[str, Any]]:
        df = self.db.df("SELECT * FROM assets;")
        return df.to_dict(orient="records")

    def delete_asset(self, symbol: str):
        self.db.execute("DELETE FROM assets WHERE symbol=?;", (symbol,))

    def close(self):
        self.db.close()
