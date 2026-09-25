"""
Experimentos de política fiscal no modelo calibrado para o Brasil.

1. Tributação de altas rendas (Lei 15.270/2025): aumento de tau_k do tamanho da
   nova receita estimada pela Fazenda, de surpresa ou anunciado com antecedência.
2. Diagrama de fase de um choque ilustrativo maior, para ver o mecanismo.
3. Curva de Laffer de longo prazo do imposto sobre o capital.
4. Aumento temporário do gasto público e aumento anunciado do imposto sobre
   consumo.
5. Sensibilidade a theta, à alíquota inicial e ao tamanho do choque.

Rode a partir da pasta Econometria/:

    python Python/macroeconomia/equilibrio_geral/experimentos.py

As figuras vão para figuras/, nesta pasta; as tabelas saem no terminal.
"""
from dataclasses import replace
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FuncFormatter
import pandas as pd

from calibracao import aumento_tau_k_lei, calcular_alvos, calibrar, carregar_dados
from modelo import (Economia, Politica, estado_estacionario, ganho_bem_estar,
                    resolver_transicao)

PASTA_FIGURAS = Path(__file__).resolve().parent / "figuras"
ANUNCIO = 2025 + 73 / 365   # 15/03/2025, data da Exposição de Motivos nº 19/2025
VIGENCIA = 2026.0           # a Lei 15.270/2025 produz efeitos desde 1º/01/2026

AZUL, LARANJA = "#2a78d6", "#eb6834"
TINTA, TINTA_2, GRADE, FUNDO = "#0b0b0b", "#52514e", "#e6e5e1", "#fcfcfb"


def _estilo() -> None:
    plt.rcParams.update({
        "figure.facecolor": FUNDO, "axes.facecolor": FUNDO, "savefig.facecolor": FUNDO,
        "axes.edgecolor": GRADE, "axes.labelcolor": TINTA_2, "axes.titlecolor": TINTA,
        "axes.titlesize": 10.5, "axes.titleweight": "bold", "axes.titlelocation": "left",
        "axes.labelsize": 9, "xtick.color": TINTA_2, "ytick.color": TINTA_2,
        "xtick.labelsize": 8.5, "ytick.labelsize": 8.5,
        "axes.grid": True, "grid.color": GRADE, "grid.linewidth": 0.7,
        "axes.spines.top": False, "axes.spines.right": False,
        "lines.linewidth": 1.8, "lines.solid_capstyle": "round",
        "lines.solid_joinstyle": "round", "legend.frameon": False,
        "legend.fontsize": 8.5, "font.size": 9, "savefig.dpi": 200,
    })


def _br(valor: float, casas: int = 2) -> str:
    """Número no formato brasileiro, com vírgula decimal e sinal de menos tipográfico."""
    return f"{valor:.{casas}f}".replace(".", ",").replace("-", "\u2212")


def _virgula(*eixos) -> None:
    formato = FuncFormatter(lambda v, _: f"{v:g}".replace(".", ",").replace("-", "\u2212"))
    for ax in eixos:
        ax.xaxis.set_major_formatter(formato)
        ax.yaxis.set_major_formatter(formato)


def economia_calibrada():
    dados = carregar_dados()
    alvos = calcular_alvos(dados)
    eco, pol = calibrar(alvos)
    return dados, alvos, eco, pol


def choque_tau_k(eco: Economia, pol0: Politica, aumento: float,
                 antecedencia: float = 0.0, horizonte: float = 200.0):
    """Aumento permanente de tau_k, anunciado `antecedencia` anos antes de valer."""
    pol1 = replace(pol0, tau_k=pol0.tau_k + aumento)
    k0 = estado_estacionario(eco, pol0).k
    regimes = [(0.0, pol0), (antecedencia, pol1)] if antecedencia > 0 else pol1
    return resolver_transicao(eco, k0, regimes, horizonte)


def efeitos(eco: Economia, pol0: Politica, aumento: float, antecedencia: float) -> dict:
    """Efeitos de longo prazo, receita estática e dinâmica e bem-estar."""
    pol1 = replace(pol0, tau_k=pol0.tau_k + aumento)
    e0, e1 = estado_estacionario(eco, pol0), estado_estacionario(eco, pol1)

    def receita_capital(pol, ee):
        return pol.tau_k * (eco.alpha * ee.y - eco.delta * ee.k)

    estatica = aumento * (eco.alpha * e0.y - eco.delta * e0.k)   # com k fixo em k0*
    dinamica = receita_capital(pol1, e1) - receita_capital(pol0, e0)
    surpresa = choque_tau_k(eco, pol0, aumento)
    anunciado = choque_tau_k(eco, pol0, aumento, antecedencia)
    return {
        "capital (%)": 100 * (e1.k / e0.k - 1),
        "PIB e salário (%)": 100 * (e1.y / e0.y - 1),
        "consumo (%)": 100 * (e1.c / e0.c - 1),
        "receita estática (% PIB)": 100 * estatica / e0.y,
        "receita de longo prazo (% PIB)": 100 * dinamica / e0.y,
        "bem-estar, surpresa (%)": 100 * ganho_bem_estar(surpresa, e0, eco),
        "bem-estar, anunciado (%)": 100 * ganho_bem_estar(anunciado, e0, eco),
    }


