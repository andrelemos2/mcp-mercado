# MCP Mercado Financeiro

Servidor MCP em Python que conecta o Claude a dados reais de ações, FIIs, criptos e indicadores macroeconômicos, com fontes gratuitas.

## Visão geral

- B3 e NYSE
- FIIs
- Criptomoedas
- Macro e notícias

## Arquitetura do projeto

O Claude Desktop chama o servidor MCP, que coleta dados de múltiplas APIs gratuitas e retorna análises estruturadas.

```text
Claude Desktop <-> MCP Server <-> APIs Gratuitas
```

### Componentes

- **Claude Desktop**: faz perguntas e recebe análises formatadas.
- **MCP Server**: `server.py`, com 6 ferramentas expostas ao Claude.
- **APIs gratuitas**: Brapi, CoinGecko, BCB, AwesomeAPI, Yahoo Finance e RSS.

## Estrutura de arquivos

```text
mcp-mercado/
├── server.py                  # Servidor MCP - 6 ferramentas
├── requirements.txt           # Dependências
├── collectors/                # Coleta de dados
│   ├── acoes.py               # B3 (Brapi) + NYSE (yfinance)
│   ├── fiis.py                # FIIs via Brapi
│   ├── cripto.py              # CoinGecko API
│   ├── macro.py               # BCB + AwesomeAPI
│   └── noticias.py            # RSS feeds financeiros
└── analise/                   # Processamento
    ├── sentimento.py          # Score bullish/bearish
    ├── comparativo.py         # Ranking de ativos
    └── alertas.py             # Variação acima do threshold
```

## As 6 ferramentas MCP

Cada função decorada com `@mcp.tool()` vira um comando que o Claude pode invocar automaticamente.

### Panorama

**`panorama_mercado()`**

Visão geral com IBOV, SELIC, dólar, cripto e sentimento bullish/bearish em um único relatório.

### Ações

**`analisar_acoes(tickers)`**

Preço, variação, volume, máxima e mínima de qualquer ação da B3 ou NYSE/NASDAQ.

### FIIs

**`analisar_fiis(tickers)`**

Dividend yield, P/VP e último rendimento dos principais fundos imobiliários.

### Cripto

**`analisar_cripto(moedas)`**

Preço em USD e BRL, variação de 24h e 7d, market cap via CoinGecko gratuito.

### Comparativo

**`comparar(ativos)`**

Ranking lado a lado de ativos mistos: ações, FIIs e criptos ao mesmo tempo.

### Notícias

**`noticias_mercado(setor)`**

Notícias agrupadas por setor e classificadas como positivas, negativas ou neutras.

## Instalação passo a passo

```bash
# 1. Clonar / criar pasta e entrar nela
mkdir mcp-mercado && cd mcp-mercado

# 2. Ambiente virtual
python -m venv venv
source venv/bin/activate     # macOS/Linux
venv\Scripts\activate        # Windows

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Testar o servidor localmente
python server.py

# 5. (Opcional) Debug visual com MCP Inspector
npx @modelcontextprotocol/inspector python server.py
```

## Configurar Claude Desktop

Edite o arquivo `claude_desktop_config.json` para registrar o servidor.

### Localização do arquivo

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

### Exemplo de configuração

```json
{
  "mcpServers": {
    "mercado-financeiro": {
      "command": "/caminho/para/mcp-mercado/venv/bin/python",
      "args": ["/caminho/para/mcp-mercado/server.py"],
      "env": {
        "PYTHONPATH": "/caminho/para/mcp-mercado"
      }
    }
  }
}
```

Substitua `/caminho/para/` pelo caminho absoluto real. No Windows, use algo como `C:\Users\seu_nome\mcp-mercado\...`. Reinicie o Claude Desktop após salvar.

## Como usar no Claude

Após configurar, basta perguntar naturalmente. O Claude decide qual ferramenta chamar.

### Exemplos de prompts

- Como está o mercado hoje? Me dê um panorama geral.
- Analisa PETR4, VALE3 e ITUB4 para mim.
- Compara Bitcoin, HGLG11 e PETR4 — qual teve melhor desempenho hoje?
- Tem algum ativo na minha lista que variou mais de 5% hoje? [BBDC4, NVDA, ethereum, MXRF11]
- Me traga notícias de cripto classificadas por sentimento.
- Como está o dólar, SELIC e IPCA agora?
- Quais FIIs têm melhor dividend yield hoje?

O Claude entende contexto. Você pode fazer perguntas encadeadas como: "Dado esse panorama, onde você acha que vale mais a pena aportar agora: FIIs ou ações de dividendos?" e ele usará os dados coletados para raciocinar.
