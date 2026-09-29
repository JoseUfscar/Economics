"""
Transição com previsão perfeita no ABM: o benchmark de expectativas
racionais para uma mudança de política sem risco agregado.

As famílias conhecem o caminho inteiro de juros, salários e transferências
depois da mudança, e esse caminho é o que as próprias decisões produzem. É o
análogo, em tempo discreto e com N famílias, de aiyagari.transicao:

  1. dado um caminho para o capital, os preços de cada trimestre saem da firma
     e do orçamento do governo;
  2. a política de cada trimestre sai da grade endógena de trás para frente,
     partindo da política do novo estado estacionário;
  3. as N famílias seguem essas políticas a partir da distribuição inicial,
     com sorteios de renda fixos, e o capital que elas acumulam é o novo
     caminho;
  4. o caminho é atualizado com relaxamento até que as duas coisas coincidam.

Com os sorteios fixos, o ponto fixo é exato para a economia de N famílias:
simulá-la de novo com as políticas encontradas reproduz o mesmo caminho.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

import economia as E
import expectativas as X
import familias as F


@dataclass
class PrevisaoPerfeita:
    K: np.ndarray                  # capital em cada trimestre
    politicas: list                # política de cada trimestre
    agregados: pd.DataFrame
    bem_estar: np.ndarray          # utilidade descontada de cada família
    tipo_inicial: np.ndarray
    iteracoes: int


def _politicas(cal: E.Calibrada, K: np.ndarray, gasto: float, grades: F.Grades) -> list:
    par, renda = cal.par, cal.renda
    T = len(K)
    politicas = [None] * T
    proxima = cal.est.politica
    grade_s = grades.poupanca(cal.est.w)
    for t in range(T - 1, -1, -1):
        R, w, y = F.precos(par, K[t])
        r = (1 - par.tau_k) * (R - par.delta)
        transferencia = par.tau_k * (R - par.delta) * K[t] + par.tau_w * w - gasto
        rendas = (1 - par.tau_w) * w * renda.z + transferencia * cal.pesos
        politicas[t] = proxima = F.politica_anterior(par, renda, proxima, r, rendas, grade_s)
    return politicas


def _simular(cal_inicial, cal, politicas, N, semente, gasto):
    rng = np.random.default_rng(semente)
    estado = E.estado_inicial(cal_inicial, X.Equilibrio(), N, rng)
    tipo = cal.renda.tipo[estado.j]
    par = cal.par
    D = par.periodo
    desconto = np.exp(-(par.rho - par.n - (1 - par.theta) * par.g) * D)
    bem_estar, peso, linhas = np.zeros(N), 1.0, []
    for politica in politicas:
        estado, registro = E.passo(cal, estado, rng, log_gamma=par.g * D, gasto=gasto,
                                   politica=politica)
        bem_estar += peso * D * estado.c ** (1 - par.theta) / (1 - par.theta)
        peso *= desconto
        linhas.append(registro)
    return pd.DataFrame(linhas), bem_estar, tipo


def previsao_perfeita(cal_inicial: E.Calibrada, cal: E.Calibrada, trimestres: int, N: int,
                      semente: int, relaxamento: float = 0.1, tol: float = 1e-5,
                      max_iter: int = 400, grades: F.Grades = F.Grades()) -> PrevisaoPerfeita:
    """
    Parte do equilíbrio de `cal_inicial` com a política de `cal`, vigente desde
    t = 0. Como em aiyagari.transicao, a oferta de capital reage muito aos
    juros futuros e a atualização precisa de relaxamento pequeno (com 0,3 ela
    diverge).
    """
    gasto = cal_inicial.par.gasto
    t = np.arange(trimestres)
    estado = E.estado_inicial(cal_inicial, X.Equilibrio(), N, np.random.default_rng(semente))
    K0 = estado.s.mean() * cal_inicial.par.fator_crescimento   # o das famílias sorteadas
    K1 = cal.est.K
    K = K1 + (K0 - K1) * np.exp(-0.015 * t)   # chute: meia-vida de uns 11 anos
    for iteracao in range(1, max_iter + 1):
        politicas = _politicas(cal, K, gasto, grades)
        agregados, bem_estar, tipo = _simular(cal_inicial, cal, politicas, N, semente, gasto)
        K_novo = agregados.K.to_numpy()
        erro = np.max(np.abs(K_novo / K - 1))
        if erro < tol:
            return PrevisaoPerfeita(K_novo, politicas, agregados, bem_estar, tipo, iteracao)
        K = (1 - relaxamento) * K + relaxamento * K_novo
    raise RuntimeError(f"a previsão perfeita não convergiu (erro {erro:.2e})")


# --- previsão perfeita para uma distribuição qualquer, pelo histograma ----------

def _loteria(grade: np.ndarray, a: np.ndarray, massa: np.ndarray) -> np.ndarray:
    """Distribui a massa de cada riqueza `a` entre os dois nós vizinhos da grade."""
    A = len(grade)
    a = np.clip(a, grade[0], grade[-1])
    acima = np.clip(np.searchsorted(grade, a, side="right"), 1, A - 1)
    peso = (a - grade[acima - 1]) / (grade[acima] - grade[acima - 1])
    return (np.bincount(acima - 1, (1 - peso) * massa, A) + np.bincount(acima, peso * massa, A))


def grade_para(cal: E.Calibrada, estado: E.Estado, pontos: int = 700) -> np.ndarray:
    """Grade de riqueza que cobre a população (a riqueza pode passar da grade do equilíbrio)."""
    a_max = max(F.Grades().s_max * cal.est.w, 1.5 * float(estado.s.max()))
    return F.grade_potencia(a_max, pontos, 2.0)


def histograma(cal: E.Calibrada, estado: E.Estado, grade: np.ndarray) -> np.ndarray:
    """
    Massa (A, J) das famílias de `estado` no início do trimestre seguinte,
    depois do sorteio de renda: a riqueza a = s e^{-(g + n) D} de cada família
    vai para os nós vizinhos, e o estado de renda muda pela cadeia de Markov.
    """
    renda = cal.renda
    a = estado.s * cal.par.fator_crescimento
    origem = np.column_stack([_loteria(grade, a[estado.j == j], np.full(np.sum(estado.j == j), 1.0))
                              for j in range(renda.estados)]) / estado.s.size
    return origem @ renda.P


def avancar(cal: E.Calibrada, politica: F.Politica, grade: np.ndarray, massa: np.ndarray) -> np.ndarray:
    """Um trimestre do histograma com a política (e o juro e as rendas guardados nela)."""
    par, renda = cal.par, cal.renda
    D = par.periodo
    saida = np.zeros_like(massa)
    for j in range(renda.estados):
        m = (1 + politica.r * D) * grade + D * politica.renda[j]
        c = np.clip(F.interpolar(m, politica.m[j], politica.c[j]), 1e-9, m / D)
        destino = _loteria(grade, (m - D * c) * par.fator_crescimento, massa[:, j])
        saida += destino[:, None] * renda.P[j]
    return saida


@dataclass
class CaminhoPerfeito:
    K: np.ndarray
    politicas: list
    iteracoes: int


def previsao_perfeita_histograma(cal: E.Calibrada, massa: np.ndarray, grade: np.ndarray,
                                 trimestres: int, relaxamento: float = 0.1, tol: float = 1e-6,
                                 max_iter: int = 2000, chute: np.ndarray | None = None,
                                 grades: F.Grades = F.Grades()) -> CaminhoPerfeito:
    """
    Previsão perfeita a partir de uma distribuição qualquer (massa na grade),
    com um contínuo de famílias: o caminho do capital cujas políticas, de trás
    para frente a partir da política estacionária, levam o histograma a esse
    mesmo caminho. Sem ruído de amostragem, cada iteração custa uma fração da
    simulação das famílias, e o ponto fixo pode ser apertado.
    """
    gasto = cal.par.gasto
    K0 = float(grade @ massa.sum(axis=1))
    if chute is None:
        K = cal.est.K + (K0 - cal.est.K) * np.exp(-0.015 * np.arange(trimestres))
    else:
        K = np.asarray(chute, dtype=float).copy()
        K[0] = K0
    for iteracao in range(1, max_iter + 1):
        politicas = _politicas(cal, K, gasto, grades)
        K_novo, m = np.empty(trimestres), massa
        for t in range(trimestres):
            K_novo[t] = grade @ m.sum(axis=1)
            m = avancar(cal, politicas[t], grade, m)
        erro = np.max(np.abs(K_novo / K - 1))
        if erro < tol:
            return CaminhoPerfeito(K_novo, politicas, iteracao)
        K = (1 - relaxamento) * K + relaxamento * K_novo
    raise RuntimeError(f"a previsão perfeita não convergiu (erro {erro:.2e})")
