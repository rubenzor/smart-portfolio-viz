"""Streamlit user interface for the Smart Portfolio Visualiser."""

from __future__ import annotations

from datetime import date, datetime
from typing import Dict, Iterable, List, Mapping

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from smart_portfolio_viz.insights import (
    AssetInsight,
    build_asset_insights,
    classify_portfolio,
    compute_horizon_returns,
    fetch_latest_news,
    portfolio_projection,
)
from smart_portfolio_viz.workflows.overview import OverviewConfig, build_portfolio_overview


st.set_page_config(
    page_title="Smart Portfolio Viz",
    page_icon="📈",
    layout="wide",
)


DEFAULT_PORTFOLIO = pd.DataFrame(
    [
        {"Ticker": "AAPL", "Weight %": 25.0},
        {"Ticker": "MSFT", "Weight %": 25.0},
        {"Ticker": "GOOGL", "Weight %": 20.0},
        {"Ticker": "AMZN", "Weight %": 15.0},
        {"Ticker": "TSLA", "Weight %": 15.0},
    ]
)


TIMEFRAME_LABELS = {
    "1 día": 1,
    "5 días": 5,
    "30 días": 30,
    "6 meses": 182,
    "1 año": 365,
}


def _parse_portfolio(df: pd.DataFrame) -> Dict[str, float]:
    cleaned = df.dropna(subset=["Ticker"]).copy()
    cleaned["Ticker"] = cleaned["Ticker"].str.upper().str.strip()
    cleaned = cleaned[cleaned["Ticker"] != ""]
    weights = cleaned.set_index("Ticker")["Weight %"].fillna(0.0) / 100
    weights = weights[weights > 0]
    return weights.to_dict()


def _load_overview(
    tickers: Iterable[str],
    weights: Mapping[str, float],
    start: datetime | None,
    end: datetime | None,
    interval: str,
    benchmark: str | None,
):
    config = OverviewConfig(
        tickers=list(tickers),
        weights=dict(weights),
        start=start,
        end=end,
        interval=interval,
        benchmark=benchmark,
    )
    return build_portfolio_overview(config)


def _format_percentage(value: float) -> str:
    if pd.isna(value):
        return "N/A"
    return f"{value:.2%}"


def _format_currency(value: float) -> str:
    if pd.isna(value):
        return "N/A"
    return f"${value:,.2f}"


st.title("Smart Portfolio Visualiser")
st.caption(
    "Construye, monitoriza y recibe recomendaciones inteligentes sobre tu cartera personalizada."
)

with st.sidebar:
    st.header("Configuración de la cartera")
    editor_df = st.data_editor(
        DEFAULT_PORTFOLIO,
        num_rows="dynamic",
        use_container_width=True,
        key="portfolio_editor",
    )
    start_date = st.date_input("Fecha de inicio", value=date(2023, 1, 1))
    end_date = st.date_input("Fecha fin", value=date.today())
    interval = st.selectbox("Intervalo", options=["1d", "1wk", "1mo"], index=0)
    benchmark_ticker = st.text_input("Benchmark opcional", value="^GSPC")
    fetch_button = st.button("Actualizar datos", use_container_width=True)

portfolio_weights = _parse_portfolio(editor_df)

if not portfolio_weights:
    st.warning("Añade al menos un activo con un peso positivo para generar la vista de cartera.")
    st.stop()

if end_date < start_date:
    st.error("La fecha de fin debe ser posterior a la fecha de inicio.")
    st.stop()

start_dt = datetime.combine(start_date, datetime.min.time())
end_dt = datetime.combine(end_date, datetime.min.time())

if fetch_button or "overview" not in st.session_state:
    with st.spinner("Descargando datos de mercado..."):
        overview = _load_overview(
            tickers=portfolio_weights.keys(),
            weights=portfolio_weights,
            start=start_dt,
            end=end_dt,
            interval=interval,
            benchmark=benchmark_ticker.strip() or None,
        )
        st.session_state["overview"] = overview
else:
    overview = st.session_state["overview"]

prices = overview.prices
weights_series = overview.weights
returns = overview.returns

st.subheader("Distribución de la cartera")
allocation_df = pd.DataFrame({"Peso": weights_series}).reset_index(names="Ticker")
pie_fig = px.pie(allocation_df, values="Peso", names="Ticker", hole=0.4)
pie_fig.update_layout(height=400)
st.plotly_chart(pie_fig, use_container_width=True)

horizon_df = compute_horizon_returns(prices)

