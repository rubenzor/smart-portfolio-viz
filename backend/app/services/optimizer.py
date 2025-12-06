# backend/app/services/optimizer.py
import numpy as np
import pandas as pd
from typing import Dict, List


def mean_variance_opt(prices: pd.DataFrame) -> Dict[str, float]:
    """
    Very simple mean-variance optimizer:
    - calcula rendimientos diarios
    - maximiza Sharpe ratio sin rf
    """
    returns = prices.pct_change().dropna()
    mu = returns.mean().values  # expected returns
    cov = returns.cov().values
    n = len(mu)

    # grid simple sobre el simplex (no es perfecto pero vale para TFG)
    grid = 2000
    best_w = None
    best_sr = -1e9

    rng = np.random.default_rng(42)
    for _ in range(grid):
        w = rng.random(n)
        w = w / w.sum()
        port_ret = np.dot(w, mu)
        port_vol = np.sqrt(w @ cov @ w)
        if port_vol == 0:
            continue
        sr = port_ret / port_vol
        if sr > best_sr:
            best_sr = sr
            best_w = w

    weights = {symbol: float(w) for symbol, w in zip(prices.columns, best_w)}
    return weights


def build_frontier(prices: pd.DataFrame, points: int = 25):
    returns = prices.pct_change().dropna()
    mu = returns.mean().values
    cov = returns.cov().values
    n = len(mu)

    rng = np.random.default_rng(123)
    risks = []
    rets = []

    for _ in range(points * 200):
        w = rng.random(n)
        w = w / w.sum()
        port_ret = np.dot(w, mu)
        port_vol = np.sqrt(w @ cov @ w)
        risks.append(port_vol)
        rets.append(port_ret)

    df = pd.DataFrame({"risk": risks, "return": rets})
    df = df.sort_values("risk")
    # quitar duplicados aproximados y coger unos cuantos puntos
    df = df.drop_duplicates(subset=["risk"])
    if len(df) > points:
        df = df.iloc[:: len(df) // points]

    return df.to_dict(orient="records")
