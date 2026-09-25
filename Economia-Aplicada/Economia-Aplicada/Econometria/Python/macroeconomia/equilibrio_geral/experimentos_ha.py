"""
Incidência distributiva do aumento de tau_k no modelo de Aiyagari calibrado
para o Brasil.

Pergunta: quem ganha e quem perde com a tributação de altas rendas da Lei
15.270/2025 quando as famílias são diferentes? O aumento de tau_k tem o tamanho
calculado em calibracao.py e é inesperado. A receita nova volta às famílias
de duas formas:

  - uniforme: transferência igual para todas as famílias;
  - isenção: só para os empregados do grupo intermediário (P50-P90), que
    contém quem ganha de R$ 3 mil a R$ 7,35 mil por mês, a faixa beneficiada
    pela redução do imposto de renda (limites de percentil da PNAD de 2025).

O modelo representativo (modelo.py) serve de comparação: nele todos perdem.

Rode a partir da pasta Econometria/ (cerca de 3 minutos):

    python Python/macroeconomia/equilibrio_geral/experimentos_ha.py
"""
from dataclasses import dataclass, replace
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from aiyagari import (EquilibrioHA, Governo, Grade, TransicaoHA, calibrar_rho, equilibrio,
                      ganho_bem_estar, transicao)
from calibracao import aumento_tau_k_lei, calcular_alvos, calibrar, carregar_dados
from calibracao_renda import GRUPOS, carregar_pnad, renda_brasil
from experimentos import (AZUL, FUNDO, LARANJA, PASTA_FIGURAS, TINTA, TINTA_2, _br, _estilo,
                          _virgula, choque_tau_k, efeitos)
from modelo import estado_estacionario

GRADE = Grade(a_max=150.0, pontos=600, curvatura=2.0)
TIPOS = list(GRUPOS)
VARIANTES = {"uniforme": None, "isenção": (0, 0, 0, 1, 0, 0, 0, 0, 0)}
TONS_TIPOS = ("#86b6ef", "#2a78d6", "#104281")   # rampa ordinal azul: base, meio, topo
# World Inequality Database (wid.world), Brasil, 2021: os 10% mais ricos têm
# cerca de 80% da riqueza e os 50% mais pobres, riqueza líquida em torno de zero.
WID_TOPO_10, WID_BASE_50 = 0.80, 0.0


@dataclass
class EconomiaHA:
    eco_ra: object
    pol_ra: object
    choque: float
    eq0: EquilibrioHA


def economia_ha(grade: Grade = GRADE) -> EconomiaHA:
    dados = carregar_dados()
    alvos = calcular_alvos(dados)
    eco_ra, pol_ra = calibrar(alvos)
    renda = renda_brasil()
    eco, gov = calibrar_rho(eco_ra, renda, Governo(tau_k=pol_ra.tau_k),
                            alvos.capital_produto, alvos.gasto_pib, grade)
    return EconomiaHA(eco_ra, pol_ra, aumento_tau_k_lei(alvos, dados),
                      equilibrio(eco, renda, gov, grade))


@dataclass
class Reforma:
    nome: str
    eq1: EquilibrioHA
    tr: TransicaoHA
    lam: np.ndarray            # variação equivalente por (a, z), em fração


def reforma(eq0: EquilibrioHA, aumento: float, pesos, nome: str,
            t: np.ndarray | None = None) -> Reforma:
    gov1 = replace(eq0.gov, tau_k=eq0.gov.tau_k + aumento, pesos=pesos)
    eq1 = equilibrio(eq0.eco, eq0.renda, gov1, eq0.grade)
    tr = transicao(eq0, gov1, eq1, t=t)
    return Reforma(nome, eq1, tr, ganho_bem_estar(tr.V0, eq0.familias.V, eq0.eco.theta))


def resumo_bem_estar(eq0: EquilibrioHA, ref: Reforma) -> pd.DataFrame:
    """Ganho médio e fração que ganha, por tipo e no total (pesos do equilíbrio inicial)."""
    theta, m, lam = eq0.eco.theta, eq0.m, ref.lam
    J = m.shape[1] // len(TIPOS)
    linhas = []
    for k, nome in enumerate(TIPOS + ["todos"]):
        bloco = slice(None) if nome == "todos" else slice(J * k, J * (k + 1))
        mk, lk = m[:, bloco], lam[:, bloco]
        v0, v1 = eq0.familias.V[:, bloco], ref.tr.V0[:, bloco]
        # Utilitário: fração do consumo de todos que iguala o bem-estar agregado.
        utilitario = (np.sum(mk * v1) / np.sum(mk * v0)) ** (1 / (1 - theta)) - 1
        linhas.append({"grupo": nome, "ganha (%)": 100 * np.sum(mk * (lk > 0)) / mk.sum(),
                       "ganho médio (%)": 100 * np.sum(mk * lk) / mk.sum(),
                       "ganho utilitário (%)": 100 * utilitario})
    return pd.DataFrame(linhas)


