"""
Problema das famílias do ABM, em tempo discreto trimestral.

Cada família é uma dinastia com riqueza a >= 0 (por membro, em unidades da
produtividade A_t) e um estado j de renda (tipo permanente x situação no
emprego), que muda pela cadeia de Markov calibrada com a PNAD Contínua em
equilibrio_geral/calibracao_renda.py. Com período D (0,25 ano), fluxos em
taxa anual e crescimento de tendência g (produtividade) e n (população):

    m = (1 + r D) a + D y_j                  dinheiro disponível
    s = m - D c >= 0                         poupança, sem endividamento
    a' = s e^{-(g + n) D}                    riqueza no trimestre seguinte
    c^-theta = e^{-rho D} (1 + r D) e^{-theta g D} E[c'^-theta]   (Euler)

A política é resolvida pelo método da grade endógena (Carroll, 2006) e a
distribuição estacionária por histograma com loterias (Young, 2010). Quando
D -> 0, o problema tende ao de equilibrio_geral/aiyagari.py.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np
import scipy.sparse as sp
from scipy.linalg import expm
from scipy.optimize import brentq
from scipy.sparse.linalg import spsolve


@dataclass(frozen=True)
class Parametros:
    """Parâmetros anuais, como em equilibrio_geral (modelo.Economia e aiyagari.Governo)."""

    alpha: float
    delta: float
    rho: float
    theta: float
    n: float
    g: float
    tau_k: float = 0.0
    tau_w: float = 0.0
    gasto: float = 0.0       # G / (A L), em taxa anual
    periodo: float = 0.25

    @property
    def fator_crescimento(self) -> float:
        return float(np.exp(-(self.g + self.n) * self.periodo))

    def r_limite(self) -> float:
        """Juro líquido acima do qual a poupança não tem estado estacionário (beta_r = 1)."""
        return float((np.exp((self.rho + self.theta * self.g) * self.periodo) - 1) / self.periodo)


@dataclass(frozen=True)
class Renda:
    """Estados de renda: produtividade z, transição trimestral P, massas pi e tipo de cada estado."""

    z: np.ndarray
    P: np.ndarray
    pi: np.ndarray
    tipo: np.ndarray

    @staticmethod
    def de_continua(renda_continua, periodo: float = 0.25, estados_por_tipo: int = 3) -> "Renda":
        """Converte a cadeia contínua de aiyagari.Renda: P = exp(Q D), exata."""
        P = expm(renda_continua.gerador * periodo)
        P = np.maximum(P, 0.0)
        P /= P.sum(axis=1, keepdims=True)
        z = np.asarray(renda_continua.z, dtype=float)
        tipo = np.arange(len(z)) // estados_por_tipo
        return Renda(z, P, np.asarray(renda_continua.estacionaria, dtype=float), tipo)

    @property
    def estados(self) -> int:
        return len(self.z)


def interpolar(x, xp, fp):
    """Interpolação linear com extrapolação linear acima do último nó."""
    y = np.interp(x, xp, fp)
    acima = x > xp[-1]
    if np.any(acima):
        inclinacao = (fp[-1] - fp[-2]) / (xp[-1] - xp[-2])
        y = np.where(acima, fp[-1] + inclinacao * (x - xp[-1]), y)
    return y


def grade_potencia(maximo: float, pontos: int, curvatura: float) -> np.ndarray:
    return maximo * np.linspace(0.0, 1.0, pontos) ** curvatura


@dataclass
class Politica:
    """Consumo em função do dinheiro disponível, por estado: nós (m, c) de cada j."""

    m: np.ndarray        # (J, S + 1)
    c: np.ndarray        # (J, S + 1)
    r: float
    renda: np.ndarray    # y_j usado na solução
    iteracoes: int

    def consumo(self, m: np.ndarray, j: np.ndarray) -> np.ndarray:
        c = np.empty_like(m, dtype=float)
        for estado in range(self.m.shape[0]):
            sel = j == estado
            if np.any(sel):
                c[sel] = interpolar(m[sel], self.m[estado], self.c[estado])
        return c


def _egm(par: Parametros, renda: Renda, r_prox: float, y_prox: np.ndarray, M: np.ndarray,
         C: np.ndarray, grade_s: np.ndarray):
    """
    Um passo da grade endógena: dada a política do trimestre seguinte (nós M,
    C), o juro r_prox e as rendas y_prox que vão vigorar nele, devolve o
    consumo em cada ponto de poupança e os novos nós.
    """
    D, theta = par.periodo, par.theta
    beta_r = np.exp(-par.rho * D) * (1 + r_prox * D) * np.exp(-theta * par.g * D)
    m_prox = (1 + r_prox * D) * grade_s[:, None] * par.fator_crescimento + D * y_prox[None, :]
    c_prox = np.column_stack([interpolar(m_prox[:, j], M[j], C[j]) for j in range(renda.estados)])
    esperado = (c_prox ** -theta) @ renda.P.T           # (S, J): E[c'^-theta | j]
    c = (beta_r * esperado) ** (-1 / theta)
    zeros = np.zeros((renda.estados, 1))
    return c, np.hstack([zeros, (grade_s[:, None] + D * c).T]), np.hstack([zeros, c.T])


def resolver_politica(par: Parametros, renda: Renda, r: float, y: np.ndarray,
                      grade_s: np.ndarray, inicial: Politica | None = None,
                      tol: float = 1e-10, max_iter: int = 200_000) -> Politica:
    """Grade endógena para o juro r (taxa anual líquida) e rendas y_j (taxa anual) constantes."""
    D = par.periodo
    if np.exp(-par.rho * D) * (1 + r * D) * np.exp(-par.theta * par.g * D) >= 1:
        raise ValueError("juro alto demais: e^{-rho D}(1 + r D)e^{-theta g D} >= 1")
    y = np.asarray(y, dtype=float)
    if inicial is None:   # último período: consome tudo
        M = np.tile([0.0, 1.0], (renda.estados, 1))
        C = M / D
    else:
        M, C = inicial.m, inicial.c
    c_velho = None
    for iteracao in range(1, max_iter + 1):
        c, M, C = _egm(par, renda, r, y, M, C, grade_s)
        if c_velho is not None and np.max(np.abs(c - c_velho) / c) < tol:
            return Politica(M, C, r, y, iteracao)
        c_velho = c
    raise RuntimeError("a grade endógena não convergiu")


def politica_anterior(par: Parametros, renda: Renda, proxima: Politica, r: float, y: np.ndarray,
                      grade_s: np.ndarray) -> Politica:
    """
    Política do trimestre t numa transição com preços conhecidos: `proxima` é a
    de t + 1 (com o juro e as rendas de t + 1 guardados nela); r e y são os de t.
    """
    _, M, C = _egm(par, renda, proxima.r, proxima.renda, proxima.m, proxima.c, grade_s)
    return Politica(M, C, r, np.asarray(y, dtype=float), 1)


@dataclass
class Distribuicao:
    grade_a: np.ndarray
    massa: np.ndarray    # (A, J), soma 1

    @property
    def media(self) -> float:
        return float(self.grade_a @ self.massa.sum(axis=1))


def distribuicao_estacionaria(par: Parametros, renda: Renda, pol: Politica,
                              grade_a: np.ndarray) -> Distribuicao:
    """
    Histograma estacionário. Cada (a, j) leva a a' pela política; a massa se
    divide entre os dois pontos vizinhos da grade (loteria) e entre os j' pela
    cadeia de Markov. Os tipos permanentes são blocos fechados, resolvidos um a
    um com a massa pi de cada tipo.
    """
    D = par.periodo
    A, J = len(grade_a), renda.estados
    massa = np.zeros((A, J))
    for tipo in np.unique(renda.tipo):
        estados = np.flatnonzero(renda.tipo == tipo)
        k = len(estados)
        linhas, colunas, valores = [], [], []
        for posicao, j in enumerate(estados):
            m = (1 + pol.r * D) * grade_a + D * pol.renda[j]
            s = m - D * pol.consumo(m, np.full(A, j))
            a_prox = np.clip(s * par.fator_crescimento, grade_a[0], grade_a[-1])
            acima = np.clip(np.searchsorted(grade_a, a_prox, side="right"), 1, A - 1)
            peso_acima = (a_prox - grade_a[acima - 1]) / (grade_a[acima] - grade_a[acima - 1])
            for destino, j_prox in enumerate(estados):
                p = renda.P[j, j_prox]
                if p == 0:
                    continue
                origem = posicao * A + np.arange(A)
                for vizinho, peso in ((acima - 1, 1 - peso_acima), (acima, peso_acima)):
                    linhas.append(origem)
                    colunas.append(destino * A + vizinho)
                    valores.append(p * peso)
        T = sp.csr_matrix((np.concatenate(valores), (np.concatenate(linhas),
                                                      np.concatenate(colunas))), shape=(k * A,) * 2)
        sistema = (T.T - sp.eye(k * A)).tolil()
        sistema[0, :] = 1.0
        lado = np.zeros(k * A)
        lado[0] = 1.0
        mu = np.maximum(spsolve(sistema.tocsc(), lado), 0.0)
        mu *= renda.pi[estados].sum() / mu.sum()
        massa[:, estados] = mu.reshape(k, A).T
    return Distribuicao(grade_a, massa)


# --- equilíbrio e calibração --------------------------------------------------

@dataclass(frozen=True)
class Grades:
    s_max: float = 300.0
    s_pontos: int = 300
    s_curvatura: float = 2.5
    a_pontos: int = 700
    a_curvatura: float = 2.0

    def poupanca(self, escala: float = 1.0) -> np.ndarray:
        return grade_potencia(self.s_max * escala, self.s_pontos, self.s_curvatura)

    def riqueza(self, escala: float = 1.0) -> np.ndarray:
        return grade_potencia(self.s_max * escala, self.a_pontos, self.a_curvatura)


def precos(par: Parametros, K: float, trabalho: float = 1.0):
    """Retorno bruto R, salário w e produto y da firma competitiva."""
    y = K**par.alpha * trabalho ** (1 - par.alpha)
    return par.alpha * y / K, (1 - par.alpha) * y / trabalho, y


def rendas(par: Parametros, renda: Renda, w: float, transferencia_media: float,
           pesos: np.ndarray | None = None, reforma: float | None = None) -> np.ndarray:
    """
    y_j = (1 - tau_w) w z_j + T_j, com T_j = pesos_j T médio (média ponderada
    dos pesos = 1). Com `reforma` (a receita do aumento de tau_k numa
    reforma), só ela segue os pesos, e o resto se divide igualmente.
    """
    pesos = np.ones(renda.estados) if pesos is None else np.asarray(pesos, dtype=float)
    pesos = pesos / (renda.pi @ pesos)
    if reforma is None:
        return (1 - par.tau_w) * w * renda.z + transferencia_media * pesos
    return (1 - par.tau_w) * w * renda.z + (transferencia_media - reforma) + reforma * pesos


@dataclass
class Estacionario:
    par: Parametros
    renda: Renda
    pesos: np.ndarray | None
    K: float
    r: float             # retorno líquido após impostos
    w: float
    y: float
    transferencia: float
    politica: Politica
    distribuicao: Distribuicao
    beneficio: np.ndarray | None = None   # estados que recebem benefício em vez de produzir
    reforma: float | None = None           # receita do aumento de tau_k que segue os pesos, se houver


def trabalho_e_beneficio(renda: Renda, beneficio: np.ndarray | None) -> tuple[float, float]:
    """
    Trabalho que produz (L) e unidades pagas como benefício pelo governo (B).
    Sem `beneficio`, todos os estados produzem, como no Aiyagari: L = E[z] = 1.
    Com ele, os estados marcados (os desempregados em descentralizada.py)
    recebem w z do governo, tributado como salário, e não produzem.
    """
    if beneficio is None:
        return 1.0, 0.0
    beneficio = np.asarray(beneficio, dtype=bool)
    return float(renda.pi[~beneficio] @ renda.z[~beneficio]), float(renda.pi[beneficio] @ renda.z[beneficio])


def _resolver_com_K(par, renda, K, pesos, grades, inicial=None, beneficio=None, tau_k_base=None):
    L, B = trabalho_e_beneficio(renda, beneficio)
    R, w, y = precos(par, K, L)
    r = (1 - par.tau_k) * (R - par.delta)
    transferencia = par.tau_k * (R - par.delta) * K + par.tau_w * w * (L + B) - par.gasto - w * B
    reforma = None if tau_k_base is None else (par.tau_k - tau_k_base) * (R - par.delta) * K
    y_j = rendas(par, renda, w, transferencia, pesos, reforma)
    pol = resolver_politica(par, renda, r, y_j, grades.poupanca(w), inicial)
    dist = distribuicao_estacionaria(par, renda, pol, grades.riqueza(w))
    return Estacionario(par, renda, pesos, K, r, w, y, transferencia, pol, dist, beneficio, reforma)


def calibrar(par: Parametros, renda: Renda, capital_produto: float, gasto_pib: float,
             grades: Grades = Grades(), beneficio: np.ndarray | None = None) -> Estacionario:
    """
    rho e tau_w tais que o equilíbrio estacionário tenha K/Y e G/Y dos dados e
    transferência nula (como aiyagari.calibrar_rho). K/Y fixa r e w, então
    basta procurar rho que faça a poupança das famílias igual a K.
    """
    L, B = trabalho_e_beneficio(renda, beneficio)
    K = capital_produto ** (1 / (1 - par.alpha)) * L
    R, w, y = precos(par, K, L)
    gasto = gasto_pib * y
    par = replace(par, gasto=gasto,
                  tau_w=(gasto + w * B - par.tau_k * (R - par.delta) * K) / (w * (L + B)))
    r = (1 - par.tau_k) * (R - par.delta)
    rho_minimo = np.log(1 + r * par.periodo) / par.periodo - par.theta * par.g
    cache = {}

    def excesso(rho):
        est = _resolver_com_K(replace(par, rho=rho), renda, K, None, grades, cache.get("pol"),
                              beneficio)
        cache["pol"] = est.politica
        return est.distribuicao.media - K

    folga = 1e-3
    while excesso(rho_minimo + folga) < 0:
        folga /= 4
        if folga < 1e-7:
            raise ValueError("risco de renda pequeno demais para sustentar esse K/Y")
    rho = brentq(excesso, rho_minimo + folga, rho_minimo + 0.1, xtol=1e-10)
    return _resolver_com_K(replace(par, rho=rho), renda, K, None, grades, cache.get("pol"), beneficio)


def equilibrio(par: Parametros, renda: Renda, pesos=None, grades: Grades = Grades(),
               K_inicial: float | None = None, beneficio: np.ndarray | None = None,
               tau_k_base: float | None = None) -> Estacionario:
    """
    Equilíbrio estacionário: K tal que a poupança das famílias iguala a
    demanda da firma. Com `tau_k_base`, só a receita do aumento de tau_k
    segue os pesos da transferência (ver `rendas`).
    """
    L, _ = trabalho_e_beneficio(renda, beneficio)
    r_max = par.r_limite() - 1e-6
    R_max = r_max / (1 - par.tau_k) + par.delta
    K_min = (par.alpha / R_max) ** (1 / (1 - par.alpha)) * L   # juro no limite: K mínimo
    cache = {}

    def excesso(logK):
        est = _resolver_com_K(par, renda, np.exp(logK), pesos, grades, cache.get("pol"), beneficio,
                              tau_k_base)
        cache["pol"] = est.politica
        return est.distribuicao.media - np.exp(logK)

    centro = np.log(K_inicial if K_inicial else K_min * 1.2)
    baixo, alto = max(centro - 0.05, np.log(K_min) + 1e-6), centro + 0.05
    while excesso(baixo) < 0:
        baixo = max(baixo - 0.05, np.log(K_min) + 1e-9)
    while excesso(alto) > 0:
        alto += 0.05
    logK = brentq(excesso, baixo, alto, xtol=1e-10)
    return _resolver_com_K(par, renda, np.exp(logK), pesos, grades, cache.get("pol"), beneficio,
                           tau_k_base)


# --- políticas para crenças de juro diferentes do equilíbrio -------------------

LACUNAS = np.geomspace(0.06, 0.0003, 14)   # distância ao limite de juro, taxa anual


class TabelaPoliticas:
    """
    Consumo por unidade de salário esperado, c = w_e * c_hat(m / w_e, j; r_e),
    para um perfil de renda por unidade de salário (1 - tau_w) z_j + T_j / w.
    Cada nó de r_e é uma política de expectativas "antecipadas" (Kreps, 1998):
    a família age como se r_e e w_e fossem durar para sempre. Entre os nós, a
    interpolação é linear em log(r_limite - r_e); crenças fora da faixa são
    truncadas nas pontas. `r_exatos` entram como nós (o juro de equilíbrio,
    para que as crenças de equilíbrio usem a política exata).
    """

    def __init__(self, par: Parametros, renda: Renda, perfil: np.ndarray, grades: Grades = Grades(),
                 lacunas: np.ndarray = LACUNAS, pontos_m: int = 500, r_exatos=()):
        self.limite = par.r_limite()
        extras = [self.limite - r for r in r_exatos]
        self.lacunas = np.unique(np.concatenate([np.asarray(lacunas, dtype=float), extras]))
        self.x = np.log(self.lacunas)
        self.grade_m = grade_potencia(grades.s_max * 1.2, pontos_m, grades.s_curvatura)
        J = renda.estados
        self.C = np.empty((len(self.lacunas), J, pontos_m))
        anterior = None
        for k in range(len(self.lacunas) - 1, -1, -1):   # do juro mais baixo ao mais alto
            anterior = resolver_politica(par, renda, self.limite - self.lacunas[k], perfil,
                                         grades.poupanca(), anterior)
            for j in range(J):
                self.C[k, j] = interpolar(self.grade_m, anterior.m[j], anterior.c[j])
        self.r_min = self.limite - self.lacunas[-1]
        self.r_max = self.limite - self.lacunas[0]

    def consumo_unitario(self, m: np.ndarray, j: np.ndarray, r_e) -> np.ndarray:
        x = np.log(np.clip(self.limite - np.asarray(r_e, dtype=float), self.lacunas[0], self.lacunas[-1]))
        x = np.broadcast_to(x, m.shape)
        k = np.clip(np.searchsorted(self.x, x, side="right") - 1, 0, len(self.x) - 2)
        peso_r = (x - self.x[k]) / (self.x[k + 1] - self.x[k])
        g = self.grade_m
        i = np.clip(np.searchsorted(g, m, side="right") - 1, 0, len(g) - 2)
        peso_m = (m - g[i]) / (g[i + 1] - g[i])     # > 1 acima da grade: extrapola
        baixo = (1 - peso_m) * self.C[k, j, i] + peso_m * self.C[k, j, i + 1]
        alto = (1 - peso_m) * self.C[k + 1, j, i] + peso_m * self.C[k + 1, j, i + 1]
        return (1 - peso_r) * baixo + peso_r * alto

    def consumo(self, m: np.ndarray, j: np.ndarray, r_e, w_e) -> np.ndarray:
        w_e = np.asarray(w_e, dtype=float)
        return w_e * self.consumo_unitario(m / w_e, j, r_e)
