"""
Modelo de Aiyagari em tempo contínuo com governo: famílias heterogêneas com
risco de renda não segurável, resolvido pelo sistema Hamilton-Jacobi-Bellman
e Kolmogorov (Achdou, Han, Lasry, Lions e Moll, 2022).

Cada família (uma dinastia, como em modelo.py) tem riqueza a >= a_min por
membro, em unidades de eficiência, e produtividade z que muda segundo uma
cadeia de Markov em tempo contínuo. Com r_liq = (1 - tau_k) r,

    da/dt = (r_liq - n - g) a + (1 - tau_w) w z + T_z - c
    beta V_z(a) = max_c u(c) + V_z'(a) da/dt + sum_z' q[z, z'] (V_z'(a) - V_z(a))

e beta = rho - n - (1 - theta) g, exatamente como no modelo representativo.
A firma é a mesma: r = alpha K^(alpha-1) - delta e w = (1 - alpha) K^alpha,
com oferta de trabalho efetivo E[z] = 1. O governo financia o gasto G com
tau_k sobre a renda do capital e tau_w sobre a do trabalho; o saldo volta às
famílias como transferência, igual para todos ou focalizada por estado de z.

Sem risco, as famílias seguem a regra de consumo do modelo representativo;
com risco, a poupança precaucional mantém r_liq abaixo de rho + theta g.

A distribuição é guardada como massas de probabilidade nos pontos da grade
(soma 1), o que vale igualmente para grades não uniformes.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np
import scipy.sparse as sp
from scipy.optimize import brentq
from scipy.sparse.linalg import spsolve

from modelo import Economia, _utilidade


@dataclass(frozen=True)
class Renda:
    """
    Produtividades z e intensidades anuais de transição entre os estados.
    Se a cadeia tiver tipos permanentes (blocos sem transição entre si), a
    distribuição de longo prazo `pi` precisa ser informada.
    """

    z: tuple
    intensidades: tuple   # matriz J x J; a diagonal é ignorada
    pi: tuple | None = None

    @property
    def gerador(self) -> np.ndarray:
        q = np.array(self.intensidades, dtype=float)
        np.fill_diagonal(q, 0.0)
        np.fill_diagonal(q, -q.sum(axis=1))
        return q

    @property
    def estacionaria(self) -> np.ndarray:
        """Distribuição de longo prazo pi, com pi q = 0 e soma 1."""
        if self.pi is not None:
            return np.asarray(self.pi, dtype=float)
        q = self.gerador
        sistema = np.vstack([q.T, np.ones(len(self.z))])
        lado_direito = np.zeros(len(self.z) + 1)
        lado_direito[-1] = 1.0
        return np.linalg.lstsq(sistema, lado_direito, rcond=None)[0]


def renda_dois_estados(razao: float, saida_baixo: float, saida_alto: float) -> Renda:
    """
    Dois estados, baixo e alto, com z_baixo = razao * z_alto e E[z] = 1.
    `saida_baixo` e `saida_alto` são as taxas anuais de saída de cada estado;
    a duração média em cada um é o inverso da taxa.
    """
    pi_baixo = saida_alto / (saida_baixo + saida_alto)
    z_alto = 1.0 / (pi_baixo * razao + 1 - pi_baixo)
    return Renda(z=(razao * z_alto, z_alto),
                 intensidades=((0.0, saida_baixo), (saida_alto, 0.0)))


@dataclass(frozen=True)
class Governo:
    """Alíquotas, gasto (G/AL) e divisão da transferência média entre estados."""

    tau_k: float = 0.0
    tau_w: float = 0.0
    gasto: float = 0.0
    pesos: tuple | None = None   # T_z = pesos_z * T médio, com média ponderada 1

    def transferencias(self, renda: Renda, media) -> np.ndarray:
        """T_z para uma transferência média (escalar ou vetor no tempo)."""
        pesos = np.ones(len(renda.z)) if self.pesos is None else np.asarray(self.pesos, float)
        pesos = pesos / (renda.estacionaria @ pesos)
        return np.multiply.outer(np.asarray(media, dtype=float), pesos)


@dataclass(frozen=True)
class Grade:
    """Grade de riqueza mais densa perto de a_min: a = a_min + (a_max - a_min) x^curvatura."""

    a_min: float = 0.0
    a_max: float = 60.0
    pontos: int = 1000
    curvatura: float = 1.0

    @property
    def a(self) -> np.ndarray:
        x = np.linspace(0.0, 1.0, self.pontos)
        return self.a_min + (self.a_max - self.a_min) * x**self.curvatura

    @property
    def passos(self) -> np.ndarray:
        return np.diff(self.a)


def precos(eco: Economia, K):
    """Retorno líquido de depreciação e salário, com trabalho efetivo igual a 1."""
    K = np.asarray(K, dtype=float)
    return eco.alpha * K ** (eco.alpha - 1) - eco.delta, (1 - eco.alpha) * K**eco.alpha


def capital_demandado(eco: Economia, r):
    return (eco.alpha / (np.asarray(r) + eco.delta)) ** (1 / (1 - eco.alpha))


@dataclass
class Familias:
    """Solução do problema das famílias para preços dados."""

    V: np.ndarray        # (pontos, J)
    c: np.ndarray
    poupanca: np.ndarray
    A: sp.csr_matrix     # gerador do processo (a, z), ordenado por blocos de z


def _politica(eco: Economia, grade: Grade, V: np.ndarray, fluxo: np.ndarray):
    """
    Consumo por diferenças finitas upwind. `fluxo` é a renda sem o consumo,
    (r_liq - n - g) a + renda do trabalho + transferência. Nas bordas da grade
    impõe-se poupança nula (restrição de estado).
    """
    theta = eco.theta
    dVf, dVb = np.empty_like(V), np.empty_like(V)
    dVf[:-1] = dVb[1:] = (V[1:] - V[:-1]) / grade.passos[:, None]
    dVf[-1] = fluxo[-1] ** -theta
    dVb[0] = fluxo[0] ** -theta
    cf = np.maximum(dVf, 1e-12) ** (-1 / theta)
    cb = np.maximum(dVb, 1e-12) ** (-1 / theta)
    sf, sb = fluxo - cf, fluxo - cb
    para_frente = sf > 0
    para_tras = (sb < 0) & ~para_frente
    c = np.where(para_frente, cf, np.where(para_tras, cb, fluxo))
    sf = np.where(para_frente, sf, 0.0)
    sb = np.where(para_tras, sb, 0.0)
    return c, sf, sb


def _gerador(grade: Grade, renda: Renda, sf: np.ndarray, sb: np.ndarray) -> sp.csr_matrix:
    """Gerador infinitesimal: deriva da riqueza (upwind) mais saltos de z."""
    I, h = grade.pontos, grade.passos
    abaixo, acima = np.zeros_like(sb), np.zeros_like(sf)
    abaixo[1:] = -sb[1:] / h[:, None]      # em a_min, sb = 0: nunca liga blocos
    acima[:-1] = sf[:-1] / h[:, None]      # em a_max, sf = 0
    abaixo, acima = abaixo.ravel(order="F"), acima.ravel(order="F")
    deriva = sp.diags([abaixo[1:], -(abaixo + acima), acima[:-1]], [-1, 0, 1],
                      shape=(I * len(renda.z),) * 2)
    return (deriva + sp.kron(sp.csr_matrix(renda.gerador), sp.eye(I))).tocsr()


def _fluxo(eco: Economia, grade: Grade, r_liq: float, renda_nao_capital) -> np.ndarray:
    fluxo = (r_liq - eco.n - eco.g) * grade.a[:, None] + np.asarray(renda_nao_capital)[None, :]
    if np.any(fluxo[0] <= 0):
        raise ValueError("a renda na restrição de endividamento precisa ser positiva")
    return fluxo


def resolver_familias(eco: Economia, renda: Renda, grade: Grade, r_liq: float,
                      renda_nao_capital: np.ndarray, V0: np.ndarray | None = None,
                      passo: float = 1000.0, tol: float = 1e-9, max_iter: int = 1000) -> Familias:
    """HJB estacionária por iteração implícita: (1/passo + beta - A) V' = u(c) + V/passo."""
    fluxo = _fluxo(eco, grade, r_liq, renda_nao_capital)
    V = _utilidade(np.maximum(fluxo, 1e-6), eco.theta) / eco.beta if V0 is None else V0
    n = V.size
    for _ in range(max_iter):
        c, sf, sb = _politica(eco, grade, V, fluxo)
        A = _gerador(grade, renda, sf, sb)
        sistema = sp.eye(n) * (1 / passo + eco.beta) - A
        novo = spsolve(sistema.tocsc(), (_utilidade(c, eco.theta) + V / passo).ravel(order="F"))
        novo = novo.reshape(V.shape, order="F")
        convergiu = np.max(np.abs(novo - V)) < tol
        V = novo
        if convergiu:
            break
    else:
        raise RuntimeError("a equação HJB não convergiu")
    c, sf, sb = _politica(eco, grade, V, fluxo)
    return Familias(V, c, fluxo - c, _gerador(grade, renda, sf, sb))


