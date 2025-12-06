from dash import html, dcc
import dash_bootstrap_components as dbc
from components.utils import empty_dark_figure



def montecarlo_section():
    return dbc.Card(
        [
            dbc.CardHeader("Simulación Montecarlo de la cartera", className="neon-card-header"),

            dbc.CardBody(
                [
                    # ---- Selector de días ----
                    html.Div(
                        [
                            dbc.Label("Días a simular", className="text-muted"),
                            dbc.Input(
                                id="mc-days",
                                type="number",
                                min=1,
                                step=1,
                                value=30,
                                className="neon-input",
                                style={"width": "110px"},
                            ),
                            dbc.Button(
                                "Simular cartera",
                                id="btn-run-mc",
                                color="primary",
                                class_name="ms-3 neon-btn",
                                style={"height": "38px"},
                            ),
                        ],
                        className="d-flex align-items-center gap-3 mb-4",
                    ),

                    # ⭐⭐⭐ AQUI VA EL MENSAJE ⭐⭐⭐
                    html.Div(id="forecast-message", className="mb-3"),

                    # ---- Gráfica actual ----
                    html.Div(
                        id="current-section",
                        children=[
                        html.H5("Montecarlo — Cartera Actual", className="mt-3"),
                        dcc.Graph(
                            id="mc-current-chart",
                            figure=empty_dark_figure(),
                            config={"displayModeBar": False}
                        ),
                        html.Div(id="mc-compare-block"),
                        ],
                        style={"marginTop": "35px"}
                    ),

                    html.Div(
                        id="optimized-section",
                        children=[
                            html.H5("Montecarlo — Cartera Optimizada", className="mt-3"),
                            dcc.Graph(
                                id="mc-optimized-chart",
                                figure=empty_dark_figure(),
                                config={"displayModeBar": False}
                            ),
                            html.Div(id="mc-compare-block"),
                        ],
                        style={"marginTop": "35px"}
                    ),


                    # ---- Comparativa ----
                    html.Div(id="mc-compare-block", className="mt-4"),
                ]
            ),
        ],
        class_name="neon-card mb-4",
    )
