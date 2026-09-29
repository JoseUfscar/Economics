"""
Modelos de referência para as taxas de crescimento, todos estimados por
mínimos quadrados e escritos como VAR(1), y_t = c + Phi y_{t-1} + e_t:

  - média: Phi = 0 (passeio aleatório com deriva no nível);
  - AR(1): Phi diagonal, uma regressão por variável;
  - VAR(1): Phi completo.

No espaço de estados o estado é o próprio y_t (Z = I, H = 0), conhecido no
fim da amostra. A média e o AR(1) são univariados: cada série usa só os
trimestres que tem (o desemprego da PNAD começa em 2012), com as lacunas no
começo da amostra.
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))   # macroeconomia/
import caminhos  # noqa: E402,F401

from espaco_estados import ModeloLinear  # noqa: E402


def _modelo(c, Phi, Sigma):
    k = len(c)
    return ModeloLinear(c=c, T=Phi, Q=Sigma, d=np.zeros(k), Z=np.eye(k), H=np.zeros((k, k)))


def media(y: np.ndarray) -> ModeloLinear:
    k = y.shape[1]
    return _modelo(np.nanmean(y, axis=0), np.zeros((k, k)), np.diag(np.nanvar(y, axis=0, ddof=1)))


def ar1(y: np.ndarray) -> ModeloLinear:
    k = y.shape[1]
    c, phi, s2 = np.empty(k), np.empty(k), np.empty(k)
    for j in range(k):
        serie = y[~np.isnan(y[:, j]), j]
        n = serie.size
        X = np.column_stack([np.ones(n - 1), serie[:-1]])
        coef, *_ = np.linalg.lstsq(X, serie[1:], rcond=None)
        residuo = serie[1:] - X @ coef
        c[j], phi[j], s2[j] = coef[0], coef[1], residuo @ residuo / (n - 1 - 2)
    return _modelo(c, np.diag(phi), np.diag(s2))


def var1(y: np.ndarray) -> ModeloLinear:
    n, k = y.shape
    X = np.column_stack([np.ones(n - 1), y[:-1]])
    coef, *_ = np.linalg.lstsq(X, y[1:], rcond=None)   # (1 + k, k)
    residuo = y[1:] - X @ coef
    Sigma = residuo.T @ residuo / (n - 1 - (1 + k))
    return _modelo(coef[0], coef[1:].T, Sigma)


def estado_final(y: np.ndarray):
    """O estado de um VAR(1) no fim da amostra é a última observação, sem incerteza."""
    return y[-1].copy(), np.zeros((y.shape[1], y.shape[1]))
