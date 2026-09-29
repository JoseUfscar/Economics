"""
A Lei 15.270/2025 no ABM sem leiloeiro (Forecast/Brasil/2013T4-2026T2/
abm2_sem_leiloeiro): o mesmo aumento de tau_k de equilibrio_geral, com as duas
formas de devolver a receita de lei_com_leiloeiro.py, em várias sementes.

Em cada semente, a economia parte da referência walrasiana e roda 100 anos
sem reforma, o mesmo aquecimento da previsão, para chegar ao regime do
próprio ABM (margens, estoques, capital e crenças). Daí se separa em três
cópias com os mesmos números aleatórios: sem reforma, com devolução uniforme
e com devolução por isenção. Como na economia com leiloeiro e no Aiyagari,
o que a reforma muda no orçamento do governo volta às famílias pelos pesos
da devolução: a transferência da economia sem reforma, trimestre a
trimestre, continua igual para todos, e a diferença segue os pesos.

A economia flutua sozinha, e uma semente só mistura o efeito da lei com o
ciclo; a média das sementes separa os dois.

Rode a partir da pasta Econometria/ (cerca de 10 minutos com 4 núcleos):

    python Python/macroeconomia/Politicas/Lei-15270/abm2_sem_leiloeiro/lei_sem_leiloeiro.py
"""
from __future__ import annotations

import copy
import sys
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))   # macroeconomia/
import caminhos  # noqa: E402,F401

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import descentralizada as DC  # noqa: E402
import expectativas as X  # noqa: E402
from experimentos import AZUL, LARANJA, TINTA, _estilo, _virgula  # noqa: E402
from experimentos_mercados import N, economia_base  # noqa: E402
from lei_com_leiloeiro import DEVOLUCOES, resumo_bem_estar  # noqa: E402

PASTA = Path(__file__).resolve().parent
ANOS_LEI = 150
AQUECIMENTO = 400        # trimestres sem reforma antes dela, como na previsão
SEMENTES_LEI = range(48)


def _economia_da_lei(args):
    """
    Uma semente: aquecimento sem reforma e, a partir do mesmo estado e dos
    mesmos números aleatórios, a economia sem reforma e com cada devolução.
    """
    eco0, reformas, semente, trimestres, aquecimento, n_familias = args
    par = eco0.cal.par
    D = par.periodo
    desconto = np.exp(-(par.rho - par.n - (1 - par.theta) * par.g) * D)
    rng = np.random.default_rng(semente)
    inicio = DC.estado_inicial(eco0, X.Aprendizado(), n_familias, rng)
    inicio, _ = DC.simular(eco0, inicio, rng, aquecimento)
    estado_rng = rng.bit_generator.state
    saida, base = {}, None
    for nome, eco in (("sem reforma", eco0), *reformas.items()):
        rng.bit_generator.state = estado_rng
        estado = copy.deepcopy(inicio)
        tipo = estado.tipo
        bem_estar, peso, linhas = np.zeros(n_familias), 1.0, []
        for t in range(trimestres):
            estado, registro = DC.trimestre(eco, estado, rng, par.g * D, par.gasto,
                                            transferencia_base=None if base is None else base[t])
            bem_estar += peso * D * estado.c ** (1 - par.theta) / (1 - par.theta)
            peso *= desconto
            linhas.append(registro)
        saida[nome] = (pd.DataFrame(linhas), bem_estar, tipo)
        if base is None:
            base = saida[nome][0].transferencia.to_numpy()
    return semente, saida


