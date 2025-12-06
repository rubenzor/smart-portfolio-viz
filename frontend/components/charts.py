# frontend/components/charts.py
from dash import html, dcc
import dash_bootstrap_components as dbc
from dash_echarts import DashECharts
import plotly.graph_objects as go

from components.montecarlo import montecarlo_section
from components.utils import empty_dark_figure


def empty_pie_option():
    return {
        "backgroundColor": "transparent",
        "tooltip": {"trigger": "item"},
        "legend": {
            "top": "bottom",
            "textStyle": {"color": "#9CA3AF"},
        },
        "series": [
            {
                "type": "pie",
                "radius": ["40%", "70%"],
                "avoidLabelOverlap": False,
                "label": {"show": False, "position": "center"},
                "emphasis": {
                    "label": {
                        "show": True,
                        "fontSize": 18,
                        "fontWeight": "bold",
                        "color": "#F9FAFB",
                    },
                },
                "labelLine": {"show": False},
                "itemStyle": {
                    "borderRadius": 8,
                    "borderColor": "#020617",
                    "borderWidth": 2,
                },
                "data": [],
            }
        ],
    }


def empty_line_option(title=""):
    return {
        "backgroundColor": "transparent",
        "title": {
            "text": title,
            "left": "center",
            "top": "2%",
            "textStyle": {"color": "#E5E7EB", "fontSize": 16},
        },
        "tooltip": {"trigger": "axis"},
        "legend": {
            "top": "12%",
            "left": "center",
            "textStyle": {"color": "#9CA3AF"},
        },
        "grid": {"top": "28%", "left": "10%", "right": "5%", "bottom": "10%"},
        "xAxis": {
            "type": "category",
            "axisLine": {"lineStyle": {"color": "#64748B"}},
            "axisLabel": {"color": "#9CA3AF"},
            "data": [],
        },
        "yAxis": {
            "type": "value",
            "axisLine": {"lineStyle": {"color": "#64748B"}},
            "axisLabel": {"color": "#9CA3AF"},
            "splitLine": {"lineStyle": {"color": "#1F2933"}},
        },
        "series": [],
    }


def empty_bar_option(title=""):
    return {
        "backgroundColor": "transparent",
        "title": {
            "text": title,
            "left": "center",
            "textStyle": {"color": "#E5E7EB"},
        },
        "tooltip": {"trigger": "axis"},
        "xAxis": {
            "type": "category",
            "axisLine": {"lineStyle": {"color": "#64748B"}},
            "axisLabel": {"color": "#9CA3AF"},
            "data": [],
        },
        "yAxis": {
            "type": "value",
            "axisLine": {"lineStyle": {"color": "#64748B"}},
            "axisLabel": {"color": "#9CA3AF"},
            "splitLine": {"lineStyle": {"color": "#1F2933"}},
        },
        "series": [
            {
                "type": "bar",
                "barWidth": "60%",
                "data": [],
                "itemStyle": {"borderRadius": [4, 4, 0, 0]},
            }
        ],
    }

def empty_corr_option(title="Matriz de correlación"):
    return {
        "backgroundColor": "transparent",
        "title": {
            "text": title,
            "left": "center",
            "top": "2%",
            "textStyle": {"color": "#E5E7EB", "fontSize": 16},
        },
        "tooltip": {"position": "top"},
        "grid": {
            "height": "65%",
            "top": "18%",
            "left": "15%",
            "right": "10%",
            "bottom": "10%",
        },
        "xAxis": {
            "type": "category",
            "data": [],
            "axisLabel": {"color": "#9CA3AF", "rotate": 30},
            "axisLine": {"lineStyle": {"color": "#64748B"}},
        },
        "yAxis": {
            "type": "category",
            "data": [],
            "axisLabel": {"color": "#9CA3AF"},
            "axisLine": {"lineStyle": {"color": "#64748B"}},
        },
        "visualMap": {
            "min": -1,
            "max": 1,
            "calculable": True,
            "orient": "horizontal",
            "left": "center",
            "bottom": "4%",
            "inRange": {"color": ["#ef4444", "#22c55e", "#22c55e"]},
            "textStyle": {"color": "#9CA3AF"},
        },
        "series": [
            {
                "name": "Correlación",
                "type": "heatmap",
                "data": [],
                "label": {"show": False},
                "emphasis": {"itemStyle": {"shadowBlur": 10}},
            }
        ],
    }