def distribuicao(A: sp.csr_matrix, grade: Grade, renda: Renda, m0: np.ndarray | None = None,
                 passo: float = 1e4, tol: float = 1e-13, max_iter: int = 500) -> np.ndarray:
    """
    Massas estacionárias da equação de Kolmogorov, A' m = 0 com soma 1.
    Itera o passo implícito m' = (I - passo A')^-1 m, que preserva a massa de
    cada tipo permanente e converge mesmo quando parte da grade não é visitada
    (ali a massa é zero e o truque usual de fixar um ponto deixa o sistema
    singular). O ponto de partida distribui pi uniformemente na grade.
    """
    I, J = grade.pontos, len(renda.z)
    m = (np.outer(np.ones(I) / I, renda.estacionaria) if m0 is None else m0).ravel(order="F")
    sistema = (sp.eye(I * J) - passo * A.T).tocsc()
    for _ in range(max_iter):
        novo = np.maximum(spsolve(sistema, m), 0.0)
        novo /= novo.sum()
        convergiu = np.max(np.abs(novo - m)) < tol
        m = novo
        if convergiu:
            break
    return m.reshape((I, J), order="F")


@dataclass
class EquilibrioHA:
    eco: Economia
    renda: Renda
    gov: Governo
    grade: Grade
    r: float
    w: float
    K: float
    transferencia: np.ndarray   # T_z
    familias: Familias
    m: np.ndarray               # massas (pontos, J), soma 1

    @property
    def Y(self) -> float:
        return self.K**self.eco.alpha

    @property
    def r_liq(self) -> float:
        return (1 - self.gov.tau_k) * self.r

    @property
    def C(self) -> float:
        return float(np.sum(self.familias.c * self.m))

    def renda_total(self) -> np.ndarray:
        """Renda disponível de cada ponto (a, z): capital, trabalho e transferência."""
        trabalho = (1 - self.gov.tau_w) * self.w * np.asarray(self.renda.z)
        return self.r_liq * self.grade.a[:, None] + trabalho[None, :] + self.transferencia[None, :]

    def momentos(self) -> dict:
        riqueza = self.grade.a
        massa = self.m.sum(axis=1)
        renda = self.renda_total().ravel()
        ordem = np.argsort(renda)
        return {
            "K/Y": self.K / self.Y,
            "r_liq": self.r_liq,
            "no limite de endividamento": float(massa[0]),
            "Gini da riqueza": gini(riqueza, massa),
            "10% mais ricos (riqueza)": parcela_topo(riqueza, massa, 0.10),
            "50% mais pobres (riqueza)": 1 - parcela_topo(riqueza, massa, 0.50),
            "Gini da renda": gini(renda[ordem], self.m.ravel()[ordem]),
        }


