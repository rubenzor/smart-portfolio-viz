# frontend/callbacks/forecasting.py

from dash import callback, Input, Output, State, no_update, ctx, html
import dash_bootstrap_components as dbc

from services.backend_api import api_post
from components.charts import make_montecarlo_figure
from components.tables import build_montecarlo_comparison
from components.utils import empty_dark_figure


@callback(
    Output("forecast-message", "children"),       # 1 — Mensaje
    Output("mc-current-chart", "figure"),         # 2 — Gráfico actual
    Output("mc-optimized-chart", "figure"),       # 3 — Gráfico optimizado
    Output("mc-compare-block", "children"),       # 4 — Comparativa P50
    Output("optimized-section", "style"),
    Input("btn-run-mc", "n_clicks"),
    State("mc-days", "value"),
    State("selected-portfolio", "data"),
    prevent_initial_call=True,
)
def run_montecarlo(n, days, portfolio):

    # ============================
    # Validación básica
    # ============================
    if not portfolio:
        return (
            "",
            empty_dark_figure(),
            empty_dark_figure(),
            dbc.Alert("No hay cartera seleccionada.", color="danger"),
        )

    pid = portfolio["id"]
    days = int(days or 30)

    # ============================
    # Llamada al backend
    # ============================
    try:
        payload = {"portfolio_id": pid, "days_forecast": days}

        # Si hay pesos optimizados en memoria → inclúyelos
        opt_store = ctx.states.get("opt-results-store.data")
        if opt_store and "optimized_weights" in opt_store:
            payload["optimized_weights"] = opt_store["optimized_weights"]

        r = api_post("/forecast/portfolio", json=payload)
        r.raise_for_status()

    except Exception as e:
        return (
            "",
            no_update,
            no_update,
            dbc.Alert(f"Error llamando al backend: {e}", color="danger"),
        )

    data = r.json()

    current = data.get("current", {})
    optimized = data.get("optimized", {})
    backend_no_change = data.get("no_change", False)

    # ============================
    # DEBUG INFO
    # ============================
    try:
        p50_actual = current["p50"][-1]
        p50_opt = optimized["p50"][-1]
        diff_real = abs(p50_actual - p50_opt)

        print("DEBUG P50 ACTUAL =", p50_actual)
        print("DEBUG P50 OPT =", p50_opt)
        print("DEBUG DIFF REAL =", diff_real)

    except Exception as e:
        print("DEBUG ERROR:", e)
        diff_real = 999

    # ============================
    # THRESHOLD DE CAMBIO SIGNIFICATIVO
    # ============================
    THRESHOLD = 0.0005  # 0.05%

    no_change_effective = backend_no_change or (diff_real < THRESHOLD)

    print("DEBUG THRESHOLD =", THRESHOLD)
    print("DEBUG no_change_effective =", no_change_effective)

    # ===========================================================
    # 📌 CASO 1 — NO CAMBIO SIGNIFICATIVO (UX BONITA + COMPACTA)
    # ===========================================================
    if no_change_effective:

        # Rendimiento esperado (P50)
        p50_actual_pct = round((current["p50"][-1] - 1) * 100, 2)

        msg = dbc.Alert(
            "No se detectan mejoras significativas al optimizar los pesos. "
            "Se muestra únicamente la simulación de la cartera actual.",
            color="info",
            className="mb-3",
            style={
                "padding": "8px 14px",
                "fontSize": "14px",
                "borderRadius": "6px",
                "maxWidth": "600px",
                "margin": "0 auto",
            },
        )

        # Tarjeta compacta con el P50 esperado
        summary_card = dbc.Card(
            dbc.CardBody([
                html.H5("Rendimiento esperado (P50)", className="text-center"),
                html.H2(
                    f"{p50_actual_pct}%",
                    className="text-center",
                    style={"color": "#00E0FF", "fontWeight": "bold"},
                ),
            ]),
            className="neon-card mb-4",
            style={"maxWidth": "400px", "margin": "0 auto"},
        )

        fig_current = make_montecarlo_figure(
            current,
            "Montecarlo — Cartera actual"
        )

        return (
            html.Div([msg, summary_card]),   # mensaje bonito + panel P50
            fig_current,                     # solo gráfica actual
            empty_dark_figure(),             # oculta optimizada
            html.Div(),                      # comparativa vacía
            {"display": "none"}              # 🔥 OCULTA TODA LA SECCIÓN OPTIMIZADA
        )


    # ===========================================================
    # 📌 CASO 2 — CAMBIO NORMAL → mostrar todo
    # ===========================================================

    fig_current = make_montecarlo_figure(
        current, "Montecarlo — Cartera actual"
    )

    fig_opt = make_montecarlo_figure(
        optimized, "Montecarlo — Cartera optimizada"
    )

    compare_block = build_montecarlo_comparison(
        current["p50"],
        optimized["p50"],
        days
    )

    return (
        html.Div(),                      # sin mensaje
        fig_current,
        fig_opt,
        compare_block,
        {"display": "block"}             # 🔥 MOSTRAR SECCIÓN OPTIMIZADA
    )

