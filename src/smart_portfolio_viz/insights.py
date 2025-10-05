"""High level insights used by the Streamlit dashboard.

The UI needs lightweight heuristics for recommendations, portfolio
classifications and quick predictions. The goal is not to build a fully fledged
quantitative engine but to provide actionable nudges that users can review and
decide whether to execute.

The helpers in this module purposefully trade sophistication for transparency;
they rely on simple momentum checks, linear trend projections and curated
substitute lists grouped by sector ETFs. This keeps the logic easy to explain in
the interface while providing a solid foundation for future iterations.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, Iterable, List, Mapping, Optional, Tuple

import numpy as np
import pandas as pd
import yfinance as yf


SECTOR_SUBSTITUTES: Dict[str, List[str]] = {
    "Technology": ["XLK", "VGT", "SMH"],
    "Communication Services": ["XLC", "VOX", "FDN"],
    "Consumer Cyclical": ["XLY", "VCR", "FDIS"],
    "Consumer Defensive": ["XLP", "VDC", "FSTA"],
    "Energy": ["XLE", "VDE", "IXC"],
    "Financial Services": ["XLF", "VFH", "KBE"],
    "Healthcare": ["XLV", "VHT", "IHF"],
    "Industrials": ["XLI", "VIS", "ITA"],
    "Basic Materials": ["XLB", "VAW", "MXI"],
    "Real Estate": ["XLRE", "VNQ", "IYR"],
    "Utilities": ["XLU", "VPU", "IDU"],
    "Unknown": ["SPY", "VT", "QQQ"],
}


TIME_HORIZONS: Mapping[str, int] = {
    "1D": 1,
    "5D": 5,
    "30D": 30,
    "6M": 182,
    "1Y": 365,
}


@dataclass(frozen=True)
class AssetInsight:
    ticker: str
    action: str
    rationale: str
    substitutes: List[str]
    predicted_price: float
    predicted_return: float


def _clean_series(series: pd.Series) -> pd.Series:
    cleaned = series.dropna()
    if cleaned.empty:
        raise ValueError("Input series is empty after dropping NaN values")
    return cleaned


def compute_horizon_returns(prices: pd.DataFrame, horizons: Mapping[str, int] = TIME_HORIZONS) -> pd.DataFrame:
    """Return percentage change for multiple lookback windows."""

    latest = prices.iloc[-1]
    results = pd.DataFrame(index=prices.columns)
    for label, days in horizons.items():
        lookback_start = prices.index.max() - pd.Timedelta(days=days)
        sliced = prices.loc[prices.index >= lookback_start]
        if sliced.empty:
            results[label] = np.nan
            continue
        baseline = sliced.iloc[0]
        returns = (latest / baseline) - 1
        results[label] = returns
    results["Latest"] = latest
    return results


@lru_cache(maxsize=64)
def _download_info(ticker: str) -> Dict[str, str]:
    try:
        info = yf.Ticker(ticker).info
    except Exception:
        info = {}
    return info or {}


def _sector_for_ticker(ticker: str) -> str:
    info = _download_info(ticker)
    return info.get("sector") or info.get("industry") or "Unknown"


def _substitutes_for_sector(sector: str, exclude: Iterable[str]) -> List[str]:
    suggestions = SECTOR_SUBSTITUTES.get(sector, SECTOR_SUBSTITUTES["Unknown"])
    return [ticker for ticker in suggestions if ticker not in set(exclude)]


def _linear_projection(series: pd.Series, horizon: int = 30) -> Tuple[float, float]:
    cleaned = _clean_series(series)
    if len(cleaned) < 2:
        last_price = float(cleaned.iloc[-1])
        return last_price, 0.0
    x = np.arange(len(cleaned))
    slope, intercept = np.polyfit(x, cleaned.values, 1)
    future_index = len(cleaned) + horizon
    predicted_price = slope * future_index + intercept
    last_price = cleaned.iloc[-1]
    predicted_return = (predicted_price / last_price) - 1
    return float(predicted_price), float(predicted_return)


def _momentum_action(series: pd.Series, lookback: int = 30) -> Tuple[str, str]:
    cleaned = _clean_series(series)
    recent = cleaned.tail(lookback)
    if len(recent) < 2:
        return "Mantener", "Historial insuficiente para generar una recomendación."
    change = (recent.iloc[-1] / recent.iloc[0]) - 1
    daily_returns = recent.pct_change().dropna()
    annualised_vol = daily_returns.std(ddof=0) * np.sqrt(252)
    rationale = f"Retorno {lookback}D: {change:.1%} · Volatilidad anualizada: {annualised_vol:.1%}"
    if change > 0.05:
        return "Comprar", rationale
    if change < -0.05:
        return "Vender", rationale
    return "Mantener", rationale


def build_asset_insights(prices: pd.DataFrame, horizon_days: int = 30) -> List[AssetInsight]:
    """Generate action suggestions and projections for each asset."""

    insights: List[AssetInsight] = []
    for column in prices.columns:
        series = prices[column]
        action, rationale = _momentum_action(series)
        predicted_price, predicted_return = _linear_projection(series, horizon=horizon_days)
        sector = _sector_for_ticker(column)
        substitutes = _substitutes_for_sector(sector, exclude=[column])
        insights.append(
            AssetInsight(
                ticker=column,
                action=action,
                rationale=rationale,
                substitutes=substitutes,
                predicted_price=predicted_price,
                predicted_return=predicted_return,
            )
        )
    return insights


def classify_portfolio(total_return: float, benchmark_return: Optional[float] = None, tolerance: float = 0.01) -> str:
    """Return a short label describing how the portfolio is performing."""

    if benchmark_return is not None:
        delta = total_return - benchmark_return
        if delta > tolerance:
            return "Overperforming"
        if delta < -tolerance:
            return "Underperforming"
        return "En línea con el benchmark"
    if total_return > 0.01:
        return "Rentabilidad positiva"
    if total_return < -0.01:
        return "Rentabilidad negativa"
    return "Estable"


def portfolio_projection(weights: Mapping[str, float], asset_insights: List[AssetInsight]) -> Tuple[float, float]:
    """Combine asset projections into portfolio level return and price estimates."""

    total_weight = sum(weights.values())
    if not np.isclose(total_weight, 1.0):
        weight_series = pd.Series(weights, dtype=float)
        if np.isclose(weight_series.sum(), 0.0):
            weight_series[:] = 1 / len(weight_series)
        else:
            weight_series = weight_series / weight_series.sum()
    else:
        weight_series = pd.Series(weights, dtype=float)

    projected_return = 0.0
    latest_price = 1.0
    for insight in asset_insights:
        weight = float(weight_series.get(insight.ticker, 0.0))
        projected_return += weight * insight.predicted_return
    projected_price = latest_price * (1 + projected_return)
    return projected_price, projected_return


@lru_cache(maxsize=64)
def fetch_latest_news(ticker: str, limit: int = 5) -> List[Mapping[str, str]]:
    """Fetch recent news items for a ticker. Falls back gracefully on errors."""

    try:
        items = yf.Ticker(ticker).news or []
    except Exception:
        return []
    news_items = []
    for item in items[:limit]:
        title = item.get("title")
        link = item.get("link") or item.get("url")
        publisher = item.get("publisher")
        if not title or not link:
            continue
        news_items.append({"title": title, "link": link, "publisher": publisher})
    return news_items
