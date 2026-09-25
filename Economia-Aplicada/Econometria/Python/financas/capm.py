"""
CAPM por OLS: retorno_ativo = alpha + beta * retorno_mercado + erro

Rode com: python3 Python/financas/capm.py
"""
import pandas as pd
import statsmodels.api as sm

df = pd.read_csv("dados/financas.csv")

X = sm.add_constant(df["retorno_mercado"])
y = df["retorno_ativo"]

modelo = sm.OLS(y, X).fit()

print(modelo.summary())
print(f"\nalpha estimado : {modelo.params['const']:.4f}")
print(f"beta estimado  : {modelo.params['retorno_mercado']:.4f}")
