"""
Equilíbrio geral estocástico com margem e busca no mercado de trabalho: a
versão de dsge.py com os fundamentos do ABM sem leiloeiro
(abm2_sem_leiloeiro/descentralizada.py), para aproximar os dois modelos que a
previsão compara. Os dois ainda diferem em muito mais que o leiloeiro:
agente representativo contra famílias heterogêneas, linearização, a forma de
estimar os choques e as séries observadas.

O que muda em relação a dsge.py:

  margem     concorrência monopolística: as firmas cobram uma margem mu sobre
             o custo marginal, então capital e trabalho recebem o produto
             marginal dividido por 1 + mu. A margem é a que aparece no ABM sem
             leiloeiro (cerca de 10%). A tecnologia (alpha) é a mesma dos
             outros modelos, e a margem reduz a participação do trabalho para
             cerca de 50%, abaixo dos 54,9% da PWT com que alpha é calibrado.
  busca      o emprego N é uma variável de estado. A cada trimestre uma
             fração s dos empregados perde o emprego e uma fração f dos
             desempregados do trimestre anterior é contratada (quem acabou de
             perder o emprego espera o trimestre seguinte, como no ABM):
                 N_t = (1 - s_t) N_{t-1} + f_t (1 - N_{t-1}).
             s e o desemprego de longo prazo vêm da mesma cadeia trimestral
             da PNAD do ABM; f_t sai da função de encontro
             f = chi theta^(1 - eta), com theta = vagas / desempregados, e as
             firmas abrem vagas até o custo esperado de contratar igualar o
             valor do trabalhador para a firma (Pissarides, 2000).
  salário    rigidez real (Hall, 2005; Blanchard e Galí, 2010): o salário
             anda com a tendência da produtividade, mas só se ajusta aos
             poucos ao produto marginal,
                 log w_t = gamma (log w_{t-1} - u_t) + (1 - gamma) log(omega pmgL_t),
             com w e o produto marginal em unidades de eficiência. É o papel
             da regra de salários do ABM, que sobe quando faltam candidatos e
             desce devagar. gamma é estimado.
  choques    os três de dsge.py e um choque na taxa de separação, que dá ao
             desemprego uma fonte própria de variação, como a separação que o
             ABM usa para reproduzir o desemprego da PNAD.

Unidades: por unidade de eficiência da força de trabalho (A L, L = população
em idade de trabalhar), fluxos em taxa anual, período de 0,25 ano. O
emprego N é a fração da força de trabalho ocupada.

Observações: 100 x Delta log de PIB, consumo das famílias, FBCF e consumo do
governo, e 100 x Delta u (variação da taxa de desemprego em p.p., só a partir
de 2012, com a PNAD Contínua), cada uma com erro de medida.

Calibração do mercado de trabalho, fora a PNAD: custo de contratar igual a
14% do salário de um trimestre (Silva e Toledo, 2009), probabilidade de
preencher uma vaga de 0,7 por trimestre (den Haan, Ramey e Watson, 2000) e
elasticidade da função de encontro de 0,5 (Petrongolo e Pissarides, 2001).
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np
from scipy.linalg import expm
from scipy.optimize import minimize

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))   # macroeconomia/
import caminhos  # noqa: E402,F401

from dsge import RHO_MAX, Estrutura, resolver_klein  # noqa: E402
from espaco_estados import ModeloLinear, filtrar  # noqa: E402

OBSERVAVEIS = ("pib", "consumo", "investimento", "governo", "desemprego")
NOMES_CHOQUES = ("rho_u", "sigma_u", "rho_z", "sigma_z", "rho_s", "sigma_s",
                 "rho_sep", "sigma_sep", "rigidez")
PREDETERMINADAS = 7      # log kappa, log N_{t-1}, log w_{t-1}, u, z, s, sep
RIGIDEZ_MAX = 0.99


@dataclass(frozen=True)
class Trabalho:
    """Mercado de trabalho e margem. Probabilidades por trimestre."""

    desemprego: float              # taxa de longo prazo (fração)
    separacao: float               # probabilidade de perder o emprego no trimestre
    margem: float = 0.10
    custo_contratacao: float = 0.14   # custo por contratação, em salários de um trimestre
    preenchimento: float = 0.7     # probabilidade de preencher uma vaga no trimestre
    eta: float = 0.5               # elasticidade do encontro em relação aos desempregados

    @property
    def encontro(self) -> float:
        """Probabilidade de o desempregado achar emprego que dá o desemprego de longo prazo."""
        return self.separacao * (1 - self.desemprego) / self.desemprego

    @staticmethod
    def da_pnad(desemprego, periodo: float = 0.25, **kwargs) -> "Trabalho":
        """
        Da calibração da PNAD (equilibrio_geral/calibracao_renda.Desemprego):
        a probabilidade de passar de empregado a desempregado num trimestre
        na cadeia com desemprego de curta e de longa duração, a mesma que o
        ABM usa.
        """
        d = desemprego
        s = d.separacao
        Q = np.array([[-s, s * d.q_curto, s * (1 - d.q_curto)],
                      [d.f_curto, -d.f_curto, 0.0],
                      [d.f_longo, 0.0, -d.f_longo]])
        P = expm(Q * periodo)
        return Trabalho(float(d.taxa), float(1 - P[0, 0]), **kwargs)


@dataclass(frozen=True)
class Choques:
    """Persistência e desvio-padrão por trimestre dos quatro choques, e a rigidez do salário."""

    rho_u: float = 0.5
    sigma_u: float = 0.01
    rho_z: float = 0.9
    sigma_z: float = 0.01
    rho_s: float = 0.9
    sigma_s: float = 0.01
    rho_sep: float = 0.8
    sigma_sep: float = 0.05
    rigidez: float = 0.8

    def __post_init__(self):
        for nome in ("rho_u", "rho_z", "rho_s", "rho_sep"):
            if not -1 < getattr(self, nome) < 1:
                raise ValueError(f"{nome} precisa estar entre -1 e 1")
        if not 0 <= self.rigidez < 1:
            raise ValueError("a rigidez do salário precisa estar em [0, 1)")


@dataclass(frozen=True)
class Estacionario:
    k: float        # K / (A L)
    kappa: float    # K_t / (A_{t-1} L_{t-1})
    N: float        # emprego
    y: float        # produção bruta
    pib: float      # produção menos o custo das vagas
    c: float
    gasto: float
    investimento: float
    w: float        # salário por ocupado
    pmgl: float     # produto marginal do trabalho dividido por 1 + mu
    omega: float    # w / pmgl
    theta: float    # vagas / desempregados
    chi: float      # eficiência do encontro
    vagas: float
    custo_vaga: float   # custo de uma vaga por trimestre
    r: float


def _desconto_valor(e: Estrutura) -> float:
    """Fator que desconta o valor de um trabalhador de um trimestre para o anterior, sem choques."""
    return float(np.exp(-e.rho * e.periodo + (1 - e.theta) * e.g * e.periodo))


def estado_estacionario(e: Estrutura, t: Trabalho) -> Estacionario:
    D = e.periodo
    r = (np.exp((e.rho + e.theta * e.g) * D) - 1) / D
    R = r / (1 - e.tau_k) + e.delta
    N = 1 - t.desemprego
    k = N * (e.alpha / (R * (1 + t.margem))) ** (1 / (1 - e.alpha))
    y = k**e.alpha * N ** (1 - e.alpha)
    pmgl = (1 - e.alpha) * y / (N * (1 + t.margem))
    # Valor do trabalhador para a firma: J = D (pmgl - w) / (1 - beta (1 - s)),
    # igual ao custo de contratar, custo_contratacao x D w.
    fator = 1 - _desconto_valor(e) * (1 - t.separacao)
    w = pmgl / (1 + t.custo_contratacao * fator)
    f = t.encontro
    theta = f / t.preenchimento
    chi = f / theta ** (1 - t.eta)
    vagas = theta * t.desemprego
    J = t.custo_contratacao * D * w
    custo_vaga = t.preenchimento * J
    pib = y - custo_vaga * vagas / D
    gasto = e.gasto_pib * pib
    investimento = k * (e.delta + (np.exp((e.g + e.n) * D) - 1) / D)
    c = pib - gasto - investimento
    if c <= 0:
        raise ValueError("consumo estacionário não positivo")
    return Estacionario(k, k * np.exp((e.g + e.n) * D), N, y, pib, c, gasto, investimento, w, pmgl,
                        w / pmgl, theta, chi, vagas, custo_vaga, r)


def rho_para_capital_produto(e: Estrutura, t: Trabalho, capital_produto: float) -> float:
    """rho que faz K / PIB = capital_produto no estado estacionário, com a margem."""
    D = e.periodo
    e1 = e
    for _ in range(50):
        ee = estado_estacionario(e1, t)
        k_y = capital_produto * ee.pib / ee.y            # K / produção bruta
        retorno = (1 - e.tau_k) * (e.alpha / ((1 + t.margem) * k_y) - e.delta)
        rho = np.log(1 + D * retorno) / D - e.theta * e.g
        if abs(rho - e1.rho) < 1e-14:
            break
        e1 = replace(e1, rho=rho)
    return float(rho)


def _equacoes(e: Estrutura, t: Trabalho, ee: Estacionario, ch: Choques, prox, atual):
    """
    Resíduos do equilíbrio em x = (log kappa, log N_{t-1}, log w_{t-1}, u, z, s, sep,
    log c, log theta); as sete primeiras são predeterminadas.
    """
    D, a, mu = e.periodo, e.alpha, t.margem

    def trimestre(x):
        lkap, lN, lw, u, z, s, sep, lc, lth = x
        k = np.exp(lkap - (e.g + e.n) * D - u)
        N_ant = np.exp(lN)
        separacao = t.separacao * np.exp(sep)
        f = ee.chi * np.exp(lth) ** (1 - t.eta)
        q = ee.chi * np.exp(lth) ** (-t.eta)
        N = (1 - separacao) * N_ant + f * (1 - N_ant)
        y = np.exp(z) * k**a * N ** (1 - a)
        pmgl = (1 - a) * y / (N * (1 + mu))
        R = a * y / (k * (1 + mu))
        w = np.exp(ch.rigidez * (lw - u) + (1 - ch.rigidez) * np.log(ee.omega * pmgl))
        vagas = np.exp(lth) * (1 - N_ant)
        return dict(k=k, N=N, y=y, pmgl=pmgl, R=R, w=w, vagas=vagas, q=q, sep=separacao,
                    c=np.exp(lc), gasto=ee.gasto * np.exp(s))

    h, h1 = trimestre(atual), trimestre(prox)
    lkap1, u1 = prox[0], prox[3]
    lc, lc1 = atual[7], prox[7]
    capital = h["k"] + D * (h["y"] - h["c"] - h["gasto"] - e.delta * h["k"]) - ee.custo_vaga * h["vagas"]
    sdf = np.exp(-e.rho * D - e.theta * (e.g * D + u1) - e.theta * (lc1 - lc))
    J, J1 = ee.custo_vaga / h["q"], ee.custo_vaga / h1["q"]
    J_ee = ee.custo_vaga / t.preenchimento
    return np.array([
        1 - capital / np.exp(lkap1),
        prox[1] - np.log(h["N"]),
        prox[2] - np.log(h["w"]),
        u1 - ch.rho_u * atual[3],
        prox[4] - ch.rho_z * atual[4],
        prox[5] - ch.rho_s * atual[5],
        prox[6] - ch.rho_sep * atual[6],
        1 - sdf * (1 + D * (1 - e.tau_k) * (h1["R"] - e.delta)),
        (J - D * (h["pmgl"] - h["w"]) - sdf * np.exp(e.g * D + u1) * (1 - h1["sep"]) * J1) / J_ee,
    ])


def _ponto(ee: Estacionario) -> np.ndarray:
    return np.array([np.log(ee.kappa), np.log(ee.N), np.log(ee.w), 0.0, 0.0, 0.0, 0.0,
                     np.log(ee.c), np.log(ee.theta)])


def _niveis(e: Estrutura, t: Trabalho, ee: Estacionario, x):
    """(log PIB, log C, log I, log G, desemprego) no trimestre, por unidade de eficiência."""
    D, a = e.periodo, e.alpha
    lkap, lN, lw, u, z, s, sep, lc, lth = x
    k = np.exp(lkap - (e.g + e.n) * D - u)
    N_ant = np.exp(lN)
    f = ee.chi * np.exp(lth) ** (1 - t.eta)
    N = (1 - t.separacao * np.exp(sep)) * N_ant + f * (1 - N_ant)
    y = np.exp(z) * k**a * N ** (1 - a)
    pib = y - ee.custo_vaga * np.exp(lth) * (1 - N_ant) / D
    gasto = ee.gasto * np.exp(s)
    c = np.exp(lc)
    return np.array([np.log(pib), lc, np.log(pib - c - gasto), np.log(gasto), 1 - N])


def _derivadas(funcao, x0: np.ndarray, m: int) -> np.ndarray:
    """Jacobiano exato por passo complexo."""
    passo = 1e-30
    J = np.empty((m, x0.size))
    for j in range(x0.size):
        dx = np.zeros(x0.size, dtype=complex)
        dx[j] = 1j * passo
        J[:, j] = funcao(x0.astype(complex) + dx).imag / passo
    return J


@dataclass(frozen=True)
class Solucao:
    estrutura: Estrutura
    trabalho: Trabalho
    choques: Choques
    ee: Estacionario
    P: np.ndarray        # transição dos sete estados, em desvios
    F: np.ndarray        # (log c, log theta) = F x
    niveis: np.ndarray   # desvios de (log PIB, log C, log I, log G) e de u = niveis @ x


def resolver(e: Estrutura, t: Trabalho, ch: Choques) -> Solucao:
    ee = estado_estacionario(e, t)
    x0 = _ponto(ee)
    n = x0.size
    A = _derivadas(lambda x: _equacoes(e, t, ee, ch, x, x0.astype(complex)), x0, n)
    B = -_derivadas(lambda x: _equacoes(e, t, ee, ch, x0.astype(complex), x), x0, n)
    P, F = resolver_klein(A, B, PREDETERMINADAS)
    completo = np.vstack([np.eye(PREDETERMINADAS), F])
    niveis = _derivadas(lambda x: _niveis(e, t, ee, x), x0, 5) @ completo
    return Solucao(e, t, ch, ee, P, F, niveis)


def espaco_estados(sol: Solucao, erros_medida, medias=None) -> ModeloLinear:
    """
    Estado (x_t, x_{t-1}); observações 100 x Delta log de (PIB, C, I, G), com
    a tendência g + n e o choque u, e 100 x Delta u. `medias` substitui a
    tendência pelo crescimento médio de cada série (e a média da variação do
    desemprego), como em dsge.espaco_estados.
    """
    e, ch = sol.estrutura, sol.choques
    n = PREDETERMINADAS
    choque = np.zeros((n, 4))
    choque[3, 0], choque[4, 1], choque[5, 2], choque[6, 3] = ch.sigma_u, ch.sigma_z, ch.sigma_s, ch.sigma_sep
    T = np.block([[sol.P, np.zeros((n, n))], [np.eye(n), np.zeros((n, n))]])
    Q = np.zeros((2 * n, 2 * n))
    Q[:n, :n] = choque @ choque.T
    tendencia = np.zeros((5, n))
    tendencia[:4, 3] = 1.0
    Z = 100 * np.hstack([sol.niveis + tendencia, -sol.niveis])
    if medias is None:
        d = np.r_[np.full(4, 100 * (e.g + e.n) * e.periodo), 0.0]
    else:
        d = np.asarray(medias, dtype=float)
    H = np.diag(np.asarray(erros_medida, dtype=float) ** 2)
    return ModeloLinear(np.zeros(2 * n), T, Q, d, Z, H)


# --- estimação ---------------------------------------------------------------

def _para_vetor(ch: Choques, erros) -> np.ndarray:
    rhos = np.array([ch.rho_u, ch.rho_z, ch.rho_s, ch.rho_sep]) / RHO_MAX
    sigmas = np.array([ch.sigma_u, ch.sigma_z, ch.sigma_s, ch.sigma_sep])
    rigidez = np.arctanh(2 * ch.rigidez / RIGIDEZ_MAX - 1)
    return np.concatenate([np.arctanh(rhos), np.log(sigmas), [rigidez], np.log(erros)])


def _de_vetor(v: np.ndarray) -> tuple[Choques, np.ndarray]:
    rhos = RHO_MAX * np.tanh(v[:4])
    sigmas = np.exp(v[4:8])
    rigidez = RIGIDEZ_MAX * (np.tanh(v[8]) + 1) / 2
    ch = Choques(rhos[0], sigmas[0], rhos[1], sigmas[1], rhos[2], sigmas[2], rhos[3], sigmas[3],
                 rigidez)
    return ch, np.exp(v[9:])


def log_verossimilhanca(e: Estrutura, t: Trabalho, ch: Choques, erros, y: np.ndarray,
                        medias=None) -> float:
    return filtrar(espaco_estados(resolver(e, t, ch), erros, medias), y).log_verossimilhanca


@dataclass(frozen=True)
class Estimativa:
    estrutura: Estrutura
    trabalho: Trabalho
    choques: Choques
    erros_medida: np.ndarray
    log_verossimilhanca: float
    n_obs: int
    medias: np.ndarray | None = None

    @property
    def modelo(self) -> ModeloLinear:
        return espaco_estados(resolver(self.estrutura, self.trabalho, self.choques),
                              self.erros_medida, self.medias)


PARTIDAS = (
    (Choques(0.3, 0.008, 0.9, 0.008, 0.9, 0.01, 0.8, 0.05, 0.5), (0.5, 0.5, 2.0, 1.0, 0.1)),
    (Choques(0.8, 0.004, 0.5, 0.01, 0.5, 0.02, 0.5, 0.1, 0.9), (0.3, 1.0, 1.0, 0.5, 0.2)),
    (Choques(0.1, 0.012, 0.97, 0.005, 0.97, 0.005, 0.95, 0.03, 0.2), (0.2, 0.3, 3.0, 1.5, 0.05)),
)


def estimar(e: Estrutura, t: Trabalho, y: np.ndarray, partidas=PARTIDAS, medias=None) -> Estimativa:
    """Máxima verossimilhança dos choques, da rigidez do salário e dos erros de medida."""
    def objetivo(v):
        try:
            ch, erros = _de_vetor(v)
            valor = -log_verossimilhanca(e, t, ch, erros, y, medias)
        except (ValueError, np.linalg.LinAlgError):
            return 1e10
        return valor if np.isfinite(valor) else 1e10

    limites = [(-6, 6)] * 4 + [(-12, 0)] * 4 + [(-4, 4)] + [(-8, 3)] * 5
    melhor = None
    for ch0, erros0 in partidas:
        ajuste = minimize(objetivo, _para_vetor(ch0, np.asarray(erros0, float)),
                          method="L-BFGS-B", bounds=limites)
        if melhor is None or ajuste.fun < melhor.fun:
            melhor = ajuste
    ch, erros = _de_vetor(melhor.x)
    return Estimativa(e, t, ch, erros, -float(melhor.fun), len(y),
                      None if medias is None else np.asarray(medias, dtype=float))
