from dash import Dash
import dash_bootstrap_components as dbc

from components.layout import layout

# Importar callbacks (necesario para que se registren)
import callbacks.portfolios
import callbacks.charts
import callbacks.optimization
import callbacks.forecasting
import callbacks.benchmark
import callbacks.overview


app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.CYBORG],
    suppress_callback_exceptions=True,
)

app.layout = layout

server = app.server

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050, debug=True)
