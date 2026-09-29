# Dados sintéticos compartilhados

Todos os arquivos são gerados por `gerar_dados.py` com semente fixa (42), o
que garante a reprodutibilidade e permite comparar as mesmas estimativas entre
R, Python, Julia e C. Para gerá-los de novo, basta rodar o script.

```
python3 dados/gerar_dados.py
```

## `macro_series.csv`

Série temporal simulada como um processo AR(1) estacionário, que pode ser
lida como uma taxa de crescimento trimestral do PIB em %. O processo gerador
é `pib_t = 0.5 + 0.55 * pib_{t-1} + erro_t`, com `erro ~ N(0, 1)`.

| coluna | descrição |
|---|---|
| `trimestre` | índice de tempo (1 a 80) |
| `pib_crescimento` | valor simulado da série |

## `painel.csv`

Painel de 12 firmas ao longo de 10 anos, com heterogeneidade não observada
por firma (efeito fixo), gerado por
`investimento_it = 2.0 + efeito_firma_i + 0.4 * vendas_it + erro_it`.

| coluna | descrição |
|---|---|
| `firma` | identificador da firma (1 a 12) |
| `ano` | ano dentro do painel (1 a 10) |
| `investimento` | variável dependente |
| `vendas` | variável explicativa |

## `financas.csv`

Retornos simulados de um ativo e do mercado para estimar um CAPM simples,
gerados por `retorno_ativo = 0.2 + 1.2 * retorno_mercado + erro`.

| coluna | descrição |
|---|---|
| `periodo` | índice de tempo (1 a 120) |
| `retorno_mercado` | retorno do mercado no período |
| `retorno_ativo` | retorno do ativo no período |

## `did.csv`

Painel curto, de dois períodos, com 60 unidades, das quais metade é tratada,
para uma diferença-em-diferenças clássica em que o efeito causal do
tratamento (ATT) embutido é de `3.0`.

| coluna | descrição |
|---|---|
| `unidade` | identificador da unidade (1 a 60) |
| `tratamento` | 1 se a unidade recebeu o tratamento, 0 caso contrário |
| `pos` | 1 se é o período pós-intervenção, 0 se pré |
| `y` | variável de resultado |

## `brasil/`

Séries reais do Brasil, da PWT 11.0, do Ipea e do IBGE, usadas na calibração
e na avaliação dos modelos de macroeconomia, com fontes, unidades e scripts
de download descritos em `dados/brasil/README.md`.