def _desvios(traj, ee0, inicio: float, anos: np.ndarray) -> pd.DataFrame:
    """Desvios em relação ao estado inicial, em datas do calendário."""
    t = anos - inicio
    tab = traj.tabela(np.clip(t, 0, traj.fim))
    antes = t < 0
    k = np.where(antes, ee0.k, tab.k)
    c = np.where(antes, ee0.c, tab.c)
    y = np.where(antes, ee0.y, tab.y)
    r = np.where(antes, ee0.r, tab.r)
    return pd.DataFrame({"ano": anos, "k": 100 * (k / ee0.k - 1), "c": 100 * (c / ee0.c - 1),
                         "y": 100 * (y / ee0.y - 1), "r": 100 * (r - ee0.r)})


def _grade(inicio: float, fim: float, saltos) -> np.ndarray:
    base = np.linspace(inicio, fim, 2001)
    extras = [s + d for s in saltos for d in (-1e-7, 0.0)]
    return np.unique(np.concatenate([base, extras]))


def figura_lei(eco, pol0, aumento, destino: Path) -> None:
    ee0 = estado_estacionario(eco, pol0)
    anunciado = choque_tau_k(eco, pol0, aumento, VIGENCIA - ANUNCIO)
    surpresa = choque_tau_k(eco, pol0, aumento)
    anos = _grade(2023, 2070, [ANUNCIO, VIGENCIA])
    d_anun = _desvios(anunciado, ee0, ANUNCIO, anos)
    d_surp = _desvios(surpresa, ee0, VIGENCIA, anos)

    fig, eixos = plt.subplots(2, 2, figsize=(9, 6), sharex=True)
    paineis = [("k", "Capital", "desvio (%)"), ("c", "Consumo", "desvio (%)"),
               ("y", "PIB e salário", "desvio (%)"), ("r", "Retorno líquido do capital", "desvio (p.p.)")]
    for ax, (var, titulo, unidade) in zip(eixos.flat, paineis):
        ax.axhline(0, color=TINTA_2, linewidth=0.8)
        for data in (ANUNCIO, VIGENCIA):
            ax.axvline(data, color=GRADE, linewidth=1.2, zorder=0)
        ax.plot(d_anun.ano, d_anun[var], color=LARANJA, label="Anunciada em mar/2025")
        ax.plot(d_surp.ano, d_surp[var], color=AZUL, label="Surpresa em jan/2026")
        ax.set_title(titulo)
        ax.set_ylabel(unidade)
    for ax in eixos[1]:
        ax.set_xlabel("ano")
    eixos[0, 0].legend(loc="lower left")
    eixos[0, 1].annotate("anúncio", (ANUNCIO, 1), xycoords=("data", "axes fraction"),
                         xytext=(-3, -2), textcoords="offset points", ha="right", va="top",
                         color=TINTA_2, fontsize=8)
    eixos[0, 1].annotate("vigência", (VIGENCIA, 1), xycoords=("data", "axes fraction"),
                         xytext=(3, -2), textcoords="offset points", ha="left", va="top",
                         color=TINTA_2, fontsize=8)
    _virgula(*eixos.flat)
    fig.suptitle(f"Aumento de {_br(100 * aumento)} p.p. em $\\tau_k$ (tamanho da Lei 15.270/2025)",
                 x=0.01, ha="left", fontsize=11.5, fontweight="bold", color=TINTA)
    fig.tight_layout()
    fig.savefig(destino)
    plt.close(fig)


