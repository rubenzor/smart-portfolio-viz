from __future__ import annotations
from typing import List, Dict, Optional
from data.repositories.portfolios_repo import PortfoliosRepo
from data.repositories.assets_repo import AssetsRepo
import pandas as pd

class PortfolioManager:
    """
    Clase de alto nivel para manejar la creación, modificación y análisis básico de carteras.
    """

    def __init__(self):
        self.portfolios_repo = PortfoliosRepo()
        self.assets_repo = AssetsRepo()

    # ────────────────────────────────────────────────────────────────
    # CREACIÓN Y GESTIÓN DE CARTERAS
    # ────────────────────────────────────────────────────────────────
    def create_portfolio(self, user_id: int, name: str) -> int:
        """
        Crea una nueva cartera para un usuario.
        """
        return self.portfolios_repo.create_portfolio(user_id, name)

    def delete_portfolio(self, portfolio_id: int):
        """
        Elimina una cartera y todos sus activos asociados.
        """
        self.portfolios_repo.delete_portfolio(portfolio_id)

    def list_user_portfolios(self, user_id: int) -> List[Dict]:
        """
        Devuelve todas las carteras asociadas a un usuario.
        """
        return self.portfolios_repo.get_user_portfolios(user_id)

    # ────────────────────────────────────────────────────────────────
    # GESTIÓN DE ACTIVOS DENTRO DE UNA CARTERA
    # ────────────────────────────────────────────────────────────────
    def add_asset_to_portfolio(self, portfolio_id: int, symbol: str, name: str,
                               weight: float, asset_type: str = "stock", currency: str = "USD"):
        """
        Añade un activo (por símbolo) a una cartera específica.
        Si el activo no existe en la base de datos de activos, lo crea automáticamente.
        """
        existing = self.assets_repo.get_asset(symbol)
        if existing is None:
            asset_id = self.assets_repo.create_asset(symbol, name, asset_type, currency)
        else:
            asset_id = existing["asset_id"]

        self.portfolios_repo.add_asset(portfolio_id, asset_id, weight)

    def remove_asset_from_portfolio(self, portfolio_id: int, symbol: str):
        """
        Elimina un activo de una cartera.
        """
        asset = self.assets_repo.get_asset(symbol)
        if not asset:
            raise ValueError(f"Asset {symbol} not found.")
        self.portfolios_repo.remove_asset(portfolio_id, asset["asset_id"])

    def get_portfolio_assets(self, portfolio_id: int) -> pd.DataFrame:
        """
        Devuelve los activos de una cartera en formato DataFrame (útil para análisis posterior).
        """
        assets = self.portfolios_repo.get_assets(portfolio_id)
        if not assets:
            return pd.DataFrame(columns=["asset_id", "symbol", "weight"])

        all_assets = {a["asset_id"]: a for a in self.assets_repo.get_all_assets()}
        data = []
        for item in assets:
            a = all_assets.get(item["asset_id"])
            if a:
                data.append({
                    "symbol": a["symbol"],
                    "name": a["name"],
                    "type": a["asset_type"],
                    "currency": a["currency"],
                    "weight": item["weight"]
                })
        return pd.DataFrame(data)

    # ────────────────────────────────────────────────────────────────
    # ANÁLISIS BÁSICO
    # ────────────────────────────────────────────────────────────────
    def normalize_weights(self, portfolio_id: int):
        """
        Normaliza los pesos de los activos para que sumen 1.
        """
        assets = self.portfolios_repo.get_assets(portfolio_id)
        if not assets:
            return

        total_weight = sum(a["weight"] for a in assets)
        if total_weight == 0:
            raise ValueError("Total weight is zero. Cannot normalize.")

        for a in assets:
            new_weight = a["weight"] / total_weight
            self.portfolios_repo.add_asset(portfolio_id, a["asset_id"], new_weight)

    def compute_portfolio_summary(self, portfolio_id: int) -> Dict[str, float]:
        """
        Devuelve un resumen básico de la cartera: nº activos, peso total y diversificación.
        """
        df = self.get_portfolio_assets(portfolio_id)
        if df.empty:
            return {"n_assets": 0, "total_weight": 0.0, "diversification": 0.0}

        total_weight = df["weight"].sum()
        n_assets = len(df)
        diversification = (1 / n_assets) if n_assets > 0 else 0

        return {
            "n_assets": int(n_assets),
            "total_weight": round(float(total_weight), 4),
            "diversification": round(float(diversification), 4)
        }

    # ────────────────────────────────────────────────────────────────
    # LIMPIEZA DE CONEXIONES
    # ────────────────────────────────────────────────────────────────
    def close(self):
        self.portfolios_repo.close()
        self.assets_repo.close()



