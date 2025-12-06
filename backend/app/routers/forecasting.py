# backend/app/routers/forecasting.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from .. import schemas
from ..services.forecasting import build_portfolio_forecast

router = APIRouter(prefix="/api/v1/forecast", tags=["forecasting"])


@router.post("/portfolio", response_model=schemas.PortfolioForecastResult)
def forecast_portfolio(
    payload: schemas.PortfolioForecastRequest,
    db: Session = Depends(get_db),
):
    """
    Forecast Montecarlo sobre:
      - cartera actual
      - cartera optimizada (método ganador)
    """
    try:
        result = build_portfolio_forecast(
            db=db,
            portfolio_id=payload.portfolio_id,
            days_forecast=payload.days_forecast,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return schemas.PortfolioForecastResult(**result)
