"""
O ABM com leiloeiro no protocolo de previsão fora da amostra (../protocolo.py).

Em cada origem T, só com informação disponível em T:
  1. calibração: dados anuais até o ano de T menos 2 (como no equilíbrio
     geral), processo de renda com a PNAD até T e tendência g + n igual ao
     crescimento médio do PIB trimestral até T; rho reproduz K/Y;
  2. história: o ABM percorre 1996-T reproduzindo o PIB e o gasto
     observados (economia.historia), o que fixa a distribuição de riqueza,
     os estados de renda e as crenças das famílias em T;
  3. choques: um VAR(1) diagonal para o crescimento da produtividade (o que
     a história inferiu) e do gasto, estimado até T;
  4. previsão: `replicas` simulações de T+1 a T+h a partir do estado em T;
     a previsão é a média das réplicas, e a incerteza, a variância entre elas.

É o desenho de Poledna, Miess, Hommes e Rabitsch (2023) para o ABM da
Áustria: agentes inicializados pelos dados e choques agregados estimados.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))   # macroeconomia/
import caminhos  # noqa: E402,F401

import economia as E  # noqa: E402
import expectativas as X  # noqa: E402
import familias as F  # noqa: E402
import protocolo  # noqa: E402
from calibracao import TAU_K_BRUTO, aliquota_liquida, calcular_alvos  # noqa: E402
from calibracao_renda import carregar_pnad, renda_brasil  # noqa: E402

REGRAS = {"eq": ("crenças fixas", X.Equilibrio), "apr": ("aprendizado", X.Aprendizado),
          "heu": ("heurísticas", X.Heuristicas), "inf": ("informação rígida", X.InformacaoRigida),
          "aten": ("atenção limitada", X.AtencaoLimitada)}
VARIANTES = {f"abm_{chave}": (f"ABM 1: {nome}", fabrica) for chave, (nome, fabrica) in REGRAS.items()}


def parametros_na_origem(anuais: pd.DataFrame, pnad, amostra: pd.DataFrame, origem: int):
    """Parâmetros, processo de renda e alvos da calibração com o que se conhece em `origem`."""
    ano = origem // 100
    ultimo = int(anuais.pib_real_pwt.dropna().index.max())
    alvos = calcular_alvos(anuais, protocolo.INICIO_CALIBRACAO,
                           min(ano - protocolo.DEFASAGEM_ANUAL, ultimo))
    tau_k = aliquota_liquida(TAU_K_BRUTO, alvos.alpha, alvos.delta, alvos.capital_produto)
    periodo = 0.25
    g = amostra.pib.mean() / 100 / periodo - alvos.n
    trimestral, anual = pnad
    renda = F.Renda.de_continua(renda_brasil(pnad=(trimestral.loc[:origem], anual.loc[:ano - 1])),
                                periodo)
    par = F.Parametros(alvos.alpha, alvos.delta, 0.0, protocolo.THETA, alvos.n, g, tau_k,
                       periodo=periodo)
    return par, renda, alvos


def calibrar_na_origem(anuais: pd.DataFrame, pnad, amostra: pd.DataFrame, origem: int,
                       grades: F.Grades = F.Grades()) -> E.Calibrada:
    par, renda, alvos = parametros_na_origem(anuais, pnad, amostra, origem)
    return E.preparar(F.calibrar(par, renda, alvos.capital_produto, alvos.gasto_pib, grades), grades)


class ModeloABM:
    def __init__(self, anuais: pd.DataFrame, chave: str, pnad=None, N: int = E.N_PADRAO,
                 replicas: int = 200, cache: dict | None = None):
        self.nome, self.fabrica = VARIANTES[chave]
        self.anuais = anuais
        self.pnad = carregar_pnad() if pnad is None else pnad
        self.N, self.replicas = N, replicas
        self.cache = {} if cache is None else cache   # calibração por origem, partilhável
        self.historias = {}

    def prever(self, amostra: pd.DataFrame, origem: int, horizonte: int):
        if origem not in self.cache:
            self.cache[origem] = calibrar_na_origem(self.anuais, self.pnad, amostra, origem)
        cal = self.cache[origem]
        estado, hist = E.historia(cal, amostra, self.fabrica(), self.N, semente=0)
        self.historias[origem] = hist
        exogenos = E.Exogenos.estimar(hist.log_gamma.iloc[1:].to_numpy(),
                                      amostra.governo.to_numpy() / 100)
        simulado = E.prever(cal, estado, hist.iloc[-1][E.NIVEIS].to_numpy(dtype=float),
                            exogenos, horizonte, self.replicas, semente=origem)
        return simulado.mean(axis=0), simulado.var(axis=0, ddof=1)
