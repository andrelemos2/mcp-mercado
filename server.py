"""
MCP Server - Inteligência de Mercado Financeiro
Ferramentas para análise de ações, FIIs, cripto e macro.
"""
import sys
from pathlib import Path

# Garante que o diretório do projeto esteja no path,
# independente de onde o Python for chamado.
sys.path.insert(0, str(Path(__file__).parent))

from mcp.server.fastmcp import FastMCP
from collectors.acoes import buscar_acoes_b3, buscar_acoes_nyse
from collectors.fiis import buscar_fiis
from collectors.cripto import buscar_cripto
from collectors.macro import buscar_macro
from collectors.noticias import buscar_noticias
from analise.sentimento import calcular_sentimento
from analise.comparativo import comparar_ativos
from analise.alertas import verificar_alertas

mcp = FastMCP("mercado-financeiro")


@mcp.tool()
async def panorama_mercado() -> str:
    """
    Retorna um panorama completo do mercado financeiro agora:
    principais índices (IBOV, S&P500, BTC), indicadores macro
    (SELIC, IPCA, dólar) e sentimento geral (alta/baixa).
    Use quando o usuário pedir visão geral, resumo do dia ou
    'como está o mercado'.
    """
    macro = await buscar_macro()
    acoes_br = await buscar_acoes_b3(["PETR4", "VALE3", "ITUB4", "BBDC4", "WEGE3"])
    cripto = await buscar_cripto(["bitcoin", "ethereum", "solana"])
    sentimento = calcular_sentimento(acoes_br, cripto, macro)

    linhas = ["# 📊 Panorama do Mercado\n"]

    linhas.append("## 🌎 Indicadores Macro")
    linhas.append(f"- **SELIC:** {macro['selic']}% a.a.")
    linhas.append(f"- **IPCA (último mês):** {macro['ipca']}%")
    linhas.append(f"- **Dólar (USD/BRL):** R$ {macro['dolar']}")
    linhas.append(f"- **Euro (EUR/BRL):** R$ {macro['euro']}\n")

    linhas.append("## 📈 Principais Ações BR")
    for a in acoes_br:
        sinal = "🟢" if a["variacao"] >= 0 else "🔴"
        linhas.append(f"- {sinal} **{a['ticker']}** R$ {a['preco']} ({a['variacao']:+.2f}%)")

    linhas.append("\n## ₿ Criptomoedas")
    for c in cripto:
        sinal = "🟢" if c["variacao_24h"] >= 0 else "🔴"
        linhas.append(f"- {sinal} **{c['nome']}** ${c['preco_usd']:,.2f} ({c['variacao_24h']:+.2f}%)")

    linhas.append(f"\n## 🧭 Sentimento Geral do Mercado")
    linhas.append(f"**{sentimento['label']}** — Score: {sentimento['score']}/100")
    linhas.append(sentimento["descricao"])

    return "\n".join(linhas)


@mcp.tool()
async def analisar_acoes(tickers: list[str]) -> str:
    """
    Busca dados detalhados de ações específicas da B3 ou NYSE.
    Retorna preço atual, variação, volume e resumo fundamentalista.

    Args:
        tickers: Lista de tickers. Ex: ["PETR4", "VALE3"] para B3
                 ou ["AAPL", "NVDA"] para NYSE.
    """
    br = [t for t in tickers if t.endswith(("3", "4", "11"))]
    us = [t for t in tickers if t not in br]

    resultados = []
    if br:
        resultados += await buscar_acoes_b3(br)
    if us:
        resultados += await buscar_acoes_nyse(us)

    if not resultados:
        return "Nenhum ativo encontrado. Verifique os tickers informados."

    linhas = [f"# 📋 Análise de Ativos\n"]
    for a in resultados:
        sinal = "🟢" if a["variacao"] >= 0 else "🔴"
        linhas.append(f"## {sinal} {a['ticker']}")
        linhas.append(f"- **Preço:** {a['preco_fmt']}")
        linhas.append(f"- **Variação:** {a['variacao']:+.2f}%")
        linhas.append(f"- **Abertura:** {a.get('abertura', 'N/A')}")
        linhas.append(f"- **Máx/Mín dia:** {a.get('maxima', 'N/A')} / {a.get('minima', 'N/A')}")
        linhas.append(f"- **Volume:** {a.get('volume_fmt', 'N/A')}\n")

    return "\n".join(linhas)


