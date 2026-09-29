"""
A economia sem leiloeiro (descentralizada.py) contra o equilíbrio walrasiano
com os mesmos fundamentos.

  - `longo_prazo`: 300 anos sem choques agregados, para três regras de
    expectativas. O que emerge (desemprego, margem, salário real, capital,
    tempo de procura, flutuações) é comparado com a referência walrasiana e
    com a PNAD;
  - `sensibilidade`: os mesmos números com parâmetros de comportamento
    abaixo e acima dos da literatura.

A Lei 15.270/2025 nesta economia está em
Politicas/Lei-15270/abm2_sem_leiloeiro/lei_sem_leiloeiro.py.

Rode a partir da pasta Econometria/ (cerca de 3 minutos com 4 núcleos; dá
para rodar só uma parte, com `longo` ou `sensibilidade`):

    python Python/macroeconomia/Forecast/Brasil/2013T4-2026T2/abm2_sem_leiloeiro/experimentos_mercados.py
"""
from __future__ import annotations

import sys
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))   # macroeconomia/
import caminhos  # noqa: E402,F401

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import descentralizada as DC  # noqa: E402
import expectativas as X  # noqa: E402
import familias as F  # noqa: E402
from calibracao import aumento_tau_k_lei, calcular_alvos, calibrar as calibrar_representativo  # noqa: E402
from calibracao import carregar_dados  # noqa: E402
from calibracao_renda import carregar_pnad, renda_brasil  # noqa: E402
from experimentos import AZUL, TINTA_2, _estilo, _virgula  # noqa: E402

PASTA = Path(__file__).resolve().parent
N = 20_000
ANOS = 300
REGRAS = {"aprendizado": X.Aprendizado, "heurísticas": X.Heuristicas,
          "atenção limitada": X.AtencaoLimitada}
PROCURA_PNAD = ["procura_menos_de_1_mes", "procura_1_mes_a_1_ano", "procura_1_a_2_anos",
                "procura_2_anos_ou_mais"]


def economia_base(comp: DC.Comportamento = DC.Comportamento()) -> tuple[DC.Economia, float]:
    """A calibração de equilibrio_geral (2000-2023), com os desempregados fora da produção."""
    dados = carregar_dados()
    alvos = calcular_alvos(dados)
    eco, pol = calibrar_representativo(alvos)
    renda = F.Renda.de_continua(renda_brasil())
    par = F.Parametros(eco.alpha, eco.delta, 0.0, eco.theta, eco.n, eco.g, pol.tau_k)
    cal = DC.referencia(par, renda, alvos.capital_produto, alvos.gasto_pib)
    return DC.Economia(cal, comp, DC.Fluxos.da_renda(renda, comp.rodadas_busca)), aumento_tau_k_lei(alvos, dados)


# --- longo prazo ------------------------------------------------------------------

def _simular(args):
    eco, regra, trimestres, semente = args
    rng = np.random.default_rng(semente)
    estado = DC.estado_inicial(eco, REGRAS[regra](), N, rng)
    return DC.simular(eco, estado, rng, trimestres)[1]


