# Econometria

Esta pasta reúne modelagem e econometria aplicada, organizada primeiro por
linguagem, com cada linguagem tratada como um projeto independente, e depois
por área da economia. A ideia é ter uma base comum para desenvolver modelos em
R, Python, Julia e C e comparar implementações da mesma técnica em
linguagens diferentes sempre que isso fizer sentido.

## Estrutura

```
Econometria/
├── R/            # projeto R (apenas base R, sem dependências externas)
├── Python/       # projeto Python (numpy, pandas, statsmodels, scipy)
├── Julia/        # projeto Julia (apenas biblioteca padrão)
├── C/            # implementações em C puro (OLS via equações normais)
└── dados/        # datasets sintéticos compartilhados + dados reais do Brasil (dados/brasil/)
```

Cada pasta de linguagem tem as mesmas quatro áreas como subpastas.

| Área | Conteúdo inicial |
|---|---|
| `macroeconometria/` | Séries temporais, com um AR(1) estimado por OLS |
| `microeconometria/` | Dados em painel, com efeitos fixos por LSDV |
| `financas/` | Econometria financeira, com o CAPM estimado por regressão de retornos |
| `trabalho_desenvolvimento/` | Avaliação de política, com diferença-em-diferenças (DID) |

Essas quatro áreas foram o ponto de partida, e uma área nova, como comércio
internacional ou organização industrial, exige apenas criar a mesma subpasta
em cada linguagem que for usá-la. A primeira área acrescentada foi
`macroeconomia/`, em Python e Julia, com modelos de equilíbrio geral, modelos
baseados em agentes e uma avaliação de previsões fora da amostra, e em Python
ela se divide em [`Politicas/Lei-15270/`](Python/macroeconomia/Politicas/Lei-15270/README.md)
e [`Forecast/Brasil/2013T4-2026T2/`](Python/macroeconomia/Forecast/Brasil/2013T4-2026T2/README.md),
como descrito em [`Python/macroeconomia/`](Python/macroeconomia/README.md).

## Datasets compartilhados (`dados/`)

Os quatro exemplos usam dados sintéticos gerados com semente fixa, para que o
mesmo modelo rodado em R, Python, Julia e C produza os mesmos coeficientes, o
que ajuda a conferir se uma implementação nova está correta comparando-a com
as das outras linguagens. Os detalhes de cada dataset e a forma de gerá-los
de novo estão em `dados/README.md`. Como os scripts sempre leem os arquivos
pelo caminho relativo `dados/...`, todo exemplo deve ser executado a partir
da pasta `Econometria/`.

## Como rodar cada linguagem

As instruções de instalação e execução de cada linguagem estão no `README.md`
da pasta correspondente (`R/`, `Python/`, `Julia/` e `C/`).

## Convenção para novos modelos

Cada modelo ocupa um script ou programa na pasta da área correspondente, com
um nome que descreva o modelo (por exemplo `var.py`, `garch.jl` ou `logit.R`)
e um cabeçalho curto que explique a equação estimada e como rodá-la. Sempre
que possível, os dados vêm de `dados/`, ou de uma subpasta própria da área
quando o dataset não fizer sentido nas outras linguagens.

## Equilíbrio geral em tempo contínuo

O projeto [Tributação do capital no Brasil em equilíbrio geral](Python/macroeconomia/Politicas/Lei-15270/equilibrio_geral/README.md)
usa modelos em tempo contínuo calibrados com dados da PWT 11.0, do Ipea e do
IBGE para medir os efeitos de um aumento da tributação da renda do capital do
tamanho da Lei 15.270/2025. A primeira parte usa o modelo de
Ramsey–Cass–Koopmans com governo, com choques inesperados e anunciados, uma
estimação estrutural avaliada por Monte Carlo e uma versão em Julia que
confere os resultados com outro algoritmo. A segunda parte introduz famílias
heterogêneas no modelo de Aiyagari, resolvido pelas equações de
Hamilton–Jacobi–Bellman e Kolmogorov, com risco de desemprego e desigualdade
calibrados com a PNAD Contínua, para mostrar quem ganha e quem perde. A
derivação completa está na [nota técnica](Python/macroeconomia/Politicas/Lei-15270/equilibrio_geral/nota_tecnica.pdf).

## Modelos baseados em agentes

O [ABM com microfundamentação neoclássica](Python/macroeconomia/Forecast/Brasil/2013T4-2026T2/abm1_com_leiloeiro/README.md)
simula 20 mil famílias com o mesmo problema de consumo e poupança do modelo de
Aiyagari, em trimestres, e expectativas que vão da previsão perfeita à
racionalidade limitada, passando pelo aprendizado adaptativo, pelas
heurísticas com troca à maneira de Brock e Hommes, pela informação rígida e
pela atenção limitada. Com previsão perfeita, o ABM reproduz os efeitos da Lei
15.270/2025 obtidos no modelo contínuo, e com as outras regras quem ganha e
quem perde continua o mesmo, embora o tamanho dos efeitos e o caminho do
capital mudem. Partindo de longe do equilíbrio, o capital e a desigualdade
voltam sozinhos quando a racionalidade é limitada, mas com crenças fixas a
economia se acomoda em outro lugar. Numa [versão sem leiloeiro](Python/macroeconomia/Forecast/Brasil/2013T4-2026T2/abm2_sem_leiloeiro/README.md),
com firmas que fixam preços e salários e busca por emprego, o desemprego
emerge perto do observado na PNAD e as firmas passam a ter poder de mercado.
Os experimentos da lei nos dois ABMs estão em
[`Politicas/Lei-15270/`](Python/macroeconomia/Politicas/Lei-15270/README.md).

## Previsão fora da amostra

A comparação entre [equilíbrio geral, ABMs e modelos estatísticos](Python/macroeconomia/Forecast/Brasil/2013T4-2026T2/README.md)
usa as Contas Nacionais Trimestrais de 1996 a 2026 e o desemprego da PNAD e
avalia previsões de 1 a 8 trimestres em 50 origens desde 2013, com cada
modelo usando apenas o que se sabia em cada data, além de registrar previsões
para 2026-2028. Os modelos formam dois pares com os mesmos fundamentos, o
equilíbrio geral contra o ABM com leiloeiro e o equilíbrio geral com margem e
busca contra o ABM sem leiloeiro.
