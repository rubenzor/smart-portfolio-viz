from dash import html, dcc
import dash_bootstrap_components as dbc
from components.modals import create_portfolio_modal


layout = dbc.Container(
    [
        # ============================================================
        # ========================== HEADER ===========================
        # ============================================================
        html.Div(
            [
                html.H1("QuInt", className="neon-title"),
                html.Div(
                    "Gestión de Carteras · Optimización Carteras · Análisis Avanzado",
                    className="neon-subtitle",
                ),
            ],
            className="header-wrapper",
        ),

        # ============================================================
        # =========================== BODY ============================
        # ============================================================
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        [
                            # ====================================================
                            # ===================== TOOLBAR ======================
                            # ====================================================
                           dbc.CardHeader(
                                html.Div(
                                    [
                                        # ---------------- IZQUIERDA: BOTONES ----------------
                                        html.Div(
                                            [
                                                dbc.Button(
                                                    "Refrescar",
                                                    id="btn-refresh-portfolios",
                                                    size="sm",
                                                    class_name="me-2 neon-btn-outline",
                                                ),
                                                dbc.Button(
                                                    "Demo",
                                                    id="btn-new-portfolio-demo",
                                                    size="sm",
                                                    color="secondary",
                                                    class_name="me-2 neon-btn-outline",
                                                ),
                                                dbc.Button(
                                                    "Nueva",
                                                    id="btn-open-create-portfolio",
                                                    size="sm",
                                                    color="success",
                                                    class_name="neon-btn",
                                                ),
                                            ],
                                            className="d-flex align-items-center",
                                            style={"gap": "10px"},
                                        ),

                                        # ---------------- DERECHA: LABEL + DROPDOWN ----------------
                                        html.Div(
                                            [
                                                html.Label(
                                                    "Selecciona cartera",
                                                    className="fw-bold mb-0",
                                                    style={
                                                        "fontSize": "0.95rem",
                                                        "color": "#BFC7D5",
                                                        "whiteSpace": "nowrap",
                                                         "paddingLeft": "115px"
                                                    },
                                                ),
                                                html.Div(
                                                    id="portfolio-select-container",    # <--- ESTE ES EL NUEVO ID REAL
                                                    style={
                                                        "minWidth": "240px",
                                                        "maxWidth": "280px",
                                                    }
                                                ),
                                            ],
                                            className="d-flex align-items-center",
                                            style={
                                                "gap": "10px",
                                                "flexShrink": 0,
                                                
                                            },
                                        ),
                                    ],
                                    style={
                                        "display": "flex",
                                        "justifyContent": "space-between",
                                        "alignItems": "center",
                                        "flexWrap": "wrap",     # ← EL FIX REAL
                                
                                    },
                                ),
                                style={
                                    "minHeight": "58px",        # ← AGRANDA EL RECTÁNGULO
                                    "padding": "10px 11px",
                                    "background": "rgba(15,20,30,0.85)",
                                    "backdropFilter": "blur(8px)",
                                    "borderTopLeftRadius": "12px",
                                    "borderTopRightRadius": "12px",
                                    "rightwidth": "10px",
                                    "display": "flex",          # ← mantiene alineado
                                    "alignItems": "center",
                                },
                            ),
                            html.Hr(
                                style={
                                    "margin": "0",
                                    "padding": "0",
                                    "border": "none",
                                    "borderTop": "1.5px solid #343F52",  # ← EL BORDE CORRECTO
                                    "opacity": "1",
                                }
                            ),
                            # ====================================================
                            # ====================== CONTENT ======================
                            # ====================================================
                            dbc.CardBody(
                                [
                                    # ---- Metadata (solo aparece cuando hay cartera seleccionada) ----
                                    html.Div(
                                        id="portfolio-meta-container",
                                        children=[
                                            html.Div(
                                                id="portfolio-meta",
                                                className="small text-muted",
                                                style={"paddingLeft": "4px"},
                                            ),
                                        ],
                                        style={"display": "none"},   # ← Por defecto oculto
                                    ),

                                    # --------------------- TABS -----------------------
                                    dcc.Tabs(
                                        id="main-tabs",
                                        value="tab-overview",
                                        children=[
                                            dcc.Tab(
                                                label="Visión General",
                                                value="tab-overview",
                                            ),
                                            dcc.Tab(
                                                label="Optimización",
                                                value="tab-opt",
                                            ),
                                            dcc.Tab(
                                                label="Analisis Avanzado",
                                                value="tab-adv",
                                            ),
                                        ],
                                        className="neon-tabs-container",
                                    ),

                                    # ------------------- TAB CONTENT -------------------
                                    dcc.Loading(
                                        id="loading-t",
                                        type="default",
                                        fullscreen=False,
                                        children=html.Div(id="main-tab-content",
                                                          style={"marginTop": "15px"})
                                    )
                                ],
                                style={
                                    "padding": "10px 20px 14px 20px",
                                    "borderBottomLeftRadius": "12px",
                                    "borderBottomRightRadius": "12px",
                                },
                            ),
                        ],
                        class_name="neon-card",
                        style={
                            "padding": "0",
                            "margin": "0",
                            "borderRadius": "12px",
                        },
                    ),
                    md=12,
                ),
            ],
            class_name="mt-3",
            style={"margin": "0", "padding": "0"},
        ),

        # ============================================================
        # =====================  MODAL GLOBAL  ========================
        # ============================================================
        create_portfolio_modal(),

        # ============================================================
        # ======================  GLOBAL STORES =======================
        # ============================================================
        dcc.Store(id="selected-portfolio"),
        dcc.Store(id="new-portfolio-assets", data=[]),
        dcc.Store(id="refresh-dashboard"),
        dcc.Store(id="opt-results-store"),
    ],
    fluid=True,
)