def gini(valores: np.ndarray, massa: np.ndarray) -> float:
    """Gini de uma distribuição discreta com valores crescentes e massas dadas."""
    massa = massa / massa.sum()
    lorenz = np.cumsum(valores * massa) / np.sum(valores * massa)
    lorenz_anterior = np.concatenate([[0.0], lorenz[:-1]])
    return float(1 - np.sum(massa * (lorenz + lorenz_anterior)))


def parcela_topo(valores: np.ndarray, massa: np.ndarray, fracao: float) -> float:
    """Parcela do total que pertence à `fracao` da população com valores mais altos."""
    massa = massa / massa.sum()
    acima = np.cumsum(massa[::-1])[::-1]          # massa com valor >= v_i
    peso = np.clip(fracao - (acima - massa), 0.0, massa)
    return float(np.sum(valores * peso) / np.sum(valores * massa))


def renda_nao_capital(eco: Economia, renda: Renda, gov: Governo, r, K):
    """Salário líquido mais transferência por estado, com o orçamento fechado."""
    _, w = precos(eco, K)
    media = gov.tau_k * np.asarray(r) * np.asarray(K) + gov.tau_w * w - gov.gasto
    transf = gov.transferencias(renda, media)
    return (1 - gov.tau_w) * np.multiply.outer(w, np.asarray(renda.z)) + transf, w, transf


