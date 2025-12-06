import yfinance as yf

def is_valid_ticker(symbol: str) -> bool:
    try:
        data = yf.Ticker(symbol).history(period="6mo")
        return not data.empty
    except:
        return False

def download_prices(symbols):
    data = yf.download(
        tickers=symbols,
        period="1y",
        interval="1d",
        auto_adjust=True,
        progress=False,
    )["Close"]

    return data