@mcp.tool()
async def analisar_fiis(tickers: list[str] = None) -> str:
    """
    Busca dados de Fundos de Investimento Imobiliário (FIIs).
    Retorna preço, dividend yield, P/VP e últimos rendimentos.
    Se nenhum ticker for informado, retorna os 10 maiores FIIs.

    Args:
        tickers: Lista de FIIs. Ex: ["HGLG11", "KNRI11", "XPML11"]
                 Se vazio, retorna ranking dos principais FIIs.
    """
    lista = tickers or ["HGLG11", "KNRI11", "XPML11", "MXRF11", "GGRC11",
                        "BTLG11", "VISC11", "HSML11", "RBRF11", "ALZR11"]
    fiis = await buscar_fiis(lista)

    linhas = ["# 🏢 Fundos Imobiliários (FIIs)\n"]
    for f in fiis:
        sinal = "🟢" if f["variacao"] >= 0 else "🔴"
        linhas.append(f"## {sinal} {f['ticker']}")
        linhas.append(f"- **Preço:** R$ {f['preco']}")
        linhas.append(f"- **Variação:** {f['variacao']:+.2f}%")
        linhas.append(f"- **Dividend Yield (12m):** {f.get('dy', 'N/A')}%")
        linhas.append(f"- **P/VP:** {f.get('pvp', 'N/A')}")
        linhas.append(f"- **Último rendimento:** R$ {f.get('ultimo_rendimento', 'N/A')}\n")

    return "\n".join(linhas)


@mcp.tool()
async def analisar_cripto(moedas: list[str] = None) -> str:
    """
    Busca cotações e análise de criptomoedas via CoinGecko (gratuito).
    Retorna preço em USD e BRL, variação 24h, market cap e volume.

    Args:
        moedas: IDs CoinGecko das moedas. Ex: ["bitcoin", "ethereum", "solana"]
                Se vazio, retorna top 10 por market cap.
    """
    lista = moedas or ["bitcoin", "ethereum", "solana", "cardano",
                       "ripple", "dogecoin", "polkadot", "chainlink",
                       "avalanche-2", "uniswap"]
    dados = await buscar_cripto(lista)

    linhas = ["# ₿ Criptomoedas\n"]
    for c in dados:
        sinal = "🟢" if c["variacao_24h"] >= 0 else "🔴"
        linhas.append(f"## {sinal} {c['nome']} ({c['simbolo'].upper()})")
        linhas.append(f"- **Preço USD:** ${c['preco_usd']:,.2f}")
        linhas.append(f"- **Preço BRL:** R$ {c['preco_brl']:,.2f}")
        linhas.append(f"- **Variação 24h:** {c['variacao_24h']:+.2f}%")
        linhas.append(f"- **Market Cap:** ${c['market_cap']:,.0f}")
        linhas.append(f"- **Volume 24h:** ${c['volume_24h']:,.0f}\n")

    return "\n".join(linhas)


@mcp.tool()
async def comparar(ativos: list[str]) -> str:
    """
    Compara múltiplos ativos lado a lado: ações, FIIs ou criptos.
    Ideal para decidir entre dois ou mais investimentos.
    Mostra variação, retorno relativo e qual teve melhor desempenho.

    Args:
        ativos: Lista mista de ativos. Ex: ["PETR4", "VALE3", "bitcoin"]
    """
    return await comparar_ativos(ativos)


@mcp.tool()
async def noticias_mercado(setor: str = "geral", limite: int = 10) -> str:
    """
    Busca e agrupa notícias financeiras por setor.
    Classifica cada notícia como positiva, negativa ou neutra.

    Args:
        setor: Filtro de setor. Opções: "geral", "acoes", "cripto",
               "fiis", "macro", "commodities", "exterior"
        limite: Número máximo de notícias (padrão: 10, máx: 30)
    """
    return await buscar_noticias(setor, min(limite, 30))


@mcp.tool()
async def alertas_variacao(tickers: list[str], threshold: float = 3.0) -> str:
    """
    Verifica quais ativos tiveram variação acima do limite definido
    (positiva ou negativa) nas últimas 24 horas.
    Útil para identificar movimentos relevantes do mercado.

    Args:
        tickers: Lista de ativos para monitorar.
                 Ex: ["PETR4", "VALE3", "ITUB4", "bitcoin"]
        threshold: Percentual mínimo de variação para alertar (padrão: 3.0%)
    """
    return await verificar_alertas(tickers, threshold)


if __name__ == "__main__":
    mcp.run()
