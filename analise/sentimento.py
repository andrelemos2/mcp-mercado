"""
Calcula o sentimento geral do mercado com base em:
- Variação das principais ações
- Variação das principais criptos
- Indicadores macro (SELIC, dólar)
"""


def calcular_sentimento(acoes: list[dict], cripto: list[dict], macro: dict) -> dict:
    """
    Retorna um score de 0 a 100 e um label textual.
    Score > 60: mercado em alta (bullish)
    Score 40-60: neutro/lateral
    Score < 40: mercado em baixa (bearish)
    """
    pontos = []

    # Peso das ações (40% do score)
    if acoes:
        variacoes_acoes = [a["variacao"] for a in acoes if isinstance(a.get("variacao"), (int, float))]
        if variacoes_acoes:
            media_acoes = sum(variacoes_acoes) / len(variacoes_acoes)
            # Converte variação % para score 0-100 (0% = 50, +5% = 100, -5% = 0)
            score_acoes = max(0, min(100, 50 + media_acoes * 10))
            pontos.append(("acoes", score_acoes, 0.4))

    # Peso das criptos (30% do score)
    if cripto:
        variacoes_cripto = [c["variacao_24h"] for c in cripto if isinstance(c.get("variacao_24h"), (int, float))]
        if variacoes_cripto:
            media_cripto = sum(variacoes_cripto) / len(variacoes_cripto)
            score_cripto = max(0, min(100, 50 + media_cripto * 5))
            pontos.append(("cripto", score_cripto, 0.3))

    # Peso do dólar (30% do score) — dólar alto = pressão negativa para BR
    dolar = macro.get("dolar")
    if isinstance(dolar, (int, float)):
        # Considera neutro ~5.0, pressão negativa acima de 5.5
        score_dolar = max(0, min(100, 100 - (dolar - 4.5) * 30))
        pontos.append(("dolar", score_dolar, 0.3))

    if not pontos:
        return {"score": 50, "label": "⚪ Neutro", "descricao": "Dados insuficientes para análise."}

    score_total = sum(score * peso for _, score, peso in pontos)
    score_total = round(score_total)

    if score_total >= 65:
        label = "🟢 Bullish (Alta)"
        descricao = "Mercado com predominância de otimismo. Maioria dos ativos em valorização."
    elif score_total >= 50:
        label = "🟡 Levemente Otimista"
        descricao = "Mercado levemente positivo, mas com cautela. Atenção a indicadores macro."
    elif score_total >= 35:
        label = "🟠 Lateral / Incerto"
        descricao = "Mercado sem direção clara. Momento de cautela e análise caso a caso."
    else:
        label = "🔴 Bearish (Baixa)"
        descricao = "Mercado sob pressão. Predominância de queda nos ativos monitorados."

    detalhes = []
    for nome, score, peso in pontos:
        detalhes.append(f"  - {nome.title()}: {score:.0f}/100 (peso {int(peso*100)}%)")

    return {
        "score": score_total,
        "label": label,
        "descricao": descricao + "\n" + "\n".join(detalhes),
    }
