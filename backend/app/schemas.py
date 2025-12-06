# backend/app/schemas.py

from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Union
from datetime import datetime


# =====================================================================
#                               ASSETS
# =====================================================================

class AssetBase(BaseModel):
    symbol: str
    name: Optional[str] = ""
    weight: float = Field(0.0, ge=0.0)
    benchmark: str


class AssetCreate(AssetBase):
    pass


class AssetOut(AssetBase):
    id: int

    class Config:
        from_attributes = True


# =====================================================================
#                              PORTFOLIOS
# =====================================================================

class PortfolioBase(BaseModel):
    name: str
    kind: str = "mixed"
    benchmarks: List[str] = []


class PortfolioCreate(PortfolioBase):
    assets: List[AssetCreate] = []
    benchmarks: List[str] = []


class PortfolioUpdate(BaseModel):
    name: Optional[str] = None
    kind: Optional[str] = None
    assets: Optional[List[AssetCreate]] = None
    benchmarks: List[str] = []


class PortfolioOut(PortfolioBase):
    id: int
    benchmarks: List[str] = Field(default=[], alias="benchmarks_py")
    created_at: datetime
    assets: List[AssetOut] = []

    class Config:
        from_attributes = True
        populate_by_name = True


# =====================================================================
#                              OPTIMIZATION
# =====================================================================

class OptimizationRequest(BaseModel):
    portfolio_id: int
    mode: Literal["auto", "manual"] = "auto"
    method: Optional[
        Literal[
            "mean_variance",
            "min_variance",
            "max_sharpe",
            "risk_parity",
            "black_litterman",
        ]
    ] = None
    horizon_days: Optional[int] = None

class OptimizationMethodResult(BaseModel):
    method: str
    expected_return: float
    volatility: float
    sharpe_ratio: float
    weights: Dict[str, float]


class OptimizationMultiResult(BaseModel):
    methods: List[OptimizationMethodResult]
    best_method: str
    reason: str
    horizon_days: int
    current_weights: Dict[str, float]
    efficient_frontier: Dict[str, List[float]]
    


# =====================================================================
#                           APPLY WEIGHTS
# =====================================================================

class WeightItem(BaseModel):
    ticker: str
    weight: float = Field(..., ge=0.0)


class ApplyWeightsRequest(BaseModel):
    weights: Union[
        Dict[str, float],             # {"AAPL": 0.5, "MSFT": 0.5}
        List[Dict[str, float]]        # [{"ticker": "...", "weight": ...}, ...]
    ]


# =====================================================================
#                           PORTFOLIO FORECAST
# =====================================================================

class PortfolioForecastRequest(BaseModel):
    portfolio_id: int
    days_forecast: int = 30


class ForecastBand(BaseModel):
    p5: List[float]
    p50: List[float]
    p95: List[float]
    weights_used: Dict[str, float]


class PortfolioForecastResult(BaseModel):
    dates: List[str]
    current: ForecastBand
    optimized: ForecastBand
    no_change: bool = False
