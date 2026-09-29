"""
Economia baseada em agentes: N famílias heterogêneas, firma competitiva e
governo, em trimestres.

Em cada trimestre t:
  1. a riqueza poupada no trimestre anterior vira riqueza por membro em
     unidades de A_t: a = s / (Gamma_t e^{n D}), com Gamma_t o crescimento da
     produtividade do trabalho;
  2. cada família sorteia o novo estado de renda pela cadeia de Markov;
  3. o leiloeiro fixa os preços que zeram os mercados de fatores:
     K = média de a, L = média de z, y = K^alpha L^(1 - alpha),
     r = (1 - tau_k)(alpha y / K - delta), w = (1 - alpha) y / L;
  4. o governo gasta G, cobra tau_k e tau_w e devolve o saldo como
     transferência, igual para todos ou com pesos por estado;
  5. cada família atualiza as crenças (expectativas.py) e escolhe o consumo
     com a política ótima para essas crenças (familias.TabelaPoliticas);
  6. o que sobra é poupado; I = y - C - G.

Nada de equilíbrio é imposto ao longo do caminho: os agregados são somas de
decisões individuais. Os únicos preços de mercado são os do leiloeiro.

Para seguir a história, `historia` escolhe Gamma_t para que o crescimento do
PIB do ABM seja o dos dados e alimenta o gasto com o crescimento observado do
consumo do governo. Consumo e FBCF saem do modelo.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, replace

import numpy as np
import pandas as pd

import familias as F

N_PADRAO = 20_000


@dataclass
class Calibrada:
    """Tudo o que o ABM precisa: equilíbrio estacionário, pesos das transferências e tabela."""

    est: F.Estacionario
    pesos: np.ndarray
    tabela: F.TabelaPoliticas

    @property
    def par(self) -> F.Parametros:
        return self.est.par

    @property
    def renda(self) -> F.Renda:
        return self.est.renda


def preparar(est: F.Estacionario, grades: F.Grades = F.Grades(),
             lacunas: np.ndarray = F.LACUNAS) -> Calibrada:
    renda, par = est.renda, est.par
    pesos = np.ones(renda.estados) if est.pesos is None else np.asarray(est.pesos, float)
    pesos = pesos / (renda.pi @ pesos)
    if est.reforma is None:
        perfil = (1 - par.tau_w) * renda.z + (est.transferencia / est.w) * pesos
    else:   # só a receita do aumento de tau_k segue os pesos (familias.rendas)
        perfil = (1 - par.tau_w) * renda.z + (est.transferencia - est.reforma + est.reforma * pesos) / est.w
    tabela = F.TabelaPoliticas(par, renda, perfil, grades, lacunas, r_exatos=(est.r,))
    return Calibrada(est, pesos, tabela)


@dataclass
class Estado:
    s: np.ndarray          # poupança do trimestre anterior, em unidades de A_{t-1} por membro
    j: np.ndarray          # estado de renda do trimestre anterior
    y: float               # produto por unidade de eficiência no trimestre anterior
    G: float               # gasto por unidade de eficiência no trimestre anterior
    crencas: object        # regra de expectativas, com o seu estado
    log_X: float = 0.0     # log da eficiência total A L
    c: np.ndarray | None = None   # consumo de cada família no trimestre anterior


def contagens(pi: np.ndarray, N: int) -> np.ndarray:
    """Número de famílias em cada estado, proporcional a pi (maiores restos)."""
    bruto = N * np.asarray(pi, dtype=float)
    n = np.floor(bruto).astype(int)
    n[np.argsort(n - bruto)[:N - n.sum()]] += 1
    return n


def estado_inicial(cal: Calibrada, crencas, N: int, rng) -> Estado:
    """
    Famílias tiradas da distribuição estacionária de forma estratificada: o
    número exato de famílias em cada estado de renda e, dentro de cada um, a
    riqueza por quantis estratificados. Um sorteio simples erraria a oferta de
    trabalho em cerca de 1% com 20 mil famílias (o tipo de maior renda tem
    produtividade 4 vezes a média), e o governo começaria com um déficit que
    não existe no modelo.
    """
    dist = cal.est.distribuicao
    n = contagens(cal.renda.pi, N)
    j = np.repeat(np.arange(cal.renda.estados), n)
    a = np.empty(N)
    inicio = 0
    for estado, k in enumerate(n):
        acumulada = np.cumsum(dist.massa[:, estado])
        acumulada /= acumulada[-1]
        quantis = (np.arange(k) + rng.random(k)) / k
        a[inicio:inicio + k] = dist.grade_a[np.minimum(np.searchsorted(acumulada, quantis),
                                                       len(acumulada) - 1)]
        inicio += k
    ordem = rng.permutation(N)
    a, j = a[ordem], j[ordem]
    crencas.iniciar(N, cal.est.r, cal.est.w, rng)
    # s tal que, com crescimento de tendência, a riqueza deste trimestre seja a.
    return Estado(s=a / cal.par.fator_crescimento, j=j, y=cal.est.y, G=cal.par.gasto,
                  crencas=crencas)


def _sortear_estados(j, P_acumulada, rng):
    u = rng.random(j.size)
    return np.minimum((u[:, None] > P_acumulada[j]).sum(axis=1), P_acumulada.shape[1] - 1)


def passo(cal: Calibrada, estado: Estado, rng, log_gamma: float | None = None,
          crescimento_pib: float | None = None, crescimento_gasto: float | None = None,
          gasto: float | None = None, politica: F.Politica | None = None) -> tuple[Estado, dict]:
    """
    Um trimestre. Informe log_gamma (crescimento da produtividade) ou
    crescimento_pib (Delta log do PIB a reproduzir); e crescimento_gasto
    (Delta log de G) ou o nível do gasto por unidade de eficiência. Com
    `politica`, as famílias seguem essa política (previsão perfeita de uma
    transição, transicao.py) em vez de formar crenças.
    """
    par, renda = cal.par, cal.renda
    D, alpha = par.periodo, par.alpha
    j = _sortear_estados(estado.j, np.cumsum(renda.P, axis=1), rng)
    z = renda.z[j]
    trabalho = z.mean()
    poupanca = estado.s.mean()
    if crescimento_pib is not None:
        log_gamma = (crescimento_pib - alpha * np.log(poupanca) + np.log(estado.y)
                     - (1 - alpha) * (par.n * D + np.log(trabalho))) / (1 - alpha)
    fator = np.exp(-log_gamma - par.n * D)
    a = estado.s * fator
    if gasto is None:
        gasto = estado.G * np.exp(crescimento_gasto) * fator
    K = poupanca * fator
    R, w, y = F.precos(par, K, trabalho)
    r = (1 - par.tau_k) * (R - par.delta)
    receita = par.tau_k * (R - par.delta) * K + par.tau_w * w * trabalho
    transferencia = receita - gasto
    pesos = cal.pesos[j]
    T = transferencia * pesos / pesos.mean()
    m = (1 + r * D) * a + D * ((1 - par.tau_w) * w * z + T)
    if politica is None:
        r_e, w_e = estado.crencas.atualizar(r, w, rng)
        c = cal.tabela.consumo(m, j, r_e, w_e)
    else:
        r_e, w_e = politica.r, w
        c = politica.consumo(m, j)
    c = np.clip(c, 1e-9, m / D)
    s = m - D * c
    C = c.mean()
    log_X = estado.log_X + log_gamma + par.n * D
    registro = {"y": y, "C": C, "I": y - C - gasto, "G": gasto, "K": K, "r": r, "w": w,
                "transferencia": transferencia, "log_gamma": log_gamma, "log_X": log_X,
                "trabalho": trabalho, "r_e": float(np.mean(r_e)), "w_e": float(np.mean(w_e))}
    fracoes = getattr(estado.crencas, "fracoes", None)
    if fracoes is not None:
        for regra, f in zip(estado.crencas.regras, fracoes):
            registro[f"fracao_{regra.nome}"] = f
    return Estado(s, j, y, gasto, estado.crencas, log_X, c), registro


def _com_logs(tabela: pd.DataFrame) -> pd.DataFrame:
    """Logs dos níveis (por unidade de eficiência vezes A L) de Y, C, I e G."""
    return tabela.assign(**{f"log_{v}": np.log(np.maximum(tabela[v], 1e-6)) + tabela.log_X
                            for v in ("y", "C", "I", "G")})


def historia(cal: Calibrada, crescimento: pd.DataFrame, crencas, N: int = N_PADRAO,
             semente: int = 0) -> tuple[Estado, pd.DataFrame]:
    """
    Percorre os trimestres de `crescimento` (em %, como protocolo.carregar_crescimento)
    reproduzindo o PIB e o gasto observados. O primeiro trimestre dos dados é o
    seguinte ao ponto de partida, o equilíbrio estacionário.
    """
    rng = np.random.default_rng(semente)
    estado = estado_inicial(cal, crencas, N, rng)
    estado, registro = passo(cal, estado, rng, log_gamma=cal.par.g * cal.par.periodo,
                             gasto=cal.par.gasto)
    linhas = [registro]
    for pib, gasto in zip(crescimento.pib.to_numpy() / 100, crescimento.governo.to_numpy() / 100):
        estado, registro = passo(cal, estado, rng, crescimento_pib=pib, crescimento_gasto=gasto)
        linhas.append(registro)
    indice = [None] + list(crescimento.index)
    return estado, _com_logs(pd.DataFrame(linhas, index=indice))


@dataclass
class Exogenos:
    """VAR(1) diagonal de (log Gamma, Delta log G) com resíduos correlacionados."""

    c: np.ndarray
    phi: np.ndarray
    L: np.ndarray    # fator de Cholesky da covariância dos resíduos
    ultimo: np.ndarray

    @staticmethod
    def estimar(log_gamma: np.ndarray, crescimento_gasto: np.ndarray) -> "Exogenos":
        return Exogenos.de_series(np.column_stack([log_gamma, crescimento_gasto]))

    @staticmethod
    def de_series(x: np.ndarray, limite_phi: float | None = None) -> "Exogenos":
        """
        AR(1) de cada coluna de x com os trimestres que ela tem (as lacunas só
        podem estar no começo) e covariância dos resíduos nos trimestres em que
        todas têm dados. `limite_phi` limita a persistência de amostras curtas.
        """
        n, k = x.shape
        c, phi = np.empty(k), np.empty(k)
        residuos = np.full((n - 1, k), np.nan)
        for j in range(k):
            ok = ~np.isnan(x[:-1, j]) & ~np.isnan(x[1:, j])
            X = np.column_stack([np.ones(ok.sum()), x[:-1, j][ok]])
            coef, *_ = np.linalg.lstsq(X, x[1:, j][ok], rcond=None)
            c[j], phi[j] = coef
            if limite_phi is not None and abs(phi[j]) > limite_phi:
                phi[j] = np.sign(phi[j]) * limite_phi
                c[j] = np.mean(x[1:, j][ok] - phi[j] * x[:-1, j][ok])
            residuos[ok, j] = x[1:, j][ok] - X @ np.array([c[j], phi[j]])
        comum = residuos[~np.isnan(residuos).any(axis=1)]
        Sigma = comum.T @ comum / (len(comum) - 2)
        return Exogenos(c, phi, np.linalg.cholesky(Sigma), x[-1].copy())

    def simular(self, passos: int, rng=None, choques: np.ndarray | None = None) -> np.ndarray:
        """Trajetória de `passos` trimestres; `choques` (passos, k) padronizados, se dados."""
        k = self.c.size
        choques = rng.standard_normal((passos, k)) if choques is None else choques
        x, saida = self.ultimo.copy(), np.empty((passos, k))
        for t in range(passos):
            x = self.c + self.phi * x + self.L @ choques[t]
            saida[t] = x
        return saida


NIVEIS = ["log_y", "log_C", "log_I", "log_G"]


def prever(cal: Calibrada, estado: Estado, niveis_origem: np.ndarray, exogenos: Exogenos,
           horizonte: int, replicas: int, semente: int) -> np.ndarray:
    """
    Crescimento acumulado (em %) de PIB, consumo, FBCF e gasto de T+1 a T+h
    em cada réplica, a partir do estado e dos logs dos níveis na origem:
    matriz (replicas, horizonte, 4). Os choques agregados vêm em pares
    antitéticos (e, -e), o que reduz o ruído de simulação da média.
    """
    rng = np.random.default_rng(semente)
    saida = np.empty((replicas, horizonte, 4))
    padronizados = None
    for k in range(replicas):
        e = replace(estado, s=estado.s.copy(), j=estado.j.copy(),
                    crencas=copy.deepcopy(estado.crencas))
        padronizados = rng.standard_normal((horizonte, 2)) if k % 2 == 0 else -padronizados
        choques = exogenos.simular(horizonte, choques=padronizados)
        linhas = []
        for t in range(horizonte):
            e, registro = passo(cal, e, rng, log_gamma=choques[t, 0], crescimento_gasto=choques[t, 1])
            linhas.append(registro)
        saida[k] = 100 * (_com_logs(pd.DataFrame(linhas))[NIVEIS].to_numpy() - niveis_origem)
    return saida
