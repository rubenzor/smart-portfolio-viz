from dash import callback, Input, Output, dcc, html
import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd

from callbacks.benchmark import _kpi_card
from services.yfinance_service import download_prices
from components.colors import BENCHMARK_COLORS, ASSET_COLORS, generate_color_map
from components.charts import empty_pie_option, empty_line_option, empty_bar_option
from components.corr_table import correlation_table

@callback(
    Output("overview-kpis-row", "children"),
    Output("alloc-chart", "option"),            # Pie chart 1 → Benchmark
    Output("alloc-asset-pie", "option"),        # Pie chart 2 → Activos
    Output("overview-perf-chart", "option"),    # Línea cartera 1 año
    Output("asset-returns-chart", "option"),    # Rentabilidad por activo
    Output("corr-corr-table", "children"),      # Correlación
    Input("selected-portfolio", "data"),
)
def update_overview_charts(portfolio):

    # Opciones vacías iniciales
    pie_bench_opt = empty_pie_option()
    pie_asset_opt = empty_pie_option()
    perf_opt = empty_line_option("Evolución cartera (1 año)")
    bar_opt = empty_bar_option("Rentabilidad por activo (1 año)")
    corr_html = "Sin datos"

    if not portfolio or not portfolio.get("assets"):
        return pie_bench_opt, pie_asset_opt, perf_opt, bar_opt, corr_html

    # ============================
    #  Filtrar activos válidos
    # ============================
    assets = [
        a for a in portfolio["assets"]
        if float(a.get("weight", 0)) > 0
    ]

    if not assets:
        return pie_bench_opt, pie_asset_opt, perf_opt, bar_opt, corr_html

    symbols = [a["symbol"] for a in assets]
    weights = np.array([float(a["weight"]) for a in assets])
    benchmarks = [a["benchmark"] for a in assets]

    # 👉 DICCIONARIO ACTIVO → BENCHMARK
    symbol_to_bench = {a["symbol"]: a["benchmark"] for a in assets}
    # ============================
    #  Descargar histórico
    # ============================
    try:
        prices = download_prices(symbols)  # dataframe con columnas = símbolos
    except:
        return pie_bench_opt, pie_asset_opt, perf_opt, bar_opt, corr_html

    if isinstance(prices, pd.Series):
        prices = prices.to_frame()

    prices = prices.dropna(how="all")
    if prices.empty:
        return pie_bench_opt, pie_asset_opt, perf_opt, bar_opt, corr_html

    # Filtrar símbolos válidos
    valid_symbols = [s for s in symbols if s in prices.columns]

    if not valid_symbols:
        return pie_bench_opt, pie_asset_opt, perf_opt, bar_opt, corr_html

    # Reindexar pesos y benchmarks
    weights = np.array([
        float(a["weight"])
        for a in assets if a["symbol"] in valid_symbols
    ])

    benchmarks = [
        a["benchmark"]
        for a in assets if a["symbol"] in valid_symbols
    ]

    symbols = valid_symbols
    prices = prices[symbols]

    # ================================================================
    # 1) PIE CHART — ASIGNACIÓN DE PESOS POR BENCHMARK
    # ================================================================
    bench_df = pd.DataFrame({
        "benchmark": benchmarks,
        "weight": weights,
    })

    bench_grouped = bench_df.groupby("benchmark").sum().reset_index()

    # ---- Map colors deterministically ----
    bench_color_map = generate_color_map(
        bench_grouped["benchmark"],
        BENCHMARK_COLORS
    )

    pie_bench_opt["series"][0]["data"] = [
        {
            "value": float(w),
            "name": b,
            "itemStyle": {"color": bench_color_map[b]}
        }
        for b, w in zip(bench_grouped["benchmark"], bench_grouped["weight"])
    ]

    # ================================================================
    # 2) PIE CHART — COMPOSICIÓN TOTAL POR ACTIVO
    # ================================================================
    asset_color_map = generate_color_map(symbols, ASSET_COLORS)

    pie_asset_opt["series"][0]["data"] = [
        {
            "value": float(w),
            "name": s,
            "itemStyle": {"color": asset_color_map[s]}
        }
        for s, w in zip(symbols, weights)
    ]

    # ================================================================
    # 3) RENTABILIDADES DIARIAS Y PERFORMANCE ACUMULADO
    # ================================================================
    rets = prices.pct_change().dropna()

    if rets.empty:
        return pie_bench_opt, pie_asset_opt, perf_opt, bar_opt, corr_html

    port_daily = (rets * weights).sum(axis=1)
    port_cum = (1 + port_daily).cumprod()

    perf_opt["xAxis"]["data"] = [d.strftime("%Y-%m-%d") for d in port_cum.index]
    perf_opt["series"] = [
        {
            "name": "Cartera",
            "type": "line",
            "smooth": True,
            "showSymbol": False,
            "data": [(v - 1) * 100 for v in port_cum],
        }
    ]

    # ===============================================================
    # ================================================================
    # ================================================================
    # 4) RENTABILIDAD POR ACTIVO — COLORES POR BENCHMARK
    # ================================================================
    total_ret = prices.iloc[-1] / prices.iloc[0] - 1

    symbols_order = list(total_ret.index)

    # asignación: activo → benchmark color
    bar_opt["xAxis"]["data"] = symbols_order

    bar_opt["series"][0]["data"] = [
        {
            "value": float(total_ret[s] * 100),
            "itemStyle": {"color": bench_color_map[symbol_to_bench[s]]}
        }
        for s in symbols_order
    ]


    # ============================
    #  CÁLCULO DE KPIS
    # ============================

    daily = port_daily

    total_return = port_cum.iloc[-1] - 1
    vol_annual = daily.std() * np.sqrt(252)

    years = len(port_cum) / 252
    cagr = (port_cum.iloc[-1]) ** (1 / years) - 1

    sharpe = cagr / vol_annual if vol_annual > 0 else 0

    # ============================
    #  TARJETAS DE KPIS
    # ============================

    kpi_cards = dbc.Row(
        [
            _kpi_card("Rentabilidad total", f"{total_return*100:.2f}%"),
            _kpi_card("Rentabilidad anualizada (CAGR)", f"{cagr*100:.2f}%"),
            _kpi_card("Volatilidad anualizada", f"{vol_annual*100:.2f}%"),
            _kpi_card("Sharpe ratio", f"{sharpe:.2f}"),
        ],
        className="g-4 mb-4"
    )
    # ================================================================
    # 5) MATRIZ DE CORRELACIÓN
    # ================================================================
    corr = rets.corr().round(2)
    corr_html = correlation_table(list(corr.columns), corr.values)

    return (
    kpi_cards,
    pie_bench_opt,
    pie_asset_opt,
    perf_opt,
    bar_opt,
    corr_html,
)
