"""
O ABM volta sozinho ao equilíbrio?

Nos outros experimentos a população parte do equilíbrio estacionário. Aqui
ela parte de longe dele, com a renda de cada família no seu estado
estacionário mas a riqueza fora do lugar:

  - capital 50% abaixo ou 50% acima do equilíbrio, com a mesma desigualdade;
  - a mesma riqueza para todas as famílias (Gini zero);
  - 1% das famílias, sorteadas, com toda a riqueza (Gini perto de um);
  - o próprio equilíbrio estacionário, como controle.

E as crenças partem dos preços que as famílias observam no primeiro
trimestre, não dos preços do equilíbrio: quem aprende não sabe onde fica o
estado estacionário. Só as regras que o usam por definição (crenças fixas,
atenção limitada e a regra fundamentalista dentro das heurísticas) o
conhecem.

A economia segue sem reforma e sem choques agregados por 1.000 anos. Com
previsão perfeita, a convergência é imposta: o caminho de preços termina,
por construção, no estado estacionário. Nas outras regras ninguém impõe
nada: se o capital e a distribuição da riqueza voltam, é porque as decisões
das famílias os trazem de volta.

A previsão perfeita é calculada para um contínuo de famílias, com o
histograma da população inicial (transicao.previsao_perfeita_histograma).
Com 20 mil famílias seguindo um caminho de preços dado, o ruído de
amostragem se acumula: quem não reage aos preços realizados torna o
equilíbrio instável, e o desvio em relação ao caminho dobra a cada 20 anos,
mais ou menos. Em transicao.previsao_perfeita esse ruído entra no próprio
ponto fixo, o que serve para 150 anos, mas não para 1.000.

Rode a partir da pasta Econometria/ (cerca de meia hora com 4 núcleos):

    python Python/macroeconomia/Forecast/Brasil/2013T4-2026T2/abm1_com_leiloeiro/convergencia.py
"""
from __future__ import annotations

import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))   # macroeconomia/
import caminhos  # noqa: E402,F401

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import economia as E  # noqa: E402
import expectativas as X  # noqa: E402
import familias as F  # noqa: E402
import transicao  # noqa: E402
from comum import CORES, PREVISAO_PERFEITA, economia_base  # noqa: E402
from experimentos import TINTA, TINTA_2, _estilo, _virgula  # noqa: E402

PASTA = Path(__file__).resolve().parent
N = 20_000
ANOS = 1000
SEMENTE = 11
CRENCAS_FIXAS = "crenças fixas"


