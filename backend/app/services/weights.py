# backend/app/services/weights.py

from typing import Dict, List, Union
from fastapi import HTTPException


def normalize_weights(raw_weights: Union[Dict[str, float], List[Dict[str, float]]]) -> List[Dict[str, float]]:
    """
    Acepta dict o lista de objetos y devuelve SIEMPRE:
    [{"ticker": "AAPL", "weight": float}, ...]
    NO renormaliza ni toca sumas, solo convierte/valida formato básico.
    """
    if isinstance(raw_weights, dict):
        items = []
        for ticker, w in raw_weights.items():
            try:
                weight = float(w)
            except (TypeError, ValueError):
                raise HTTPException(400, f"Peso inválido para {ticker}")
            items.append({"ticker": str(ticker).upper(), "weight": weight})

    elif isinstance(raw_weights, list):
        items = []
        for obj in raw_weights:
            if not isinstance(obj, dict):
                raise HTTPException(400, "Cada elemento de la lista de pesos debe ser un objeto JSON")
            if "ticker" not in obj or "weight" not in obj:
                raise HTTPException(400, "Cada peso debe tener 'ticker' y 'weight'")
            ticker = str(obj["ticker"]).upper()
            try:
                weight = float(obj["weight"])
            except (TypeError, ValueError):
                raise HTTPException(400, f"Peso inválido para {ticker}")
            items.append({"ticker": ticker, "weight": weight})
    else:
        raise HTTPException(400, "Formato inválido para 'weights'")

    return items