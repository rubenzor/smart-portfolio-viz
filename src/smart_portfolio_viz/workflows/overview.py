"""Orchestrators that turn raw inputs into portfolio overview artefacts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Mapping, Optional

import pandas as pd

from smart_portfolio_viz.analytics.portfolio import (
    PerformanceReport,
    PortfolioSnapshot,
    compute_returns,
    normalise_weights,
    performance,
)
from smart_portfolio_viz.data.yahoo import build_price_frame


@dataclass(frozen=True)
class OverviewConfig:
    """User supplied configuration for a portfolio overview calculation."""

    tickers: Iterable[str]
    weights: Mapping[str, float]
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    interval: str = "1d"
    benchmark: Optional[str] = None


@dataclass(frozen=True)
class PortfolioOverview:
    """Aggregated data ready to be consumed by UI layers."""

    prices: pd.DataFrame
    returns: pd.DataFrame
    weights: pd.Series
    portfolio_returns: pd.Series
    performance: PerformanceReport
    benchmark_returns: Optional[pd.Series]
    benchmark_performance: Optional[PerformanceReport]
    contributions: pd.Series
    correlation_matrix: pd.DataFrame


def _fetch_prices(config: OverviewConfig) -> tuple[pd.DataFrame, Optional[pd.Series]]:
    prices = build_price_frame(
        tickers=config.tickers,
        start=config.start,
        end=config.end,
        interval=config.interval,
    )

    benchmark_series: Optional[pd.Series] = None
    if config.benchmark:
        benchmark_prices = build_price_frame(
            tickers=[config.benchmark],
            start=config.start,
            end=config.end,
            interval=config.interval,
        )
        benchmark_series = benchmark_prices.iloc[:, 0]

    return prices, benchmark_series


def _compute_contributions(returns: pd.DataFrame, weights: pd.Series) -> pd.Series:
    annualised_returns = returns.mean() * 252
    contributions = annualised_returns.mul(weights)
    return contributions.sort_values(ascending=False)


def build_portfolio_overview(config: OverviewConfig) -> PortfolioOverview:
    """Load market data and compute key analytics in a single step."""

    prices, benchmark_series = _fetch_prices(config)
    weight_vector = normalise_weights(config.weights).reindex(prices.columns).fillna(0.0)

    returns = compute_returns(prices)
    portfolio_returns = returns.mul(weight_vector, axis=1).sum(axis=1)

    snapshot = PortfolioSnapshot(
        prices=prices,
        weights=weight_vector.to_dict(),
        benchmark=benchmark_series,
    )
    report = performance(snapshot)

    benchmark_returns: Optional[pd.Series] = None
    benchmark_report: Optional[PerformanceReport] = None
    if benchmark_series is not None:
        benchmark_returns = compute_returns(benchmark_series.to_frame()).iloc[:, 0]
        benchmark_snapshot = PortfolioSnapshot(
            prices=benchmark_series.to_frame(name=benchmark_series.name or "Benchmark"),
            weights={benchmark_series.name or "Benchmark": 1.0},
        )
        benchmark_report = performance(benchmark_snapshot)

    contributions = _compute_contributions(returns, weight_vector)
    correlation_matrix = returns.corr().fillna(0.0)

    return PortfolioOverview(
        prices=prices,
        returns=returns,
        weights=weight_vector,
        portfolio_returns=portfolio_returns,
        performance=report,
        benchmark_returns=benchmark_returns,
        benchmark_performance=benchmark_report,
        contributions=contributions,
        correlation_matrix=correlation_matrix,
    )
