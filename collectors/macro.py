"""
Coleta indicadores macroeconômicos:
- SELIC e IPCA via API do Banco Central (gratuita, sem chave)
- Dólar e Euro via AwesomeAPI (gratuita, sem chave)
"""
import httpx
from datetime import datetime

BCB_BASE = "https://api.bcb.gov.br/dados/serie/bcdata.sgs"
AWESOME_BASE = "https://economia.awesomeapi.com.br/json/last"


async def buscar_macro() -> dict:
    resultado = {
        "selic": "N/A",
        "ipca": "N/A",
        "dolar": "N/A",
        "euro": "N/A",
        "atualizado": datetime.now().strftime("%d/%m/%Y %H:%M"),
    }

    async with httpx.AsyncClient(timeout=10) as client:
        # SELIC Over (código 11)
        try:
            r = await client.get(f"{BCB_BASE}.11/dados/ultimos/1?formato=json")
            if r.status_code == 200:
                resultado["selic"] = float(r.json()[0]["valor"])
        except Exception:
            pass

        # IPCA mensal (código 433)
        try:
            r = await client.get(f"{BCB_BASE}.433/dados/ultimos/1?formato=json")
            if r.status_code == 200:
                resultado["ipca"] = float(r.json()[0]["valor"])
        except Exception:
            pass

        # Dólar e Euro via AwesomeAPI
        try:
            r = await client.get(f"{AWESOME_BASE}/USD-BRL,EUR-BRL")
            if r.status_code == 200:
                data = r.json()
                resultado["dolar"] = float(data["USDBRL"]["bid"])
                resultado["euro"] = float(data["EURBRL"]["bid"])
        except Exception:
            pass

    return resultado
