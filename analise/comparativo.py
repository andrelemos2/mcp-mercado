"""
Compara múltiplos ativos lado a lado (ações B3, NYSE, FIIs, cripto).
Detecta automaticamente o tipo de cada ativo pelo ticker.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from collectors.acoes import buscar_acoes_b3, buscar_acoes_nyse
from collectors.fiis import buscar_fiis
from collectors.cripto import buscar_cripto

CRIPTO_IDS = {
    "btc": "bitcoin", "eth": "ethereum", "sol": "solana",
    "ada": "cardano", "xrp": "ripple", "doge": "dogecoin",
    "bnb": "binancecoin", "matic": "matic-network",
}


def _classificar(ticker: str) -> str:
    t = ticker.lower()
    if t in CRIPTO_IDS or t in CRIPTO_IDS.values():
        return "cripto"
    if ticker.endswith("11"):
        return "fii"
    if ticker.endswith(("3", "4", "5", "6")) and len(ticker) == 5:
        return "b3"
    return "nyse"


async def comparar_ativos(ativos: list[str]) -> str:
    b3, nyse, fiis_list, criptos = [], [], [], []

    for a in ativos:
        tipo = _classificar(a)
        if tipo == "cripto":
            criptos.append(CRIPTO_IDS.get(a.lower(), a.lower()))
        elif tipo == "fii":
            fiis_list.append(a.upper())
        elif tipo == "b3":
            b3.append(a.upper())
        else:
            nyse.append(a.upper())

    # Busca todos em paralelo
    import asyncio
    tasks = []
    if b3:
        tasks.append(buscar_acoes_b3(b3))
    if nyse:
        tasks.append(buscar_acoes_nyse(nyse))
    if fiis_list:
        tasks.append(buscar_fiis(fiis_list))
    if criptos:
        tasks.append(buscar_cripto(criptos))

    resultados_raw = await asyncio.gather(*tasks, return_exceptions=True)

    # Normaliza todos para formato comum
    todos = []
    for res in resultados_raw:
        if isinstance(res, Exception):
            continue
        for item in res:
            variacao = item.get("variacao") or item.get("variacao_24h") or 0
            preco_fmt = item.get("preco_fmt") or (
                f"$ {item['preco_usd']:,.2f}" if item.get("preco_usd") else "N/A"
            )
            nome = item.get("ticker") or item.get("nome") or item.get("id", "?")
            todos.append({
                "nome": nome,
                "preco": preco_fmt,
                "variacao": round(float(variacao), 2),
            })

    if not todos:
        return "Não foi possível obter dados dos ativos informados."

    # Ordena por variação (melhor performance primeiro)
    todos.sort(key=lambda x: x["variacao"], reverse=True)

    linhas = [f"# ⚖️ Comparativo de Ativos\n"]
    linhas.append("| # | Ativo | Preço | Variação |")
    linhas.append("|---|-------|-------|----------|")

    for i, item in enumerate(todos, 1):
        sinal = "🟢" if item["variacao"] >= 0 else "🔴"
        linhas.append(
            f"| {i} | **{item['nome']}** | {item['preco']} | {sinal} {item['variacao']:+.2f}% |"
        )

    melhor = todos[0]
    pior = todos[-1]
    linhas.append(f"\n**🏆 Melhor desempenho:** {melhor['nome']} ({melhor['variacao']:+.2f}%)")
    linhas.append(f"**📉 Pior desempenho:** {pior['nome']} ({pior['variacao']:+.2f}%)")

    if len(todos) >= 2:
        diff = abs(melhor["variacao"] - pior["variacao"])
        linhas.append(f"**📊 Diferença entre o melhor e o pior:** {diff:.2f} pontos percentuais")

    return "\n".join(linhas)
