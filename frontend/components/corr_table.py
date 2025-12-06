from dash import html
import dash_bootstrap_components as dbc

def get_color(value):
    """Color según la intensidad de correlación"""
    if value <= -0.6:
        return "#b91c1c" 
    elif value <= -0.3:
        return "#ef4444"
    elif value <= 0:
        return "#facc15"
    elif value <= 0.3:
        return "#a3e635"
    elif value <= 0.6:
        return "#4ade80"
    else:
        return "#22c55e"

def correlation_table(assets, matrix):
    header = [html.Th(a) for a in [""] + assets]
    rows = []

    for i, a in enumerate(assets):
        row_cells = [html.Th(a)]
        for j, _ in enumerate(assets):
            val = round(matrix[i][j], 2)
            color = get_color(val)
            row_cells.append(
                html.Td(
                    f"{val:.2f}",
                    style={
                        "backgroundColor": color,
                        "padding": "8px",
                        "textAlign": "center",
                        "color": "#19233b",
                        "fontWeight": "bold",
                    },
                )
            )
        rows.append(html.Tr(row_cells))

    return dbc.Table(
        [html.Thead(html.Tr(header)), html.Tbody(rows)],
        bordered=True,
        hover=True,
        responsive=True,
        className="custom-table-container",
    )