"""
Coleta dados de Fundos de Investimento Imobiliário (FIIs)
via Brapi.dev — gratuito, sem necessidade de chave de API.
"""
import httpx

BRAPI_BASE = "https://brapi.dev/api/quote"


async def buscar_fiis(tickers: list[str]) -> list[dict]:
    symbols = ",".join(tickers)
    resultados = []

    async with httpx.AsyncClient(timeout=15) as client:
        try:
            r = await client.get(
                f"{BRAPI_BASE}/{symbols}",
                params={"range": "1d", "interval": "1d", "fundamental": "true"},
            )
            if r.status_code != 200:
                return _fallback(tickers)

            for item in r.json().get("results", []):
                preco = item.get("regularMarketPrice")
                anterior = item.get("regularMarketPreviousClose")
                variacao = ((preco - anterior) / anterior * 100) if preco and anterior else 0

                # Dados fundamentalistas (quando disponíveis)
                summary = item.get("summaryProfile", {}) or {}
                fi = item.get("financialData", {}) or {}

                resultados.append({
                    "ticker": item.get("symbol", "?"),
                    "preco": round(preco, 2) if preco else None,
                    "variacao": round(variacao, 2),
                    "dy": item.get("dividendYield"),          # dividend yield 12m
                    "pvp": item.get("priceToBook"),            # P/VP
                    "ultimo_rendimento": item.get("lastDividendValue"),
                    "liquidez": item.get("regularMarketVolume"),
                })
        except Exception:
            return _fallback(tickers)

    return resultados if resultados else _fallback(tickers)


def _fallback(tickers: list[str]) -> list[dict]:
    return [{"ticker": t, "preco": None, "variacao": 0,
             "dy": "N/A", "pvp": "N/A", "ultimo_rendimento": "N/A"} for t in tickers]
