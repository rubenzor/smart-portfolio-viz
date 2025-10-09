from __future__ import annotations
from typing import Optional, List, Dict, Any
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from data.duckdb_connector import DuckDBConnection


# ────────────────────────────────────────────────────────────────
# Definición de tablas
# ────────────────────────────────────────────────────────────────
DDL_PORTFOLIOS = """
CREATE TABLE IF NOT EXISTS portfolios (
    portfolio_id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

DDL_PORTFOLIO_ASSETS = """
CREATE TABLE IF NOT EXISTS portfolio_assets (
    portfolio_id INTEGER,
    asset_id INTEGER,
    weight FLOAT DEFAULT 0.0,
    PRIMARY KEY (portfolio_id, asset_id)
);
"""

# ────────────────────────────────────────────────────────────────
# Repositorio de Portfolios
# ────────────────────────────────────────────────────────────────
class PortfoliosRepo:
    def __init__(self):
        self.db = DuckDBConnection(read_only=False)
        self.db.execute(DDL_PORTFOLIOS)
        self.db.execute(DDL_PORTFOLIO_ASSETS)

    def create_portfolio(self, user_id: int, name: str) -> int:
        next_id = self.db.df("SELECT COALESCE(MAX(portfolio_id),0)+1 AS nid FROM portfolios;").iloc[0]["nid"]
        self.db.execute(
            "INSERT INTO portfolios(portfolio_id, user_id, name) VALUES (?, ?, ?);",
            (int(next_id), user_id, name)
        )
        return int(next_id)

    def get_user_portfolios(self, user_id: int) -> List[Dict[str, Any]]:
        df = self.db.df("SELECT * FROM portfolios WHERE user_id=?;", (user_id,))
        return df.to_dict(orient="records")

    def get_portfolio(self, portfolio_id: int) -> Optional[Dict[str, Any]]:
        df = self.db.df("SELECT * FROM portfolios WHERE portfolio_id=?;", (portfolio_id,))
        return None if df.empty else df.iloc[0].to_dict()

    def delete_portfolio(self, portfolio_id: int):
        self.db.execute("DELETE FROM portfolio_assets WHERE portfolio_id=?;", (portfolio_id,))
        self.db.execute("DELETE FROM portfolios WHERE portfolio_id=?;", (portfolio_id,))

    def add_asset(self, portfolio_id: int, asset_id: int, weight: float):
        self.db.execute(
            "INSERT OR REPLACE INTO portfolio_assets(portfolio_id, asset_id, weight) VALUES (?, ?, ?);",
            (portfolio_id, asset_id, weight)
        )

    def remove_asset(self, portfolio_id: int, asset_id: int):
        self.db.execute("DELETE FROM portfolio_assets WHERE portfolio_id=? AND asset_id=?;", (portfolio_id, asset_id))

    def get_assets(self, portfolio_id: int) -> List[Dict[str, Any]]:
        df = self.db.df("SELECT * FROM portfolio_assets WHERE portfolio_id=?;", (portfolio_id,))
        return df.to_dict(orient="records")

    def close(self):
        self.db.close()
