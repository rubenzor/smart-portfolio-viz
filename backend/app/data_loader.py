import os
from datetime import datetime, timedelta

import yfinance as yf
import requests
import pandas as pd

ALPACA_KEY = os.getenv("ALPACA_KEY")
ALPACA_SECRET = os.getenv("ALPACA_SECRET")
ALPACA_BASE = os.getenv("ALPACA_BASE", "https://data.alpaca.markets")

def _load_yahoo(symbol: str, days: int = 365) -> pd.Series:
    df = yf.download(symbol, period=f"{days}d", interval="1d", auto_adjust=True, progress=False)
    if df.empty:
        raise ValueError(f"Yahoo no devolvió datos para {symbol}")
    return df["Close"].dropna()

def _load_alpaca_stock(symbol: str, days: int = 365) -> pd.Series:
    if not ALPACA_KEY or not ALPACA_SECRET:
        raise ValueError("No hay credenciales Alpaca")

    end = datetime.utcnow()
    start = end - timedelta(days=days + 10)
    url = f"{ALPACA_BASE}/v2/stocks/{symbol}/bars"
    params = {
        "timeframe": "1Day",
        "start": start.isoformat() + "Z",
        "end": end.isoformat() + "Z",
        "limit": days + 10,
    }
    r = requests.get(
        url,
        headers={
            "APCA-API-KEY-ID": ALPACA_KEY,
            "APCA-API-SECRET-KEY": ALPACA_SECRET,
        },
        params=params,
        timeout=10,
    )
    r.raise_for_status()
    data = r.json()
    bars = data.get("bars", [])
    if not bars:
        raise ValueError(f"Alpaca no devolvió datos para {symbol}")
    closes = [b["c"] for b in bars]
    idx = pd.date_range(end=end, periods=len(closes), freq="B")
    return pd.Series(closes, index=idx).dropna()

def load_price_history(symbol: str, days: int = 365) -> pd.Series:
    """
    Primero intenta Alpaca si hay credenciales.
    Si falla o no hay keys, usa Yahoo Finance.
    """
    # Simple heuristic: si es crypto tipo BTC-USD, usamos Yahoo directamente
    if "-" in symbol or "=" in symbol:
        return _load_yahoo(symbol, days)

    # Intentar Alpaca
    if ALPACA_KEY and ALPACA_SECRET:
        try:
            return _load_alpaca_stock(symbol, days)
        except Exception:
            pass

    # Fallback Yahoo
    return _load_yahoo(symbol, days)
