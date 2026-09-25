# Dados sintéticos compartilhados

Todos gerados por `gerar_dados.py` com seed fixa (42), para reprodutibilidade
e para comparar as mesmas estimativas entre R, Python, Julia e C. Para
regerar:

```
python3 dados/gerar_dados.py
```

## `macro_series.csv`

Série temporal simulada como um processo AR(1) estacionário — pense nela
como uma taxa de crescimento trimestral do PIB (%).

| coluna | descrição |
|---|---|
| `trimestre` | índice de tempo (1 a 80) |
| `pib_crescimento` | valor simulado da série |

DGP: `pib_t = 0.5 + 0.55 * pib_{t-1} + erro_t`, `erro ~ N(0, 1)`.

## `painel.csv`

Painel de 12 firmas ao longo de 10 anos, com heterogeneidade não observada
por firma (efeito fixo).

| coluna | descrição |
|---|---|
| `firma` | identificador da firma (1 a 12) |
| `ano` | ano dentro do painel (1 a 10) |
| `investimento` | variável dependente |
| `vendas` | variável explicativa |

DGP: `investimento_it = 2.0 + efeito_firma_i + 0.4 * vendas_it + erro_it`.

## `financas.csv`

Retornos simulados de um ativo e do mercado, para estimar um CAPM simples.

| coluna | descrição |
|---|---|
| `periodo` | índice de tempo (1 a 120) |
| `retorno_mercado` | retorno do mercado no período |
| `retorno_ativo` | retorno do ativo no período |

DGP: `retorno_ativo = 0.2 + 1.2 * retorno_mercado + erro`.

## `did.csv`

Painel curto (2 períodos) de 60 unidades, metade tratada, para uma
diferença-em-diferenças clássica.

| coluna | descrição |
|---|---|
| `unidade` | identificador da unidade (1 a 60) |
| `tratamento` | 1 se a unidade recebeu o tratamento, 0 caso contrário |
| `pos` | 1 se é o período pós-intervenção, 0 se pré |
| `y` | variável de resultado |

DGP: efeito causal do tratamento (ATT) embutido = `3.0`.

## `brasil/`

Séries **reais** do Brasil (PWT 11.0, Ipea e IBGE) usadas na calibração do
modelo de equilíbrio geral. Ver `dados/brasil/README.md` para fontes,
unidades e o script de download.
