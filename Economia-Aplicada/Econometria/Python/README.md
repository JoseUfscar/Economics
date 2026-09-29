# Python

## Setup

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r Python/requirements.txt
```

## Rodando os exemplos

Os comandos devem ser executados a partir da pasta `Econometria/`, porque os
scripts leem os arquivos em `dados/...`.

```
python3 Python/macroeconometria/ar1.py
python3 Python/microeconometria/painel_fe.py
python3 Python/financas/capm.py
python3 Python/trabalho_desenvolvimento/diff_in_diff.py
```

Os modelos de [`macroeconomia/`](macroeconomia/README.md) têm instruções
próprias, divididas entre a [Lei 15.270/2025](macroeconomia/Politicas/Lei-15270/README.md),
em `macroeconomia/Politicas/Lei-15270/`, com os modelos de equilíbrio geral em
tempo contínuo, e a [previsão fora da amostra](macroeconomia/Forecast/Brasil/2013T4-2026T2/README.md),
em `macroeconomia/Forecast/Brasil/2013T4-2026T2/`, com os DSGEs e os modelos
baseados em agentes, e os comandos deles também rodam a partir da pasta
`Econometria/`.

## Bibliotecas

As bibliotecas `numpy`, `pandas`, `scipy` e `statsmodels` cobrem OLS, séries
temporais (ARIMA e SARIMAX) e a maior parte da microeconometria básica,
enquanto `matplotlib` gera as figuras dos modelos de macroeconomia. Para
painéis mais exigentes, com efeitos aleatórios ou variáveis instrumentais,
vale acrescentar [`linearmodels`](https://bashtage.github.io/linearmodels/)
ao `requirements.txt`.
