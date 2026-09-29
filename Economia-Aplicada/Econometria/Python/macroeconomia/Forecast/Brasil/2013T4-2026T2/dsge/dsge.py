"""
Versão estocástica do modelo de Ramsey com governo
(Politicas/Lei-15270/equilibrio_geral/modelo.py)
para previsão trimestral.

A economia é a mesma, em tempo discreto com período de `periodo` anos
(0,25 = trimestre), mais três choques:

  - tendência: o crescimento da produtividade do trabalho, log Gamma_t =
    g * periodo + u_t, com u_t AR(1). É o choque permanente de Aguiar e
    Gopinath (2007), importante em economias emergentes;
  - produtividade transitória: Y = e^{z_t} K^alpha (A L)^(1 - alpha), z_t AR(1);
  - gasto do governo: G/(AL) = gasto * e^{s_t}, s_t AR(1).

Os fluxos (Y, C, I, G) são taxas anuais, como no modelo contínuo:

    K_{t+1} = K_t + periodo (Y_t - C_t - G_t - delta K_t)
    x_t^-theta = e^{-rho periodo} E_t[x_{t+1}^-theta (1 + periodo (1 - tau_k)(R_{t+1} - delta))]

com x = C/L. Quando periodo -> 0, o estado estacionário e a velocidade de
convergência tendem aos de modelo.py (ver test_dsge.py).

O modelo é linearizado em logaritmos em torno do crescimento balanceado e
resolvido pelo método de Klein (2000). As observações são as taxas de
crescimento trimestrais, em %, de PIB, consumo das famílias, FBCF e consumo
do governo, cada uma com erro de medida independente. Os parâmetros
estruturais vêm da calibração anual (equilibrio_geral/calibracao.py, na
pasta da Lei 15.270); os dos
choques e dos erros de medida são estimados por máxima verossimilhança.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy.linalg import ordqz
from scipy.optimize import minimize

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))   # macroeconomia/
import caminhos  # noqa: E402,F401

from espaco_estados import ModeloLinear, filtrar  # noqa: E402

OBSERVAVEIS = ("pib", "consumo", "investimento", "governo")
NOMES_CHOQUES = ("rho_u", "sigma_u", "rho_z", "sigma_z", "rho_s", "sigma_s")
RHO_MAX = 0.995


@dataclass(frozen=True)
class Estrutura:
    """Parâmetros estruturais em frequência anual, como em modelo.Economia."""

    alpha: float
    delta: float
    rho: float
    theta: float
    n: float
    g: float
    tau_k: float
    gasto_pib: float
    periodo: float = 0.25


@dataclass(frozen=True)
class Choques:
    """Persistência e desvio-padrão por período dos três choques."""

    rho_u: float = 0.5
    sigma_u: float = 0.01
    rho_z: float = 0.9
    sigma_z: float = 0.01
    rho_s: float = 0.9
    sigma_s: float = 0.01

    def __post_init__(self):
        for nome in ("rho_u", "rho_z", "rho_s"):
            if not -1 < getattr(self, nome) < 1:
                raise ValueError(f"{nome} precisa estar entre -1 e 1")


@dataclass(frozen=True)
class Estacionario:
    k: float      # K / (A L)
    kappa: float  # K_t / (A_{t-1} L_{t-1}), a variável predeterminada
    y: float
    c: float
    gasto: float
    investimento: float
    r: float      # retorno líquido após impostos, taxa anual


def estado_estacionario(e: Estrutura) -> Estacionario:
    D = e.periodo
    r = (np.exp((e.rho + e.theta * e.g) * D) - 1) / D
    k = (e.alpha / (e.delta + r / (1 - e.tau_k))) ** (1 / (1 - e.alpha))
    y = k**e.alpha
    gasto = e.gasto_pib * y
    investimento = k * (e.delta + (np.exp((e.g + e.n) * D) - 1) / D)
    c = y - gasto - investimento
    if c <= 0:
        raise ValueError("consumo estacionário não positivo")
    return Estacionario(k, k * np.exp((e.g + e.n) * D), y, c, gasto, investimento, r)


def rho_para_capital_produto(e: Estrutura, capital_produto: float) -> float:
    """rho que faz o estado estacionário discreto ter K/Y = capital_produto."""
    retorno = (1 - e.tau_k) * (e.alpha / capital_produto - e.delta)
    return np.log(1 + e.periodo * retorno) / e.periodo - e.theta * e.g


def _equacoes(e: Estrutura, ee: Estacionario, ch: Choques, prox, atual):
    """Resíduos do equilíbrio em x = (log kappa, u, z, s, log c)."""
    D = e.periodo
    lkap, u, z, s, lc = atual
    lkap1, u1, z1, s1, lc1 = prox
    k = np.exp(lkap - (e.g + e.n) * D - u)
    y = np.exp(z) * k**e.alpha
    capital = k + D * (y - np.exp(lc) - ee.gasto * np.exp(s) - e.delta * k)
    k1 = np.exp(lkap1 - (e.g + e.n) * D - u1)
    retorno = 1 + D * (1 - e.tau_k) * (e.alpha * np.exp(z1) * k1 ** (e.alpha - 1) - e.delta)
    return np.array([
        1 - capital / np.exp(lkap1),
        1 - np.exp(-e.rho * D - e.theta * (e.g * D + u1) - e.theta * (lc1 - lc)) * retorno,
        u1 - ch.rho_u * u,
        z1 - ch.rho_z * z,
        s1 - ch.rho_s * s,
    ])


def _jacobianos(e, ee, ch):
    """Derivadas exatas por passo complexo no estado estacionário."""
    x0 = np.array([np.log(ee.kappa), 0.0, 0.0, 0.0, np.log(ee.c)], dtype=complex)
    passo = 1e-30
    A, B = np.empty((5, 5)), np.empty((5, 5))
    for j in range(5):
        dx = np.zeros(5, dtype=complex)
        dx[j] = 1j * passo
        A[:, j] = _equacoes(e, ee, ch, x0 + dx, x0).imag / passo
        B[:, j] = -_equacoes(e, ee, ch, x0, x0 + dx).imag / passo
    return A, B


def resolver_klein(A: np.ndarray, B: np.ndarray, n_pre: int):
    """
    Solução de A E_t[x_{t+1}] = B x_t, com as n_pre primeiras variáveis
    predeterminadas: x_pre' = P x_pre e x_salto = F x_pre (Klein, 2000).
    Exige exatamente n_pre raízes estáveis (condição de Blanchard-Kahn).
    """
    BB, AA, alfa, beta, Q, Z = ordqz(B, A, sort="iuc", output="complex")
    estaveis = int(np.sum(np.abs(alfa) < np.abs(beta)))
    if estaveis != n_pre:
        raise ValueError(f"{estaveis} raízes estáveis para {n_pre} variáveis predeterminadas: "
                         "sem solução única e estável")
    Z11, Z21 = Z[:n_pre, :n_pre], Z[n_pre:, :n_pre]
    inversa = np.linalg.inv(Z11)
    P = Z11 @ np.linalg.solve(AA[:n_pre, :n_pre], BB[:n_pre, :n_pre]) @ inversa
    F = Z21 @ inversa
    return P.real, F.real


@dataclass(frozen=True)
class Solucao:
    estrutura: Estrutura
    choques: Choques
    ee: Estacionario
    P: np.ndarray        # transição do estado (log kappa, u, z, s), em desvios
    F: np.ndarray        # log c = F x
    niveis: np.ndarray   # desvios de (log y, log c, log i, log g) = niveis @ x


def resolver(e: Estrutura, ch: Choques) -> Solucao:
    ee = estado_estacionario(e)
    A, B = _jacobianos(e, ee, ch)
    P, F = resolver_klein(A, B, 4)
    a = e.alpha
    y = np.array([a, -a, 1.0, 0.0])
    c = F[0]
    g = np.array([0.0, 0.0, 0.0, 1.0])
    i = (ee.y * y - ee.c * c - ee.gasto * g) / ee.investimento
    return Solucao(e, ch, ee, P, F, np.vstack([y, c, i, g]))


def espaco_estados(sol: Solucao, erros_medida, medias=None) -> ModeloLinear:
    """
    Estado (x_t, x_{t-1}); observações 100 * Delta log de (Y, C, I, G):
    100 [niveis (x_t - x_{t-1}) + u_t] + d, com d = 100 (g + n) periodo no
    crescimento balanceado. `medias` substitui d por um crescimento médio
    próprio de cada série (a variante com tendência dos dados trimestrais).
    """
    e, ch = sol.estrutura, sol.choques
    choque = np.zeros((4, 3))
    choque[1, 0], choque[2, 1], choque[3, 2] = ch.sigma_u, ch.sigma_z, ch.sigma_s
    T = np.block([[sol.P, np.zeros((4, 4))], [np.eye(4), np.zeros((4, 4))]])
    Q = np.zeros((8, 8))
    Q[:4, :4] = choque @ choque.T
    tendencia = np.zeros((4, 4))
    tendencia[:, 1] = 1.0
    Z = 100 * np.hstack([sol.niveis + tendencia, -sol.niveis])
    d = (np.full(4, 100 * (e.g + e.n) * e.periodo) if medias is None
         else np.asarray(medias, dtype=float))
    H = np.diag(np.asarray(erros_medida, dtype=float) ** 2)
    return ModeloLinear(np.zeros(8), T, Q, d, Z, H)


# --- estimação ---------------------------------------------------------------

def _para_vetor(ch: Choques, erros) -> np.ndarray:
    rhos = np.array([ch.rho_u, ch.rho_z, ch.rho_s]) / RHO_MAX
    sigmas = np.array([ch.sigma_u, ch.sigma_z, ch.sigma_s])
    return np.concatenate([np.arctanh(rhos), np.log(sigmas), np.log(erros)])


def _de_vetor(v: np.ndarray) -> tuple[Choques, np.ndarray]:
    rhos = RHO_MAX * np.tanh(v[:3])
    sigmas = np.exp(v[3:6])
    ch = Choques(rhos[0], sigmas[0], rhos[1], sigmas[1], rhos[2], sigmas[2])
    return ch, np.exp(v[6:])


def log_verossimilhanca(e: Estrutura, ch: Choques, erros, y: np.ndarray, medias=None) -> float:
    return filtrar(espaco_estados(resolver(e, ch), erros, medias), y).log_verossimilhanca


@dataclass(frozen=True)
class Estimativa:
    estrutura: Estrutura
    choques: Choques
    erros_medida: np.ndarray
    log_verossimilhanca: float
    n_obs: int
    medias: np.ndarray | None = None

    @property
    def modelo(self) -> ModeloLinear:
        return espaco_estados(resolver(self.estrutura, self.choques), self.erros_medida,
                              self.medias)


PARTIDAS = (
    (Choques(0.3, 0.008, 0.9, 0.008, 0.9, 0.01), (0.5, 0.5, 2.0, 1.0)),
    (Choques(0.8, 0.004, 0.5, 0.01, 0.5, 0.02), (0.3, 1.0, 1.0, 0.5)),
    (Choques(0.1, 0.012, 0.97, 0.005, 0.97, 0.005), (0.2, 0.3, 3.0, 1.5)),
)


def estimar(e: Estrutura, y: np.ndarray, partidas=PARTIDAS, medias=None) -> Estimativa:
    """Máxima verossimilhança dos choques e erros de medida, com várias partidas."""
    def objetivo(v):
        try:
            ch, erros = _de_vetor(v)
            valor = -log_verossimilhanca(e, ch, erros, y, medias)
        except (ValueError, np.linalg.LinAlgError):
            return 1e10
        return valor if np.isfinite(valor) else 1e10

    melhor = None
    for ch0, erros0 in partidas:
        ajuste = minimize(objetivo, _para_vetor(ch0, np.asarray(erros0, float)),
                          method="L-BFGS-B", bounds=[(-6, 6)] * 3 + [(-12, 0)] * 3 + [(-8, 3)] * 4)
        if melhor is None or ajuste.fun < melhor.fun:
            melhor = ajuste
    ch, erros = _de_vetor(melhor.x)
    return Estimativa(e, ch, erros, -float(melhor.fun), len(y),
                      None if medias is None else np.asarray(medias, dtype=float))
