from fastapi import APIRouter, Query
from app.services.search_service import search_tickers

router = APIRouter()


@router.get("/search/ticker")
def search_ticker(q: str = Query(..., min_length=1)):
    """
    Endpoint para buscar activos con Yahoo Finance autocomplete.
    Devuelve siempre lista (vacía en caso de error).
    """
    try:
        return search_tickers(q)
    except Exception:
        return []
