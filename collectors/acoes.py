"""
Coleta cotações de ações:
- B3 via Brapi.dev (gratuito, sem chave para uso básico)
- NYSE/NASDAQ via yfinance (gratuito, sem chave)
"""
import httpx

BRAPI_BASE = "https://brapi.dev/api/quote"


def _fmt_preco(valor, moeda="R$") -> str:
    if valor is None:
        return "N/A"
    return f"{moeda} {valor:,.2f}"


def _fmt_volume(valor) -> str:
    if valor is None:
        return "N/A"
    if valor >= 1_000_000:
        return f"{valor/1_000_000:.1f}M"
    if valor >= 1_000:
        return f"{valor/1_000:.1f}K"
    return str(valor)


async def buscar_acoes_b3(tickers: list[str]) -> list[dict]:
    """Busca cotações da B3 via Brapi.dev"""
    symbols = ",".join(tickers)
    resultados = []

    async with httpx.AsyncClient(timeout=15) as client:
        try:
            r = await client.get(f"{BRAPI_BASE}/{symbols}?range=1d&interval=1d")
            if r.status_code != 200:
                return _fallback_b3(tickers)

            data = r.json()
            for item in data.get("results", []):
                preco = item.get("regularMarketPrice")
                anterior = item.get("regularMarketPreviousClose")
                variacao = ((preco - anterior) / anterior * 100) if preco and anterior else 0

                resultados.append({
                    "ticker": item.get("symbol", "?"),
                    "preco": preco,
                    "preco_fmt": _fmt_preco(preco),
                    "variacao": round(variacao, 2),
                    "abertura": _fmt_preco(item.get("regularMarketOpen")),
                    "maxima": _fmt_preco(item.get("regularMarketDayHigh")),
                    "minima": _fmt_preco(item.get("regularMarketDayLow")),
                    "volume": item.get("regularMarketVolume"),
                    "volume_fmt": _fmt_volume(item.get("regularMarketVolume")),
                    "mercado": "B3",
                })
        except Exception:
            return _fallback_b3(tickers)

    return resultados


async def buscar_acoes_nyse(tickers: list[str]) -> list[dict]:
    """
    Busca cotações da NYSE/NASDAQ via Yahoo Finance (yfinance).
    Requer: pip install yfinance
    """
    resultados = []
    try:
        import yfinance as yf
        for ticker in tickers:
            try:
                info = yf.Ticker(ticker).fast_info
                preco = info.last_price
                anterior = info.previous_close
                variacao = ((preco - anterior) / anterior * 100) if preco and anterior else 0
                resultados.append({
                    "ticker": ticker,
                    "preco": preco,
                    "preco_fmt": f"$ {preco:,.2f}" if preco else "N/A",
                    "variacao": round(variacao, 2),
                    "abertura": f"$ {info.open:,.2f}" if info.open else "N/A",
                    "maxima": f"$ {info.day_high:,.2f}" if info.day_high else "N/A",
                    "minima": f"$ {info.day_low:,.2f}" if info.day_low else "N/A",
                    "volume": info.three_month_average_volume,
                    "volume_fmt": _fmt_volume(info.three_month_average_volume),
                    "mercado": "NYSE/NASDAQ",
                })
            except Exception:
                resultados.append({"ticker": ticker, "preco": None,
                                   "preco_fmt": "N/A", "variacao": 0, "mercado": "NYSE"})
    except ImportError:
        # yfinance não instalado — retorna placeholder
        for ticker in tickers:
            resultados.append({
                "ticker": ticker,
                "preco": None,
                "preco_fmt": "Instale yfinance: pip install yfinance",
                "variacao": 0,
                "mercado": "NYSE/NASDAQ",
            })
    return resultados


def _fallback_b3(tickers: list[str]) -> list[dict]:
    """Retorna estrutura vazia quando a API falha."""
    return [{"ticker": t, "preco": None, "preco_fmt": "Indisponível",
             "variacao": 0, "mercado": "B3"} for t in tickers]