summary_table = horizon_df.copy()
summary_table["Peso"] = weights_series
summary_table = summary_table[["Peso", "Latest", "1D", "5D", "30D", "6M", "1Y"]]
summary_table = summary_table.rename(columns={"Latest": "Precio actual"})
summary_table = summary_table.reset_index().rename(columns={"index": "Ticker"})

summary_table["Peso"] = summary_table["Peso"].apply(_format_percentage)
summary_table["Precio actual"] = summary_table["Precio actual"].apply(_format_currency)
for col in ["1D", "5D", "30D", "6M", "1Y"]:
    summary_table[col] = summary_table[col].apply(_format_percentage)

st.markdown("### Tabla de asignaciones y retornos rápidos")
st.dataframe(summary_table, use_container_width=True)

st.markdown("---")
st.subheader("Monitor de activos")

timeframe_options = list(TIMEFRAME_LABELS.keys())
default_timeframe = "30 días" if "30 días" in TIMEFRAME_LABELS else timeframe_options[0]
timeframe = st.select_slider("Ventana temporal", options=timeframe_options, value=default_timeframe)
days_back = TIMEFRAME_LABELS.get(timeframe, 30)

asset_tabs = st.tabs(list(prices.columns))
for ticker, tab in zip(prices.columns, asset_tabs):
    with tab:
        ticker_series = prices[ticker]
        start_window = ticker_series.index.max() - pd.Timedelta(days=days_back)
        windowed = ticker_series.loc[ticker_series.index >= start_window]
        if len(windowed) < 2:
            windowed = ticker_series

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(x=windowed.index, y=windowed.values, mode="lines", name=ticker)
        )
        fig.update_layout(height=300, title=f"Evolución de {ticker}")
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.subheader("Recomendaciones y predicciones")

portfolio_fig = go.Figure()
portfolio_fig.add_trace(
    go.Scatter(
        x=overview.performance.cumulative_returns.index,
        y=overview.performance.cumulative_returns.values,
        mode="lines",
        name="Cartera",
    )
)
if overview.benchmark_returns is not None:
    benchmark_cum = (overview.benchmark_returns + 1).cumprod() - 1
    portfolio_fig.add_trace(
        go.Scatter(x=benchmark_cum.index, y=benchmark_cum.values, mode="lines", name="Benchmark")
    )
portfolio_fig.update_layout(height=300, title="Evolución acumulada")
st.plotly_chart(portfolio_fig, use_container_width=True)

benchmark_total = overview.benchmark_performance.total_return if overview.benchmark_performance else None
status = classify_portfolio(overview.performance.total_return, benchmark_total)
st.metric(
    label="Estado de la cartera",
    value=status,
    delta=_format_percentage(overview.performance.total_return),
)

asset_insights: List[AssetInsight] = build_asset_insights(prices)
projection_price, projection_return = portfolio_projection(weights_series.to_dict(), asset_insights)

st.metric(
    label="Proyección de cartera (30 días)",
    value=_format_percentage(projection_return),
    delta=f"Valor hipotético: {_format_currency(projection_price)}",
)

insight_rows = []
prediction_rows = []
for insight in asset_insights:
    insight_rows.append(
        {
            "Ticker": insight.ticker,
            "Acción": insight.action,
            "Justificación": insight.rationale,
            "Sustitutos sugeridos": ", ".join(insight.substitutes) if insight.substitutes else "-",
        }
    )
    prediction_rows.append(
        {
            "Ticker": insight.ticker,
            "Precio proyectado": _format_currency(insight.predicted_price),
            "Retorno esperado": _format_percentage(insight.predicted_return),
        }
    )

st.markdown("#### Acciones recomendadas por activo")
st.dataframe(pd.DataFrame(insight_rows), use_container_width=True)

st.markdown("#### Predicciones de precio (30 días)")
st.dataframe(pd.DataFrame(prediction_rows), use_container_width=True)

st.markdown("---")
st.subheader("Noticias y contexto")

news_tabs = st.tabs(list(prices.columns))
for ticker, tab in zip(prices.columns, news_tabs):
    with tab:
        news_items = fetch_latest_news(ticker, limit=5)
        if not news_items:
            st.info("No se han encontrado noticias recientes.")
            continue
        for item in news_items:
            publisher = f" ({item['publisher']})" if item.get("publisher") else ""
            st.markdown(f"- [{item['title']}]({item['link']}){publisher}")

st.markdown("---")
st.caption(
    "Las recomendaciones son heurísticas basadas en información histórica y no constituyen asesoramiento financiero."
)
