# ======================================================
# ===============  CALLBACKS DE CARTERAS  ==============
# ======================================================

from dash import callback, Input, Output, State, ctx, no_update, ALL
from dash.exceptions import PreventUpdate
from dash import html, dcc
import dash_bootstrap_components as dbc
from services.backend_api import API_BASE

import requests

from services.backend_api import api_get, api_post, API_BASE
from services.portfolio_logic import normalize_weights
from components.tables import build_assets_table
from services.portfolio_logic import detect_benchmark


# ======================================================
# ========== BENCHMARKS REALES (12 ÍNDICES) ============
# ======================================================

BENCHMARK_LIST = [
    "NASDAQ",
    "S&P500",
    "DOWJONES",
    "IBEX35",
    "EUROSTOXX50",
    "FTSE100",
    "DAX",
    "CAC40",
    "MSCI_WORLD",
    "MSCI_EM",
    "NIKKEI225",
    "GOLD",
    "CRYPTO",
]

# Mapeo a Yahoo Finance (por si lo necesitas en otras partes)
BENCHMARK_TICKERS = {
    "NASDAQ": "^IXIC",
    "S&P500": "^GSPC",
    "DOWJONES": "^DJI",
    "IBEX35": "^IBEX",
    "EUROSTOXX50": "^STOXX50E",
    "FTSE100": "^FTSE",
    "DAX": "^GDAXI",
    "CAC40": "^FCHI",
    "MSCI_WORLD": "URTH",       # ETF MSCI World
    "MSCI_EM": "EEM",           # ETF MSCI Emerging Markets
    "NIKKEI225": "^N225",
    "GOLD": "GC=F",
    "CRYPTO": "BTC-USD",
}

BENCHMARK_ICONS = {
    "NASDAQ": "🇺🇸",
    "S&P500": "🇺🇸",
    "DOWJONES": "🇺🇸",
    "IBEX35": "🇪🇸",
    "EUROSTOXX50": "🇪🇺",
    "FTSE100": "🇬🇧",
    "DAX": "🇩🇪",
    "CAC40": "🇫🇷",
    "MSCI_WORLD": "🌍",
    "MSCI_EM": "🌏",
    "NIKKEI225": "🇯🇵",
    "GOLD": "🟡",
    "CRYPTO": "🪙",
    "FOREX": "💱",
}


# ======================================================
# === MOTOR PARA DEDUCIR BENCHMARK A PARTIR DEL TICKER =
# ======================================================

def infer_benchmark_from_symbol(symbol: str):
    """
    Devuelve el benchmark adecuado según el ticker detectado.
    Usa reglas reales basadas en sufijos y tickers típicos.
    """
    if not symbol:
        return None

    s = symbol.upper()

    # ---- Crypto ----
    if s.endswith("-USD") or s.endswith("-USDT"):
        return "CRYPTO"

    # ---- Forex ----
    if "=X" in s:
        return "FOREX"

    # ---- Oro / materias primas ----
    if s in ["GC=F", "SI=F", "CL=F"]:
        return "GOLD"

    # ---- España (.MC) ----
    if s.endswith(".MC"):
        return "IBEX35"

    # ---- Alemania ----
    if s.endswith(".DE"):
        return "DAX"

    # ---- Francia ----
    if s.endswith(".PA"):
        return "CAC40"

    # ---- UK ----
    if s.endswith(".L"):
        return "FTSE100"

    # ---- Japón ----
    if s.endswith(".T"):
        return "NIKKEI225"

    # ---- ETFs / acciones USA ligadas a índices ----
    if s in ["SPY", "VOO", "IVV"]:
        return "S&P500"

    if s in ["QQQ", "AAPL", "MSFT", "META", "TSLA", "NVDA", "AMZN", "GOOGL"]:
        return "NASDAQ"

    # ---- ETFs globales ----
    if s in ["URTH"]:
        return "MSCI_WORLD"

    if s in ["EEM"]:
        return "MSCI_EM"

    # ---- Índices directos ----
    index_map = {
        "^IXIC": "NASDAQ",
        "^GSPC": "S&P500",
        "^DJI": "DOWJONES",
        "^IBEX": "IBEX35",
        "^STOXX50E": "EUROSTOXX50",
        "^FTSE": "FTSE100",
        "^GDAXI": "DAX",
        "^FCHI": "CAC40",
        "^N225": "NIKKEI225",
    }
    if s in index_map:
        return index_map[s]

    return None  # no se puede inferir


