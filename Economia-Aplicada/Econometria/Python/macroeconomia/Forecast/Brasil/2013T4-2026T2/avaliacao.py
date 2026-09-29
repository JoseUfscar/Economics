"""
Medidas de acurácia das previsões fora da amostra.

  - raiz do erro quadrático médio (RMSE), da previsão pontual;
  - CRPS da previsão de densidade normal (Gneiting e Raftery, 2007): quanto
    menor, melhor; para uma previsão sem incerteza vira o erro absoluto;
  - cobertura do intervalo de 90%: fração dos realizados dentro dele;
  - teste de Diebold e Mariano (1995) com a correção de Harvey, Leybourne e
    Newbold (1997) para amostras pequenas;
  - teste de Clark e West (2007) quando um modelo está aninhado no outro (a
    média no AR(1), o AR(1) no VAR(1)): nesse caso o DM rejeita de menos a
    favor do modelo maior, porque o maior paga o ruído de estimar parâmetros
    que, sob a hipótese nula, são zero;
  - correção de Holm (1979) para as comparações de vários modelos com a
    mesma referência, na mesma variável e no mesmo horizonte.
"""
import numpy as np
import pandas as pd
from scipy import stats

Z_90 = stats.norm.ppf(0.95)


def crps_normal(media, dp, realizado):
    media, dp, realizado = (np.asarray(v, dtype=float) for v in (media, dp, realizado))
    z = (realizado - media) / dp
    return dp * (z * (2 * stats.norm.cdf(z) - 1) + 2 * stats.norm.pdf(z) - 1 / np.sqrt(np.pi))


def _variancia_longo_prazo(d: np.ndarray, h: int) -> float:
    """
    Variância de longo prazo com h - 1 autocovariâncias (o erro de previsão h
    passos à frente é MA(h-1)); se ela sair negativa, usa os pesos de Bartlett.
    """
    n = d.size
    desvio = d - d.mean()
    gamas = [desvio @ desvio / n] + [desvio[k:] @ desvio[:-k] / n for k in range(1, h)]
    variancia = gamas[0] + 2 * sum(gamas[1:])
    if variancia <= 0:
        variancia = gamas[0] + 2 * sum((1 - k / h) * g for k, g in enumerate(gamas[1:], start=1))
    return float(variancia)


def diebold_mariano(erro_1, erro_2, h: int) -> tuple[float, float]:
    """
    Estatística e p-valor bilateral de H0: mesma perda quadrática esperada.
    Negativa quando a previsão 1 erra menos.
    """
    d = np.asarray(erro_1, float) ** 2 - np.asarray(erro_2, float) ** 2
    n = d.size
    variancia = _variancia_longo_prazo(d, h)
    if variancia <= 0:
        return np.nan, np.nan
    dm = d.mean() / np.sqrt(variancia / n)
    dm *= np.sqrt((n + 1 - 2 * h + h * (h - 1) / n) / n)
    return float(dm), float(2 * stats.t.sf(abs(dm), df=n - 1))


def clark_west(erro_pequeno, erro_grande, previsto_pequeno, previsto_grande, h: int) -> tuple[float, float]:
    """
    Clark e West (2007) para modelos aninhados. H0: o modelo grande não erra
    menos que o pequeno; H1: erra menos. Usa f = e_p^2 - [e_g^2 - (p_p - p_g)^2],
    em que o último termo desconta o ruído de estimação do modelo grande, e
    devolve a estatística t de f (positiva a favor do grande) e o p-valor
    unilateral pela normal.
    """
    e_p, e_g = np.asarray(erro_pequeno, float), np.asarray(erro_grande, float)
    ajuste = (np.asarray(previsto_pequeno, float) - np.asarray(previsto_grande, float)) ** 2
    f = e_p**2 - (e_g**2 - ajuste)
    variancia = _variancia_longo_prazo(f, h)
    if variancia <= 0:
        return np.nan, np.nan
    estatistica = f.mean() / np.sqrt(variancia / f.size)
    return float(estatistica), float(stats.norm.sf(estatistica))


def holm(p_valores) -> np.ndarray:
    """P-valores ajustados de Holm (1979); NaN fica fora da família e continua NaN."""
    p = np.asarray(p_valores, dtype=float)
    ajustado = np.full(p.shape, np.nan)
    validos = np.flatnonzero(~np.isnan(p))
    if validos.size == 0:
        return ajustado
    ordem = validos[np.argsort(p[validos])]
    m = ordem.size
    passos = np.minimum(1.0, (m - np.arange(m)) * p[ordem])
    ajustado[ordem] = np.maximum.accumulate(passos)
    return ajustado


# Pares aninhados: (modelo, referência) -> qual dos dois é o pequeno.
ANINHADOS = {("Média", "AR(1)"): "Média", ("VAR(1)", "AR(1)"): "AR(1)",
             ("AR(1)", "Média"): "Média"}


def resumo(previsoes: pd.DataFrame, referencia: str = "AR(1)") -> pd.DataFrame:
    """
    Por modelo, variável e horizonte: RMSE, RMSE relativo à referência, CRPS
    e os testes contra a referência, nas mesmas origens: `p_valor` é o de
    Diebold-Mariano (bilateral); `p_valor_cw`, o de Clark-West, só nos pares
    aninhados (unilateral, a favor do modelo grande); `p_teste` é o
    Clark-West quando existe e o Diebold-Mariano nos outros casos; e
    `p_holm` corrige `p_teste` para as comparações de todos os modelos com a
    referência na mesma variável e no mesmo horizonte.
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
        p_cw = np.nan
        if (modelo, referencia) in ANINHADOS:
            if ANINHADOS[(modelo, referencia)] == modelo:
                _, p_cw = clark_west(grupo.erro, ref.erro, grupo.previsto, ref.previsto, h)
            else:
                _, p_cw = clark_west(ref.erro, grupo.erro, ref.previsto, grupo.previsto, h)
        linhas.append({"modelo": modelo, "variavel": variavel, "h": h, "n": len(grupo),
                       "rmse": rmse, "rmse_relativo": rmse / rmse_ref,
                       "crps": grupo.crps.mean(), "crps_relativo": grupo.crps.mean() / ref.crps.mean(),
                       "cobertura_90": np.mean(np.abs(grupo.erro) <= Z_90 * grupo.dp),
                       "dm": estatistica, "p_valor": p_valor, "p_valor_cw": p_cw,
                       "p_teste": p_valor if np.isnan(p_cw) else p_cw})
    tabela = pd.DataFrame(linhas)
    tabela["p_holm"] = np.nan
    for _, indice in tabela.groupby(["variavel", "h"]).groups.items():
        tabela.loc[indice, "p_holm"] = holm(tabela.loc[indice, "p_teste"].to_numpy())
    return tabela