def ciclos(h: pd.DataFrame, descarte: int = 400) -> dict:
    """
    Flutuações que emergem sem choques agregados, em dados anuais: desvio do
    crescimento do produto, persistência, lei de Okun (variação do desemprego
    contra crescimento) e curva de Beveridge (vagas contra desemprego).
    """
    anual = h.iloc[descarte:].groupby(np.arange(len(h) - descarte) // 4).mean()
    crescimento = 100 * np.diff(np.log(anual.y))
    variacao_u = 100 * np.diff(anual.desemprego)
    okun = np.polyfit(crescimento, variacao_u, 1)[0]
    return {"desvio do crescimento anual (p.p.)": float(np.std(crescimento)),
            "autocorrelação do crescimento": float(np.corrcoef(crescimento[1:], crescimento[:-1])[0, 1]),
            "desvio do desemprego (p.p.)": float(100 * anual.desemprego.std()),
            "coeficiente de Okun": float(okun),
            "correlação vagas x desemprego": float(np.corrcoef(anual.vagas, anual.desemprego)[0, 1])}


def resumo_longo_prazo(eco: DC.Economia, historias: dict, descarte: int = 400) -> pd.DataFrame:
    est = eco.cal.est
    alpha = eco.cal.par.alpha
    pnad = carregar_pnad()[0].loc[201201:202504, PROCURA_PNAD].mean() / 100
    pnad = pnad / pnad.sum()
    linhas = [{"economia": "referência walrasiana (PNAD)", "produto": 1.0, "capital": 1.0,
               "salário real": 1.0, "juro líquido (%)": 100 * est.r,
               "desemprego (%)": 100 * eco.cal.renda.pi[DC.desempregados(eco.cal.renda)].sum(),
               "margem (%)": 0.0, "participação do trabalho (%)": 100 * (1 - alpha),
               "famílias racionadas (%)": 0.0, "ficaram sem comprar tudo (%)": 0.0,
               "procura até 1 ano (%)": 100 * (pnad.iloc[0] + pnad.iloc[1]),
               "procura 1 a 2 anos (%)": 100 * pnad.iloc[2],
               "procura 2 anos ou mais (%)": 100 * pnad.iloc[3]}]
    for regra, h in historias.items():
        f = h.iloc[descarte:].mean()
        linhas.append({"economia": f"sem leiloeiro, {regra}", "produto": f.y / est.y, "capital": f.K / est.K,
                       "salário real": f.w / est.w, "juro líquido (%)": 100 * f.r,
                       "desemprego (%)": 100 * f.desemprego, "margem (%)": 100 * f.margem_alvo,
                       "participação do trabalho (%)": 100 * f.participacao_trabalho,
                       "famílias racionadas (%)": 100 * f.racionadas,
                       "ficaram sem comprar tudo (%)": 100 * f.sem_comprar_tudo,
                       "procura até 1 ano (%)": 100 * f.procura_ate_1_ano,
                       "procura 1 a 2 anos (%)": 100 * f.procura_1_a_2_anos,
                       "procura 2 anos ou mais (%)": 100 * f.procura_2_anos_ou_mais,
                       **ciclos(h, descarte)})
    return pd.DataFrame(linhas)


# --- sensibilidade ------------------------------------------------------------------

SENSIBILIDADE = {
    "base": {},
    "margem máxima 10%": {"margem_maxima": 0.10},
    "margem máxima 25%": {"margem_maxima": 0.25},
    "revisão de preço 0,5": {"revisao_preco": 0.5},
    "passo do salário 1,5%": {"passo_salario": 0.015},
    "passo do salário 6%": {"passo_salario": 0.06},
    "procura de fornecedor 0,1": {"procura_fornecedor": 0.1},
    "procura de fornecedor 0,5": {"procura_fornecedor": 0.5},
    "100 firmas": {"firmas": 100},
    "400 firmas": {"firmas": 400},
    "depreciação do estoque 2%": {"depreciacao_estoque": 0.02},
    "depreciação do estoque 10%": {"depreciacao_estoque": 0.10},
}


def _sensibilidade(args):
    nome, mudancas, anos, semente = args
    eco, _ = economia_base(replace(DC.Comportamento(), **mudancas))
    rng = np.random.default_rng(semente)
    estado = DC.estado_inicial(eco, X.Aprendizado(), N, rng)
    _, h = DC.simular(eco, estado, rng, 4 * anos)
    f = h.iloc[-4 * (anos - 50):].mean()
    est = eco.cal.est
    return {"variante": nome, "semente": semente, "produto": f.y / est.y, "capital": f.K / est.K,
            "salário real": f.w / est.w, "desemprego (%)": 100 * f.desemprego,
            "margem (%)": 100 * f.margem_alvo, "juro líquido (%)": 100 * f.r,
            "famílias racionadas (%)": 100 * f.racionadas}


def sensibilidade(anos: int = 150, sementes=(0, 1)) -> pd.DataFrame:
    casos = [(nome, mudancas, anos, s) for nome, mudancas in SENSIBILIDADE.items() for s in sementes]
    with ProcessPoolExecutor() as executor:
        linhas = list(executor.map(_sensibilidade, casos))
    return pd.DataFrame(linhas).groupby("variante", sort=False).mean(numeric_only=True).drop(
        columns="semente").reset_index()


# --- figuras -----------------------------------------------------------------------

def figura_longo_prazo(eco: DC.Economia, h: pd.DataFrame, destino: Path) -> None:
    _estilo()
    anual = h.groupby(np.arange(len(h)) // 4).mean()
    anos = np.arange(1, len(anual) + 1)
    est = eco.cal.est
    fig, eixos = plt.subplots(3, 1, figsize=(8.5, 7.4), sharex=True)
    series = [
        (eixos[0], 100 * (anual.y / est.y - 1), "produto, % em relação à referência", 0.0),
        (eixos[1], 100 * anual.desemprego, "desemprego, %",
         100 * eco.cal.renda.pi[DC.desempregados(eco.cal.renda)].sum()),
        (eixos[2], 100 * anual.margem_alvo, "margem média sobre o custo, %", 0.0),
    ]
    for ax, serie, rotulo, referencia in series:
        ax.plot(anos, serie, color=AZUL, linewidth=1.1)
        ax.axhline(referencia, color=TINTA_2, linestyle="--", linewidth=0.9)
        ax.set_ylabel(rotulo)
        _virgula(ax)
    eixos[0].set_title("Sem leiloeiro, com aprendizado: o que emerge sem choques agregados")
    eixos[2].set_xlabel("anos")
    fig.tight_layout()
    fig.savefig(destino)
    plt.close(fig)


def main(partes=("longo", "sensibilidade")) -> None:
    eco, _ = economia_base()
    est = eco.cal.est
    print(f"Referência walrasiana: K = {est.K:.3f}, r = {100 * est.r:.2f}%, w = {est.w:.3f}, "
          f"tau_w = {eco.cal.par.tau_w:.3f}, rho = {eco.cal.par.rho:.4f}")
    pasta_res, pasta_fig = PASTA / "resultados", PASTA / "figuras"
    pasta_res.mkdir(exist_ok=True)
    pasta_fig.mkdir(exist_ok=True)
    formato = {"display.width": 250, "display.max_columns": 30, "display.float_format": "{:.3f}".format}
    if "longo" in partes:
        with ProcessPoolExecutor() as executor:
            historias = dict(zip(REGRAS, executor.map(_simular, [(eco, r, 4 * ANOS, 1) for r in REGRAS])))
        resumo = resumo_longo_prazo(eco, historias)
        resumo.to_csv(pasta_res / "mercados_longo_prazo.csv", index=False, float_format="%.6g")
        anuais = {r: h.groupby(np.arange(len(h)) // 4).mean() for r, h in historias.items()}
        pd.concat(anuais, names=["regra", "ano"]).to_csv(pasta_res / "mercados_historia.csv",
                                                          float_format="%.5g")
        figura_longo_prazo(eco, historias["aprendizado"], pasta_fig / "mercados_longo_prazo.png")
        with pd.option_context(*[v for par in formato.items() for v in par]):
            print(resumo.T.to_string())
    if "sensibilidade" in partes:
        sens = sensibilidade()
        sens.to_csv(pasta_res / "mercados_sensibilidade.csv", index=False, float_format="%.6g")
        with pd.option_context(*[v for par in formato.items() for v in par]):
            print(sens.to_string(index=False))
    print(f"\nResultados em {pasta_res} e figuras em {pasta_fig}")


if __name__ == "__main__":
    main(sys.argv[1:] or ("longo", "sensibilidade"))