def empty_frontier_option():
    return {
        "backgroundColor": "transparent",
        "tooltip": {"trigger": "axis"},
        "xAxis": {
            "type": "value",
            "name": "Riesgo",
            "axisLine": {"lineStyle": {"color": "#64748B"}},
            "axisLabel": {"color": "#9CA3AF"},
            "splitLine": {"lineStyle": {"color": "#1F2933"}},
        },
        "yAxis": {
            "type": "value",
            "name": "Rentabilidad",
            "axisLine": {"lineStyle": {"color": "#64748B"}},
            "axisLabel": {"color": "#9CA3AF"},
            "splitLine": {"lineStyle": {"color": "#1F2933"}},
        },
        "series": [
            {
                "type": "line",
                "smooth": True,
                "showSymbol": False,
                "lineStyle": {"width": 3, "color": "#22D3EE"},
                "areaStyle": {
                    "opacity": 0.15,
                    "color": {
                        "type": "linear",
                        "x": 0,
                        "y": 0,
                        "x2": 0,
                        "y2": 1,
                        "colorStops": [
                            {"offset": 0, "color": "#22D3EE"},
                            {"offset": 1, "color": "rgba(15,23,42,0)"},
                        ],
                    },
                },
                "data": [],
            }
        ],
    }


def empty_forecast_option():
    return {
        "backgroundColor": "transparent",
        "tooltip": {"trigger": "axis"},
        "xAxis": {
            "type": "category",
            "axisLine": {"lineStyle": {"color": "#64748B"}},
            "axisLabel": {"color": "#9CA3AF"},
        },
        "yAxis": {
            "type": "value",
            "axisLine": {"lineStyle": {"color": "#64748B"}},
            "axisLabel": {"color": "#9CA3AF"},
            "splitLine": {"lineStyle": {"color": "#1F2933"}},
        },
        "series": [
            {
                "name": "Forecast",
                "type": "line",
                "smooth": True,
                "showSymbol": False,
                "lineStyle": {"width": 3, "color": "#A855F7"},
                "areaStyle": {
                    "opacity": 0.18,
                    "color": {
                        "type": "linear",
                        "x": 0,
                        "y": 0,
                        "x2": 0,
                        "y2": 1,
                        "colorStops": [
                            {"offset": 0, "color": "#A855F7"},
                            {"offset": 1, "color": "rgba(15,23,42,0)"},
                        ],
                    },
                },
                "data": [],
            }
        ],
    }

# ======================================================
# ==================  VISIÓN GENERAL  ==================
# ======================================================

def overview_tab(portfolio):
    if not portfolio or not portfolio.get("assets"):
        return dbc.Alert(
            "Selecciona o crea una cartera con activos para ver el resumen.",
            color="info",
        )

    return dcc.Loading(
        id="loading-overview",
        type="default",
        fullscreen=False,
        children=html.Div(
            [
                html.H4("Resumen de cartera", className="mb-4"),

                # -------- KPIs (rellenados por callback) --------
                html.Div(id="overview-kpis-row", className="mb-4"),

                # ========== FILA 1: Evolución cartera vs benchmark ==========
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.Div(
                                "Evolución de la cartera vs benchmarks (desde creación)",
                                className="neon-section-title mb-2",
                            ),
                            DashECharts(
                                id="overview-perf-chart",
                                option=empty_line_option(
                                    "Evolución cartera vs benchmarks (desde creación)"
                                ),
                                style={"height": "360px", "width": "100%"},
                            ),
                        ]
                    ),
                    class_name="neon-card mb-4",
                ),

                # ========== FILA 2: Asignación por benchmark + composición ==========
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Card(
                                dbc.CardBody(
                                    [
                                        html.Div(
                                            "Asignación de pesos por benchmark",
                                            className="neon-section-title mb-2",
                                        ),
                                        DashECharts(
                                            id="alloc-chart",
                                            option=empty_pie_option(),
                                            style={
                                                "height": "320px",
                                                "width": "100%",
                                            },
                                        ),
                                    ]
                                ),
                                class_name="neon-card",
                            ),
                            md=6,
                            class_name="mb-4",
                        ),
                        dbc.Col(
                            dbc.Card(
                                dbc.CardBody(
                                    [
                                        html.Div(
                                            "Composición por activo (agrupado por benchmark)",
                                            className="neon-section-title mb-2",
                                        ),
                                        DashECharts(
                                            id="alloc-asset-pie",
                                            option=empty_pie_option(),
                                            style={
                                                "height": "320px",
                                                "width": "100%",
                                            },
                                        ),
                                    ]
                                ),
                                class_name="neon-card",
                            ),
                            md=6,
                            class_name="mb-4",
                        ),
                    ],
                    class_name="g-4",
                ),

                dbc.Row(
                        dbc.Col(
                            dbc.Card(
                                dbc.CardBody(
                                    [
                                        html.Div(
                                            "Rentabilidad por activo (desde creación)",
                                            className="neon-section-title mb-2",
                                        ),
                                        html.Div(
                                            DashECharts(
                                                id="asset-returns-chart",
                                                option=empty_bar_option(
                                                    "Rentabilidad por activo (desde creación)"
                                                ),
                                                style={
                                                    "height": "350px",
                                                    "width": "100%",
                                                    "minWidth": "900px"  # ← fuerza espacio horizontal
                                                },
                                            ),
                                            style={
                                                "overflowX": "auto",  # ← scroll horizontal
                                                "paddingBottom": "10px",
                                            },
                                        ),
                                    ]
                                ),
                                class_name="neon-card mb-4",
                            ),
                            md=12,
                        )
                    ),
                    
                dbc.Row(
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader(
                                    "Matriz de correlación",
                                    className="neon-section-title mb-2",
                                ),
                                dbc.CardBody(
                                    html.Div(
                                        id="corr-corr-table",
                                        className="corr-table-wrapper",
                                        style={
                                            "overflowX": "auto",  # scroll horizontal
                                            "width": "100%",
                                        },
                                    ),
                                ),
                            ],
                            className="neon-card mb-4",
                        ),
                        md=12,
                    )
                ),
            ]
        ),
    )