# ======================================================
# ===============   MODAL DE NUEVA CARTERA   ===========
# ======================================================

@callback(
    Output("create-portfolio-modal", "is_open"),
    Input("btn-open-create-portfolio", "n_clicks"),
    Input("btn-cancel-create-portfolio", "n_clicks"),
    Input("btn-save-portfolio", "n_clicks"),
    State("create-portfolio-modal", "is_open"),
    State("new-portfolio-name", "value"),
    prevent_initial_call=True,
)
def toggle_create_modal(n_open, n_cancel, n_save, is_open, name):
    trigger = ctx.triggered_id

    if trigger == "btn-open-create-portfolio":
        return True

    if trigger == "btn-cancel-create-portfolio":
        return False

    if trigger == "btn-save-portfolio":
        # Si no hay nombre, no cierres el modal
        if not name:
            return True
        return False

    return is_open


# ======================================================
# =================  BUSCADOR DE ACTIVOS  ==============
# ======================================================
@callback(
    Output("search-asset", "options"),
    Input("search-asset", "search_value"),
    Input("search-asset", "value"),
)
def smart_search_assets(search_value, selected_value):
    # 1) Si el usuario acaba de seleccionar una opción → NO actualizar
    if ctx.triggered_id == "search-asset" and selected_value:
        raise PreventUpdate

    # 2) Si no hay búsqueda → lista vacía
    if not search_value or len(search_value) < 2:
        return []

    # 3) Buscar activos
    try:
        resp = requests.get(
            f"{API_BASE}/search/ticker",
            params={"q": search_value},
            timeout=5,
        )
        resp.raise_for_status()
        raw = resp.json()
    except Exception:
        return []

    return [
        {"label": f"{item['symbol']} — {item.get('name','')}", "value": item["symbol"]}
        for item in raw
    ]


# ======================================================
# =================  BENCHMARKS (STATIC)  ==============
# ======================================================

@callback(
    Output("new-benchmarks", "options"),
    Input("new-benchmarks", "search_value"),
)
def smart_search_benchmarks(_):
    """
    Benchmarks humanos con iconos (suficientes para la App).
    """
    return [
        {"label": f"{BENCHMARK_ICONS.get(b, '')}  {b}", "value": b}
        for b in BENCHMARK_LIST
    ]


# ======================================================
# ======  (YA NO USAMOS BENCHMARK POR ACTIVO MANUAL) ===
# ======  LA COLUMNA DERECHA ES PESO INICIAL (%)  ======
# ======================================================

# Nota: el dropdown "asset-benchmark" se ha eliminado del modal.
# En su lugar, hay un Input numérico: id="new-asset-weight".


# ======================================================
# ==============  AÑADIR / ELIMINAR ACTIVOS  ===========
# ======================================================
from dash.exceptions import PreventUpdate

@callback(
    Output("new-portfolio-assets", "data"),
    Output("new-portfolio-assets-view", "children"),
    Output("new-asset-error", "children"),

    Input("btn-add-asset", "n_clicks"),
    Input({"type": "delete-asset", "index": ALL}, "n_clicks"),

    State("search-asset", "value"),
    State("asset-weight-input", "value"),
    State("new-portfolio-assets", "data"),

    prevent_initial_call=True,
)
def manage_assets(add_clicks, delete_clicks, symbol, weight, assets):
    trigger = ctx.triggered_id

    # Inicializar si está vacío
    if assets is None:
        assets = []

    # ------------------------------------
    # AÑADIR NUEVO ACTIVO
    # ------------------------------------
    if trigger == "btn-add-asset":
        if not symbol:
            return assets, build_assets_table(assets), "Selecciona un activo."

        # Validar peso
        try:
            w = float(weight)
        except:
            return assets, build_assets_table(assets), "Peso inválido."

        if w < 0 or w > 100:
            return assets, build_assets_table(assets), "Peso debe estar entre 0 y 100."

        # Detectar benchmark automáticamente (puedo mejorarlo si quieres)
        benchmark = infer_benchmark_from_symbol(symbol)

        # Guardar peso como proporción
        assets.append({
            "symbol": symbol.upper(),
            "benchmark": benchmark,
            "weight": w / 100.0,
        })

        return assets, build_assets_table(assets), ""

    # ------------------------------------
    # ELIMINAR ACTIVO
    # ------------------------------------
    if isinstance(trigger, dict) and trigger.get("type") == "delete-asset":
        idx = trigger["index"]
        new_assets = [a for i, a in enumerate(assets) if i != idx]
        return new_assets, build_assets_table(new_assets), ""

    raise PreventUpdate



