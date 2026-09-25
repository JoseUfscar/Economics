"""
Painel com efeitos fixos por firma (LSDV): investimento_it = a_i + b*vendas_it + erro_it

Rode com: python3 Python/microeconometria/painel_fe.py
"""
import pandas as pd
import statsmodels.api as sm

df = pd.read_csv("dados/painel.csv")

dummies_firma = pd.get_dummies(df["firma"], prefix="firma", drop_first=True, dtype=float)
X = pd.concat([df["vendas"], dummies_firma], axis=1)
X = sm.add_constant(X)
y = df["investimento"]

modelo = sm.OLS(y, X).fit()

print(modelo.summary())
print(f"\nEfeito estimado de vendas sobre investimento: {modelo.params['vendas']:.4f}")
