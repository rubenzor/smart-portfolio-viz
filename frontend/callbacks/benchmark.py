
import time
import numpy as np
from dash import callback, Input, Output, State, html   
import dash_bootstrap_components as dbc
import pandas as pd

from components.colors import ASSET_COLORS, BENCHMARK_COLORS, generate_color_map 


def _kpi_card(title, value_str, subtitle=None, color="#E879F9"):
    return dbc.Col(
        dbc.Card(
            dbc.CardBody(
                [
                    html.Div(title, className="kpi-title"),
                    html.Div(
                        value_str,
                        className="kpi-value",
                        style={"color": color},
                    ),
                    html.Div(
                        subtitle or "",
                        className="kpi-subtitle",
                    ),
                ]
            ),
            class_name="kpi-card neon-card",
        ),
        md=3,
        xs=6,
    )