# ======================================================
# ==============   GUARDAR / CARGAR CARTERAS ===========
# ======================================================


@callback(
    Output("portfolio-select-container", "children"),
    Output("selected-portfolio", "data", allow_duplicate=True),
    Input("btn-refresh-portfolios", "n_clicks"),
    Input("btn-new-portfolio-demo", "n_clicks"),
    Input("btn-save-portfolio", "n_clicks"),
    State("new-portfolio-name", "value"),
    State("new-portfolio-assets", "data"),
    prevent_initial_call=True,
)
def load_portfolios(refresh, demo, save, new_name, new_assets):
    trigger = ctx.triggered_id

    # --- Crear demo ---
    if trigger == "btn-new-portfolio-demo":
        demo_assets = [
            {"symbol": "AAPL", "benchmark": "NASDAQ", "weight": 0.25},
            {"symbol": "MSFT", "benchmark": "NASDAQ", "weight": 0.25},
            {"symbol": "SPY", "benchmark": "S&P500",  "weight": 0.25},
            {"symbol": "BTC-USD", "benchmark": "CRYPTO", "weight": 0.25},
        ]
        api_post("/portfolios", json={"name": "Cartera demo", "assets": demo_assets})

    # --- Guardar nueva cartera ---
    if trigger == "btn-save-portfolio" and new_name and new_assets:
        cleaned = normalize_weights(new_assets)
        payload = [{
            "symbol": a["symbol"],
            "weight": float(a["weight"]),
            "benchmark": a.get("benchmark") or detect_benchmark(a["symbol"])
        } for a in cleaned]
        api_post("/portfolios", json={"name": new_name, "assets": payload})

    # --- Obtener todas ---
    r = api_get("/portfolios")
    p_list = r.json()

    options = [{"label": p["name"], "value": p["id"]} for p in p_list]

    first_id = p_list[-1]["id"]  # seleccionamos la última creada

    dropdown = dcc.Dropdown(
        id="portfolio-select-dropdown",
        options=options,
        value=first_id,
        clearable=False,
        className="dropdown-dark"
    )

    selected_full = next((p for p in p_list if p["id"] == first_id), None)

    return dropdown, selected_full

@callback(
    Output("selected-portfolio", "data", allow_duplicate=True),
    Input("portfolio-select-dropdown", "value"),
    prevent_initial_call=True
)
def change_selected_portfolio(portfolio_id):

    if not portfolio_id:
        raise PreventUpdate

    r = api_get(f"/portfolios/{portfolio_id}")
    if r.status_code != 200:
        raise PreventUpdate

    return r.json()


# ======================================================
# =======  MOSTRAR U OCULTAR METADATOS CARTERA =========
# ======================================================

@callback(
    Output("portfolio-meta-container", "style"),
    Input("selected-portfolio", "data"),
)
def show_meta(selected):
    if selected:
        return {"display": "block"}
    return {"display": "none"}


# ======================================================
# ========  NAVEGAR AUTOMÁTICAMENTE A OVERVIEW =========
# ======================================================

@callback(
    Output("main-tabs", "value"),
    Input("portfolio-select-dropdown", "value"),
    prevent_initial_call=True,
    allow_missing=True,
)
def auto_go_to_overview(_):
    return "tab-overview"



@callback(
    Output("asset-weight-input", "value"),
    Output("asset-weight-slider", "value"),
    Input("asset-weight-input", "value"),
    Input("asset-weight-slider", "value"),
)
def sync_weight(input_value, slider_value):
    # Saber quién disparó
    trigger = ctx.triggered_id

    # Si cambia el INPUT → actualizar slider
    if trigger == "asset-weight-input":
        try:
            v = float(input_value)
            v = max(0, min(100, v))  # limitar rango
            return v, v
        except:
            return no_update, no_update

    # Si cambia el SLIDER → actualizar input
    if trigger == "asset-weight-slider":
        try:
            v = float(slider_value)
            return v, v
        except:
            return no_update, no_update

    # Estado inicial
    return no_update, no_update

@callback(
    Output("selected-portfolio", "data"),
    Input("portfolio-select-dropdown", "value"),
    prevent_initial_call=True
)
def update_selected_portfolio(portfolio_id):
    if not portfolio_id:
        return dash.no_update

    r = api_get(f"/portfolios/{portfolio_id}")
    if r.status_code != 200:
        return dash.no_update

    return r.json()

