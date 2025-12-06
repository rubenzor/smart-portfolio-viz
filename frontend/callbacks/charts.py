# frontend/callbacks/charts.py
import time
from dash import callback, Input, Output, State,html
from components.charts import optimization_tab
from components.charts import overview_tab
from components.corr_table import correlation_table
import requests
import pandas as pd 

@callback(
    Output("main-tab-content", "children"),
    Input("main-tabs", "value"),
    State("selected-portfolio", "data"),
)
def render_main_tab(tab, portfolio):
    time.sleep(0.6) 

    if tab == "tab-overview":
        return overview_tab(portfolio)
    elif tab == "tab-opt":
        return optimization_tab()
    elif tab == "tab-adv":
            return html.Div(
                [
                    html.H3("Análisis avanzado", className="text-center mt-4 mb-3"),
                    html.P(
                        "Próximamente: análisis de sentimiento, señales AI y métricas avanzadas.",
                        className="text-muted text-center",
                    ),
                ],
                className="p-4",
            )

""" @callback(
    Output("corr-corr-table", "children"),
    Input("selected-portfolio", "data"),
    prevent_initial_call=True
)
def update_corr_table(portfolio):

    # -------------------------------
    # Validación inicial
    # -------------------------------
    if not portfolio or not portfolio.get("assets"):
        return "Sin datos"

    # Extraer símbolos con peso > 0
    symbols = [
        a["symbol"]
        for a in portfolio.get("assets", [])
        if float(a.get("weight", 0)) > 0
    ]

    if len(symbols) < 2:
        return "Se requieren al menos 2 activos para correlaciones"

    pf_id = portfolio["id"]

    # -------------------------------
    # Llamada al backend
    # -------------------------------
    try:
        r = requests.get(f"http://backend:8000/api/v1/portfolios/{pf_id}/history?days=365")
        r.raise_for_status()
        raw = r.json()
    except Exception as e:
        return f"Error cargando datos: {e}"

    # -------------------------------
    # Convertir histórico
    # -------------------------------
    try:
        df = parse_backend_history(raw, symbols)
    except Exception:
        return "Error procesando histórico"

    if df.empty:
        return "Sin datos suficientes"

    # Limpiar columnas vacías
    df = df.dropna(axis=1, how="all")

    # Mantener solo columnas válidas
    df = df[[s for s in symbols if s in df.columns]]

    if df.shape[1] < 2:
        return "Datos insuficientes para correlación"

    # -------------------------------
    # Calcular correlación
    # -------------------------------
    returns = df.pct_change().dropna()
    corr = returns.corr().round(2)

    # -------------------------------
    # Renderizar tabla ORIGINAL
    # -------------------------------
    return correlation_table(list(corr.columns), corr.values)
 """

def parse_backend_history(raw, symbols):
    dates = pd.to_datetime(raw["dates"])
    df = pd.DataFrame({"date": dates}).set_index("date")


    for sym in symbols:
        df[sym] = raw["assets"].get(sym, None)

    return df