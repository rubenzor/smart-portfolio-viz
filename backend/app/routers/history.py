from fastapi import APIRouter, HTTPException
from app.services.history_service import fetch_history
from app.db import SessionLocal
from app.models import Portfolio

router = APIRouter(prefix="/api/v1/portfolios")

@router.get("/{pf_id}/history")
def get_portfolio_history(pf_id: int, days: int = 365):
    db = SessionLocal()

    portfolio = db.query(Portfolio).filter(Portfolio.id == pf_id).first()
    if not portfolio:
        raise HTTPException(404, "Portfolio not found")

    symbols = [a.symbol for a in portfolio.assets]

    history = fetch_history(symbols, days)

    return history

@router.get("/asset_returns/{pf_id}")
def asset_returns(pf_id: int, days: int = 365):
    db = SessionLocal()
    pf = db.query(Portfolio).filter(Portfolio.id == pf_id).first()
    if not pf:
        raise HTTPException(404, "Portfolio not found")

    symbols = [a.symbol for a in pf.assets]
    hist = fetch_history(symbols, days)

    df = pd.DataFrame(hist["assets"])
    df.index = pd.to_datetime(hist["dates"])

    # rentabilidad = (último / primero) - 1
    returns = (df.iloc[-1] / df.iloc[0] - 1).to_dict()

    return {"returns": returns}
