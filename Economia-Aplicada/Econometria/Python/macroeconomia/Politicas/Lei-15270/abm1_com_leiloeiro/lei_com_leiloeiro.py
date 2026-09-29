"""
A Lei 15.270/2025 no ABM com leiloeiro (Forecast/Brasil/2013T4-2026T2/
abm1_com_leiloeiro): o mesmo aumento de tau_k de equilibrio_geral
(+0,85 p.p. sobre a renda líquida do capital, de surpresa), com a receita
nova devolvida igual para todos ou só aos empregados do grupo intermediário
(a faixa beneficiada pela isenção), para cada regra de expectativas.

O benchmark neoclássico é a previsão perfeita (transicao.py): as famílias
conhecem o caminho de preços que as próprias decisões produzem. As outras
regras (expectativas.py) aprendem, escolhem heurísticas, têm informação
rígida ou atenção limitada.

Para cada regra, duas economias partem do mesmo equilíbrio estacionário e
recebem os mesmos sorteios de renda de cada família (números aleatórios
comuns): uma sem mudança, outra com a reforma. A diferença entre elas é o
efeito da política, sem ruído de amostragem. O bem-estar de cada família é
a utilidade descontada que ela de fato obtém ao longo de 150 anos.

Além disso, `estabilidade` mostra que crer para sempre no estado
estacionário não é expectativa racional fora dele: com essas crenças a
economia se afasta do equilíbrio, enquanto com aprendizado ela volta.

Rode a partir da pasta Econometria/ (cerca de 10 minutos):

    python Python/macroeconomia/Politicas/Lei-15270/abm1_com_leiloeiro/lei_com_leiloeiro.py
"""
from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))   # macroeconomia/
import caminhos  # noqa: E402,F401

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import economia as E  # noqa: E402
import transicao  # noqa: E402
import expectativas as X  # noqa: E402
import familias as F  # noqa: E402
from calibracao_renda import GRUPOS  # noqa: E402
from comum import CORES, PREVISAO_PERFEITA, economia_base  # noqa: E402,F401
from experimentos import TINTA, TINTA_2, _estilo, _virgula  # noqa: E402

PASTA = Path(__file__).resolve().parent
ANOS = 150
N = 20_000
DEVOLUCOES = {"uniforme": None, "isenção": (0, 0, 0, 1, 0, 0, 0, 0, 0)}
REGRAS = {
    "aprendizado": X.Aprendizado,
    "heurísticas": X.Heuristicas,
    "informação rígida": X.InformacaoRigida,
    "atenção limitada": X.AtencaoLimitada,
}
TIPOS = list(GRUPOS)
# Aiyagari contínuo (equilibrio_geral/README.md): capital de longo prazo e
# ganho médio de bem-estar por grupo, em %.
HA_CAPITAL = {"uniforme": -1.45, "isenção": -1.41}
HA_GANHO = {"uniforme": (0.58, -0.06, -0.35, 0.23), "isenção": (-0.42, 0.49, -0.44, -0.06)}


def reformada(cal0: E.Calibrada, aumento: float, pesos) -> E.Calibrada:
    par1 = replace(cal0.par, tau_k=cal0.par.tau_k + aumento)
    est1 = F.equilibrio(par1, cal0.renda, pesos, K_inicial=cal0.est.K)
    return E.preparar(est1)


def simular(cal_inicial: E.Calibrada, cal: E.Calibrada, regra, trimestres: int, semente: int):
    """
    Parte do equilíbrio de `cal_inicial` e segue com a política de `cal`. As
    regras de equilíbrio passam a usar o equilíbrio de `cal`; as com memória
    começam das crenças antigas. Devolve os agregados e a utilidade descontada
    de cada família.
    """
    rng = np.random.default_rng(semente)
    estado = E.estado_inicial(cal_inicial, regra, N, rng)
    regra.iniciar(N, cal.est.r, cal.est.w, rng)
    regra.herdar(cal_inicial.est.r, cal_inicial.est.w)
    tipo_inicial = cal.renda.tipo[estado.j]
    par = cal.par
    D = par.periodo
    desconto = np.exp(-(par.rho - par.n - (1 - par.theta) * par.g) * D)
    bem_estar = np.zeros(N)
    peso = 1.0
    linhas = []
    for _ in range(trimestres):
        estado, registro = E.passo(cal, estado, rng, log_gamma=par.g * D, gasto=cal_inicial.par.gasto)
        bem_estar += peso * D * estado.c ** (1 - par.theta) / (1 - par.theta)
        peso *= desconto
        linhas.append(registro)
    return pd.DataFrame(linhas), bem_estar, tipo_inicial


def ganho(bem_estar_1, bem_estar_0, theta):
    return (bem_estar_1 / bem_estar_0) ** (1 / (1 - theta)) - 1


