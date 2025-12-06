# backend/app/routers/optimization.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict   
from ..db import get_db
from .. import models, schemas
from ..services.pricing import load_prices
from ..services.portfolio_ops import (
    choose_best_optimization_method,
    build_reason,
    compute_efficient_frontier,
)

router = APIRouter(prefix="/api/v1/optimize", tags=["optimization"])


def get_portfolio_weights_from_db(db: Session, portfolio_id: int) -> Dict[str, float]:
    """
    Lee de la BD los pesos actuales de la cartera.
    Devuelve: {"AAPL": 0.25, "MSFT": 0.35, ...}
    """
    pf = db.query(models.Portfolio).filter_by(id=portfolio_id).first()
    if not pf:
        raise HTTPException(404, "Portfolio not found")

    if not pf.assets:
        raise HTTPException(400, "Portfolio has no assets")

    return {a.symbol: float(a.weight) for a in pf.assets}


@router.post("", response_model=schemas.OptimizationMultiResult)
def optimize_portfolio(
    payload: schemas.OptimizationRequest,
    db: Session = Depends(get_db),
):
    # -----------------------------------------------------------
    # 1. Obtener cartera y pesos actuales
    # -----------------------------------------------------------
    pf = db.query(models.Portfolio).filter_by(id=payload.portfolio_id).first()
    if not pf:
        raise HTTPException(404, "Portfolio not found")

    symbols = [a.symbol for a in pf.assets]
    if not symbols:
        raise HTTPException(400, "Portfolio has no assets")

    current_weights = get_portfolio_weights_from_db(db, payload.portfolio_id)

    # -----------------------------------------------------------
    # 2. Cargar precios históricos
    # -----------------------------------------------------------
    prices = load_prices(symbols, days=504)
    if prices is None or prices.empty:
        raise HTTPException(400, "Price history unavailable")

    returns_df = prices.pct_change().dropna()
    if len(returns_df) < 126:
        raise HTTPException(400, "Not enough data for 126-day optimization window")

    # -----------------------------------------------------------
    # 3. Horizonte: SIEMPRE 126 días (auto y manual por defecto)
    # -----------------------------------------------------------
    if payload.mode == "manual" and payload.horizon_days:
        horizon_days = min(max(payload.horizon_days, 10), len(returns_df))
    else:
        horizon_days = 126

    window = returns_df.tail(horizon_days)

    # -----------------------------------------------------------
    # 4. Ejecutar TODOS los métodos y elegir el mejor
    # -----------------------------------------------------------
    try:
        methods_results, best, second = choose_best_optimization_method(window)
    except Exception as e:
        raise HTTPException(400, str(e))

    # -----------------------------------------------------------
    # 5. Frontera eficiente Markowitz (común a todos los métodos)
    # -----------------------------------------------------------
    frontier = compute_efficient_frontier(window)
    if not frontier["risks"] or not frontier["returns"]:
        # fallback básico para no devolver listas vacías
        frontier = {"risks": [0.0], "returns": [0.0]}

    # -----------------------------------------------------------
    # 6. Razón del método óptimo
    # -----------------------------------------------------------
    reason = build_reason(
        best_method=best["method"],
        horizon_days=horizon_days,
        best=best,
        second=second,
    )

    # -----------------------------------------------------------
    # 7. Respuesta final multi-método
    # -----------------------------------------------------------
    return schemas.OptimizationMultiResult(
        methods=[schemas.OptimizationMethodResult(**m) for m in methods_results],
        best_method=best["method"],
        reason=reason,
        horizon_days=horizon_days,          # siempre 126 por diseño
        current_weights=current_weights,    # pesos reales de la BD
        efficient_frontier=frontier,
    )