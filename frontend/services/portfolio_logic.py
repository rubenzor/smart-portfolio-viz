
def sum_weights(assets):
    return sum(float(a["weight"]) for a in assets)

# frontend/services/portfolio_logic.py

def detect_benchmark(symbol: str) -> str:
    """
    Deducción automática del benchmark según el ticker.
    Muy fácil de extender añadiendo más reglas.
    """
    s = symbol.upper()

    # ---------------------------
    #   REGLAS USA
    # ---------------------------
    NASDAQ = {"AAPL", "MSFT", "AMZN", "GOOGL", "META", "TSLA", "NVDA"}
    if s in NASDAQ:
        return "NASDAQ"

    SP500 = {"SPY", "VOO", "IVV"}
    if s in SP500:
        return "S&P500"

    DOW = {"DIA"}
    if s in DOW:
        return "DOWJONES"

    # ---------------------------
    #   ESPAÑA — IBEX 35
    # ---------------------------
    if s.endswith(".MC"):
        return "IBEX35"

    # ---------------------------
    #   CRYPTO
    # ---------------------------
    if "-USD" in s or s.endswith("USDT") or s.endswith("USDC"):
        return "CRYPTO"

    # ---------------------------
    #   EUROZONA
    # ---------------------------
    EUROSTOXX = {"EXW1.DE", "FEZ"}
    if s in EUROSTOXX:
        return "EUROSTOXX50"

    # ---------------------------
    #   DEFAULT
    # ---------------------------
    return "UNASSIGNED"


def normalize_weights(assets):
    """
    Toma una lista de activos [{"symbol": , "weight": , ...}]
    y devuelve los mismos con pesos normalizados a 1.0
    """
    weights = [float(a.get("weight", 0)) for a in assets]
    total = sum(weights)

    if total == 0:
        return assets

    for a in assets:
        a["weight"] = float(a["weight"]) / total

    return assets
