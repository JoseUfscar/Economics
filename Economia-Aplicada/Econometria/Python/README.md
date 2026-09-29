# Python

## Setup

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r Python/requirements.txt
```

`requirements.txt` tem as versões mínimas. Para reproduzir os resultados dos
modelos de macroeconomia até a última casa, use as versões exatas com que eles
foram gerados, em `requirements-versoes.txt` (Python 3.11).

## Rodando os exemplos

A partir da **pasta `Econometria/`** (os scripts leem `dados/...`):

```
python3 Python/macroeconometria/ar1.py
python3 Python/microeconometria/painel_fe.py
python3 Python/financas/capm.py
python3 Python/trabalho_desenvolvimento/diff_in_diff.py
```

Os modelos de [`macroeconomia/`](macroeconomia/README.md) têm instruções
próprias: a [Lei 15.270/2025](macroeconomia/Politicas/Lei-15270/README.md)
(`macroeconomia/Politicas/Lei-15270/`, com os modelos de equilíbrio geral em
tempo contínuo) e a [previsão fora da
amostra](macroeconomia/Forecast/Brasil/2013T4-2026T2/README.md)
(`macroeconomia/Forecast/Brasil/2013T4-2026T2/`, com os DSGEs e os modelos
baseados em agentes). Rode os comandos deles também a partir da pasta
`Econometria/`.

## Bibliotecas

`numpy`, `pandas`, `scipy` e `statsmodels` cobrem OLS, séries temporais
(ARIMA/SARIMAX), e a maioria dos modelos de microeconometria básica.
`matplotlib` gera as figuras do modelo de equilíbrio geral. Para
painéis mais robustos (efeitos aleatórios, IV em painel) considere adicionar
[`linearmodels`](https://bashtage.github.io/linearmodels/) ao
`requirements.txt`.
