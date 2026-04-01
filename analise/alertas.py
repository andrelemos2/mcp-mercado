"""
Verifica alertas de variação de preço para uma lista de ativos.
Identifica movimentos relevantes acima do threshold definido.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from analise.comparativo import _classificar, CRIPTO_IDS
from collectors.acoes import buscar_acoes_b3, buscar_acoes_nyse
from collectors.fiis import buscar_fiis
from collectors.cripto import buscar_cripto
import asyncio


async def verificar_alertas(tickers: list[str], threshold: float = 3.0) -> str:
    b3, nyse, fiis_list, criptos = [], [], [], []

    for a in tickers:
        tipo = _classificar(a)
        if tipo == "cripto":
            criptos.append(CRIPTO_IDS.get(a.lower(), a.lower()))
        elif tipo == "fii":
            fiis_list.append(a.upper())
        elif tipo == "b3":
            b3.append(a.upper())
        else:
            nyse.append(a.upper())

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

    alertas_alta = []
    alertas_baixa = []
    sem_movimento = []

    for res in resultados_raw:
        if isinstance(res, Exception):
            continue
        for item in res:
            variacao = float(item.get("variacao") or item.get("variacao_24h") or 0)
            nome = item.get("ticker") or item.get("nome") or item.get("id", "?")
            preco = item.get("preco_fmt") or (
                f"$ {item.get('preco_usd', 0):,.2f}" if item.get("preco_usd") else "N/A"
            )

            entrada = {"nome": nome, "variacao": round(variacao, 2), "preco": preco}

            if variacao >= threshold:
                alertas_alta.append(entrada)
            elif variacao <= -threshold:
                alertas_baixa.append(entrada)
            else:
                sem_movimento.append(entrada)

    linhas = [f"# 🔔 Alertas de Variação (threshold: ±{threshold}%)\n"]

    if not alertas_alta and not alertas_baixa:
        linhas.append(f"✅ Nenhum ativo monitorado ultrapassou {threshold}% de variação.")
    else:
        if alertas_alta:
            linhas.append(f"## 🟢 ALTA RELEVANTE ({len(alertas_alta)} ativos)")
            for a in sorted(alertas_alta, key=lambda x: x["variacao"], reverse=True):
                linhas.append(f"- **{a['nome']}** → {a['preco']} ({a['variacao']:+.2f}%)")

        if alertas_baixa:
            linhas.append(f"\n## 🔴 QUEDA RELEVANTE ({len(alertas_baixa)} ativos)")
            for a in sorted(alertas_baixa, key=lambda x: x["variacao"]):
                linhas.append(f"- **{a['nome']}** → {a['preco']} ({a['variacao']:+.2f}%)")

    if sem_movimento:
        linhas.append(f"\n## ⚪ Sem movimento relevante ({len(sem_movimento)} ativos)")
        nomes = ", ".join(a["nome"] for a in sem_movimento)
        linhas.append(nomes)

    return "\n".join(linhas)
