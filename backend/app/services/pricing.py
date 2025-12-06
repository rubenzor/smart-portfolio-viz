# backend/app/services/pricing.py
import yfinance as yf
import pandas as pd
from typing import List, Dict


def load_prices(symbols, days=365):
    data = yf.download(
        symbols,
        period=f"{days}d",
        interval="1d",
        auto_adjust=False,
        progress=False
    )

    # Si es MultiIndex, aplanamos
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = ['_'.join(col).strip() for col in data.columns]

    # Intentar usar Adj Close, si no existe usar Close
    if any(col.startswith("Adj Close") for col in data.columns):
        close_cols = [c for c in data.columns if c.startswith("Adj Close")]
    else:
        close_cols = [c for c in data.columns if c.startswith("Close")]

    # Renombrar columnas a solo el ticker
    clean_data = data[close_cols].copy()
    clean_data.columns = [col.split("_")[-1] for col in clean_data.columns]

    # Quitar filas vacías
    clean_data.dropna(inplace=True)

    return clean_data


def portfolio_timeseries(prices: pd.DataFrame, weights: Dict[str, float]) -> pd.Series:
    """
    Calcula la serie temporal del valor del portfolio normalizado a 1.
    prices: DF (dates x symbols)
    weights: dict symbol -> weight (no es necesario que sumen 1, se normaliza)
    """
    if not weights:
        raise ValueError("No weights")

    w = pd.Series(weights)
    w = w / w.sum()

    # asegurar que sólo usamos símbolos presentes
    w = w[w.index.isin(prices.columns)]
    prices = prices[w.index]

    # normalizar a 1 en t0
    norm_prices = prices / prices.iloc[0]
    port_index = (norm_prices * w).sum(axis=1)
    return port_index