def ganho_por_decil_de_riqueza(eq0: EquilibrioHA, lam: np.ndarray) -> np.ndarray:
    """Ganho médio (em %) em cada décimo da distribuição inicial de riqueza."""
    massa = eq0.m.sum(axis=1)
    acumulada = np.cumsum(massa) - massa / 2
    decil = np.minimum((acumulada * 10).astype(int), 9)
    return np.array([100 * np.sum(eq0.m[decil == d] * lam[decil == d]) / eq0.m[decil == d].sum()
                     for d in range(10)])


def desigualdade(eq0: EquilibrioHA) -> pd.DataFrame:
    """Momentos de desigualdade do modelo e dos dados."""
    _, anual = carregar_pnad()
    mom = eq0.momentos()
    gini_ibge = anual.loc[2012:2025, "gini_renda_domiciliar_pc"].mean()
    return pd.DataFrame([
        ("Gini da renda", mom["Gini da renda"], gini_ibge, "IBGE, PNAD 2012-2025 (domiciliar per capita)"),
        ("Gini da riqueza", mom["Gini da riqueza"], np.nan, ""),
        ("10% mais ricos: parcela da riqueza", mom["10% mais ricos (riqueza)"], WID_TOPO_10, "WID, 2021"),
        ("50% mais pobres: parcela da riqueza", mom["50% mais pobres (riqueza)"], WID_BASE_50, "WID, 2021"),
    ], columns=["momento", "modelo", "dados", "fonte"])


def _lorenz(valores, massas):
    ordem = np.argsort(valores)
    v, m = valores[ordem], massas[ordem]
    pop = np.concatenate([[0.0], np.cumsum(m) / m.sum()])
    return pop, np.concatenate([[0.0], np.cumsum(v * m) / np.sum(v * m)])


def figura_lorenz(eq0: EquilibrioHA, destino: Path) -> None:
    _, anual = carregar_pnad()
    faixas = [c for c in anual.columns if c.startswith("massa_")]
    parcelas = anual.loc[2012:2025, faixas].mean().to_numpy()
    pop_dados = np.array([0, .1, .2, .3, .4, .5, .6, .7, .8, .9, .95, .99, 1.0])
    lorenz_dados = np.concatenate([[0.0], np.cumsum(parcelas) / parcelas.sum()])

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.5, 4.3))
    ocupados = np.asarray(eq0.renda.estacionaria).reshape(3, 3)[:, 0]
    z = np.asarray(eq0.renda.z).reshape(3, 3)[:, 0]
    pop, lor = _lorenz(np.repeat(z, 100), np.repeat(ocupados, 100))
    for ax in (ax1, ax2):
        ax.plot([0, 1], [0, 1], color=TINTA_2, linewidth=0.8)
    ax1.plot(pop, lor, color=AZUL, label="modelo (3 tipos)")
    ax1.plot(pop_dados, lorenz_dados, "o", color=LARANJA, markersize=5,
             markeredgecolor=FUNDO, markeredgewidth=1.2, label="PNAD 2012-2025")
    ax1.set(title="Renda do trabalho dos ocupados", xlabel="fração dos ocupados",
            ylabel="fração acumulada da renda")
    ax1.legend(loc="upper left")

    pop, lor = _lorenz(np.repeat(eq0.grade.a, eq0.m.shape[1]), eq0.m.ravel())
    ax2.plot(pop, lor, color=AZUL, label="modelo")
    ax2.plot([0.5, 0.9], [WID_BASE_50, 1 - WID_TOPO_10], "o", color=LARANJA, markersize=5,
             markeredgecolor=FUNDO, markeredgewidth=1.2, label="WID 2021")
    ax2.set(title="Riqueza das famílias", xlabel="fração das famílias",
            ylabel="fração acumulada da riqueza")
    ax2.legend(loc="upper left")
    _virgula(ax1, ax2)
    fig.tight_layout()
    fig.savefig(destino)
    plt.close(fig)


def figura_bem_estar(eq0: EquilibrioHA, reformas: list[Reforma], destino: Path) -> None:
    riqueza = eq0.grade.a / eq0.K
    massa = eq0.m.sum(axis=1)
    limite = riqueza[np.searchsorted(np.cumsum(massa), 0.995)]
    visivel = riqueza <= limite
    fig, eixos = plt.subplots(1, len(reformas), figsize=(9.5, 4.2), sharey=True)
    for ax, ref in zip(eixos, reformas):
        ax.axhline(0, color=TINTA_2, linewidth=0.8)
        for k, (nome, cor) in enumerate(zip(TIPOS, TONS_TIPOS)):
            ax.plot(riqueza[visivel], 100 * ref.lam[visivel, 3 * k], color=cor, label=nome)
        ax.set(title=f"Devolução {ref.nome}", xlabel="riqueza inicial / riqueza média")
    eixos[0].set_ylabel("variação equivalente (% do consumo)")
    eixos[0].legend(title="empregados do grupo", loc="lower left", title_fontsize=8.5)
    _virgula(*eixos)
    fig.tight_layout()
    fig.savefig(destino)
    plt.close(fig)


