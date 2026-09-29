"""
O ABM sem leiloeiro (descentralizada.py) no protocolo de previsão fora da
amostra (../protocolo.py), com o desenho do ABM com leiloeiro
(../abm1_com_leiloeiro/previsao_abm.py). Em cada origem T, só com informação disponível em T:

  1. calibração: a mesma de previsao_abm (dados anuais até T - 2, PNAD até T,
     tendência igual ao crescimento médio do PIB até T), com os
     desempregados fora da produção (descentralizada.referencia);
  2. aquecimento: 100 anos sem choques agregados a partir da referência
     walrasiana, para que firmas, margens, estoques, capital e crenças
     cheguem ao regime do próprio ABM (o mesmo descarte da análise de longo
     prazo em experimentos_mercados.py);
  3. história: o ABM percorre 1996-T reproduzindo o PIB (pelo crescimento da
     produtividade), o gasto do governo e, desde 2012, a taxa de desemprego
     dessazonalizada da PNAD (pela probabilidade de separação do trimestre);
  4. choques: AR(1) do crescimento da produtividade, do crescimento do gasto
     e do desvio da separação em relação à da PNAD (este só desde 2012), com
     resíduos correlacionados;
  5. previsão: `replicas` simulações de T+1 a T+h a partir do estado em T,
     com choques em pares antitéticos; a previsão é a média das réplicas, e
     a incerteza, a variância entre elas.

Prevê o crescimento acumulado de PIB, consumo das famílias, FBCF e consumo
do governo e a variação da taxa de desemprego, em p.p.
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))   # macroeconomia/
import caminhos  # noqa: E402,F401

import previsao_abm  # noqa: E402
import descentralizada as DC  # noqa: E402
import economia as E  # noqa: E402
import protocolo  # noqa: E402
from calibracao_renda import carregar_pnad  # noqa: E402

AQUECIMENTO = 400        # trimestres
REPLICAS = 200
SEPARACAO_MINIMA = 0.05  # fração da separação da PNAD, piso para o log do desvio
PERSISTENCIA_MAXIMA = 0.95
VARIANTES = {f"abm2_{chave}": (f"ABM 2: {nome}", fabrica)
             for chave, (nome, fabrica) in previsao_abm.REGRAS.items()}
AGREGADOS = ["y", "C", "I", "G"]


def economia_na_origem(anuais: pd.DataFrame, pnad, amostra: pd.DataFrame, origem: int,
                       comp: DC.Comportamento = DC.Comportamento()) -> DC.Economia:
    par, renda, alvos = previsao_abm.parametros_na_origem(anuais, pnad, amostra, origem)
    cal = DC.referencia(par, renda, alvos.capital_produto, alvos.gasto_pib)
    return DC.Economia(cal, comp, DC.Fluxos.da_renda(renda, comp.rodadas_busca))


def historia(eco: DC.Economia, dados: pd.DataFrame, crencas, N: int = E.N_PADRAO, semente: int = 0,
             aquecimento: int = AQUECIMENTO) -> tuple[DC.Estado, pd.DataFrame]:
    """
    Aquecimento e depois os trimestres de `dados` (colunas pib e governo, em %,
    e taxa_desemprego, em %, vazia antes da PNAD). Devolve o estado no último
    trimestre e o registro de cada trimestre da história.
    """
    rng = np.random.default_rng(semente)
    estado = DC.estado_inicial(eco, crencas, N, rng)
    estado, _ = DC.simular(eco, estado, rng, aquecimento)
    linhas = []
    for pib, gasto, taxa in dados[["pib", "governo", protocolo.TAXA_DESEMPREGO]].to_numpy():
        estado, registro = DC.trimestre(eco, estado, rng, crescimento_pib=pib / 100,
                                        crescimento_gasto=gasto / 100,
                                        desemprego_alvo=None if np.isnan(taxa) else taxa / 100)
        linhas.append(registro)
    return estado, pd.DataFrame(linhas, index=dados.index)


def desvio_separacao(hist: pd.DataFrame, dados: pd.DataFrame, eco: DC.Economia) -> np.ndarray:
    """log da separação sobre a da PNAD nos trimestres com alvo de desemprego; vazio nos outros."""
    base = eco.fluxos.separacao
    desvio = np.log(np.maximum(hist.probabilidade_separacao.to_numpy(), SEPARACAO_MINIMA * base) / base)
    return np.where(dados[protocolo.TAXA_DESEMPREGO].notna().to_numpy(), desvio, np.nan)


def exogenos(eco: DC.Economia, hist: pd.DataFrame, dados: pd.DataFrame) -> E.Exogenos:
    x = np.column_stack([hist.log_gamma.to_numpy(), dados.governo.to_numpy() / 100,
                         desvio_separacao(hist, dados, eco)])
    return E.Exogenos.de_series(x, limite_phi=PERSISTENCIA_MAXIMA)


def _niveis(registro: dict) -> np.ndarray:
    """Logs dos níveis de PIB, consumo, FBCF e gasto e a taxa de desemprego."""
    logs = [np.log(max(registro[v], 1e-6)) + registro["log_X"] for v in AGREGADOS]
    return np.array(logs + [registro["desemprego"]])


def prever(eco: DC.Economia, estado: DC.Estado, origem: dict, choques: E.Exogenos, horizonte: int,
           replicas: int, semente: int) -> np.ndarray:
    """
    Crescimento acumulado (em %) de PIB, consumo, FBCF e gasto e variação do
    desemprego (em p.p.) de T+1 a T+h em cada réplica, a partir do estado e
    do registro de T: matriz (replicas, horizonte, 5).
    """
    rng = np.random.default_rng(semente)
    base = _niveis(origem)
    separacao = eco.fluxos.separacao
    saida = np.empty((replicas, horizonte, 5))
    padronizados = None
    for k in range(replicas):
        e = copy.deepcopy(estado)
        padronizados = (rng.standard_normal((horizonte, choques.c.size)) if k % 2 == 0
                        else -padronizados)
        caminho = choques.simular(horizonte, choques=padronizados)
        for t in range(horizonte):
            log_gamma, crescimento_gasto, desvio = caminho[t]
            e, registro = DC.trimestre(eco, e, rng, log_gamma=log_gamma, crescimento_gasto=crescimento_gasto,
                                       separacao=min(separacao * np.exp(desvio), 0.5))
            saida[k, t] = 100 * (_niveis(registro) - base)
    return saida


class ModeloDescentralizado:
    variaveis = protocolo.VARIAVEIS

    def __init__(self, anuais: pd.DataFrame, chave: str, pnad=None, N: int = E.N_PADRAO,
                 replicas: int = REPLICAS, aquecimento: int = AQUECIMENTO, cache: dict | None = None):
        self.nome, self.fabrica = VARIANTES[chave]
        self.anuais = anuais
        self.pnad = carregar_pnad() if pnad is None else pnad
        self.N, self.replicas, self.aquecimento = N, replicas, aquecimento
        self.cache = {} if cache is None else cache   # economia calibrada por origem, partilhável
        self.historias = {}

    def prever(self, amostra: pd.DataFrame, origem: int, horizonte: int):
        if origem not in self.cache:
            self.cache[origem] = economia_na_origem(self.anuais, self.pnad, amostra, origem)
        eco = self.cache[origem]
        estado, hist = historia(eco, amostra, self.fabrica(), self.N, semente=0,
                                aquecimento=self.aquecimento)
        self.historias[origem] = hist
        simulado = prever(eco, estado, hist.iloc[-1].to_dict(), exogenos(eco, hist, amostra),
                          horizonte, self.replicas, semente=origem)
        return simulado.mean(axis=0), simulado.var(axis=0, ddof=1)
