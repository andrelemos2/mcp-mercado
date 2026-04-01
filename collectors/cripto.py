"""
Coleta dados de criptomoedas via CoinGecko API pública.
Totalmente gratuita, sem necessidade de chave de API.
Limite: ~30 requisições/minuto no plano free.
"""
import httpx

COINGECKO_BASE = "https://api.coingecko.com/api/v3"


async def buscar_cripto(moedas: list[str]) -> list[dict]:
    """
    Args:
        moedas: IDs do CoinGecko (ex: "bitcoin", "ethereum", "solana").
                Veja lista completa em: https://api.coingecko.com/api/v3/coins/list
    """
    ids = ",".join(moedas)
    resultados = []

    async with httpx.AsyncClient(timeout=15) as client:
        try:
            r = await client.get(
                f"{COINGECKO_BASE}/coins/markets",
                params={
                    "vs_currency": "usd",
                    "ids": ids,
                    "price_change_percentage": "24h,7d",
                    "order": "market_cap_desc",
                },
            )
            if r.status_code != 200:
                return _fallback(moedas)

            # Busca preço em BRL também
            r_brl = await client.get(
                f"{COINGECKO_BASE}/simple/price",
                params={"ids": ids, "vs_currencies": "brl"},
            )
            precos_brl = r_brl.json() if r_brl.status_code == 200 else {}

            for item in r.json():
                coin_id = item.get("id", "")
                resultados.append({
                    "id": coin_id,
                    "nome": item.get("name", coin_id),
                    "simbolo": item.get("symbol", "?"),
                    "preco_usd": item.get("current_price", 0),
                    "preco_brl": precos_brl.get(coin_id, {}).get("brl", 0),
                    "variacao_24h": item.get("price_change_percentage_24h", 0) or 0,
                    "variacao_7d": item.get("price_change_percentage_7d_in_currency", 0) or 0,
                    "market_cap": item.get("market_cap", 0),
                    "volume_24h": item.get("total_volume", 0),
                    "ranking": item.get("market_cap_rank"),
                })
        except Exception:
            return _fallback(moedas)

    return resultados if resultados else _fallback(moedas)


def _fallback(moedas: list[str]) -> list[dict]:
    return [{"id": m, "nome": m, "simbolo": "?", "preco_usd": 0,
             "preco_brl": 0, "variacao_24h": 0, "variacao_7d": 0,
             "market_cap": 0, "volume_24h": 0} for m in moedas]
