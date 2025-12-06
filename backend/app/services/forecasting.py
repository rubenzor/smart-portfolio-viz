# backend/app/services/forecasting.py

from typing import Dict, List, Tuple
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from .pricing import load_prices
from .portfolio_ops import choose_best_optimization_method
from .. import models


TRADING_DAYS = 252
HISTORY_DAYS = 126     # días de histórico para estimar parámetros
MIN_OBS = 60
N_SIMULATIONS = 1000
START_VALUE = 1.0


# ---------------------------------------------------------------------
# Helpers: cargar cartera y pesos desde BD
# ---------------------------------------------------------------------

def get_portfolio_symbols_and_weights(
    db: Session,
    portfolio_id: int,
) -> Tuple[List[str], Dict[str, float]]:
    """
    Devuelve:
        symbols: lista de tickers
        weights: dict {ticker: weight}
    """
    pf = db.query(models.Portfolio).filter_by(id=portfolio_id).first()
    if not pf:
        raise ValueError("Portfolio not found")

    if not pf.assets:
        raise ValueError("Portfolio has no assets")

    weights = {a.symbol: float(a.weight) for a in pf.assets}
    symbols = list(weights.keys())
    total_w = sum(weights.values())
    if total_w <= 0:
        raise ValueError("Portfolio weights sum <= 0")

    # Normalizamos por seguridad
    weights = {k: v / total_w for k, v in weights.items()}

    return symbols, weights


def load_portfolio_returns(
    db: Session,
    portfolio_id: int,
    history_days: int = HISTORY_DAYS,
) -> Tuple[pd.DataFrame, Dict[str, float]]:
    """
    Carga precios históricos de los activos de la cartera y devuelve:
        - returns_df: DataFrame de retornos simples (pct_change) alineados
        - weights_dict: dict {ticker: weight} normalizados
    """
    symbols, weights = get_portfolio_symbols_and_weights(db, portfolio_id)

    prices = load_prices(symbols, days=history_days)
    if prices is None or prices.empty:
        raise ValueError("Price history unavailable")

    returns_df = prices.pct_change().dropna()
    if len(returns_df) < MIN_OBS:
        raise ValueError("Not enough data to estimate portfolio returns")

    # Filtramos columnas a las que tengan precios + pesos
    cols = [c for c in returns_df.columns if c in weights]
    if not cols:
        raise ValueError("No overlapping symbols between prices and portfolio")

    returns_df = returns_df[cols]
    weights = {k: weights[k] for k in cols}
    # Renormalizamos por si hemos perdido algún activo
    total_w = sum(weights.values())
    weights = {k: v / total_w for k, v in weights.items()}

    return returns_df, weights


# ---------------------------------------------------------------------
# Montecarlo sobre cartera
# ---------------------------------------------------------------------

def _to_log_returns(df: pd.DataFrame) -> pd.DataFrame:
    return np.log1p(df.dropna())


def monte_carlo_portfolio(
    log_returns: pd.DataFrame,
    weights_dict: Dict[str, float],
    days_forecast: int,
    n_sims: int = N_SIMULATIONS,
    start_value: float = START_VALUE,
    seed: int = 42,
) -> Dict[str, object]:
    """
    Simula trayectorias del valor de la cartera mediante Montecarlo.
    Devuelve bandas y los pesos usados.
    """
    if log_returns.empty:
        raise ValueError("Empty log_returns for Monte Carlo simulation")

    # Alineamos pesos con columnas reales
    cols = list(log_returns.columns)
    w = np.array([weights_dict.get(c, 0.0) for c in cols], dtype=float)

    if w.sum() <= 0:
        raise ValueError("All portfolio weights are zero after alignment")
    w = w / w.sum()

    # Guardamos también los pesos "ordenados" según log_returns.columns
    weights_used = {col: float(val) for col, val in zip(cols, w)}

    # Parámetros diarios del portfolio
    mu_vec = log_returns.mean().values
    cov_mat = log_returns.cov().values

    mu_p = float(np.dot(w, mu_vec))
    sigma_p = float(np.sqrt(w.T @ cov_mat @ w))

    # Montecarlo
    if sigma_p <= 0:
        values = np.full((n_sims, days_forecast),
                         start_value * np.exp(mu_p * np.arange(1, days_forecast + 1)))
    else:
        rng = np.random.default_rng(seed)
        rets = rng.normal(loc=mu_p, scale=sigma_p, size=(n_sims, days_forecast))
        cum_log = np.cumsum(rets, axis=1)
        values = start_value * np.exp(cum_log)

    # Percentiles por día
    p5 = np.percentile(values, 5, axis=0).tolist()
    p50 = np.percentile(values, 50, axis=0).tolist()
    p95 = np.percentile(values, 95, axis=0).tolist()

    return {
        "p5": p5,
        "p50": p50,
        "p95": p95,
        "weights_used": weights_used
    }


