from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import APIKeyHeader
from typing import Optional
from auth.session_manager import get_session_user
from portfolio.portfolio_manager import PortfolioManager
from analytics.performance_analyzer import PerformanceAnalyzer
from analytics.risk_analyzer import RiskAnalyzer

router = APIRouter()
api_key_header = APIKeyHeader(name="Authorization", auto_error=False)

# ────────────────────────────────────────────────
# HELPER: obtener user_id desde token
# ────────────────────────────────────────────────
def get_user_id_from_token(authorization: Optional[str]) -> int:
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing auth token")

    token = authorization.split(" ", 1)[1] if authorization.startswith("Bearer ") else authorization.strip()
    user_id = get_session_user(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user_id

# ────────────────────────────────────────────────
# ENDPOINT: PERFORMANCE
# ────────────────────────────────────────────────
@router.get("/analytics/{portfolio_id}/performance", summary="Obtiene métricas de rendimiento de una cartera")
def get_performance(portfolio_id: int, authorization: Optional[str] = Depends(api_key_header)):
    user_id = get_user_id_from_token(authorization)
    pm = PortfolioManager()

    # Verificamos propiedad de la cartera
    portfolios = pm.list_user_portfolios(user_id)
    if portfolio_id not in [p["portfolio_id"] for p in portfolios]:
        pm.close()
        raise HTTPException(status_code=403, detail="Portfolio not owned by this user")

    # Obtenemos datos del portfolio
    portfolio_data = pm.get_portfolio_assets(portfolio_id)

    analyzer = PerformanceAnalyzer(portfolio_data)
    metrics = analyzer.compute_metrics()

    pm.close()
    return {"portfolio_id": portfolio_id, "performance_metrics": metrics}


# ────────────────────────────────────────────────
# ENDPOINT: RISK
# ────────────────────────────────────────────────
@router.get("/analytics/{portfolio_id}/risk", summary="Obtiene métricas de riesgo de una cartera")
def get_risk(portfolio_id: int, authorization: Optional[str] = Depends(api_key_header)):
    user_id = get_user_id_from_token(authorization)
    pm = PortfolioManager()

    # Verificamos propiedad de la cartera
    portfolios = pm.list_user_portfolios(user_id)
    if portfolio_id not in [p["portfolio_id"] for p in portfolios]:
        pm.close()
        raise HTTPException(status_code=403, detail="Portfolio not owned by this user")

    # Obtenemos datos del portfolio
    portfolio_data = pm.get_portfolio_assets(portfolio_id)

    analyzer = RiskAnalyzer(portfolio_data)
    metrics = analyzer.compute_metrics()

    pm.close()
    return {"portfolio_id": portfolio_id, "risk_metrics": metrics}
