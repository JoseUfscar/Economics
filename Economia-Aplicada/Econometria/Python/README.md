# Python

## Setup

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r Python/requirements.txt
```

## Rodando os exemplos

A partir da **pasta `Econometria/`** (os scripts leem `dados/...`):

```
python3 Python/macroeconometria/ar1.py
python3 Python/microeconometria/painel_fe.py
python3 Python/financas/capm.py
python3 Python/trabalho_desenvolvimento/diff_in_diff.py
```

Os [modelos de equilíbrio geral](macroeconomia/equilibrio_geral/README.md)
(`macroeconomia/equilibrio_geral/`, agente representativo e famílias
heterogêneas) têm instruções próprias para calibração, experimentos, estimação
e testes; rode os comandos deles também a partir da pasta `Econometria/`.

## Bibliotecas

`numpy`, `pandas`, `scipy` e `statsmodels` — cobrem OLS, séries temporais
(ARIMA/SARIMAX), e a maioria dos modelos de microeconometria básica.
`matplotlib` gera as figuras do modelo de equilíbrio geral. Para
painéis mais robustos (efeitos aleatórios, IV em painel) considere adicionar
[`linearmodels`](https://bashtage.github.io/linearmodels/) ao
`requirements.txt`.
