"""Utility helpers for retrieving market data from Yahoo Finance.

The goal of this module is to provide a thin wrapper around the `yfinance`
package with a couple of extra conveniences that are common in the project:

* Normalising tickers so that the rest of the codebase does not have to worry
  about whitespace or lower/upper case issues.
* Input validation with informative exceptions (helpful for the UI layer).
* Converting the downloaded data into tidy ``pandas`` data frames that can be
  consumed by analytics modules.

The functions defined here are intentionally synchronous and side‑effect free
(with the exception of the network call performed by ``yfinance``). This keeps
things simple while we iterate on the broader architecture. When we eventually
introduce caching or asynchronous fetching we can evolve these helpers.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List, Optional

import pandas as pd
import yfinance as yf


@dataclass(frozen=True)
class PriceRequest:
    """Parameters for a price history request.

    Attributes
    ----------
    tickers:
        An iterable of ticker symbols accepted by Yahoo Finance. They are
        normalised (trimmed and upper‑cased) before being sent to the API.
    start:
        Optional start date for the historical window. If ``None`` Yahoo will
        return the longest available history.
    end:
        Optional end date (inclusive). Defaults to ``datetime.utcnow`` inside
        :func:`download_price_history` when not provided.
    interval:
        Frequency of the candles to request. It must be one of the intervals
        supported by Yahoo Finance (``1d``, ``1wk``, ``1mo``, ...).
    """

    tickers: Iterable[str]
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    interval: str = "1d"

    def normalised_tickers(self) -> List[str]:
        """Return a list of cleaned ticker symbols.

        ``yfinance`` is case sensitive for some non‑US exchanges and it is easy
        to introduce leading/trailing whitespaces when receiving input from a
        form. To reduce the amount of tedious input cleaning scattered across
        the project we centralise it here.
        """

        normalised = []
        for raw in self.tickers:
            ticker = raw.strip().upper()
            if not ticker:
                raise ValueError("Ticker symbols must not be empty after trimming")
            normalised.append(ticker)
        if not normalised:
            raise ValueError("At least one ticker must be provided")
        return normalised


def download_price_history(request: PriceRequest) -> pd.DataFrame:
    """Download OHLCV data for the requested tickers.

    The function delegates to :func:`yfinance.download` and returns a data frame
    indexed by ``DatetimeIndex`` with a column hierarchy compatible with what
    the rest of the project expects. Only the ``Adj Close`` column is retained
    by default because it is the series typically used for return
    calculations.
    """

    tickers = request.normalised_tickers()
    end = request.end or datetime.utcnow()

    data = yf.download(
        tickers=tickers,
        start=request.start,
        end=end,
        interval=request.interval,
        auto_adjust=False,
        progress=False,
        group_by="ticker",
    )
    if data.empty:
        raise ValueError("Yahoo Finance returned an empty data frame for the given parameters")

    # ``yfinance`` sometimes returns a Series when a single ticker is provided,
    # therefore we normalise the shape so downstream code can rely on a
    # consistent multi-index column structure.
    if isinstance(data, pd.Series):
        data = data.to_frame().T

    if not isinstance(data.columns, pd.MultiIndex):
        # When the index is not a multi-index we manually construct one keeping
        # the same semantics as the multi-ticker response.
        data.columns = pd.MultiIndex.from_product([tickers, data.columns])

    # Keep only the adjusted close price. We drop columns with missing data to
    # avoid surprises when computing returns.
    adj_close = data.xs("Adj Close", axis=1, level=1)
    adj_close = adj_close.dropna(how="all")

    if adj_close.empty:
        raise ValueError("Adjusted close series is empty after removing missing values")

    return adj_close.sort_index()


def build_price_frame(
    tickers: Iterable[str],
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    interval: str = "1d",
) -> pd.DataFrame:
    """Convenience wrapper returning a tidy price frame.

    Parameters are identical to :class:`PriceRequest`. The helper exists to keep
    call sites concise when customisation is not necessary.
    """

    request = PriceRequest(tickers=tickers, start=start, end=end, interval=interval)
    return download_price_history(request)
