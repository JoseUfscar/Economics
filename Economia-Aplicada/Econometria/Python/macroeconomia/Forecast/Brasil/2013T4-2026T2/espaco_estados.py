"""
Modelos lineares gaussianos em espaço de estados, comuns a todos os modelos
comparados (o de equilíbrio geral e as referências estatísticas):

    estado:     xi_{t+1} = c + T xi_t + eta_{t+1},   eta ~ N(0, Q)
    observação: y_t      = d + Z xi_t + eps_t,       eps ~ N(0, H)

O filtro de Kalman dá a verossimilhança e a distribuição do estado no fim da
amostra; a partir dela, `prever_acumulado` calcula média e variância da soma
das observações nos h trimestres seguintes (o crescimento acumulado, quando
as observações são taxas de crescimento).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.linalg import cho_factor, cho_solve, solve_discrete_lyapunov


@dataclass(frozen=True)
class ModeloLinear:
    c: np.ndarray
    T: np.ndarray
    Q: np.ndarray
    d: np.ndarray
    Z: np.ndarray
    H: np.ndarray

    @property
    def media_estacionaria(self) -> np.ndarray:
        return np.linalg.solve(np.eye(self.T.shape[0]) - self.T, self.c)

    @property
    def cov_estacionaria(self) -> np.ndarray:
        if np.max(np.abs(np.linalg.eigvals(self.T))) >= 1:
            raise ValueError("o estado não é estacionário")
        return solve_discrete_lyapunov(self.T, self.Q)


@dataclass(frozen=True)
class Filtrado:
    log_verossimilhanca: float
    media: np.ndarray      # E[xi_T | y_1..y_T]
    cov: np.ndarray        # Var[xi_T | y_1..y_T]


def filtrar(modelo: ModeloLinear, y: np.ndarray, media0: np.ndarray | None = None,
            cov0: np.ndarray | None = None) -> Filtrado:
    """
    Filtro de Kalman com y de dimensão (n, k). Sem condição inicial dada, o
    estado parte da distribuição estacionária. Observações faltantes (NaN)
    ficam fora da atualização e da verossimilhança daquele trimestre.
    """
    a = modelo.media_estacionaria if media0 is None else media0
    P = modelo.cov_estacionaria if cov0 is None else cov0
    total = 0.0
    for obs in y:
        visto = ~np.isnan(obs)
        if not visto.any():
            a_f, P_f = a, P
        else:
            Z, d = modelo.Z[visto], modelo.d[visto]
            H = modelo.H[np.ix_(visto, visto)]
            v = obs[visto] - d - Z @ a
            F = Z @ P @ Z.T + H
            fator = cho_factor(F)
            total -= 0.5 * (2 * np.sum(np.log(np.diag(fator[0]))) + v @ cho_solve(fator, v)
                            + visto.sum() * np.log(2 * np.pi))
            ganho = cho_solve(fator, Z @ P).T          # P Z' F^-1
            a_f = a + ganho @ v
            P_f = P - ganho @ Z @ P
            P_f = (P_f + P_f.T) / 2
        a = modelo.c + modelo.T @ a_f
        P = modelo.T @ P_f @ modelo.T.T + modelo.Q
    return Filtrado(float(total), a_f, P_f)


def prever_acumulado(modelo: ModeloLinear, media: np.ndarray, cov: np.ndarray,
                     horizonte: int) -> tuple[np.ndarray, np.ndarray]:
    """
    Média e variância de S_h = y_{T+1} + ... + y_{T+h}, h = 1..horizonte,
    dado xi_T ~ N(media, cov). Devolve duas matrizes (horizonte, k).

    Empilha (xi, S): xi' = c + T xi + eta e S' = S + d + Z xi' + eps, que é
    linear, então média e covariância seguem exatamente.
    """
    n, k = modelo.T.shape[0], modelo.Z.shape[0]
    Z, T, Q = modelo.Z, modelo.T, modelo.Q
    M = np.block([[T, np.zeros((n, k))], [Z @ T, np.eye(k)]])
    constante = np.concatenate([modelo.c, modelo.d + Z @ modelo.c])
    ruido = np.block([[Q, Q @ Z.T], [Z @ Q, Z @ Q @ Z.T + modelo.H]])
    m = np.concatenate([media, np.zeros(k)])
    V = np.zeros((n + k, n + k))
    V[:n, :n] = cov
    medias, variancias = np.empty((horizonte, k)), np.empty((horizonte, k))
    for h in range(horizonte):
        m = constante + M @ m
        V = M @ V @ M.T + ruido
        medias[h], variancias[h] = m[n:], np.diag(V)[n:]
    return medias, variancias


def simular(modelo: ModeloLinear, n: int, rng, media0=None, cov0=None) -> np.ndarray:
    """Amostra de n observações, com o estado inicial sorteado."""
    a = modelo.media_estacionaria if media0 is None else media0
    P = modelo.cov_estacionaria if cov0 is None else cov0
    xi = rng.multivariate_normal(a, P, method="eigh")
    k, dim = modelo.Z.shape
    y = np.empty((n, k))
    for t in range(n):
        y[t] = modelo.d + modelo.Z @ xi + rng.multivariate_normal(np.zeros(k), modelo.H, method="eigh")
        xi = modelo.c + modelo.T @ xi + rng.multivariate_normal(np.zeros(dim), modelo.Q, method="eigh")
    return y
