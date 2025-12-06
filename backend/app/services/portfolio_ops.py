# backend/app/services/portfolio_ops.py

from typing import Dict, List, Tuple, Optional

import numpy as np
import pandas as pd
import scipy.optimize as optimize


# =====================================================================
#                               CONSTANTS
# =====================================================================

TRADING_DAYS = 252
MIN_OBS = 60   # Observaciones mínimas para optimizar
FIXED_HORIZON_DAYS = 126  # Ventana fija para todos los métodos


# =====================================================================
#                        HELPER FUNCTIONS
# =====================================================================

def _to_log_returns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convierte retornos simples a log-returns y elimina NaNs.
    """
    return np.log1p(df.dropna())


def _annualized_stats(log_ret: pd.DataFrame) -> Tuple[pd.Series, pd.DataFrame]:
    """
    Retorno medio anualizado (mu)
    Matriz de covarianza anualizada (cov)
    """
    mu = log_ret.mean() * TRADING_DAYS
    cov = log_ret.cov() * TRADING_DAYS
    return mu, cov


def _portfolio_stats(w: np.ndarray, mu: pd.Series, cov: pd.DataFrame) -> Dict[str, float]:
    """
    Retorno esperado, volatilidad y Sharpe anualizados.
    """
    ret = float(np.dot(w, mu.values))
    vol = float(np.sqrt(w.T @ cov.values @ w))
    sharpe = ret / vol if vol > 0 else 0.0

    return {
        "expected_return": ret,
        "volatility": vol,
        "sharpe_ratio": sharpe
    }


# =====================================================================
#                     OPTIMIZATION METHODS (NO MONTECARLO)
# =====================================================================

def opt_mean_variance(window: pd.DataFrame, risk_aversion: float = 3.0) -> Dict[str, float]:
    """
    Mean-Variance clásico: maximiza utilidad = μᵀw - λσ²
    """
    log_ret = _to_log_returns(window)
    mu, cov = _annualized_stats(log_ret)

    tickers = list(window.columns)
    n = len(tickers)

    def objective(w):
        stats = _portfolio_stats(w, mu, cov)
        return -(stats["expected_return"] - risk_aversion * (stats["volatility"] ** 2))

    cons = ({'type': 'eq', 'fun': lambda w: np.sum(w) - 1},)
    bounds = [(0, 1)] * n
    x0 = np.array([1/n] * n)

    res = optimize.minimize(objective, x0, method="SLSQP", bounds=bounds, constraints=cons)

    if not res.success:
        raise ValueError(f"Mean-Variance optimization failed: {res.message}")

    stats = _portfolio_stats(res.x, mu, cov)

    return {
        "weights": dict(zip(tickers, res.x)),
        **stats
    }


def opt_min_variance(window: pd.DataFrame) -> Dict[str, float]:
    """
    Mínima volatilidad, sin restricciones de retorno.
    """
    log_ret = _to_log_returns(window)
    mu, cov = _annualized_stats(log_ret)

    tickers = list(window.columns)
    n = len(tickers)

    def objective(w):
        return _portfolio_stats(w, mu, cov)["volatility"]

    cons = ({'type': 'eq', 'fun': lambda w: np.sum(w) - 1},)
    bounds = [(0, 1)] * n
    x0 = np.array([1/n] * n)

    res = optimize.minimize(objective, x0, method="SLSQP", bounds=bounds, constraints=cons)

    if not res.success:
        raise ValueError(f"Min-Variance optimization failed: {res.message}")

    stats = _portfolio_stats(res.x, mu, cov)

    return {
        "weights": dict(zip(tickers, res.x)),
        **stats
    }


def opt_max_sharpe(window: pd.DataFrame) -> Dict[str, float]:
    """
    Maximiza ratio Sharpe – tu Markowitz EXACTO.
    """
    log_ret = _to_log_returns(window)
    mu, cov = _annualized_stats(log_ret)

    tickers = list(window.columns)
    n = len(tickers)

    def objective(w):
        stats = _portfolio_stats(w, mu, cov)
        return -stats["sharpe_ratio"]  # minimizar -Sharpe

    cons = ({'type': 'eq', 'fun': lambda w: np.sum(w) - 1},)
    bounds = [(0, 1)] * n
    x0 = np.array([1/n] * n)

    res = optimize.minimize(objective, x0, method="SLSQP",
                            bounds=bounds, constraints=cons)

    if not res.success:
        raise ValueError(f"Max-Sharpe optimization failed: {res.message}")

    stats = _portfolio_stats(res.x, mu, cov)

    return {
        "weights": dict(zip(tickers, res.x)),
        **stats
    }


def opt_risk_parity(window: pd.DataFrame) -> Dict[str, float]:
    """
    Equal Risk Contribution (Risk Parity).
    """
    log_ret = _to_log_returns(window)
    mu, cov = _annualized_stats(log_ret)

    tickers = list(window.columns)
    n = len(tickers)

    def risk_contribution(w):
        w = np.array(w)
        port_vol = np.sqrt(w.T @ cov.values @ w)
        mrc = cov.values @ w  # marginal contributions
        rc = w * mrc / port_vol
        return rc, port_vol

    def objective(w):
        rc, vol = risk_contribution(w)
        target = vol / n
        return float(np.sum((rc - target) ** 2))

    cons = ({'type': 'eq', 'fun': lambda w: np.sum(w) - 1},)
    bounds = [(0, 1)] * n
    x0 = np.array([1/n] * n)

    res = optimize.minimize(objective, x0, method="SLSQP",
                            bounds=bounds, constraints=cons)

    if not res.success:
        raise ValueError(f"Risk-Parity optimization failed: {res.message}")

    stats = _portfolio_stats(res.x, mu, cov)

    return {
        "weights": dict(zip(tickers, res.x)),
        **stats
    }


def opt_black_litterman(window: pd.DataFrame,
                        views: Optional[Dict] = None) -> Dict[str, float]:
    """
    Placeholder de Black-Litterman.
    En el futuro añadirás:
    - P, Q
    - tau
    - distribución posterior
    """
    return opt_mean_variance(window, risk_aversion=1.0)


# =====================================================================
#                        MULTI-METHOD SELECTOR
# =====================================================================

def choose_best_optimization_method(window: pd.DataFrame):
    """
    Ejecuta TODOS los métodos y devuelve:
    - Lista completa `methods_results`
    - El mejor método `best`
    - El segundo mejor método `second`
    """
    METHODS = [
        ("mean_variance", opt_mean_variance),
        ("min_variance", opt_min_variance),
        ("max_sharpe", opt_max_sharpe),
        ("risk_parity", opt_risk_parity),
        ("black_litterman", opt_black_litterman),
    ]

    results = []

    for name, fn in METHODS:
        try:
            out = fn(window)
            results.append({
                "method": name,
                "expected_return": out["expected_return"],
                "volatility": out["volatility"],
                "sharpe_ratio": out["sharpe_ratio"],
                "weights": out["weights"]
            })
        except Exception:
            continue

    if not results:
        raise ValueError("No optimization method succeeded")

    results_sorted = sorted(results,
                            key=lambda r: r["sharpe_ratio"],
                            reverse=True)

    best = results_sorted[0]
    second = results_sorted[1] if len(results_sorted) > 1 else None

    return results_sorted, best, second


# =====================================================================
#                              REASON BUILDER
# =====================================================================

def build_reason(best_method: str, horizon_days: int,
                 best: Dict[str, float],
                 second: Optional[Dict[str, float]]) -> str:

    sr = round(best["sharpe_ratio"], 3)
    vol = round(best["volatility"] * 100, 2)
    ret = round(best["expected_return"] * 100, 2)

    method_name = {
        "mean_variance": "Mean-Variance",
        "min_variance": "Minimum Variance",
        "max_sharpe": "Maximum Sharpe",
        "risk_parity": "Risk Parity",
        "black_litterman": "Black-Litterman"
    }.get(best_method, best_method)

    if second:
        sr2 = round(second["sharpe_ratio"], 3)
        extra = f" Comparado con la alternativa siguiente (Sharpe {sr2})."
    else:
        extra = ""

    return (
        f"El método óptimo es {method_name} con Sharpe {sr}, "
        f"retorno anual esperado {ret}% y volatilidad {vol}%, "
        f"usando un horizonte de {horizon_days} días.{extra}"
    )

def compute_efficient_frontier(
    window: pd.DataFrame,
    n_points: int = 50
) -> Dict[str, List[float]]:
    """
    Calcula una aproximación determinista de la frontera eficiente de Markowitz
    (sin Montecarlo), usando una cuadrícula de retornos objetivo.

    Devuelve:
        {
            "risks": [ ... ],
            "returns": [ ... ]
        }
    con al menos ~20 puntos (si es posible).
    """
    log_ret = _to_log_returns(window)
    if log_ret.empty:
        return {"risks": [], "returns": []}

    mu, cov = _annualized_stats(log_ret)
    n = len(mu)
    if n == 0:
        return {"risks": [], "returns": []}

    mu_vals = mu.values
    min_ret = float(mu_vals.min())
    max_ret = float(mu_vals.max())

    # Evitar cuadrícula degenerada
    if max_ret <= min_ret:
        return {"risks": [], "returns": []}

    target_returns = np.linspace(min_ret, max_ret, n_points)

    bounds = [(0.0, 1.0)] * n
    base_cons = ({'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0},)
    x0 = np.array([1.0 / n] * n)

    risks: List[float] = []
    rets: List[float] = []

    for r_target in target_returns:
        def ret_constraint(w, r=r_target):
            return float(np.dot(w, mu_vals) - r)

        cons = base_cons + ({'type': 'eq', 'fun': ret_constraint},)

        # Minimizamos varianza para ese retorno objetivo
        res = optimize.minimize(
            lambda w: float(w.T @ cov.values @ w),
            x0,
            method="SLSQP",
            bounds=bounds,
            constraints=cons,
        )

        if not res.success:
            continue

        stats = _portfolio_stats(res.x, mu, cov)
        risks.append(stats["volatility"])
        rets.append(stats["expected_return"])

    # Si tenemos muy pocos puntos, intentamos interpolar
    if len(risks) >= 2 and len(risks) < 20:
        # Interpolación lineal en función del riesgo
        risks_np = np.array(risks)
        rets_np = np.array(rets)
        order = np.argsort(risks_np)
        risks_sorted = risks_np[order]
        rets_sorted = rets_np[order]

        new_risks = np.linspace(risks_sorted[0], risks_sorted[-1], 20)
        new_rets = np.interp(new_risks, risks_sorted, rets_sorted)

        risks = new_risks.tolist()
        rets = new_rets.tolist()

    return {
        "risks": risks,
        "returns": rets,
    }