def figura_grupos(resumos: dict, ganho_ra: float, destino: Path) -> None:
    grupos = TIPOS + ["todos (média)"]
    x = np.arange(len(grupos))
    largura = 0.34
    fig, ax = plt.subplots(figsize=(8.5, 4.3))
    ax.axhline(0, color=TINTA_2, linewidth=0.8)
    ax.axhline(ganho_ra, color=TINTA_2, linewidth=1.0, linestyle=(0, (4, 3)), zorder=1,
               label=f"modelo representativo ({_br(ganho_ra, 3)}%)")
    for i, ((nome, resumo), cor) in enumerate(zip(resumos.items(), (AZUL, LARANJA))):
        valores = resumo["ganho médio (%)"].to_numpy()
        barras = ax.bar(x + (i - 0.5) * largura, valores, width=largura * 0.92, color=cor,
                        label=f"devolução {nome}")
        for barra, v in zip(barras, valores):
            ax.annotate(_br(v, 2), (barra.get_x() + barra.get_width() / 2, v),
                        xytext=(0, 3 if v >= 0 else -3), textcoords="offset points",
                        ha="center", va="bottom" if v >= 0 else "top", color=TINTA, fontsize=8,
                        bbox={"boxstyle": "square,pad=0.15", "facecolor": FUNDO, "edgecolor": "none"},
                        zorder=3)
    ax.set_xticks(x, grupos)
    ax.set(ylabel="variação equivalente média (% do consumo)")
    ax.set_title("Quem ganha e quem perde: ganho médio por grupo de renda")
    ax.legend(loc="upper right")
    ax.grid(axis="x", visible=False)
    ax.yaxis.set_major_formatter(
        plt.FuncFormatter(lambda v, _: f"{v:g}".replace(".", ",").replace("-", "\u2212")))
    fig.tight_layout()
    fig.savefig(destino)
    plt.close(fig)


def figura_transicao(eco_ra, pol_ra, choque, eq0: EquilibrioHA, reformas, destino: Path) -> None:
    ee0 = estado_estacionario(eco_ra, pol_ra)
    ra = choque_tau_k(eco_ra, pol_ra, choque)
    t = np.linspace(0, 80, 801)
    k_ra, _ = ra.avaliar(t)
    fig, ax = plt.subplots(figsize=(7.5, 4.3))
    ax.axhline(0, color=TINTA_2, linewidth=0.8)
    ax.plot(t, 100 * (k_ra / ee0.k - 1), color=TINTA_2, linestyle=(0, (4, 3)),
            label="modelo representativo")
    for ref, cor in zip(reformas, (AZUL, LARANJA)):
        ax.plot(t, 100 * (np.interp(t, ref.tr.t, ref.tr.K) / eq0.K - 1), color=cor,
                label=f"heterogêneo, devolução {ref.nome}")
    ax.set(xlabel="anos desde o aumento", ylabel="capital: desvio do inicial (%)")
    ax.set_title("Transição do capital")
    ax.legend(loc="center right")
    _virgula(ax)
    fig.tight_layout()
    fig.savefig(destino)
    plt.close(fig)


def main() -> None:
    _estilo()
    PASTA_FIGURAS.mkdir(exist_ok=True)
    base = economia_ha()
    eq0 = base.eq0
    print(f"Calibração heterogênea: rho = {eq0.eco.rho:.4f} (representativo: "
          f"{base.eco_ra.rho:.4f}), tau_w = {eq0.gov.tau_w:.3f}, r_liq = {eq0.r_liq:.2%}")
    with pd.option_context("display.width", 160, "display.max_colwidth", 60):
        print(desigualdade(eq0).to_string(index=False, float_format="%.3f"))

    reformas = [reforma(eq0, base.choque, pesos, nome) for nome, pesos in VARIANTES.items()]
    ganho_ra = efeitos(base.eco_ra, base.pol_ra, base.choque, 0.8)["bem-estar, surpresa (%)"]
    resumos = {}
    for ref in reformas:
        resumos[ref.nome] = resumo_bem_estar(eq0, ref)
        print(f"\nDevolução {ref.nome}: capital de longo prazo {100 * (ref.eq1.K / eq0.K - 1):+.2f}% "
              f"(representativo -1,46%); transição em {ref.tr.iteracoes} iterações")
        print(resumos[ref.nome].to_string(index=False, float_format="%.3f"))
        decis = ganho_por_decil_de_riqueza(eq0, ref.lam)
        print("Ganho médio por décimo de riqueza (%):", " ".join(f"{v:+.3f}" for v in decis))
    print(f"\nModelo representativo: {ganho_ra:.3f}% para todos")

    figura_lorenz(eq0, PASTA_FIGURAS / "ha_lorenz.png")
    figura_bem_estar(eq0, reformas, PASTA_FIGURAS / "ha_bem_estar.png")
    figura_grupos(resumos, ganho_ra, PASTA_FIGURAS / "ha_grupos.png")
    figura_transicao(base.eco_ra, base.pol_ra, base.choque, eq0, reformas,
                     PASTA_FIGURAS / "ha_transicao.png")
    print(f"\nFiguras gravadas em {PASTA_FIGURAS}")


if __name__ == "__main__":
    main()