def optimization_tab():
    return html.Div(
        [
            # Mensaje
            html.Div(id="opt-msg", className="mb-3"),

            # Header
            dbc.Card(
                [
                    dbc.CardHeader("Método y horizonte", className="neon-card-header"),
                    dbc.CardBody(html.Div(id="opt-header-info", className="neon-subcard")),
                ],
                className="neon-card mb-4",
            ),

            # Botón Optimizar
            html.Div(
                dbc.Button(
                    "Optimizar",
                    id="btn-run-opt",
                    color="primary",
                    class_name="neon-btn-wide",
                ),
                className="text-center mb-4",
            ),

            # 🔥 SOLO AQUÍ EL LOADING (contenedor dinámico)
            dcc.Loading(
                id="loading-opt-section",
                type="default",
                fullscreen=False,
                children=html.Div(
                    [
                        # FRONTIERA EFICIENTE
                        dbc.Card(
                            [
                                dbc.CardHeader("Frontera Eficiente", className="neon-card-header"),
                                dbc.CardBody(
                                    dcc.Graph(
                                        id="opt-frontier-chart",
                                        config={"displayModeBar": False},
                                        style={"height": "420px"},
                                    )
                                ),
                            ],
                            className="neon-card mb-4",
                        ),

                        # TABLA DE PESOS
                        dbc.Card(
                            [
                                dbc.CardHeader("Comparativa de pesos", className="neon-card-header"),
                                dbc.CardBody(html.Div(id="opt-table-container")),
                            ],
                            className="neon-card mb-4",
                        ),

                        # MONTECARLO
                        montecarlo_section(),
                    ]
                ),
            ),

            # Botón aplicar pesos
            html.Div(
                dbc.Button(
                    "Aplicar pesos optimizados",
                    id="btn-apply-opt",
                    color="success",
                    class_name="neon-btn-wide",
                ),
                className="text-center mb-4",
            ),
        ]
    )


def forecasting_tab(portfolio):
    if not portfolio or not portfolio.get("assets"):
        return dbc.Alert(
            "Selecciona una cartera con activos para hacer forecasting.",
            color="info",
        )

    symbols = [a["symbol"] for a in portfolio["assets"]]

    return html.Div(
        [
            html.H4("Forecast sobre activo"),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Label("Activo"),
                            dcc.Dropdown(
                                id="fc-symbol",
                                options=[{"label": s, "value": s} for s in symbols],
                                value=symbols[0],
                                clearable=False,
                                className="neon-dropdown",
                            ),
                            dbc.Label("Método", className="mt-2"),
                            dcc.Dropdown(
                                id="fc-method",
                                options=[
                                    {"label": "Holt-Winters", "value": "HW"},
                                    {
                                        "label": "Naive (último valor)",
                                        "value": "Naive",
                                    },
                                ],
                                value="HW",
                                clearable=False,
                                className="neon-dropdown",
                            ),
                            dbc.Label("Días de histórico", className="mt-2"),
                            dbc.Input(
                                id="fc-days",
                                type="number",
                                value=300,
                                min=60,
                                max=1000,
                                className="neon-input",
                            ),
                            dbc.Label("Horizonte (días)", className="mt-2"),
                            dbc.Input(
                                id="fc-horizon",
                                type="number",
                                value=30,
                                min=5,
                                max=365,
                                className="neon-input",
                            ),
                            dbc.Button(
                                "Ejecutar forecast",
                                id="btn-run-fc",
                                color="info",
                                class_name="mt-3 neon-btn",
                            ),
                        ],
                        md=4,
                    ),
                    dbc.Col(
                        [
                            DashECharts(
                                id="forecast-chart",
                                option=empty_forecast_option(),
                                style={"height": "380px", "width": "100%"},
                            ),
                        ],
                        md=8,
                    ),
                ]
            ),
        ]
    )


