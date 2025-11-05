from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from datetime import datetime, timezone

# ── repos propios
from data.repositories.portfolios_repo import PortfoliosRepo
from data.repositories.assets_repo import AssetsRepo
from data.duckdb_connector import DuckDBConnection

# ── precio: yfinance (opcional, pero recomendado)
try:
    import yfinance as yf
except ImportError as e:
    yf = None


@dataclass
class RiskConfig:
    lookback: str = "2y"      # ventana temporal, formato yfinance (e.g., '1y','2y','6mo')
    benchmark: str = "^GSPC"  # S&P 500 como predeterminado
    rf_annual: float = 0.0    # tasa libre de riesgo anual (0 por defecto)
    trading_days: int = 252   # convención anual


class PriceLoader:
    """
    Descarga precios Ajusted Close para una lista de símbolos usando yfinance.
    Puedes reemplazar esta clase por un loader que lea de tus tablas 'price_data' si lo prefieres.
    """
    @staticmethod
    def fetch_adj_close(symbols: List[str], period: str) -> pd.DataFrame:
        if yf is None:
            raise RuntimeError(
                "yfinance no está instalado. Ejecuta: `pip install yfinance` "
                "o sustituye PriceLoader por un lector de tu propia base de datos."
            )
        data = yf.download(symbols, period=period, auto_adjust=True, progress=False)
        # yfinance devuelve multi-index si hay varias columnas; normalizamos a DataFrame (Adj Close ya auto_adjust)
        if isinstance(data, pd.DataFrame) and "Adj Close" in data.columns:
            df = data["Adj Close"].copy()
        else:
            # cuando auto_adjust=True, la columna principal es 'Close'
            if isinstance(data, pd.DataFrame) and "Close" in data.columns:
                df = data["Close"].copy()
            else:
                df = data.copy()
        if isinstance(df, pd.Series):
            df = df.to_frame()
        return df.dropna(how="all")


class RiskAnalyzer:
    """
    Calcula métricas de riesgo de una cartera de renta variable agregando los activos con sus pesos.
    Persiste resultados en DuckDB (tabla risk_metrics).
    """

    DDL_RISK = """
    CREATE TABLE IF NOT EXISTS risk_metrics (
        portfolio_id INTEGER,
        as_of TIMESTAMP,
        window TEXT,
        benchmark TEXT,
        metric TEXT,
        value DOUBLE
    );
    """

    def __init__(self, config: Optional[RiskConfig] = None):
        self.config = config or RiskConfig()
        self.port_repo = PortfoliosRepo()
        self.assets_repo = AssetsRepo()
        self.db = DuckDBConnection(read_only=False)
        self.db.execute(self.DDL_RISK)

    # ───────────────────────────────────────── helpers de cartera
    def _portfolio_symbols_and_weights(self, portfolio_id: int) -> Tuple[List[str], List[float]]:
        # portfolio_assets: (asset_id, weight); assets_repo: (asset_id -> symbol)
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
                # esta fase 4.1 es renta variable; ignoramos otros tipos para evitar ruido
                continue
            symbols.append(asset["symbol"])
            weights.append(float(row["weight"]))
        if not symbols:
            raise ValueError("No hay activos de tipo 'stock'/'etf' en la cartera.")
        # normalizamos pesos por si acaso
        wsum = sum(weights)
        if wsum <= 0:
            raise ValueError("La suma de pesos es cero o negativa.")
        weights = [w / wsum for w in weights]
        return symbols, weights

    def _portfolio_series(self, portfolio_id: int) -> Tuple[pd.Series, pd.Series]:
        """
        Devuelve:
          - serie de retornos diarios del portfolio (ponderado)
          - serie de retornos diarios del benchmark
        """
        symbols, weights = self._portfolio_symbols_and_weights(portfolio_id)
        prices = PriceLoader.fetch_adj_close(symbols, self.config.lookback)
        if prices.isna().all(axis=None):
            raise ValueError("No se pudieron descargar precios para los símbolos dados.")
        prices = prices.dropna(how="any")
        rets = prices.pct_change().dropna()
        # mezcla ponderada
        w = np.array(weights)
        # si hay 1 columna, aseguremos dims
        if rets.shape[1] == 1:
            port_ret = rets.iloc[:, 0]
        else:
            port_ret = (rets.values @ w)
            port_ret = pd.Series(port_ret, index=rets.index, name="portfolio_ret")

        # benchmark
        bench_prices = PriceLoader.fetch_adj_close([self.config.benchmark], self.config.lookback)
        bench_ret = bench_prices.pct_change().dropna().iloc[:, 0]
        # alinear índices
        df = pd.concat([port_ret, bench_ret], axis=1, join="inner")
        df.columns = ["portfolio", "benchmark"]
        return df["portfolio"], df["benchmark"]

    # ───────────────────────────────────────── métricas
    def _annualize(self, daily_value: float) -> float:
        return daily_value * np.sqrt(self.config.trading_days)

    def _downside_std(self, series: pd.Series) -> float:
        downside = series[series < 0]
        return downside.std(ddof=1)

    def _max_drawdown(self, equity: pd.Series) -> float:
        cummax = equity.cummax()
        drawdown = (equity / cummax) - 1.0
        return float(drawdown.min())

    def _var_cvar(self, series: pd.Series, alpha: float = 0.95) -> Tuple[float, float]:
        # serie de retornos diarios
        q = series.quantile(1 - alpha)  # p.ej., 5% peor
        # CVaR = media de la cola de pérdidas (<= q)
        tail = series[series <= q]
        cvar = tail.mean() if len(tail) > 0 else q
        return float(q), float(cvar)

    def _beta(self, port: pd.Series, bench: pd.Series) -> float:
        cov = np.cov(port, bench)[0, 1]
        var_b = np.var(bench)
        return float(cov / var_b) if var_b > 0 else np.nan

    # ───────────────────────────────────────── API pública
    def analyze_portfolio(self, portfolio_id: int) -> Dict[str, float]:
        """
        Calcula métricas de riesgo clave sobre retornos diarios.
        Persiste resultados en la tabla 'risk_metrics'.
        """
        port, bench = self._portfolio_series(portfolio_id)
        rf_daily = (1 + self.config.rf_annual) ** (1 / self.config.trading_days) - 1

        vol_daily = float(port.std(ddof=1))
        vol_annual = self._annualize(vol_daily)
        beta = self._beta(port, bench)

        # Equity curve para MDD
        equity = (1 + port).cumprod()
        mdd = self._max_drawdown(equity)

        # VaR / CVaR (diario)
        var95, cvar95 = self._var_cvar(port, alpha=0.95)

        # resultados
        out = {
            "vol_daily": vol_daily,
            "vol_annual": vol_annual,
            "beta": beta,
            "max_drawdown": mdd,
            "VaR_95_daily": var95,
            "CVaR_95_daily": cvar95,
        }

        # persistimos
        as_of = datetime.now(timezone.utc).isoformat()
        for k, v in out.items():
            self.db.execute(
                "INSERT INTO risk_metrics(portfolio_id, as_of, window, benchmark, metric, value) VALUES (?,?,?,?,?,?);",
                (portfolio_id, as_of, self.config.lookback, self.config.benchmark, k, float(v) if v is not None else None)
            )
        return out

    def close(self):
        self.port_repo.close()
        self.assets_repo.close()
        self.db.close()