# ---------------------------------------------------------------------
# Forecast combinado: cartera actual vs optimizada
# ---------------------------------------------------------------------
def build_portfolio_forecast(
    db: Session,
    portfolio_id: int,
    days_forecast: int,
) -> Dict[str, object]:
    """
    Calcula el forecast Montecarlo para:
        - cartera actual (pesos de BD)
        - cartera optimizada (método ganador)

    Devuelve:
        {
          "dates": [...],
          "current": {p5, p50, p95},
          "optimized": {p5, p50, p95},
          "no_change": bool
        }
    """
    if days_forecast <= 0:
        raise ValueError("days_forecast must be positive")

    # 1) Histórico de retornos + pesos actuales
    returns_df, current_weights = load_portfolio_returns(
        db=db,
        portfolio_id=portfolio_id,
        history_days=HISTORY_DAYS,
    )

    window = returns_df.tail(HISTORY_DAYS)
    log_ret = _to_log_returns(window)

    # 2) Determinar pesos optimizados (sin Montecarlo todavía)
    methods_results, best, _ = choose_best_optimization_method(window)
    optimized_weights = best["weights"]

    # 3) Normalizar pesos antes de comparar
    cw = {k: float(v) for k, v in current_weights.items()}
    ow = {k: float(v) for k, v in optimized_weights.items()}

    # Compara sin orden
    no_change = (sorted(cw.items()) == sorted(ow.items()))

    # 4) Montecarlo cartera actual
    current_bands = monte_carlo_portfolio(
        log_returns=log_ret,
        weights_dict=current_weights,
        days_forecast=days_forecast,
        n_sims=N_SIMULATIONS,
        start_value=START_VALUE,
    )

    # 5) Montecarlo cartera optimizada
    optimized_bands = monte_carlo_portfolio(
        log_returns=log_ret,
        weights_dict=optimized_weights,
        days_forecast=days_forecast,
        n_sims=N_SIMULATIONS,
        start_value=START_VALUE,
    )

    # 6) Construcción de fechas futuras
    last_date = returns_df.index[-1]
    future_dates = pd.bdate_range(
        last_date + pd.Timedelta(days=1),
        periods=days_forecast,
    )
    dates = [d.strftime("%Y-%m-%d") for d in future_dates]

    # 7) Respuesta final
    return {
        "dates": dates,
        "current": {
            "p5": current_bands["p5"],
            "p50": current_bands["p50"],
            "p95": current_bands["p95"],
            "weights_used": current_bands["weights_used"],
        },
        "optimized": {
            "p5": optimized_bands["p5"],
            "p50": optimized_bands["p50"],
            "p95": optimized_bands["p95"],
            "weights_used": optimized_bands["weights_used"],
        },
        "no_change": no_change,
    }


def weights_are_equal(w1: Dict[str, float], w2: Dict[str, float], tol: float = 1e-4) -> bool:
    """
    Compara pesos de dos carteras. Devuelve True si todos los pesos
    difieren menos que 'tol'.
    """
    if set(w1.keys()) != set(w2.keys()):
        return False

    for k in w1:
        if abs(w1[k] - w2[k]) > tol:
            return False

    return True