def make_efficient_frontier_chart(risks, returns, opt_risk=None, opt_return=None):
    """
    Versión estable del gráfico de frontera eficiente.
    Se usa en casos donde se requiere un hover más detallado.
    """
    risks = [float(r) for r in risks or []]
    returns = [float(r) for r in returns or []]

    fig = go.Figure()

    # --- Línea de la frontera ---
    if risks and returns and len(risks) == len(returns):
        fig.add_trace(
            go.Scatter(
                x=risks,
                y=returns,
                mode="lines",
                name="Frontera eficiente",
                line=dict(color="#00E0FF", width=2),
            )
        )

    # --- Punto óptimo ---
    if opt_risk is not None and opt_return is not None:
        fig.add_trace(
            go.Scatter(
                x=[float(opt_risk)],
                y=[float(opt_return)],
                mode="markers",
                name="Cartera óptima",
                marker=dict(size=12, color="#00FFAA"),
            )
        )

    fig.update_layout(
        xaxis_title="Riesgo (volatilidad)",
        yaxis_title="Retorno esperado",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#EEEEEE"),
        margin=dict(l=20, r=20, t=20, b=20),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
    )

    return fig



def make_frontier_chart(risks, returns, opt_risk=None, opt_return=None):
    """
    Esta es la función **principal** usada en callbacks.
    Es compacta, clara y profesional.
    """
    fig = go.Figure()

    # --- Línea ---
    if risks and returns and len(risks) == len(returns):
        fig.add_trace(
            go.Scatter(
                x=risks,
                y=returns,
                mode="lines",
                line=dict(color="#00E0FF", width=2),
                name="Frontera eficiente",
            )
        )

    # --- Punto óptimo ---
    if opt_risk is not None and opt_return is not None:
        fig.add_trace(
            go.Scatter(
                x=[opt_risk],
                y=[opt_return],
                mode="markers",
                marker=dict(color="#00FFAA", size=10),
                name="Cartera óptima",
            )
        )

    fig.update_layout(
        margin=dict(l=20, r=20, t=10, b=10),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        height=420,
        xaxis_title="Riesgo (volatilidad)",
        yaxis_title="Retorno esperado",
        xaxis=dict(gridcolor="rgba(255,255,255,0.08)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.08)"),
    )

    return fig

def make_montecarlo_figure(result, title, weights_dict=None):

    if not result:
        return empty_dark_figure()

    days = list(range(len(result["p50"])))
    p5 = result["p5"]
    p50 = result["p50"]
    p95 = result["p95"]

    fig = go.Figure()

    # ------------------- Banda P5–P95 -------------------
    fig.add_trace(
        go.Scatter(
            x=days + days[::-1],
            y=p95 + p5[::-1],
            fill="toself",
            fillcolor="rgba(0, 224, 255, 0.12)",
            line=dict(color="rgba(0,0,0,0)"),
            hoverinfo="skip",
            name="P5–P95",
        )
    )

    # ------------------- Línea P50 -------------------
    fig.add_trace(
        go.Scatter(
            x=days,
            y=p50,
            mode="lines",
            line=dict(color="#00E0FF", width=3),
            name="P50 (esperado)",
        )
    )

    fig.update_layout(
        template="plotly_dark",
        margin=dict(l=40, r=20, t=50, b=50),
        height=380,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            title="Tiempo (días)",
            gridcolor="rgba(255,255,255,0.05)",
            showline=False,
        ),
        yaxis=dict(
            title="Rentabilidad simulada",
            gridcolor="rgba(255,255,255,0.05)",
            showline=False,
        ),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            borderwidth=0,
            font=dict(size=12)
        ),
    )

    return fig
