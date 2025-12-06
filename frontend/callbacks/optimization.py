# frontend/callbacks/optimization.py
import time
from dash import callback, Input, Output, State, html, no_update, ctx
import dash_bootstrap_components as dbc

from services.backend_api import api_post, api_get, api_patch, api_put
from components.charts import make_frontier_chart
from components.tables import (
    build_optimization_comparison_table,
    build_optimization_methods_table,
)

@callback(
    Output("opt-msg", "children"),
    Output("opt-frontier-chart", "figure"),
    Output("opt-table-container", "children"),
    Output("opt-header-info", "children"),
    Output("opt-results-store", "data"),
    Input("btn-run-opt", "n_clicks"),
    State("selected-portfolio", "data"),
    prevent_initial_call=True,
)
def run_optimization(n_clicks, portfolio):
    time.sleep(1.0)
    if not n_clicks:
        return (no_update, make_frontier_chart([], []), no_update, no_update, no_update)

    if not portfolio:
        return (
            dbc.Alert("Selecciona una cartera primero.", color="warning"),
            make_frontier_chart([], []),
            "",
            "",
            None,
        )

    pid = portfolio["id"]

    # ------------ Llamada al backend ------------
    r = api_post("/optimize", json={"portfolio_id": pid})
    if r.status_code != 200:
        return (
            dbc.Alert(f"Error al optimizar: {r.text}", color="danger"),
            make_frontier_chart([], []),
            "",
            "",
            None,
        )

    data = r.json() or {}

   # ------------ Datos multi-método ------------
    methods = data.get("methods") or []

    best_method_name = data.get("best_method")
    reason = data.get("reason")
    horizon_days = data.get("horizon_days")

    risks = data.get("efficient_frontier", {}).get("risks", [])
    rets = data.get("efficient_frontier", {}).get("returns", [])

    # Pesos actuales desde BD (backend envía esto correctamente)
    current_weights = data.get("current_weights", {})

    # --- Pesos optimizados ---
    # El backend NO envía optimized_weights.
    # Hay que obtenerlos del método ganador dentro de "methods".

    best_method = next(
        (m for m in methods if m.get("method") == best_method_name),
        None
    )

    if best_method:
        optimized_weights = best_method.get("weights", {})
    else:
        optimized_weights = {}   # fallback


    # ------------ Punto óptimo ------------
    winner = next((m for m in methods if m.get("method") == best_method_name), None)
    opt_risk = winner.get("volatility") if winner else None
    opt_return = winner.get("expected_return") if winner else None

    # ------------ Tabla de métodos ------------
    methods_table = build_optimization_methods_table(methods, best_method_name)

    # ------------ Tabla de pesos ------------
    weights_table = build_optimization_comparison_table(
        current_weights=current_weights,
        optimized_weights=optimized_weights,
    )

    # ------------ Texto del horizonte ------------
    resumen = html.Div(
        [
            html.P(f"Método seleccionado automáticamente: {best_method_name}", className="mb-1"),
            html.P(f"Razón: {reason}", className="text-muted mb-1"),
            html.P(f"Horizonte histórico utilizado: {horizon_days} días",
                   className="text-muted mb-0"),
        ],
        className="mt-3"
    )

    header_children = html.Div([methods_table, resumen])

    # ------------ Gráfica ------------
    fig = make_frontier_chart(risks, rets, opt_risk, opt_return)

    store_data = {
        "portfolio_id": pid,
        "optimized_weights": optimized_weights,
    }

    msg = dbc.Alert("Optimización completada ✅", color="success")

    return msg, fig, weights_table, header_children, store_data
@callback(
    Output("opt-msg", "children", allow_duplicate=True),
    Output("main-tabs", "value", allow_duplicate=True),
    Output("selected-portfolio", "data", allow_duplicate=True),
    Input("btn-apply-opt", "n_clicks"),
    State("opt-results-store", "data"),
    prevent_initial_call=True,
)
def apply_optimized_weights(n_clicks, opt_data):

    if not n_clicks:
        return no_update, no_update, no_update

    if not opt_data or "portfolio_id" not in opt_data or "optimized_weights" not in opt_data:
        return (
            dbc.Alert("Primero ejecuta la optimización.", color="warning"),
            no_update,
            no_update,
        )

    pid = opt_data["portfolio_id"]
    weights = opt_data["optimized_weights"]

    # =============================
    # 1) Obtener cartera actual
    # =============================
    r0 = api_get(f"/portfolios/{pid}")
    if r0.status_code != 200:
        return (
            dbc.Alert("No se pudo cargar la cartera.", color="danger"),
            no_update,
            no_update,
        )

    pf = r0.json()
    assets = pf.get("assets", [])

    # =============================
    # 2) Actualizar pesos
    # =============================
    updated_assets = []
    for a in assets:
        sym = a["symbol"]
        new_w = float(weights.get(sym, a["weight"]))  # usar optimizado si existe
        if new_w > 0:
            a["weight"] = new_w
            updated_assets.append(a)

    # =============================
    # 3) Enviar PUT al backend
    # =============================
    payload = {
        "assets": updated_assets,
        "benchmarks": pf.get("benchmarks", []),
        "name": pf.get("name"),
        "kind": pf.get("kind"),
    }

    r = api_put(f"/portfolios/{pid}", json=payload)
    if r.status_code != 200:
        return (
            dbc.Alert(f"Error al aplicar: {r.text}", color="danger"),
            no_update,
            no_update,
        )

    # =============================
    # 4) Recargar cartera
    # =============================
    r2 = api_get(f"/portfolios/{pid}")
    updated_pf = r2.json() if r2.status_code == 200 else pf

    return (
        dbc.Alert("Pesos aplicados correctamente ✅", color="success"),
        "tab-overview",
        updated_pf,
    )