"""
Coleta e classifica notícias financeiras via feeds RSS públicos.
Sem necessidade de API key. Fontes: InfoMoney, Valor, Investing.com BR.
"""
import feedparser
import httpx
from datetime import datetime

FEEDS = {
    "geral": [
        "https://www.infomoney.com.br/feed/",
        "https://valoreconomico.globo.com/rss/economia/financas.xml",
    ],
    "acoes": [
        "https://www.infomoney.com.br/mercados/acoes/feed/",
        "https://br.investing.com/rss/news_25.rss",
    ],
    "cripto": [
        "https://www.infomoney.com.br/guias/criptomoedas/feed/",
        "https://br.cointelegraph.com/rss",
    ],
    "fiis": [
        "https://www.infomoney.com.br/onde-investir/fundos-imobiliarios/feed/",
        "https://fiis.com.br/feed/",
    ],
    "macro": [
        "https://valoreconomico.globo.com/rss/economia.xml",
        "https://agenciabrasil.ebc.com.br/economia/feed/atom/",
    ],
    "commodities": [
        "https://www.infomoney.com.br/mercados/commodities/feed/",
    ],
    "exterior": [
        "https://br.investing.com/rss/news_301.rss",
    ],
}

# Palavras-chave para classificar sentimento
POSITIVO = ["sobe", "alta", "lucro", "crescimento", "valoriza", "recorde",
            "positivo", "aprova", "supera", "expansão", "otimismo"]
NEGATIVO = ["cai", "queda", "perde", "recessão", "inflação", "risco",
            "negativo", "crise", "incerteza", "piora", "prejuízo"]


def _sentimento_noticia(texto: str) -> str:
    texto = texto.lower()
    pos = sum(1 for p in POSITIVO if p in texto)
    neg = sum(1 for n in NEGATIVO if n in texto)
    if pos > neg:
        return "🟢 Positiva"
    elif neg > pos:
        return "🔴 Negativa"
    return "⚪ Neutra"


async def buscar_noticias(setor: str = "geral", limite: int = 10) -> str:
    feeds = FEEDS.get(setor, FEEDS["geral"])
    artigos = []

    for url in feeds:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:limite // len(feeds) + 2]:
                titulo = entry.get("title", "")
                resumo = entry.get("summary", "")[:250]
                link = entry.get("link", "")
                data = entry.get("published", "")

                artigos.append({
                    "titulo": titulo,
                    "resumo": resumo,
                    "link": link,
                    "data": data,
                    "sentimento": _sentimento_noticia(titulo + " " + resumo),
                    "fonte": feed.feed.get("title", url),
                })
        except Exception:
            continue

    artigos = artigos[:limite]

    if not artigos:
        return f"Nenhuma notícia encontrada para o setor '{setor}'."

    # Agrupa por sentimento
    positivas = [a for a in artigos if "Positiva" in a["sentimento"]]
    negativas = [a for a in artigos if "Negativa" in a["sentimento"]]
    neutras = [a for a in artigos if "Neutra" in a["sentimento"]]

    linhas = [f"# 📰 Notícias de Mercado — {setor.title()}\n"]
    linhas.append(f"**Total:** {len(artigos)} notícias | "
                  f"🟢 {len(positivas)} positivas | "
                  f"🔴 {len(negativas)} negativas | "
                  f"⚪ {len(neutras)} neutras\n")

    for grupo, label in [(positivas, "🟢 Positivas"), (negativas, "🔴 Negativas"), (neutras, "⚪ Neutras")]:
        if not grupo:
            continue
        linhas.append(f"## {label}")
        for a in grupo:
            linhas.append(f"**{a['titulo']}**")
            if a["resumo"]:
                linhas.append(f"{a['resumo']}...")
            linhas.append(f"[Leia mais]({a['link']}) — {a['fonte']}\n")

    return "\n".join(linhas)
