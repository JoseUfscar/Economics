"""
Modelo de Ramsey-Cass-Koopmans com governo, em tempo contínuo.

Tudo é medido por unidade de trabalho efetivo, k = K/(AL) e c = C/(AL), com
A(t) = e^{gt} e L(t) = e^{nt}. O equilíbrio competitivo é o sistema

    dk/dt = k^alpha - c - gasto - (delta + n + g) k
    dc/dt = c [(1 - tau_k)(alpha k^(alpha-1) - delta) - rho - theta g] / theta

em que tau_k tributa a renda do capital líquida de depreciação, tau_c tributa
o consumo e `gasto` é o consumo do governo (G/AL). A diferença entre receita
e gasto volta às famílias como transferência lump-sum. A derivação completa
está em nota_tecnica.pdf.

A política pode mudar ao longo do tempo em datas conhecidas desde t = 0
(regimes). Isso cobre choques inesperados, anunciados e temporários.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import sqrt

import numpy as np
import pandas as pd
from scipy.integrate import solve_bvp


@dataclass(frozen=True)
class Economia:
    """Tecnologia, preferências e crescimento, em frequência anual."""

    alpha: float = 0.33  # participação do capital na renda
    delta: float = 0.05  # depreciação
    rho: float = 0.04    # taxa de desconto intertemporal
    theta: float = 2.0   # inverso da elasticidade de substituição intertemporal
    n: float = 0.01      # crescimento da população
    g: float = 0.02      # crescimento da produtividade do trabalho

    def __post_init__(self):
        if not 0 < self.alpha < 1:
            raise ValueError("alpha deve estar entre 0 e 1")
        if self.theta <= 0 or self.delta < 0:
            raise ValueError("theta deve ser positivo e delta não negativo")
        if self.beta <= 0:
            raise ValueError("a utilidade só é finita se rho - n - (1 - theta) g > 0")

    @property
    def beta(self) -> float:
        """Desconto efetivo da utilidade ao longo do crescimento balanceado."""
        return self.rho - self.n - (1 - self.theta) * self.g


@dataclass(frozen=True)
class Politica:
    """Alíquotas e gasto do governo (gasto em unidades de trabalho efetivo)."""

    tau_k: float = 0.0
    tau_c: float = 0.0
    gasto: float = 0.0

    def __post_init__(self):
        if self.tau_k >= 1 or self.tau_c <= -1 or self.gasto < 0:
            raise ValueError("exige-se tau_k < 1, tau_c > -1 e gasto >= 0")


@dataclass(frozen=True)
class EstadoEstacionario:
    k: float
    c: float
    y: float
    r: float                # retorno líquido após impostos (= rho + theta g)
    lambda_estavel: float
    lambda_instavel: float
    inclinacao: float       # dc/dk do braço estável no estado estacionário


def estado_estacionario(eco: Economia, pol: Politica = Politica()) -> EstadoEstacionario:
    """Estado estacionário e autovalores do sistema linearizado."""
    retorno_bruto = eco.delta + (eco.rho + eco.theta * eco.g) / (1 - pol.tau_k)
    k = (eco.alpha / retorno_bruto) ** (1 / (1 - eco.alpha))
    y = k**eco.alpha
    c = y - pol.gasto - (eco.delta + eco.n + eco.g) * k
    if c <= 0:
        raise ValueError("gasto público alto demais: consumo estacionário não positivo")

    # Jacobiano de (dk/dt, dc/dt) em (k*, c*): [[a, -1], [b, 0]] com b < 0,
    # logo det < 0 e há uma raiz estável e outra instável (ponto de sela).
    a = eco.alpha * k ** (eco.alpha - 1) - (eco.delta + eco.n + eco.g)
    b = c * (1 - pol.tau_k) * eco.alpha * (eco.alpha - 1) * k ** (eco.alpha - 2) / eco.theta
    raiz = sqrt(a * a - 4 * b)
    estavel, instavel = (a - raiz) / 2, (a + raiz) / 2
    # Autovetor estável (1, s): a - s = lambda_estavel.
    return EstadoEstacionario(k, c, y, eco.rho + eco.theta * eco.g,
                              estavel, instavel, a - estavel)


def _campo(eco: Economia, pol: Politica, z: np.ndarray):
    """Lado direito do sistema em logaritmos, z = (log k, log c)."""
    y_k = np.exp((eco.alpha - 1) * z[0])
    c_k = np.exp(z[1] - z[0])
    gasto_k = pol.gasto * np.exp(-z[0])
    dlogk = y_k - c_k - gasto_k - (eco.delta + eco.n + eco.g)
    dlogc = ((1 - pol.tau_k) * (eco.alpha * y_k - eco.delta)
             - eco.rho - eco.theta * eco.g) / eco.theta
    return dlogk, dlogc


def _jacobiano_campo(eco: Economia, pol: Politica, z: np.ndarray):
    y_k = np.exp((eco.alpha - 1) * z[0])
    c_k = np.exp(z[1] - z[0])
    gasto_k = pol.gasto * np.exp(-z[0])
    return ((eco.alpha - 1) * y_k + c_k + gasto_k, -c_k,
            (1 - pol.tau_k) * eco.alpha * (eco.alpha - 1) * y_k / eco.theta, 0.0 * y_k)


def _regimes(politicas) -> tuple[tuple[float, Politica], ...]:
    """Aceita uma Politica ou uma lista [(inicio, Politica), ...] com inicio 0."""
    if isinstance(politicas, Politica):
        return ((0.0, politicas),)
    regimes = tuple((float(t), p) for t, p in politicas)
    inicios = [t for t, _ in regimes]
    if not regimes or inicios[0] != 0 or np.any(np.diff(inicios) <= 0):
        raise ValueError("os regimes devem começar em t = 0, em ordem crescente")
    return regimes


@dataclass(frozen=True)
class Trajetoria:
    """Solução do equilíbrio em [0, fim]; depois de `fim` vale o estado final."""

    eco: Economia
    regimes: tuple
    k0: float
    fim: float
    final: EstadoEstacionario
    _sol: object

    def _indice(self, t: np.ndarray) -> np.ndarray:
        inicios = np.array([r[0] for r in self.regimes])
        return np.searchsorted(inicios, t, side="right") - 1

    def avaliar(self, t):
        """Devolve (k(t), c(t)). Nas datas de mudança vale o regime novo."""
        t = np.asarray(t, dtype=float)
        tt = np.atleast_1d(t)
        if np.any(tt < 0) or np.any(tt > self.fim + 1e-9):
            raise ValueError(f"t deve estar em [0, {self.fim:g}]")
        inicios = np.array([r[0] for r in self.regimes])
        duracoes = np.diff(np.append(inicios, self.fim))
        j = self._indice(tt)
        z = self._sol.sol(np.clip((tt - inicios[j]) / duracoes[j], 0, 1))
        colunas = np.arange(tt.size)
        k = np.exp(z[2 * j, colunas])
        c = np.exp(z[2 * j + 1, colunas])
        if t.ndim == 0:
            return float(k[0]), float(c[0])
        return k, c

    def politica(self, t) -> list[Politica]:
        return [self.regimes[j][1] for j in self._indice(np.atleast_1d(t))]

    def tabela(self, t) -> pd.DataFrame:
        """Variáveis de equilíbrio por unidade de trabalho efetivo."""
        t = np.atleast_1d(np.asarray(t, dtype=float))
        k, c = self.avaliar(t)
        j = self._indice(t)
        tau_k = np.array([p.tau_k for _, p in self.regimes])[j]
        tau_c = np.array([p.tau_c for _, p in self.regimes])[j]
        gasto = np.array([p.gasto for _, p in self.regimes])[j]
        a = self.eco.alpha
        y = k**a
        lucro_liquido = a * k ** (a - 1) - self.eco.delta   # R - delta
        receita = tau_k * lucro_liquido * k + tau_c * c
        return pd.DataFrame({
            "t": t, "k": k, "c": c, "y": y,
            "investimento": y - c - gasto,
            "gasto": gasto,
            "r": (1 - tau_k) * lucro_liquido,
            "salario": (1 - a) * y,
            "receita": receita,
            "transferencia": receita - gasto,
        })


def resolver_transicao(eco: Economia, k0: float, politicas,
                       horizonte: float = 150.0, tol: float = 1e-8) -> Trajetoria:
    """
    Resolve o caminho de sela a partir de k(0) = k0.

    `politicas` é uma Politica ou uma lista [(inicio, Politica), ...]. Todas as
    datas são conhecidas em t = 0, de modo que a lista representa tanto um
    choque inesperado (um regime novo desde 0) quanto um anúncio.

    Cada regime é um trecho reescalado para s em [0, 1] e os trechos são
    empilhados num único problema de contorno. As condições são:
      - k(0) = k0;
      - k contínuo nas mudanças de regime; log c salta apenas se tau_c muda,
        pois o multiplicador da família é contínuo e x^-theta = mu (1 + tau_c);
      - no fim do último trecho, (k, c) está sobre a direção estável do
        estado estacionário final (aproximação linear do braço de sela).
    `horizonte` é a duração do último regime até o corte numérico.
    """
    if k0 <= 0:
        raise ValueError("k0 deve ser positivo")
    regimes = _regimes(politicas)
    inicios = np.array([t for t, _ in regimes])
    fim = inicios[-1] + horizonte
    duracoes = np.diff(np.append(inicios, fim))
    m = len(regimes)
    final = estado_estacionario(eco, regimes[-1][1])

    def edo(_s, z):
        dz = np.empty_like(z)
        for j, (_, pol) in enumerate(regimes):
            dk, dc = _campo(eco, pol, z[2 * j:2 * j + 2])
            dz[2 * j] = duracoes[j] * dk
            dz[2 * j + 1] = duracoes[j] * dc
        return dz

    def edo_jac(_s, z):
        jac = np.zeros((2 * m, 2 * m, z.shape[1]))
        for j, (_, pol) in enumerate(regimes):
            blocos = _jacobiano_campo(eco, pol, z[2 * j:2 * j + 2])
            i = 2 * j
            jac[i, i], jac[i, i + 1], jac[i + 1, i], jac[i + 1, i + 1] = (
                duracoes[j] * b for b in blocos)
        return jac

    saltos = [np.log((1 + regimes[j][1].tau_c) / (1 + regimes[j + 1][1].tau_c)) / eco.theta
              for j in range(m - 1)]

    def contorno(za, zb):
        residuos = [za[0] - np.log(k0)]
        for j in range(m - 1):
            residuos.append(za[2 * j + 2] - zb[2 * j])
            residuos.append(za[2 * j + 3] - zb[2 * j + 1] - saltos[j])
        k_fim, c_fim = np.exp(zb[-2:])
        residuos.append((c_fim - final.c - final.inclinacao * (k_fim - final.k)) / final.c)
        return np.array(residuos)

    # Chute inicial: convergência exponencial ao estado final, com c sobre
    # uma aproximação do braço estável (em potência, para manter c > 0).
    s = np.linspace(0, 1, 101)
    elasticidade = final.inclinacao * final.k / final.c
    chute = np.empty((2 * m, s.size))
    for j in range(m):
        t = inicios[j] + duracoes[j] * s
        k = final.k + (k0 - final.k) * np.exp(final.lambda_estavel * t)
        chute[2 * j] = np.log(k)
        chute[2 * j + 1] = np.log(final.c) + elasticidade * np.log(k / final.k)

    sol = solve_bvp(edo, contorno, s, chute, fun_jac=edo_jac, tol=tol, max_nodes=100_000)
    if not sol.success:
        raise RuntimeError(f"o problema de contorno não convergiu: {sol.message}")
    return Trajetoria(eco, regimes, float(k0), float(fim), final, sol)


def fluxos_anuais(traj: Trajetoria, anos: int) -> pd.DataFrame:
    """
    Agregados anuais observáveis, com A(0) = L(0) = 1.

    Produto, consumo, gasto e investimento bruto são fluxos integrados no ano
    [j-1, j]; o capital é o estoque no fim do ano, K(j). A integral usa
    Gauss-Legendre com 16 nós, separando o ano nas datas de mudança de regime.
    """
    if anos > traj.fim:
        raise ValueError("anos não pode passar do fim da trajetória")
    nos, pesos = np.polynomial.legendre.leggauss(16)
    crescimento = traj.eco.n + traj.eco.g
    trocas = [t for t, _ in traj.regimes[1:]]
    trechos = []   # (ano, a, b): subintervalos de cada ano sem mudança de regime
    for ano in range(1, anos + 1):
        cortes = sorted({ano - 1.0, float(ano)} | {t for t in trocas if ano - 1 < t < ano})
        trechos += [(ano, a, b) for a, b in zip(cortes[:-1], cortes[1:])]
    ano, a, b = (np.array(v) for v in zip(*trechos))
    meio, raio = ((a + b) / 2)[:, None], ((b - a) / 2)[:, None]
    t = meio + raio * nos
    tab = traj.tabela(t.ravel())
    peso = (np.exp(crescimento * t) * raio * pesos).ravel()
    indice = np.repeat(ano - 1, nos.size)

    def integral(v):
        return np.bincount(indice, weights=peso * tab[v].to_numpy(), minlength=anos)

    Y, C, G, K_medio = (integral(v) for v in ("y", "c", "gasto", "k"))
    fins = np.arange(1, anos + 1, dtype=float)
    k_fim, _ = traj.avaliar(fins)
    return pd.DataFrame({"ano": fins.astype(int), "K_fim": np.exp(crescimento * fins) * k_fim,
                         "Y": Y, "C": C, "G": G, "I": Y - C - G, "K_medio": K_medio})


def _utilidade(c, theta):
    return np.log(c) if theta == 1 else c ** (1 - theta) / (1 - theta)


def valor(traj_ou_ee, eco: Economia | None = None) -> float:
    """
    V = integral de e^{-beta t} u(c(t)) dt, com u CRRA em c = C/(AL).

    Como x = C/L = e^{gt} c, a utilidade da dinastia é proporcional a V (para
    theta = 1 difere dela por uma constante comum a todas as trajetórias).
    Aceita uma Trajetoria ou um EstadoEstacionario (com `eco`).
    """
    if isinstance(traj_ou_ee, EstadoEstacionario):
        return _utilidade(traj_ou_ee.c, eco.theta) / eco.beta
    traj = traj_ou_ee
    beta, theta = traj.eco.beta, traj.eco.theta
    nos, pesos = np.polynomial.legendre.leggauss(16)
    trocas = [t for t, _ in traj.regimes[1:]]
    cortes = np.unique(np.concatenate([np.arange(0, traj.fim, 1.0), trocas, [traj.fim]]))
    total = 0.0
    for a, b in zip(cortes[:-1], cortes[1:]):
        t = (a + b) / 2 + (b - a) / 2 * nos
        _, c = traj.avaliar(t)
        total += (b - a) / 2 * pesos @ (np.exp(-beta * t) * _utilidade(c, theta))
    _, c_fim = traj.avaliar(traj.fim)
    return total + np.exp(-beta * traj.fim) * _utilidade(c_fim, theta) / beta


def ganho_bem_estar(nova, referencia, eco: Economia | None = None) -> float:
    """
    Variação equivalente em consumo: fração lambda do consumo em todas as
    datas que deixaria a família indiferente entre `referencia` e `nova`.
    """
    eco = eco or nova.eco
    v_nova, v_ref = valor(nova, eco), valor(referencia, eco)
    if eco.theta == 1:
        return float(np.expm1(eco.beta * (v_nova - v_ref)))
    return float((v_nova / v_ref) ** (1 / (1 - eco.theta)) - 1)


def receita_estacionaria(eco: Economia, pol: Politica) -> dict:
    """Receita de longo prazo por unidade de trabalho efetivo e como fração de y."""
    ee = estado_estacionario(eco, pol)
    capital = pol.tau_k * (eco.alpha * ee.y - eco.delta * ee.k)
    consumo = pol.tau_c * ee.c
    return {"capital": capital, "consumo": consumo,
            "capital_pib": capital / ee.y, "consumo_pib": consumo / ee.y}
