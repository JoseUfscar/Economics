"""
Modelo AR(1) por OLS: pib_t = c + phi * pib_{t-1} + erro_t

Rode com: python3 Python/macroeconometria/ar1.py
"""
import pandas as pd
import statsmodels.api as sm

df = pd.read_csv("dados/macro_series.csv")
y = df["pib_crescimento"].iloc[1:].reset_index(drop=True)
y_lag = df["pib_crescimento"].iloc[:-1].reset_index(drop=True)

X = sm.add_constant(y_lag.rename("pib_crescimento_lag"))
modelo = sm.OLS(y, X).fit()

print(modelo.summary())
print(f"\nc estimado   : {modelo.params['const']:.4f}")
print(f"phi estimado : {modelo.params['pib_crescimento_lag']:.4f}")
