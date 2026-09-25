"""
Gera os datasets sinteticos usados pelos exemplos de todas as linguagens
(R, Python, Julia, C) em cada area do projeto. Rode uma vez com:

    python3 dados/gerar_dados.py

Usa uma seed fixa para que os resultados sejam reprodutiveis e comparaveis
entre as implementacoes nas diferentes linguagens.
"""
import numpy as np
import pandas as pd

rng = np.random.default_rng(42)

# --- macroeconometria: serie temporal AR(1) --------------------------------
# ex: crescimento trimestral do PIB (%), processo autorregressivo estacionario
n = 80
phi, c, sigma = 0.55, 0.5, 1.0
serie = np.zeros(n)
serie[0] = c / (1 - phi)
for t in range(1, n):
    serie[t] = c + phi * serie[t - 1] + rng.normal(0, sigma)
pd.DataFrame({"trimestre": np.arange(1, n + 1), "pib_crescimento": serie}).to_csv(
    "dados/macro_series.csv", index=False
)

# --- microeconometria: painel (efeitos fixos) -------------------------------
# ex: investimento (y) explicado por vendas (x), com heterogeneidade por firma
n_firmas, n_anos = 12, 10
linhas = []
efeito_firma = rng.normal(0, 3, n_firmas)
for i in range(n_firmas):
    vendas0 = rng.uniform(50, 150)
    for t in range(n_anos):
        vendas = vendas0 + t * rng.uniform(1, 5) + rng.normal(0, 2)
        investimento = 2.0 + efeito_firma[i] + 0.4 * vendas + rng.normal(0, 3)
        linhas.append((i + 1, t + 1, investimento, vendas))
pd.DataFrame(linhas, columns=["firma", "ano", "investimento", "vendas"]).to_csv(
    "dados/painel.csv", index=False
)

# --- financas: CAPM (retorno do ativo vs retorno de mercado) ---------------
n_obs = 120
alpha, beta = 0.2, 1.2
retorno_mercado = rng.normal(0.8, 4.0, n_obs)
retorno_ativo = alpha + beta * retorno_mercado + rng.normal(0, 2.5, n_obs)
pd.DataFrame(
    {"periodo": np.arange(1, n_obs + 1), "retorno_mercado": retorno_mercado, "retorno_ativo": retorno_ativo}
).to_csv("dados/financas.csv", index=False)

# --- trabalho/desenvolvimento: diferenca-em-diferencas ----------------------
# ex: efeito de um programa (tratamento) sobre renda, pre e pos intervencao
n_unidades = 60
efeito_tratamento = 3.0
linhas = []
for i in range(n_unidades):
    tratado = 1 if i < n_unidades // 2 else 0
    base = rng.normal(20, 3)
    for pos in (0, 1):
        y = base + 1.5 * pos + tratado * pos * efeito_tratamento + rng.normal(0, 1.5)
        linhas.append((i + 1, tratado, pos, y))
pd.DataFrame(linhas, columns=["unidade", "tratamento", "pos", "y"]).to_csv(
    "dados/did.csv", index=False
)

print("Datasets gerados em dados/: macro_series.csv, painel.csv, financas.csv, did.csv")