def resumo_bem_estar(b1, b0, tipo, theta) -> pd.DataFrame:
    linhas = []
    for k, nome in enumerate(TIPOS + ["todos"]):
        sel = np.ones_like(tipo, dtype=bool) if nome == "todos" else tipo == k
        individual = ganho(b1[sel], b0[sel], theta)
        linhas.append({"grupo": nome, "ganho médio (%)": 100 * individual.mean(),
                       "ganha (%)": 100 * np.mean(individual > 0),
                       "ganho utilitário (%)": 100 * ganho(b1[sel].sum(), b0[sel].sum(), theta)})
    return pd.DataFrame(linhas)


def experimento(cal0, aumento, trimestres=4 * ANOS, semente=11):
    reformas = {nome: reformada(cal0, aumento, pesos) for nome, pesos in DEVOLUCOES.items()}
    caminhos, tabelas = {}, []

    def perfeita(cal1):
        pp = transicao.previsao_perfeita(cal0, cal1, trimestres, N, semente)
        return pp.agregados, pp.bem_estar, pp.tipo_inicial

    casos = {PREVISAO_PERFEITA: (lambda: perfeita(cal0), perfeita)}
    for nome, fabrica in REGRAS.items():
        casos[nome] = ((lambda f=fabrica: simular(cal0, cal0, f(), trimestres, semente)),
                       (lambda cal1, f=fabrica: simular(cal0, cal1, f(), trimestres, semente)))
    for regra_nome, (rodar_base, rodar_reforma) in casos.items():
        base, b0, tipo = rodar_base()
        for devolucao, cal1 in reformas.items():
            novo, b1, _ = rodar_reforma(cal1)
            desvio = 100 * (novo[["K", "y", "C", "r"]] / base[["K", "y", "C", "r"]] - 1)
            caminhos[(regra_nome, devolucao)] = desvio
            bem = resumo_bem_estar(b1, b0, tipo, cal0.par.theta)
            longo = desvio.iloc[-80:].mean()
            tabelas.append(bem.assign(regra=regra_nome, devolucao=devolucao,
                                      capital_longo_prazo=longo.K,
                                      capital_equilibrio=100 * (cal1.est.K / cal0.est.K - 1)))
    return reformas, caminhos, pd.concat(tabelas, ignore_index=True)


SENSIBILIDADE = {
    ("aprendizado", "ganho 0,01"): lambda: X.Aprendizado(0.01),
    ("aprendizado", "ganho 0,05"): lambda: X.Aprendizado(0.05),
    ("heurísticas", "intensidade 0,2"): lambda: X.Heuristicas(intensidade=0.2),
    ("heurísticas", "intensidade 5"): lambda: X.Heuristicas(intensidade=5.0),
    ("informação rígida", "lambda 0,10"): lambda: X.InformacaoRigida(lam=0.10),
    ("informação rígida", "lambda 0,50"): lambda: X.InformacaoRigida(lam=0.50),
    ("atenção limitada", "m 0,70"): lambda: X.AtencaoLimitada(0.70),
    ("atenção limitada", "m 0,95"): lambda: X.AtencaoLimitada(0.95),
}


def sensibilidade(cal0, aumento, trimestres=4 * ANOS, semente=11) -> pd.DataFrame:
    """Devolução uniforme com parâmetros comportamentais abaixo e acima dos da literatura."""
    cal1 = reformada(cal0, aumento, DEVOLUCOES["uniforme"])
    linhas = []
    for (regra, parametro), fabrica in SENSIBILIDADE.items():
        base, b0, tipo = simular(cal0, cal0, fabrica(), trimestres, semente)
        novo, b1, _ = simular(cal0, cal1, fabrica(), trimestres, semente)
        bem = resumo_bem_estar(b1, b0, tipo, cal0.par.theta).set_index("grupo")
        capital = 100 * (novo.K / base.K - 1)
        linhas.append({"regra": regra, "parametro": parametro,
                       **{g: bem.loc[g, "ganho médio (%)"] for g in TIPOS + ["todos"]},
                       "capital em 30 anos (%)": capital.iloc[119],
                       "capital mínimo (%)": capital.min()})
    return pd.DataFrame(linhas)


def estabilidade(cal0: E.Calibrada, trimestres=4 * ANOS, semente=11) -> pd.DataFrame:
    """Capital sem reforma, partindo do equilíbrio, com crenças fixas e com aprendizado."""
    caminhos = {}
    for nome, fabrica in (("crenças fixas no estado estacionário", X.Equilibrio),
                          ("aprendizado", X.Aprendizado)):
        tabela, _, _ = simular(cal0, cal0, fabrica(), trimestres, semente)
        caminhos[nome] = tabela.K / cal0.est.K
    return pd.DataFrame(caminhos)


