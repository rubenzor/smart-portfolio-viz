from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from datetime import datetime, timezone

from data.repositories.portfolios_repo import PortfoliosRepo
from data.repositories.assets_repo import AssetsRepo
from data.duckdb_connector import DuckDBConnection

try:
    import yfinance as yf
except ImportError:
    yf = None


@dataclass
class PerfConfig:
    lookback: str = "2y"
    benchmark: str = "^GSPC"
    rf_annual: float = 0.0
    trading_days: int = 252


class PriceLoader:
    @staticmethod
    def fetch_adj_close(symbols: List[str], period: str) -> pd.DataFrame:
        if yf is None:
            raise RuntimeError("Instala yfinance (`pip install yfinance`) o usa tu lector propio.")
        data = yf.download(symbols, period=period, auto_adjust=True, progress=False)
        if isinstance(data, pd.DataFrame) and "Adj Close" in data.columns:
            df = data["Adj Close"].copy()
        else:
            if isinstance(data, pd.DataFrame) and "Close" in data.columns:
                df = data["Close"].copy()
            else:
                df = data.copy()
        if isinstance(df, pd.Series):
            df = df.to_frame()
        return df.dropna(how="all")


class PerformanceAnalyzer:
    """
    Métricas de performance para renta variable: Sharpe, Sortino, Alpha, Tracking Error, retorno acumulado.
    Persiste resultados en DuckDB (tabla performance_metrics).
    """

    DDL_PERF = """
    CREATE TABLE IF NOT EXISTS performance_metrics (
        portfolio_id INTEGER,
        as_of TIMESTAMP,
        window TEXT,
        benchmark TEXT,
        metric TEXT,
        value DOUBLE
    );
    """

    def __init__(self, config: Optional[PerfConfig] = None):
        self.config = config or PerfConfig()
        self.port_repo = PortfoliosRepo()
        self.assets_repo = AssetsRepo()
        self.db = DuckDBConnection(read_only=False)
        self.db.execute(self.DDL_PERF)

    # ───────────────────────── helpers
    def _portfolio_symbols_and_weights(self, portfolio_id: int) -> Tuple[List[str], List[float]]:
        pa = self.port_repo.get_assets(portfolio_id)
        if not pa:
            raise ValueError("La cartera no tiene activos.")
        all_assets = {a["asset_id"]: a for a in self.assets_repo.get_all_assets()}
        symbols, weights = [], []
        for row in pa:
            asset = all_assets.get(row["asset_id"])
            if asset is None:
                continue
            if asset["asset_type"] not in ("stock", "etf"):
                continue
            symbols.append(asset["symbol"])
            weights.append(float(row["weight"]))
        if not symbols:
            raise ValueError("No hay activos de tipo 'stock'/'etf' en la cartera.")
        wsum = sum(weights)
        if wsum <= 0:
            raise ValueError("La suma de pesos es cero o negativa.")
        weights = [w / wsum for w in weights]
        return symbols, weights

    def _portfolio_series(self, portfolio_id: int) -> Tuple[pd.Series, pd.Series]:
        symbols, weights = self._portfolio_symbols_and_weights(portfolio_id)
        prices = PriceLoader.fetch_adj_close(symbols, self.config.lookback).dropna(how="any")
        rets = prices.pct_change().dropna()
        w = np.array(weights)
        if rets.shape[1] == 1:
            port_ret = rets.iloc[:, 0]
        else:
            port_ret = pd.Series(rets.values @ w, index=rets.index, name="portfolio_ret")

        bench_prices = PriceLoader.fetch_adj_close([self.config.benchmark], self.config.lookback)
        bench_ret = bench_prices.pct_change().dropna().iloc[:, 0]
        df = pd.concat([port_ret, bench_ret], axis=1, join="inner")
        df.columns = ["portfolio", "benchmark"]
        return df["portfolio"], df["benchmark"]

    # ───────────────────────── métricas
    def _annualize_mean(self, daily_mean: float) -> float:
        return (1 + daily_mean) ** self.config.trading_days - 1

    def _annualize_vol(self, daily_std: float) -> float:
        return daily_std * np.sqrt(self.config.trading_days)

    def _downside_std(self, series: pd.Series) -> float:
        return series[series < 0].std(ddof=1)

    def _alpha_tracking(self, port: pd.Series, bench: pd.Series, rf_daily: float) -> Tuple[float, float]:
        # alpha & tracking error anuales
        excess_p = port - rf_daily
        excess_b = bench - rf_daily
        diff = excess_p - excess_b
        te_daily = diff.std(ddof=1)
        te_annual = self._annualize_vol(te_daily)
        # alpha aproximada (media de excesos relativos anualizada)
        alpha_daily = (excess_p - excess_b).mean()
        alpha_annual = self._annualize_mean(alpha_daily)
        return float(alpha_annual), float(te_annual)

    # ───────────────────────── API pública
    def analyze_portfolio(self, portfolio_id: int) -> Dict[str, float]:
        port, bench = self._portfolio_series(portfolio_id)
        rf_daily = (1 + self.config.rf_annual) ** (1 / self.config.trading_days) - 1

        mu_p_d = float(port.mean())
        sd_p_d = float(port.std(ddof=1))
        mu_b_d = float(bench.mean())
        sd_b_d = float(bench.std(ddof=1))

        sharpe = (mu_p_d - rf_daily) / sd_p_d if sd_p_d > 0 else np.nan
        sortino = (mu_p_d - rf_daily) / (self._downside_std(port) or np.nan)

        cumret = float((1 + port).prod() - 1)
        cumret_b = float((1 + bench).prod() - 1)

        alpha, tracking_error = self._alpha_tracking(port, bench, rf_daily)

        out = {
            "mean_daily": mu_p_d,
            "vol_daily": sd_p_d,
            "sharpe": sharpe,
            "sortino": sortino,
            "cum_return": cumret,
            "cum_return_benchmark": cumret_b,
            "alpha_annual": alpha,
            "tracking_error_annual": tracking_error,
        }

        as_of = datetime.now(timezone.utc).isoformat()
        for k, v in out.items():
            self.db.execute(
                "INSERT INTO performance_metrics(portfolio_id, as_of, window, benchmark, metric, value) VALUES (?,?,?,?,?,?);",
                (portfolio_id, as_of, self.config.lookback, self.config.benchmark, k, float(v) if v is not None else None)
            )
        return out

    def close(self):
        self.port_repo.close()
        self.assets_repo.close()
        self.db.close()
