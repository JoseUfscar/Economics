"""
Diferenca-em-diferencas: y = b0 + b1*tratamento + b2*pos + b3*(tratamento*pos) + erro
b3 e o efeito causal estimado do tratamento (ATT).

Rode com: python3 Python/trabalho_desenvolvimento/diff_in_diff.py
"""
import pandas as pd
import statsmodels.api as sm

df = pd.read_csv("dados/did.csv")
df["tratamento_pos"] = df["tratamento"] * df["pos"]

X = sm.add_constant(df[["tratamento", "pos", "tratamento_pos"]])
y = df["y"]

modelo = sm.OLS(y, X).fit()

print(modelo.summary())
print(f"\nEfeito do tratamento (ATT, DID): {modelo.params['tratamento_pos']:.4f}")
