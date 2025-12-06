import yfinance as yf
import pandas as pd


def fetch_history(symbols, days=365):
    """
    Descarga histórico y lo devuelve en el formato EXACTO
    que el frontend necesita:
    
    {
        "dates": [...],
        "assets": { symbol: [ .. precios .. ] }
    }
    """
    if isinstance(symbols, str):
        symbols = [symbols]

    try:
        df = yf.download(
            symbols,
            period=f"{days}d",
            interval="1d",
            auto_adjust=True,
            progress=False,
        )
    except Exception as e:
        print("YF ERROR:", e)
        return {"dates": [], "assets": {}}

    # MultiIndex → quedarse solo con Close o Adj Close
    if isinstance(df.columns, pd.MultiIndex):
        df = df["Close"] if "Close" in df.columns else df[df.columns[0]]

    # Si solo un activo → convertir serie en DF
    if isinstance(df, pd.Series):
        df = df.to_frame()

    df = df.dropna(how="all")

    if df.empty:
        return {"dates": [], "assets": {}}

    dates = df.index.strftime("%Y-%m-%d").tolist()

    assets = {
        col: df[col].fillna(method="ffill").fillna(method="bfill").tolist()
        for col in df.columns
    }

    return {
        "dates": dates,
        "assets": assets,
    }
