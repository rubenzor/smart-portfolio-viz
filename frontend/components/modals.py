from dash import html, dcc
import dash_bootstrap_components as dbc

def create_portfolio_modal():
    """
    Modal de creación de cartera.

    Cambios importantes:
    - A la derecha de "Buscar activo…" ya NO hay un selector de benchmark.
    - En su lugar, hay un Input numérico para el peso inicial (%).
    - El benchmark del activo se infiere automáticamente a partir del ticker
      en los callbacks (ver callbacks/portfolios.py).
    """
    return dbc.Modal(
        [
            dbc.ModalHeader("Crear nueva cartera"),

            dbc.ModalBody(
                [
                    # ============================
                    # 1) NOMBRE DE LA CARTERA
                    # ============================
                    dbc.Label("Nombre de la cartera"),
                    dbc.Input(
                        id="new-portfolio-name",
                        type="text",
                        placeholder="Mi cartera",
                        className="mb-3",
                    ),

                    # ============================
                    # 2) SELECCIÓN DE BENCHMARKS
                    # (para comparativa general; máx. 4)
                    # ============================
                    dbc.Label("Benchmarks (máx. 4)"),
                    dcc.Dropdown(
                        id="new-benchmarks",
                        options=[],   # se llenará por callback dinámico
                        multi=True,
                        placeholder="Selecciona hasta 4 benchmarks",
                        className="neon-dropdown mb-3",
                    ),

                    # ============================
                    # 3) AÑADIR ACTIVOS
                    # ============================
                    html.Hr(),
                    html.H5("Añadir activos", className="mb-3"),

                    dbc.Row(
                        [
                            # Ticker search
                            dbc.Col(
                                dcc.Dropdown(
                                    id="search-asset",
                                    placeholder="Buscar activo…",
                                    options=[],
                                    className="neon-dropdown",
                                ),
                                md=6,
                            ),

                            # Input porcentaje
                            dbc.Col(
                                dbc.Input(
                                    id="asset-weight-input",
                                    type="number",
                                    min=0,
                                    max=100,
                                    step=0.1,
                                    value=0,
                                    placeholder="Peso (%)",
                                    className="neon-input",
                                ),
                                md=3,
                            ),

                            # Slider porcentaje
                            dbc.Col(
                                dcc.Slider(
                                    id="asset-weight-slider",
                                    min=0, max=100, step=0.1,
                                    value=0,
                                    tooltip={"placement": "bottom", "always_visible": True},
                                ),
                                md=3,
                            ),
                        ],
                        class_name="mb-3",
                    ),


                    dbc.Button(
                        "Añadir activo",
                        id="btn-add-asset",
                        color="primary",
                        class_name="w-100 mb-3",
                    ),

                    html.Div(id="new-asset-error", className="text-danger mb-3"),

                    # ============================
                    # 4) TABLA AGRUPADA POR BENCHMARK
                    # ============================
                    html.H5("Activos añadidos", className="mt-3"),
                    html.Div(id="new-portfolio-assets-view"),
                ]
            ),

            dbc.ModalFooter(
                [
                    dbc.Button("Cancelar", id="btn-cancel-create-portfolio", color="secondary"),
                    dbc.Button("Guardar cartera", id="btn-save-portfolio", color="success"),
                ]
            ),
        ],
        id="create-portfolio-modal",
        size="lg",
        is_open=False,
        scrollable=True,
    )
