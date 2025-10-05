"""Core portfolio analytics used across the application.

The focus is on producing metrics that are useful for the dashboard views and
for downstream optimisation (tracking error, risk, drawdowns, ...). The module
is deliberately self contained so it can also be executed in notebooks while we
iterate on the product design.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Tuple

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class PortfolioSnapshot:
    """Represents the evolution of a portfolio in time.

    Parameters
    ----------
    prices:
        Adjusted close prices indexed by date and with one column per asset.
    weights:
        Target weights for each asset. They should sum to one.
    benchmark:
        Optional benchmark price series used for relative comparisons.
    """

    prices: pd.DataFrame
    weights: Mapping[str, float]
    benchmark: pd.Series | None = None

    def aligned(self) -> Tuple[pd.DataFrame, pd.Series | None]:
        """Return prices and benchmark filtered to the available assets."""

        assets = [c for c in self.prices.columns if c in self.weights]
        if not assets:
            raise ValueError("None of the provided weights match the price columns")
        filtered_prices = self.prices[assets].sort_index()
        benchmark = self.benchmark.sort_index() if self.benchmark is not None else None
        return filtered_prices, benchmark


def normalise_weights(weights: Mapping[str, float]) -> pd.Series:
    """Return a normalised weight series that sums to one."""

    series = pd.Series(weights, dtype=float)
    total = series.sum()
    if np.isclose(total, 0):
        raise ValueError("Portfolio weights must not sum to zero")
    return series / total


def compute_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """Compute daily log-returns from adjusted close prices."""

    returns = np.log(prices / prices.shift(1))
    return returns.dropna(how="all")


@dataclass(frozen=True)
class PerformanceReport:
    total_return: float
    annualised_return: float
    annualised_volatility: float
    sharpe_ratio: float
    max_drawdown: float
    cumulative_returns: pd.Series
    drawdown_series: pd.Series


def performance(snapshot: PortfolioSnapshot, trading_days: int = 252) -> PerformanceReport:
    """Compute risk and performance metrics for a weighted portfolio."""

    prices, benchmark = snapshot.aligned()
    returns = compute_returns(prices)
    weights = normalise_weights(snapshot.weights).reindex(prices.columns).fillna(0.0)

    portfolio_returns = returns.mul(weights, axis=1).sum(axis=1)
    cumulative_returns = (portfolio_returns + 1).cumprod() - 1

    total_return = cumulative_returns.iloc[-1]
    annualised_return = (1 + total_return) ** (trading_days / len(portfolio_returns)) - 1
    annualised_volatility = portfolio_returns.std(ddof=0) * np.sqrt(trading_days)
    sharpe_ratio = (
        np.nan if np.isclose(annualised_volatility, 0) else annualised_return / annualised_volatility
    )

    wealth_index = (portfolio_returns + 1).cumprod()
    running_max = wealth_index.cummax()
    drawdowns = wealth_index / running_max - 1
    max_drawdown = drawdowns.min()

    return PerformanceReport(
        total_return=float(total_return),
        annualised_return=float(annualised_return),
        annualised_volatility=float(annualised_volatility),
        sharpe_ratio=float(sharpe_ratio),
        max_drawdown=float(max_drawdown),
        cumulative_returns=cumulative_returns,
        drawdown_series=drawdowns,
    )


def tracking_error(portfolio_returns: pd.Series, benchmark_returns: pd.Series) -> float:
    """Calculate the annualised tracking error between portfolio and benchmark."""

    active_returns = portfolio_returns - benchmark_returns
    return float(active_returns.std(ddof=0) * np.sqrt(252))


def information_ratio(portfolio_returns: pd.Series, benchmark_returns: pd.Series) -> float:
    """Annualised information ratio based on daily log returns."""

    te = tracking_error(portfolio_returns, benchmark_returns)
    if np.isclose(te, 0):
        return np.nan
    active_returns = portfolio_returns - benchmark_returns
    annualised_active = active_returns.mean() * 252
    return float(annualised_active / te)
