from fastapi import APIRouter, HTTPException
from app.db import SessionLocal
from app.models import Portfolio
from app.services.history_service import fetch_history
from app.services.pricing import portfolio_timeseries

router = APIRouter(prefix="/api/v1/overview", tags=["overview"])


@router.get("/{pf_id}")
def overview_portfolio(pf_id: int, days: int = 365):
    db = SessionLocal()

    pf = db.query(Portfolio).filter(Portfolio.id == pf_id).first()
    if not pf:
        raise HTTPException(404, "Portfolio not found")

    symbols = [a.symbol for a in pf.assets]
    weights = {a.symbol: a.weight for a in pf.assets}

    # ⬇️ NEW: usamos el endpoint nuevo de history
    hist = fetch_history(symbols, days)

    df = pd.DataFrame(hist["assets"])
    df.index = pd.to_datetime(hist["dates"])

    # serie temporal de la cartera
    port_curve = portfolio_timeseries(df, weights)

    return {
        "timeseries": {
            "dates": hist["dates"],
            "portfolio": port_curve.tolist()
        }
    }
