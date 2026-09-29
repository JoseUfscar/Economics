"""
Medidas de acurácia das previsões fora da amostra.

  - raiz do erro quadrático médio (RMSE), da previsão pontual;
  - CRPS da previsão de densidade normal (Gneiting e Raftery, 2007): quanto
    menor, melhor; para uma previsão sem incerteza vira o erro absoluto;
  - cobertura do intervalo de 90%: fração dos realizados dentro dele;
  - teste de Diebold e Mariano (1995) com a correção de Harvey, Leybourne e
    Newbold (1997) para amostras pequenas.
"""
import numpy as np
import pandas as pd
from scipy import stats

Z_90 = stats.norm.ppf(0.95)


def crps_normal(media, dp, realizado):
    media, dp, realizado = (np.asarray(v, dtype=float) for v in (media, dp, realizado))
    z = (realizado - media) / dp
    return dp * (z * (2 * stats.norm.cdf(z) - 1) + 2 * stats.norm.pdf(z) - 1 / np.sqrt(np.pi))


def diebold_mariano(erro_1, erro_2, h: int) -> tuple[float, float]:
    """
    Estatística e p-valor bilateral de H0: mesma perda quadrática esperada.
    Negativa quando a previsão 1 erra menos. A variância de longo prazo usa
    h - 1 autocovariâncias (o erro de previsão h passos à frente é MA(h-1));
    se ela sair negativa, usa os pesos de Bartlett.
    """
    d = np.asarray(erro_1, float) ** 2 - np.asarray(erro_2, float) ** 2
    n = d.size
    desvio = d - d.mean()
    gamas = [desvio @ desvio / n] + [desvio[k:] @ desvio[:-k] / n for k in range(1, h)]
    variancia = gamas[0] + 2 * sum(gamas[1:])
    if variancia <= 0:
        variancia = gamas[0] + 2 * sum((1 - k / h) * g for k, g in enumerate(gamas[1:], start=1))
    if variancia <= 0:
        return np.nan, np.nan
    dm = d.mean() / np.sqrt(variancia / n)
    dm *= np.sqrt((n + 1 - 2 * h + h * (h - 1) / n) / n)
    return float(dm), float(2 * stats.t.sf(abs(dm), df=n - 1))


def resumo(previsoes: pd.DataFrame, referencia: str = "AR(1)") -> pd.DataFrame:
    """
    Por modelo, variável e horizonte: RMSE, RMSE relativo à referência, CRPS
    e o p-valor de Diebold-Mariano contra a referência (mesmas origens).
    """
    p = previsoes.dropna(subset=["realizado"]).assign(
        erro=lambda x: x.realizado - x.previsto,
        crps=lambda x: crps_normal(x.previsto, x.dp, x.realizado))
    base = p[p.modelo == referencia].set_index(["variavel", "h", "origem"]).sort_index()
    linhas = []
    for (modelo, variavel, h), grupo in p.groupby(["modelo", "variavel", "h"], sort=False):
        grupo = grupo.set_index("origem").sort_index()
        ref = base.loc[(variavel, h)].reindex(grupo.index)
        rmse = np.sqrt(np.mean(grupo.erro**2))
        rmse_ref = np.sqrt(np.mean(ref.erro**2))
        estatistica, p_valor = ((np.nan, np.nan) if modelo == referencia
                                else diebold_mariano(grupo.erro, ref.erro, h))
        linhas.append({"modelo": modelo, "variavel": variavel, "h": h, "n": len(grupo),
                       "rmse": rmse, "rmse_relativo": rmse / rmse_ref,
                       "crps": grupo.crps.mean(), "crps_relativo": grupo.crps.mean() / ref.crps.mean(),
                       "cobertura_90": np.mean(np.abs(grupo.erro) <= Z_90 * grupo.dp),
                       "dm": estatistica, "p_valor": p_valor})
    return pd.DataFrame(linhas)
