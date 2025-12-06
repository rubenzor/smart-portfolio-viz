import requests

YF_SEARCH_URL = "https://query2.finance.yahoo.com/v1/finance/search"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Origin": "https://finance.yahoo.com",
    "Referer": "https://finance.yahoo.com/",
    "Connection": "keep-alive",
}


def search_tickers(query: str) -> list:
    if not query or len(query) < 1:
        return []

    try:
        # 🌟 Yahoo a veces requiere cookies previas
        s = requests.Session()
        s.headers.update(HEADERS)

        # 1) Hacer petición inicial para obtener cookies válidas
        s.get("https://finance.yahoo.com", timeout=5)

        # 2) Llamada real al endpoint de búsqueda
        resp = s.get(
            YF_SEARCH_URL,
            params={"q": query, "quotesCount": 20},
            timeout=5
        )

        resp.raise_for_status()
        raw = resp.json()

    except Exception as e:
        print("ERROR Yahoo Finance:", e)
        return []

    quotes = raw.get("quotes", [])
    results = []

    for item in quotes:
        symbol = item.get("symbol")
        if not symbol:
            continue

        name = (
            item.get("shortname")
            or item.get("longname")
            or item.get("typeDisp")
            or ""
        )

        results.append({
            "symbol": symbol.upper(),
            "name": name,
        })

    return results