def figura_capital(caminhos, destino: Path) -> None:
    _estilo()
    fig, eixos = plt.subplots(1, 2, figsize=(9.5, 4.2), sharey=True)
    anos = np.arange(1, 4 * ANOS + 1) / 4
    for ax, devolucao in zip(eixos, DEVOLUCOES):
        for regra, cor in CORES.items():
            ax.plot(anos, caminhos[(regra, devolucao)].K, color=cor, label=regra, linewidth=1.4)
        ax.axhline(HA_CAPITAL[devolucao], color=TINTA_2, linestyle="--", linewidth=1)
        ax.annotate("Aiyagari contínuo", (ANOS * 0.55, HA_CAPITAL[devolucao]), xytext=(0, 5),
                    textcoords="offset points", color=TINTA_2, fontsize=8)
        ax.set_title(f"Devolução {devolucao}")
        ax.set(xlabel="anos depois da reforma", xlim=(0, ANOS))
        _virgula(ax)
    eixos[0].set_ylabel("capital, % em relação a sem reforma")
    eixos[0].legend(loc="upper right")
    fig.tight_layout()
    fig.savefig(destino)
    plt.close(fig)


def figura_bem_estar(tabela: pd.DataFrame, destino: Path) -> None:
    _estilo()
    fig, eixos = plt.subplots(1, 2, figsize=(9.5, 4.4), sharey=True)
    grupos = TIPOS + ["todos"]
    largura = 0.14
    for ax, devolucao in zip(eixos, DEVOLUCOES):
        dados = tabela[tabela.devolucao == devolucao]
        x = np.arange(len(grupos))
        for k, (regra, cor) in enumerate(CORES.items()):
            valores = dados[dados.regra == regra].set_index("grupo").loc[grupos, "ganho médio (%)"]
            ax.bar(x + (k - 2.5) * largura, valores, largura, color=cor, label=regra)
        ax.bar(x + 2.5 * largura, HA_GANHO[devolucao], largura, color="none", edgecolor=TINTA_2,
               hatch="///", linewidth=0.8, label="Aiyagari contínuo")
        ax.axhline(0, color=TINTA, linewidth=0.8)
        _virgula(ax)
        ax.set_xticks(x, ["50% menor\nrenda", "40%\nseguintes", "10% maior\nrenda", "todos"])
        ax.set_title(f"Devolução {devolucao}")
    eixos[0].set_ylabel("ganho de bem-estar, % do consumo")
    alcas, rotulos = eixos[0].get_legend_handles_labels()
    fig.legend(alcas, rotulos, loc="lower center", ncol=6, fontsize=8)
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    fig.savefig(destino)
    plt.close(fig)


def main() -> None:
    cal0, aumento = economia_base()
    print(f"ABM calibrado: rho = {cal0.par.rho:.4f}, tau_w = {cal0.par.tau_w:.3f}, "
          f"r = {100 * cal0.est.r:.2f}% (limite {100 * cal0.par.r_limite():.2f}%); "
          f"aumento de tau_k = {100 * aumento:.2f} p.p.")
    reformas, caminhos, tabela = experimento(cal0, aumento)
    for devolucao, cal1 in reformas.items():
        print(f"Novo equilíbrio estacionário, devolução {devolucao}: capital "
              f"{100 * (cal1.est.K / cal0.est.K - 1):+.2f}% (Aiyagari contínuo: {HA_CAPITAL[devolucao]:+.2f}%)")
    with pd.option_context("display.width", 150, "display.float_format", "{:.3f}".format):
        for devolucao in DEVOLUCOES:
            print(f"\nDevolução {devolucao}: ganho médio de bem-estar (%) por grupo e regra")
            t = tabela[tabela.devolucao == devolucao]
            print(t.pivot_table(index="regra", columns="grupo", values="ganho médio (%)",
                                sort=False)[TIPOS + ["todos"]])
            print("Capital nos últimos 20 anos (%):",
                  t.groupby("regra", sort=False).capital_longo_prazo.first().round(3).to_dict())
    pasta_res, pasta_fig = PASTA / "resultados", PASTA / "figuras"
    pasta_res.mkdir(exist_ok=True)
    pasta_fig.mkdir(exist_ok=True)
    tabela.to_csv(pasta_res / "lei_15270_bem_estar.csv", index=False, float_format="%.6g")
    pd.concat({f"{r}|{d}": c for (r, d), c in caminhos.items()}, names=["caso", "trimestre"]).to_csv(
        pasta_res / "lei_15270_caminhos.csv", float_format="%.6g")
    sens = sensibilidade(cal0, aumento)
    sens.to_csv(pasta_res / "sensibilidade.csv", index=False, float_format="%.6g")
    with pd.option_context("display.width", 160, "display.float_format", "{:.3f}".format):
        print("\nSensibilidade (devolução uniforme): ganho médio de bem-estar (%) e capital")
        print(sens.to_string(index=False))
    estavel = estabilidade(cal0)
    estavel.to_csv(pasta_res / "estabilidade.csv", float_format="%.6g")
    print("\nCapital sem reforma, em relação ao equilíbrio, depois de 25, 75 e 150 anos:")
    print(estavel.iloc[[99, 299, 599]].round(4).to_string())
    figura_capital(caminhos, pasta_fig / "lei_capital.png")
    figura_bem_estar(tabela, pasta_fig / "lei_bem_estar.png")
    print(f"\nResultados em {pasta_res} e figuras em {pasta_fig}")


if __name__ == "__main__":
    main()