def figura_diagrama_fase(eco, pol0, aumento, antecedencia, destino: Path) -> None:
    pol1 = replace(pol0, tau_k=pol0.tau_k + aumento)
    e0, e1 = estado_estacionario(eco, pol0), estado_estacionario(eco, pol1)
    surpresa = choque_tau_k(eco, pol0, aumento)
    anunciado = choque_tau_k(eco, pol0, aumento, antecedencia)
    t = np.linspace(0, 150, 3001)
    ks, cs = surpresa.avaliar(t)
    ka, ca = anunciado.avaliar(np.union1d(t, [antecedencia]))
    k_vig, c_vig = anunciado.avaliar(antecedencia)

    k_min, k_max = 0.9 * e1.k, 1.04 * e0.k
    grade_k = np.linspace(k_min, k_max, 300)
    locus_k = grade_k**eco.alpha - pol0.gasto - (eco.delta + eco.n + eco.g) * grade_k

    fig, ax = plt.subplots(figsize=(7.5, 5))
    ax.plot(grade_k, locus_k, color=TINTA_2, linewidth=1.2)
    ax.axvline(e0.k, color=TINTA_2, linewidth=1.2, linestyle=(0, (4, 3)))
    ax.axvline(e1.k, color=TINTA_2, linewidth=1.2)
    ax.plot(ka, ca, color=LARANJA, label=f"Anunciado {antecedencia:g} anos antes")
    ax.plot(ks, cs, color=AZUL, label="Surpresa (braço estável novo)")
    for (k, c) in ((e0.k, e0.c), (ks[0], cs[0]), (ka[0], ca[0])):
        ax.plot([e0.k, k], [e0.c, c], color=TINTA_2, linewidth=0.8, linestyle=":")
    marcadores = [(e0.k, e0.c, "E0", (6, -12)), (e1.k, e1.c, "E1", (6, -12)),
                  (k_vig, c_vig, "vigência", (6, -14))]
    for k, c, rotulo, desloc in marcadores:
        ax.plot(k, c, "o", color=TINTA, markersize=5, markeredgecolor=FUNDO, markeredgewidth=1.5)
        ax.annotate(rotulo, (k, c), xytext=desloc, textcoords="offset points",
                    color=TINTA, fontsize=8.5)
    ax.annotate("ċ = 0 antes", (e0.k, 0.02), xycoords=("data", "axes fraction"),
                xytext=(4, 0), textcoords="offset points", color=TINTA_2, fontsize=8)
    ax.annotate("ċ = 0 depois", (e1.k, 0.02), xycoords=("data", "axes fraction"),
                xytext=(4, 0), textcoords="offset points", color=TINTA_2, fontsize=8)
    ax.annotate("k̇ = 0", (grade_k[-1], locus_k[-1]), xytext=(-4, 6),
                textcoords="offset points", ha="right", color=TINTA_2, fontsize=8)
    c_todos = np.concatenate([cs, ca, [e0.c, e1.c]])
    ax.set(xlim=(k_min, k_max), ylim=(0.97 * c_todos.min(), 1.03 * c_todos.max()),
           xlabel="capital por trabalhador efetivo, k", ylabel="consumo por trabalhador efetivo, c")
    ax.set_title(f"Diagrama de fase: aumento ilustrativo de {100 * aumento:.0f} p.p. em $\\tau_k$")
    ax.legend(loc="upper left")
    _virgula(ax)
    fig.tight_layout()
    fig.savefig(destino)
    plt.close(fig)


def curva_laffer(eco: Economia, pol0: Politica, aliquotas: np.ndarray) -> pd.DataFrame:
    y0 = estado_estacionario(eco, pol0).y
    linhas = []
    for tau in aliquotas:
        # k* não depende do gasto; zerá-lo evita consumo negativo em alíquotas
        # altíssimas, em que o PIB já não comportaria o gasto atual.
        ee = estado_estacionario(eco, Politica(tau_k=tau))
        receita = tau * (eco.alpha * ee.y - eco.delta * ee.k)
        linhas.append({"tau_k": tau, "receita_pib_inicial": 100 * receita / y0})
    return pd.DataFrame(linhas)


def figura_laffer(eco, pol0, destino: Path) -> pd.Series:
    curva = curva_laffer(eco, pol0, np.linspace(0, 0.95, 191))
    pico = curva.loc[curva.receita_pib_inicial.idxmax()]
    atual = curva_laffer(eco, pol0, np.array([pol0.tau_k])).iloc[0]
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    ax.plot(100 * curva.tau_k, curva.receita_pib_inicial, color=AZUL)
    for ponto, rotulo, desloc in ((atual, "Brasil hoje", (8, -14)), (pico, "pico", (0, 8))):
        ax.plot(100 * ponto.tau_k, ponto.receita_pib_inicial, "o", color=AZUL,
                markersize=6, markeredgecolor=FUNDO, markeredgewidth=1.5)
        ax.annotate(f"{rotulo}: {100 * ponto.tau_k:.0f}%, {_br(ponto.receita_pib_inicial, 1)}% do PIB",
                    (100 * ponto.tau_k, ponto.receita_pib_inicial), xytext=desloc,
                    textcoords="offset points", ha="left" if desloc[0] else "center",
                    color=TINTA, fontsize=8.5)
    ax.set(xlabel="alíquota sobre a renda líquida do capital, $\\tau_k$ (%)",
           ylabel="receita de longo prazo (% do PIB inicial)",
           ylim=(0, 1.12 * curva.receita_pib_inicial.max()))
    _virgula(ax)
    ax.set_title("Curva de Laffer de longo prazo do imposto sobre o capital")
    fig.tight_layout()
    fig.savefig(destino)
    plt.close(fig)
    return pico


