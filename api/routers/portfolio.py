from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import APIKeyHeader
from typing import Optional
from pydantic import BaseModel, Field
from portfolio.portfolio_manager import PortfolioManager
from auth.session_manager import get_session_user

router = APIRouter()

# 🔐 Reutilizamos el esquema de autenticación
api_key_header = APIKeyHeader(name="Authorization", auto_error=False)


# ────────────────────────────────────────────────────────────────
# MODELOS Pydantic
# ────────────────────────────────────────────────────────────────
class CreatePortfolioIn(BaseModel):
    name: str = Field(..., description="Nombre de la cartera")

class AddAssetIn(BaseModel):
    symbol: str
    name: str
    weight: float
    asset_type: Optional[str] = "stock"
    currency: Optional[str] = "USD"


# ────────────────────────────────────────────────────────────────
# HELPERS
# ────────────────────────────────────────────────────────────────
def get_user_id_from_token(authorization: Optional[str]) -> int:
    """Extrae el user_id a partir del token Authorization"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing auth token")

    if authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1]
    else:
        token = authorization.strip()

    user_id = get_session_user(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user_id


# ────────────────────────────────────────────────────────────────
# ENDPOINTS
# ────────────────────────────────────────────────────────────────
@router.post("/portfolios/create", summary="Crear un nuevo portfolio")
def create_portfolio(payload: CreatePortfolioIn, authorization: Optional[str] = Depends(api_key_header)):
    """
    Crea una nueva cartera asociada al usuario autenticado.
    """
    user_id = get_user_id_from_token(authorization)
    pm = PortfolioManager()
    pid = pm.create_portfolio(user_id, payload.name)
    pm.close()
    return {"portfolio_id": pid, "status": "created"}


@router.get("/portfolios/my", summary="Listar portfolios del usuario autenticado")
def list_my_portfolios(authorization: Optional[str] = Depends(api_key_header)):
    user_id = get_user_id_from_token(authorization)
    pm = PortfolioManager()
    portfolios = pm.list_user_portfolios(user_id)
    pm.close()
    return portfolios


@router.post("/portfolios/{portfolio_id}/add_asset", summary="Añadir un activo a una cartera")
def add_asset(portfolio_id: int, payload: AddAssetIn, authorization: Optional[str] = Depends(api_key_header)):
    user_id = get_user_id_from_token(authorization)
    pm = PortfolioManager()

    # Verificamos que la cartera pertenece al usuario
    portfolios = pm.list_user_portfolios(user_id)
    if portfolio_id not in [p["portfolio_id"] for p in portfolios]:
        pm.close()
        raise HTTPException(status_code=403, detail="Portfolio not owned by this user")

    pm.add_asset_to_portfolio(portfolio_id, payload.symbol, payload.name, payload.weight, payload.asset_type, payload.currency)
    pm.close()
    return {"status": "asset_added", "portfolio_id": portfolio_id, "symbol": payload.symbol}


@router.delete("/portfolios/{portfolio_id}/remove_asset", summary="Eliminar un activo de una cartera")
def remove_asset(portfolio_id: int, symbol: str, authorization: Optional[str] = Depends(api_key_header)):
    user_id = get_user_id_from_token(authorization)
    pm = PortfolioManager()

    # Verificamos propiedad
    portfolios = pm.list_user_portfolios(user_id)
    if portfolio_id not in [p["portfolio_id"] for p in portfolios]:
        pm.close()
        raise HTTPException(status_code=403, detail="Portfolio not owned by this user")

    try:
        pm.remove_asset_from_portfolio(portfolio_id, symbol)
        pm.close()
        return {"status": "asset_removed", "symbol": symbol}
    except ValueError as e:
        pm.close()
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/portfolios/{portfolio_id}/summary", summary="Resumen de una cartera")
def get_summary(portfolio_id: int, authorization: Optional[str] = Depends(api_key_header)):
    user_id = get_user_id_from_token(authorization)
    pm = PortfolioManager()

    # Verificamos propiedad
    portfolios = pm.list_user_portfolios(user_id)
    if portfolio_id not in [p["portfolio_id"] for p in portfolios]:
        pm.close()
        raise HTTPException(status_code=403, detail="Portfolio not owned by this user")

    summary = pm.compute_portfolio_summary(portfolio_id)
    pm.close()
    return summary