def _resolver_com_precos(eco, renda, gov, grade, r, K, V0=None, m0=None):
    receita, w, transf = renda_nao_capital(eco, renda, gov, r, K)
    fam = resolver_familias(eco, renda, grade, (1 - gov.tau_k) * r, receita, V0)
    m = distribuicao(fam.A, grade, renda, m0)
    return fam, m, float(w), transf


def oferta_de_capital(m: np.ndarray, grade: Grade) -> float:
    return float(np.sum(grade.a[:, None] * m))


def equilibrio(eco: Economia, renda: Renda, gov: Governo, grade: Grade = Grade(),
               tol: float = 1e-10) -> EquilibrioHA:
    """Taxa de juros que iguala a oferta de capital das famílias à demanda da firma."""
    # Sem risco, r_liq = rho + theta g; com risco a poupança precaucional o reduz.
    r_max = (eco.rho + eco.theta * eco.g) / (1 - gov.tau_k) - 1e-6
    cache = {}

    def excesso(r):
        K_d = float(capital_demandado(eco, r))
        fam, m, _, _ = _resolver_com_precos(eco, renda, gov, grade, r, K_d, cache.get("V"))
        cache["V"] = fam.V
        return oferta_de_capital(m, grade) - K_d

    if excesso(r_max) < 0:
        raise ValueError("sem equilíbrio dentro da grade: risco de renda pequeno demais "
                         "para este rho (ou a_max pequeno)")
    r_min = 0.5 * r_max
    while excesso(r_min) > 0:
        r_min *= 0.5
    r = brentq(excesso, r_min, r_max, xtol=tol)
    K = float(capital_demandado(eco, r))
    fam, m, w, transf = _resolver_com_precos(eco, renda, gov, grade, r, K, cache.get("V"))
    return EquilibrioHA(eco, renda, gov, grade, r, w, K, transf, fam, m)


def calibrar_rho(eco: Economia, renda: Renda, gov: Governo, capital_produto: float,
                 gasto_pib: float, grade: Grade = Grade(), tol: float = 1e-10):
    """
    Escolhe rho e tau_w para que o equilíbrio tenha K/Y = `capital_produto`,
    G/Y = `gasto_pib` e transferência nula (o gasto é financiado por tau_k e
    tau_w). Como K/Y fixa r, basta um problema das famílias por candidato a rho.
    Devolve (Economia, Governo) calibrados.
    """
    K = capital_produto ** (1 / (1 - eco.alpha))
    r, w = precos(eco, K)
    gasto = gasto_pib * K**eco.alpha
    gov = replace(gov, gasto=gasto, tau_w=(gasto - gov.tau_k * r * K) / w)
    r_liq = (1 - gov.tau_k) * r
    cache = {}

    def excesso(rho):
        candidato = replace(eco, rho=rho)
        fam, m, _, _ = _resolver_com_precos(candidato, renda, gov, grade, r, K, cache.get("V"))
        cache["V"] = fam.V
        return oferta_de_capital(m, grade) - K

    # A oferta explode quando rho + theta g se aproxima de r_liq por cima; com
    # pouco risco, o rho calibrado fica muito perto desse limite.
    limite = r_liq - eco.theta * eco.g
    folga = 1e-3
    while excesso(limite + folga) < 0:
        folga /= 10
        if folga < 1e-10:
            raise ValueError("risco de renda pequeno demais para sustentar esse K/Y")
    rho_max = limite + 0.05
    while excesso(rho_max) > 0:
        rho_max += 0.05
    rho = brentq(excesso, limite + folga, rho_max, xtol=tol)
    return replace(eco, rho=rho), gov


@dataclass
class TransicaoHA:
    """Caminho de equilíbrio depois de uma mudança de política em t = 0."""

    t: np.ndarray
    K: np.ndarray
    r: np.ndarray
    w: np.ndarray
    transferencia_media: np.ndarray
    tau_k: np.ndarray
    V0: np.ndarray            # valor em t = 0 sob a política nova, (pontos, J)
    m: np.ndarray             # massas ao longo do tempo, (nós, pontos, J)
    C: np.ndarray
    iteracoes: int