def lei(eco0: DC.Economia, aumento: float, sementes=SEMENTES_LEI, anos: int = ANOS_LEI,
        aquecimento: int = AQUECIMENTO, n_familias: int = N):
    reformas = {nome: replace(eco0, cal=DC.reformada(eco0.cal, aumento, pesos))
                for nome, pesos in DEVOLUCOES.items()}
    casos = [(eco0, reformas, s, 4 * anos, aquecimento, n_familias) for s in sementes]
    with ProcessPoolExecutor() as executor:
        resultados = dict(executor.map(_economia_da_lei, casos))
    tabelas, caminhos = [], {}
    theta = eco0.cal.par.theta
    for devolucao in DEVOLUCOES:
        desvios = []
        for semente, saida in resultados.items():
            base, b0, tipo = saida["sem reforma"]
            novo, b1, _ = saida[devolucao]
            desvio = pd.DataFrame({
                "K": 100 * (novo.K / base.K - 1), "y": 100 * (novo.y / base.y - 1),
                "desemprego": 100 * (novo.desemprego - base.desemprego),
                "r": 100 * (novo.r - base.r)})
            desvios.append(desvio)
            bem = resumo_bem_estar(b1, b0, tipo, theta).assign(semente=semente)
            tabelas.append(bem.assign(devolucao=devolucao,
                                      capital_longo_prazo=desvio.K.iloc[-80:].mean(),
                                      desemprego_longo_prazo=desvio.desemprego.iloc[-80:].mean(),
                                      capital_equilibrio=100 * (reformas[devolucao].cal.est.K
                                                                / eco0.cal.est.K - 1)))
        caminhos[devolucao] = pd.concat(desvios, keys=list(resultados), names=["semente", "trimestre"])
    return pd.concat(tabelas, ignore_index=True), caminhos


def resumo_lei(tabela: pd.DataFrame) -> pd.DataFrame:
    """Média e erro-padrão entre as sementes, por devolução e grupo."""
    agrupado = tabela.groupby(["devolucao", "grupo"], sort=False)
    media = agrupado[["ganho médio (%)", "capital_longo_prazo", "desemprego_longo_prazo",
                      "capital_equilibrio"]].mean()
    raiz = np.sqrt(agrupado.size())
    return media.assign(**{"erro-padrão do ganho": agrupado["ganho médio (%)"].std() / raiz,
                           "erro-padrão do capital": agrupado["capital_longo_prazo"].std() / raiz,
                           "erro-padrão do desemprego": agrupado["desemprego_longo_prazo"].std() / raiz}
                        ).reset_index()


# --- figura -------------------------------------------------------------------------

def figura_lei(caminhos: dict, tabela: pd.DataFrame, destino: Path) -> None:
    _estilo()
    fig, eixos = plt.subplots(1, 2, figsize=(9.5, 4.2))
    cores = {"uniforme": AZUL, "isenção": LARANJA}
    for devolucao, caminho in caminhos.items():
        media = caminho.groupby(level="trimestre").mean()
        anual = media.groupby(np.arange(len(media)) // 4).mean()
        anos = np.arange(1, len(anual) + 1)
        eixos[0].plot(anos, anual.K, color=cores[devolucao], label=f"devolução {devolucao}")
        eixos[1].plot(anos, anual.desemprego, color=cores[devolucao], label=f"devolução {devolucao}")
        equilibrio = tabela[tabela.devolucao == devolucao].capital_equilibrio.iloc[0]
        eixos[0].axhline(equilibrio, color=cores[devolucao], linestyle="--", linewidth=0.9)
    eixos[0].set(title="Capital", ylabel="% em relação a sem reforma", xlabel="anos")
    eixos[1].set(title="Desemprego", ylabel="p.p. em relação a sem reforma", xlabel="anos")
    eixos[1].axhline(0, color=TINTA, linewidth=0.8)
    for ax in eixos:
        _virgula(ax)
    eixos[0].legend(loc="lower left")
    fig.tight_layout()
    fig.savefig(destino)
    plt.close(fig)


def main() -> None:
    eco, aumento = economia_base()
    pasta_res, pasta_fig = PASTA / "resultados", PASTA / "figuras"
    pasta_res.mkdir(exist_ok=True)
    pasta_fig.mkdir(exist_ok=True)
    tabela, caminhos_lei = lei(eco, aumento)
    tabela.to_csv(pasta_res / "mercados_lei_15270.csv", index=False, float_format="%.6g")
    lei_resumo = resumo_lei(tabela)
    lei_resumo.to_csv(pasta_res / "mercados_lei_15270_resumo.csv", index=False, float_format="%.6g")
    figura_lei(caminhos_lei, tabela, pasta_fig / "mercados_lei_capital.png")
    with pd.option_context("display.width", 250, "display.max_columns", 30,
                           "display.float_format", "{:.3f}".format):
        print(lei_resumo.to_string(index=False))
    print(f"\nResultados em {pasta_res} e figuras em {pasta_fig}")


if __name__ == "__main__":
    main()