def figura_outros_choques(eco, pol0, destino: Path) -> None:
    ee0 = estado_estacionario(eco, pol0)
    gasto_alto = replace(pol0, gasto=pol0.gasto + 0.02 * ee0.y)
    temporario = resolver_transicao(eco, ee0.k, [(0.0, gasto_alto), (5.0, pol0)])
    consumo = replace(pol0, tau_c=pol0.tau_c + 0.05)
    iva = resolver_transicao(eco, ee0.k, [(0.0, pol0), (2.0, consumo)])
    anos = _grade(-3, 40, [0.0, 2.0, 5.0])

    fig = plt.figure(figsize=(10, 6.2), layout="constrained")
    linhas = [(temporario, "Gasto público +2% do PIB por 5 anos, de surpresa"),
              (iva, "Imposto sobre consumo +5 p.p., anunciado 2 anos antes")]
    for subfig, (traj, titulo) in zip(fig.subfigures(2, 1, hspace=0.06), linhas):
        d = _desvios(traj, ee0, 0.0, anos)
        eixos = subfig.subplots(1, 3, sharex=True)
        for ax, (var, nome, unidade) in zip(eixos, [("k", "Capital", "%"), ("c", "Consumo", "%"),
                                                    ("r", "Retorno líquido", "p.p.")]):
            ax.axhline(0, color=TINTA_2, linewidth=0.8)
            ax.plot(d.ano, d[var], color=AZUL)
            ax.set_title(nome, fontsize=9.5)
            ax.set_ylabel(f"desvio ({unidade})")
            ax.set_xlabel("anos desde o anúncio")
        _virgula(*eixos)
        subfig.suptitle(titulo, x=0.01, ha="left", fontsize=11, fontweight="bold", color=TINTA)
    fig.savefig(destino)
    plt.close(fig)


def sensibilidade(dados, alvos, antecedencia: float) -> pd.DataFrame:
    """Recalibra rho em cada caso para manter K/Y e compara os efeitos."""
    lei = aumento_tau_k_lei(alvos, dados)
    casos = [("base", 2.0, 0.18, lei), ("theta = 1", 1.0, 0.18, lei),
             ("theta = 4", 4.0, 0.18, lei), ("tau_k bruto 14%", 2.0, 0.14, lei),
             ("tau_k bruto 22%", 2.0, 0.22, lei), ("choque +2,5 p.p.", 2.0, 0.18, 0.025),
             ("choque +5 p.p.", 2.0, 0.18, 0.05)]
    linhas = []
    for nome, theta, tau_bruto, aumento in casos:
        eco, pol = calibrar(alvos, theta=theta, tau_bruto=tau_bruto)
        linha = {"caso": nome, "rho": eco.rho, "tau_k": pol.tau_k}
        linha.update(efeitos(eco, pol, aumento, antecedencia))
        linhas.append(linha)
    return pd.DataFrame(linhas)


def main() -> None:
    _estilo()
    PASTA_FIGURAS.mkdir(exist_ok=True)
    dados, alvos, eco, pol = economia_calibrada()
    ee = estado_estacionario(eco, pol)
    lei = aumento_tau_k_lei(alvos, dados)
    antecedencia = VIGENCIA - ANUNCIO

    figura_lei(eco, pol, lei, PASTA_FIGURAS / "lei_15270.png")
    figura_diagrama_fase(eco, pol, 0.10, 3.0, PASTA_FIGURAS / "diagrama_fase.png")
    pico = figura_laffer(eco, pol, PASTA_FIGURAS / "laffer.png")
    figura_outros_choques(eco, pol, PASTA_FIGURAS / "outros_choques.png")

    print(f"Estado inicial: k* = {ee.k:.4f}, y* = {ee.y:.4f}, c* = {ee.c:.4f}, r* = {ee.r:.2%}")
    print(f"Choque da Lei 15.270/2025: +{100 * lei:.2f} p.p. em tau_k, "
          f"anunciado {antecedencia:.2f} ano antes da vigência\n")
    resultado = pd.Series(efeitos(eco, pol, lei, antecedencia))
    print(resultado.to_string(float_format="%.3f"))
    print(f"\nPico da curva de Laffer: tau_k = {pico.tau_k:.1%}, "
          f"receita de {pico.receita_pib_inicial:.1f}% do PIB inicial")
    print("\nSensibilidade (rho recalibrado para manter K/Y):")
    with pd.option_context("display.width", 200, "display.max_columns", 20):
        print(sensibilidade(dados, alvos, antecedencia).to_string(index=False, float_format="%.3f"))
    print(f"\nFiguras gravadas em {PASTA_FIGURAS}")


if __name__ == "__main__":
    main()