def grade_temporal(horizonte: float = 150.0, nos: int = 200) -> np.ndarray:
    """Passos curtos no início, quando a economia mais se move: t_n = T (n/N)^2."""
    return horizonte * np.linspace(0.0, 1.0, nos + 1) ** 2


def transicao(inicial: EquilibrioHA, gov_novo: Governo, final: EquilibrioHA,
              vigencia: float = 0.0, t: np.ndarray | None = None, tol: float = 1e-6,
              relaxamento: float = 0.1, max_iter: int = 500) -> TransicaoHA:
    """
    Choque em t = 0: a política passa de `inicial.gov` para `gov_novo` na data
    `vigencia` (0 = de surpresa; > 0 = anunciada). `final` é o estado
    estacionário com a política nova. Itera no caminho do capital:

      1. dados K(t), calcula r(t), w(t) e a transferência que fecha o orçamento;
      2. resolve a HJB para trás a partir de V_final, com passo implícito
         (1/dt + beta - A_n) V_n = u(c_n) + V_{n+1}/dt;
      3. avança as massas para frente a partir da distribuição inicial,
         (I - dt A_n') m_{n+1} = m_n;
      4. atualiza K(t) com relaxamento até a oferta igualar a demanda.

    A oferta de capital reage muito a juros futuros (a curva de oferta do
    modelo de Aiyagari é quase horizontal perto de rho + theta g), então o
    passo 4 precisa de relaxamento pequeno: com 0,3 a iteração oscila e diverge.
    """
    eco, renda, grade = inicial.eco, inicial.renda, inicial.grade
    t = grade_temporal() if t is None else t
    dt = np.diff(t)
    N, I, J = len(dt), grade.pontos, len(renda.z)
    tau_k = np.where(t < vigencia, inicial.gov.tau_k, gov_novo.tau_k)
    K = final.K + (inicial.K - final.K) * np.exp(-0.06 * t)   # chute: convergência de ~6% ao ano
    identidade = sp.eye(I * J)
    for iteracao in range(1, max_iter + 1):
        r, w = precos(eco, K)
        media = tau_k * r * K + gov_novo.tau_w * w - gov_novo.gasto
        receitas = ((1 - gov_novo.tau_w) * np.multiply.outer(w, np.asarray(renda.z))
                    + gov_novo.transferencias(renda, media))
        V = final.familias.V
        geradores = [None] * N
        consumo = np.zeros((N + 1, I, J))
        for n in range(N - 1, -1, -1):
            fluxo = _fluxo(eco, grade, (1 - tau_k[n]) * r[n], receitas[n])
            c, sf, sb = _politica(eco, grade, V, fluxo)
            A = _gerador(grade, renda, sf, sb)
            sistema = identidade * (1 / dt[n] + eco.beta) - A
            V = spsolve(sistema.tocsc(), (_utilidade(c, eco.theta) + V / dt[n]).ravel(order="F"))
            V = V.reshape((I, J), order="F")
            geradores[n], consumo[n] = A, c
        consumo[N] = final.familias.c
        m = np.empty((N + 1, I, J))
        m[0] = inicial.m
        for n in range(N):
            proximo = spsolve((identidade - dt[n] * geradores[n].T).tocsc(), m[n].ravel(order="F"))
            m[n + 1] = proximo.reshape((I, J), order="F")
        K_novo = np.einsum("i,nij->n", grade.a, m)
        erro = np.max(np.abs(K_novo - K) / K)
        K = (1 - relaxamento) * K + relaxamento * K_novo
        if erro < tol:
            break
    else:
        raise RuntimeError("a transição não convergiu")
    r, w = precos(eco, K)
    media = tau_k * r * K + gov_novo.tau_w * w - gov_novo.gasto
    C = np.einsum("nij,nij->n", consumo, m)
    return TransicaoHA(t, K, r, w, media, tau_k, V, m, C, iteracao)


def ganho_bem_estar(V_novo: np.ndarray, V_antigo: np.ndarray, theta: float) -> np.ndarray:
    """
    Variação equivalente por ponto (a, z): fração do consumo, em todas as datas,
    que deixaria a família indiferente entre ficar no equilíbrio antigo e a
    trajetória nova. Com u CRRA, V escala com (1 + lambda)^(1 - theta).
    """
    if theta == 1:
        raise NotImplementedError("use theta diferente de 1 (com log, lambda = exp(beta dV) - 1)")
    return (V_novo / V_antigo) ** (1 / (1 - theta)) - 1
