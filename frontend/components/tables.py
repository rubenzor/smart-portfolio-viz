from dash import html
import dash_bootstrap_components as dbc
from dash_iconify import DashIconify
import pandas as pd

def build_assets_table(assets):
    if not assets:
        return html.Div(
            "No hay activos añadidos aún.",
            className="text-muted fst-italic p-2",
        )

    rows = []
    for i, a in enumerate(assets):
        rows.append(
            html.Tr(
                [
                    html.Td(
                        a["symbol"],
                        className="asset-symbol-cell",
                    ),
                    html.Td(
                        f"{float(a['weight']):.4f}",
                        className="asset-weight-cell",
                    ),
                    html.Td(
                        dbc.Button(
                            DashIconify(
                                icon="solar:trash-bin-minimalistic-bold",
                                width=20,
                                color="#f87171",  # rojo suave
                            ),
                            id={"type": "delete-asset", "index": i},
                            size="sm",
                            color="link",
                            class_name="asset-delete-btn",
                            title="Eliminar activo",
                        ),
                        className="text-end",
                    ),
                ],
                className="asset-row",
            )
        )

    return dbc.Table(
        [
            html.Thead(
                html.Tr(
                    [
                        html.Th("Símbolo", className="asset-header"),
                        html.Th("Peso", className="asset-header"),
                        html.Th("", className="asset-header text-end"),
                    ]
                )
            ),
            html.Tbody(rows),
        ],
        bordered=False,
        hover=True,
        className="custom-table-container",
    )

def build_optimization_comparison_table(current_weights, optimized_weights):
    """
    Construye la tabla comparativa:
    | Activo | Peso actual | Peso optimizado | Cambio |
    """
    # Unión de todos los símbolos
    all_assets = sorted(set(current_weights.keys()) | set(optimized_weights.keys()))
    if not all_assets:
        return html.Div(
            "No hay resultados de optimización disponibles.",
            className="text-muted fst-italic p-2",
        )

    header = html.Thead(
        html.Tr(
            [
                html.Th("Activo"),
                html.Th("Peso actual", className="text-end"),
                html.Th("Peso optimizado", className="text-end"),
                html.Th("Cambio", className="text-end"),
            ]
        )
    )

    body_rows = []
    for sym in all_assets:
        cw = float(current_weights.get(sym, 0) or 0.0)
        ow = float(optimized_weights.get(sym, 0) or 0.0)
        delta = ow - cw

        if delta > 0:
            delta_color = "#22c55e"  # verde
        elif delta < 0:
            delta_color = "#ef4444"  # rojo
        else:
            delta_color = "#e5e7eb"  # neutro

        body_rows.append(
            html.Tr(
                [
                    html.Td(sym),
                    html.Td(f"{cw:.4f}", className="text-end"),
                    html.Td(f"{ow:.4f}", className="text-end"),
                    html.Td(
                        f"{delta:+.4f}",
                        className="text-end",
                        style={"color": delta_color, "fontWeight": "600"},
                    ),
                ]
            )
        )

    table = dbc.Table(
        [header, html.Tbody(body_rows)],
        bordered=False,
        hover=True,
        className="custom-table-container",
    )

    return table
def build_optimization_methods_table(methods, best_method_name):
    """
    Tabla estilizada igual que la comparativa de pesos.
    Columnas: Método | Retorno | Riesgo | Sharpe
    Se marca el ganador con un badge verde.
    """

    if not methods:
        return html.Div("No hay métodos disponibles.", className="text-muted fst-italic p-2")

    # Preparar filas
    rows = []
    for m in methods:

        method_name = m.get("method") or m.get("name", "-")

        is_winner = (method_name == best_method_name)

        # Badge ganador
        winner_badge = None
        if is_winner:
            winner_badge = html.Span(
                " GANADOR",
                className="ms-2",
                style={
                    "color": "#00FFAA",
                    "fontWeight": "bold",
                    "fontSize": "0.85rem",
                },
            )

        # Formateo de métricas
        ret = m.get("expected_return", None)
        vol = m.get("volatility", None)
        sharpe = m.get("sharpe_ratio") or m.get("sharpe")

        ret_txt = f"{ret:.2%}" if isinstance(ret, (int, float)) else "-"
        vol_txt = f"{vol:.2%}" if isinstance(vol, (int, float)) else "-"
        sharpe_txt = f"{sharpe:.2f}" if isinstance(sharpe, (int, float)) else "-"

        rows.append(
            html.Tr(
                [
                    html.Td(
                        [
                            html.Span(method_name),
                            winner_badge if is_winner else ""
                        ]
                    ),
                    html.Td(ret_txt),
                    html.Td(vol_txt),
                    html.Td(sharpe_txt),
                ],
            )
        )

    # Encabezado al estilo dark
    table_header = html.Thead(
        html.Tr(
            [
                html.Th("Método"),
                html.Th("Retorno"),
                html.Th("Riesgo"),
                html.Th("Sharpe"),
            ],
        )
    )

    table_body = html.Tbody(rows)

    # Contenedor estilizado igual que la comparativa de pesos
    return html.Div(
        dbc.Table(
            [table_header, table_body],
            bordered=False,
            hover=True,
            responsive=True,
            class_name="custom-table-container"  # misma clase que la otra tabla
        )
    )
def build_montecarlo_comparison(p50_curr, p50_opt, days):

    diff = p50_opt[-1] - p50_curr[-1]
    color = "#00FFAA" if diff > 0 else "#FF4C4C"

    return dbc.Card(
        [
            dbc.CardHeader(
                "Comparativa Montecarlo (P50)",
                className="neon-card-header text-center",
                style={"fontSize": "1.05rem"}
            ),
            dbc.CardBody(
                html.Div(
                    [
                        html.Div(
                            [
                                html.P(
                                    f"P50 actual ({days} días): {p50_curr[-1]:.2%}",
                                    className="mb-1",
                                    style={"fontSize": "0.95rem"}
                                ),
                                html.P(
                                    f"P50 optimizada ({days} días): {p50_opt[-1]:.2%}",
                                    className="mb-3",
                                    style={"fontSize": "0.95rem"}
                                ),
                                html.H4(
                                    f"Diferencia: {diff:.2%}",
                                    style={
                                        "color": color,
                                        "fontWeight": "700",
                                        "marginTop": "8px"
                                    },
                                    className="mb-0"
                                ),
                            ],
                            className="text-center",
                        )
                    ],
                    style={"padding": "4px 6px"}
                )
            ),
        ],
        class_name="neon-card mt-4",
        style={
            "maxWidth": "500px",
            "margin": "0 auto",         # centro horizontal
            "borderRadius": "14px",
        },
    )