def _concentrar(s, rng):
    donos = rng.choice(s.size, max(1, s.size // 100), replace=False)
    nova = np.zeros_like(s)
    nova[donos] = s.sum() / donos.size
    return nova


CONTROLE = "equilíbrio estacionário"
PARTIDAS = {
    CONTROLE: lambda s, rng: s,
    "capital 50% abaixo": lambda s, rng: 0.5 * s,
    "capital 50% acima": lambda s, rng: 1.5 * s,
    "riqueza igual para todos": lambda s, rng: np.full_like(s, s.mean()),
    "1% com toda a riqueza": _concentrar,
}
REGRAS = {
    PREVISAO_PERFEITA: None,
    CRENCAS_FIXAS: X.Equilibrio,
    "aprendizado": X.Aprendizado,
    "heurísticas": X.Heuristicas,
    "informação rígida": X.InformacaoRigida,
    "atenção limitada": X.AtencaoLimitada,
}
COM_MEMORIA = ("aprendizado", "heurísticas", "informação rígida")
CORES_REGRAS = {**CORES, CRENCAS_FIXAS: TINTA_2}


# --- medidas da distribuição --------------------------------------------------

def gini(x: np.ndarray) -> float:
    x = np.sort(np.asarray(x, dtype=float))
    n = x.size
    return float((2 * np.arange(1, n + 1) - n - 1) @ x / (n * x.sum()))


def participacao_topo(x: np.ndarray, fracao: float = 0.1) -> float:
    x = np.sort(np.asarray(x, dtype=float))
    return float(x[-max(1, int(round(fracao * x.size))):].sum() / x.sum())


class Referencia:
    """Distribuição estacionária da riqueza (somada sobre os estados de renda)."""

    def __init__(self, cal: E.Calibrada):
        dist = cal.est.distribuicao
        self.grade = dist.grade_a
        self.acumulada = np.cumsum(dist.massa.sum(axis=1))
        self.acumulada /= self.acumulada[-1]
        self.gini = gini_histograma(self.grade, dist.massa.sum(axis=1))

    def distancia(self, a: np.ndarray) -> float:
        """Kolmogorov-Smirnov: maior diferença entre as funções de distribuição, nos nós da grade."""
        empirica = np.searchsorted(np.sort(a), self.grade, side="right") / a.size
        return float(np.max(np.abs(empirica - self.acumulada)))

    def distancia_histograma(self, grade: np.ndarray, massa: np.ndarray) -> float:
        """A mesma distância para um histograma em outra grade (massa somada sobre a renda)."""
        acumulada = np.interp(self.grade, grade, np.cumsum(massa) / massa.sum())
        return float(np.max(np.abs(acumulada - self.acumulada)))


def gini_histograma(grade: np.ndarray, massa: np.ndarray) -> float:
    massa = massa / massa.sum()
    riqueza = np.cumsum(grade * massa) / (grade @ massa)
    lorenz_anterior = np.concatenate([[0.0], riqueza[:-1]])
    return float(1 - massa @ (riqueza + lorenz_anterior))


def topo_histograma(grade: np.ndarray, massa: np.ndarray, fracao: float = 0.1) -> float:
    """Fração da riqueza com a `fracao` mais rica, num histograma."""
    massa = massa[::-1] / massa.sum()
    grade = grade[::-1]
    cauda = np.cumsum(massa)
    k = int(np.searchsorted(cauda, fracao))
    antes = cauda[k - 1] if k > 0 else 0.0
    return float((grade[:k] @ massa[:k] + (fracao - antes) * grade[k]) / (grade @ massa))


# --- população inicial e simulação ----------------------------------------------

def precos_iniciais(cal: E.Calibrada, estado: E.Estado) -> tuple[float, float]:
    """Juro líquido e salário que a população inicial produz (antes do primeiro sorteio de renda)."""
    par = cal.par
    K = estado.s.mean() * par.fator_crescimento
    R, w, _ = F.precos(par, K, cal.renda.z[estado.j].mean())
    return (1 - par.tau_k) * (R - par.delta), w


def populacao(cal: E.Calibrada, transformar, regra, N: int, rng,
              crencas_observadas: bool = True) -> E.Estado:
    """
    Estados de renda estratificados do equilíbrio estacionário e riqueza
    transformada. Com `crencas_observadas`, as regras com memória começam
    acreditando nos preços do primeiro trimestre.
    """
    estado = E.estado_inicial(cal, regra, N, rng)
    estado.s = transformar(estado.s, rng)
    if crencas_observadas:
        regra.herdar(*precos_iniciais(cal, estado))
    return estado


def trajetoria(cal: E.Calibrada, estado: E.Estado, rng, trimestres: int,
               politicas: list | None = None) -> tuple[np.ndarray, pd.DataFrame]:
    """
    Simula sem choques agregados. Devolve o capital de cada trimestre (em
    relação ao do equilíbrio) e, a cada ano, o juro líquido e o esperado, o
    Gini e a fração do 10% mais rico na riqueza, e a distância à distribuição
    estacionária. Com `politicas`, as famílias seguem a política de cada
    trimestre.
    """
    par, est = cal.par, cal.est
    D = par.periodo
    referencia = Referencia(cal)
    K = np.empty(trimestres)
    anos = []
    for t in range(trimestres):
        politica = None if politicas is None else politicas[t]
        estado, registro = E.passo(cal, estado, rng, log_gamma=par.g * D, gasto=par.gasto,
                                   politica=politica)
        K[t] = registro["K"] / est.K
        if (t + 1) % 4 == 0:
            a = estado.s * par.fator_crescimento
            anos.append({"ano": (t + 1) // 4, "K": K[t], "r": 100 * (registro["r"] - est.r),
                         "r_e": 100 * (registro["r_e"] - est.r), "gini": gini(a),
                         "topo_10": participacao_topo(a), "distancia": referencia.distancia(a)})
    return K, pd.DataFrame(anos).set_index("ano")


def previsao_perfeita_continua(cal: E.Calibrada, estado: E.Estado, trimestres: int):
    """
    O caminho de previsão perfeita de um contínuo de famílias com a
    distribuição de `estado`, com as mesmas medidas de `trajetoria`, a partir
    do histograma. O juro esperado é o realizado.
    """
    est = cal.est
    referencia = Referencia(cal)
    grade = transicao.grade_para(cal, estado)
    massa = transicao.histograma(cal, estado, grade)
    caminho = transicao.previsao_perfeita_histograma(cal, massa, grade, trimestres)
    anos = []
    for t, politica in enumerate(caminho.politicas):
        massa = transicao.avancar(cal, politica, grade, massa)
        if (t + 1) % 4 == 0:
            riqueza = massa.sum(axis=1)
            r = 100 * (politica.r - est.r)
            anos.append({"ano": (t + 1) // 4, "K": caminho.K[t] / est.K, "r": r, "r_e": r,
                         "gini": gini_histograma(grade, riqueza),
                         "topo_10": topo_histograma(grade, riqueza),
                         "distancia": referencia.distancia_histograma(grade, riqueza)})
    return caminho.K / est.K, pd.DataFrame(anos).set_index("ano")


def anos_ate_convergir(K: np.ndarray, faixa: float = 0.01) -> float:
    """Anos até o capital entrar de vez na faixa de ±1% do equilíbrio (NaN se não entrar)."""
    fora = np.flatnonzero(np.abs(K - 1) >= faixa)
    if fora.size == 0:
        return 0.0
    if fora[-1] >= K.size - 40:   # ainda fora nos últimos 10 anos
        return np.nan
    return (fora[-1] + 1) / 4


def rodar(cal: E.Calibrada, regra_nome: str, partida_nome: str, anos: int = ANOS, N: int = N,
          semente: int = SEMENTE, crencas_observadas: bool = True):
    transformar = PARTIDAS[partida_nome]
    trimestres = 4 * anos
    rng = np.random.default_rng(semente)
    if REGRAS[regra_nome] is None:
        estado = populacao(cal, transformar, X.Equilibrio(), N, rng, crencas_observadas=False)
        return previsao_perfeita_continua(cal, estado, trimestres)
    estado = populacao(cal, transformar, REGRAS[regra_nome](), N, rng, crencas_observadas)
    return trajetoria(cal, estado, rng, trimestres)


def resumir(K: np.ndarray, anual: pd.DataFrame, **chaves) -> dict:
    final = anual.iloc[-10:].mean()
    distancia = anual.distancia.reindex([100, 300])
    return {**chaves,
            "K em 10 anos": K[39], "K em 50 anos": K[199],
            "K mínimo": K.min(), "K máximo": K.max(),
            "K nos últimos 10 anos": K[-40:].mean(),
            "anos até ±1%": anos_ate_convergir(K),
            "Gini inicial": anual.gini.iloc[0], "Gini final": final.gini,
            "topo 10% final": final.topo_10,
            "distância em 100 anos": distancia.loc[100],
            "distância em 300 anos": distancia.loc[300],
            "distância final": final.distancia}


def _caso(args):
    cal, regra_nome, partida_nome, anos, crencas_observadas = args
    K, anual = rodar(cal, regra_nome, partida_nome, anos, crencas_observadas=crencas_observadas)
    rotulo = "preços observados" if crencas_observadas else "equilíbrio"
    print(f"  {regra_nome:18s} {partida_nome:26s} {rotulo:18s} K final {K[-40:].mean():.3f}  "
          f"Gini {anual.gini.iloc[-1]:.2f}  distância {anual.distancia.iloc[-1]:.3f}", flush=True)
    return (regra_nome, partida_nome, crencas_observadas), K, anual


def experimento(cal: E.Calibrada, anos: int = ANOS, processos: int | None = None):
    """
    Todas as regras a partir de todas as partidas, com as crenças começando
    dos preços observados; e, como sensibilidade, as regras com memória
    começando das crenças do equilíbrio. Os casos rodam em paralelo.
    """
    casos = [(cal, r, p, anos, True) for r in REGRAS for p in PARTIDAS]
    casos += [(cal, r, p, anos, False) for r in COM_MEMORIA for p in PARTIDAS if p != CONTROLE]
    with ProcessPoolExecutor(processos) as executor:
        saidas = list(executor.map(_caso, casos))
    resumos, caminhos = [], {}
    for (regra_nome, partida_nome, observadas), K, anual in saidas:
        if observadas:
            caminhos[(regra_nome, partida_nome)] = anual
        resumos.append(resumir(K, anual, regra=regra_nome, partida=partida_nome,
                               crencas_iniciais="preços observados" if observadas else "equilíbrio"))
    return pd.DataFrame(resumos), caminhos


def _anos_gravados(anos: int) -> np.ndarray:
    return np.union1d(np.arange(1, min(anos, 100) + 1), np.arange(110, anos + 1, 10))


def figura(caminhos, gini_estacionario: float, destino: Path) -> None:
    _estilo()
    fig, eixos = plt.subplots(2, 2, figsize=(9.5, 7.2))
    paineis = [
        (eixos[0, 0], "capital 50% abaixo", "K", 150, "capital / capital de equilíbrio"),
        (eixos[0, 1], "capital 50% acima", "K", 150, None),
        (eixos[1, 0], "riqueza igual para todos", "gini", None, "Gini da riqueza"),
        (eixos[1, 1], "1% com toda a riqueza", "gini", None, None),
    ]
    for ax, partida, variavel, ate, rotulo in paineis:
        for regra, cor in CORES_REGRAS.items():
            serie = caminhos[(regra, partida)][variavel]
            if ate is not None:
                serie = serie.loc[:ate]
            estilo = "--" if regra == CRENCAS_FIXAS else "-"
            ax.plot(serie.index, serie, color=cor, linestyle=estilo, linewidth=1.3, label=regra)
        referencia = 1.0 if variavel == "K" else gini_estacionario
        ax.axhline(referencia, color=TINTA, linewidth=0.8, linestyle=":")
        ax.set_title(f"Partida: {partida}")
        ax.set_xlabel("anos")
        if rotulo:
            ax.set_ylabel(rotulo)
        _virgula(ax)
    alcas, rotulos = eixos[0, 0].get_legend_handles_labels()
    fig.legend(alcas, rotulos, loc="lower center", ncol=6, fontsize=8)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(destino)
    plt.close(fig)


def main() -> None:
    cal, _ = economia_base()
    referencia = Referencia(cal)
    print(f"Equilíbrio: K = {cal.est.K:.3f}, r = {100 * cal.est.r:.2f}%, "
          f"Gini da riqueza = {referencia.gini:.3f}")
    resumo, caminhos = experimento(cal)
    pasta_res, pasta_fig = PASTA / "resultados", PASTA / "figuras"
    pasta_res.mkdir(exist_ok=True)
    pasta_fig.mkdir(exist_ok=True)
    resumo.to_csv(pasta_res / "convergencia.csv", index=False, float_format="%.6g")
    anos = _anos_gravados(ANOS)
    pd.concat({f"{r}|{p}": c.loc[anos] for (r, p), c in caminhos.items()},
              names=["caso", "ano"]).to_csv(pasta_res / "convergencia_caminhos.csv", float_format="%.5g")
    figura(caminhos, referencia.gini, pasta_fig / "convergencia.png")
    colunas = ["regra", "partida", "crencas_iniciais", "K em 10 anos", "K mínimo", "K máximo",
               "K nos últimos 10 anos", "anos até ±1%", "Gini final", "distância em 100 anos",
               "distância final"]
    with pd.option_context("display.width", 200, "display.max_columns", 20,
                           "display.float_format", "{:.3f}".format):
        print(resumo[colunas].to_string(index=False))
    print(f"\nResultados em {pasta_res} e figura em {pasta_fig}")


if __name__ == "__main__":
    main()
