"""Testes do problema das famílias. Rode da pasta Econometria/:

    python -m unittest discover -s Python/macroeconomia/Forecast/Brasil/2013T4-2026T2/abm1_com_leiloeiro -v
"""
import sys
import unittest
from dataclasses import replace
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))   # macroeconomia/
import caminhos  # noqa: E402,F401

import familias as F  # noqa: E402
from calibracao import calcular_alvos, calibrar as calibrar_representativo, carregar_dados  # noqa: E402
from calibracao_renda import renda_brasil  # noqa: E402


def economia_calibrada():
    alvos = calcular_alvos(carregar_dados())
    eco, pol = calibrar_representativo(alvos)
    renda = F.Renda.de_continua(renda_brasil())
    par = F.Parametros(eco.alpha, eco.delta, 0.0, eco.theta, eco.n, eco.g, pol.tau_k)
    return F.calibrar(par, renda, alvos.capital_produto, alvos.gasto_pib), alvos


class TestRenda(unittest.TestCase):
    def test_transicao_trimestral(self):
        continua = renda_brasil()
        renda = F.Renda.de_continua(continua)
        np.testing.assert_allclose(renda.P.sum(axis=1), 1.0, atol=1e-12)
        np.testing.assert_allclose(renda.pi @ renda.P, renda.pi, atol=1e-12)
        self.assertAlmostEqual(renda.pi @ renda.z, 1.0)
        # Com período curto, P = I + Q D a menos de O(D^2).
        curta = F.Renda.de_continua(continua, periodo=1e-5)
        np.testing.assert_allclose((curta.P - np.eye(9)) / 1e-5, continua.gerador, atol=1e-3)


class TestPolitica(unittest.TestCase):
    def test_sem_risco_igual_a_solucao_analitica(self):
        # Um só estado e renda constante: longe da restrição, D c = (m + H)(1 - G_c / R),
        # com R = (1 + r D) e^{-(g+n) D}, G_c = (e^{-rho D}(1 + r D) e^{-theta g D})^{1/theta}
        # e H = D y / (R - 1), o valor presente da renda futura.
        renda = F.Renda(np.array([1.0]), np.array([[1.0]]), np.array([1.0]), np.array([0]))
        par = F.Parametros(alpha=0.4, delta=0.05, rho=0.05, theta=2.0, n=0.01, g=0.01)
        r, y, D = 0.05, 1.0, par.periodo
        pol = F.resolver_politica(par, renda, r, np.array([y]), F.grade_potencia(20_000, 400, 2.5))
        R = (1 + r * D) * np.exp(-(par.g + par.n) * D)
        G_c = (np.exp(-par.rho * D) * (1 + r * D) * np.exp(-par.theta * par.g * D)) ** (1 / par.theta)
        H = D * y / (R - 1)
        for m in (3000.0, 6000.0):
            analitico = (m + H) * (1 - G_c / R) / D
            self.assertAlmostEqual(pol.consumo(np.array([m]), np.array([0]))[0] / analitico, 1, places=3)

    def test_equacao_de_euler_com_risco(self):
        est, _ = economia_calibrada()
        par, renda, pol = est.par, est.renda, est.politica
        D = par.periodo
        beta_r = np.exp(-par.rho * D) * (1 + est.r * D) * np.exp(-par.theta * par.g * D)
        rng = np.random.default_rng(0)
        for j in range(renda.estados):
            m = rng.uniform(1.0, 60.0, 200)
            c = pol.consumo(m, np.full(m.size, j))
            s = m - D * c
            interior = s > 1e-3
            m_prox = (1 + est.r * D) * s[interior, None] * par.fator_crescimento + D * pol.renda[None, :]
            c_prox = np.column_stack([pol.consumo(m_prox[:, k], np.full(m_prox.shape[0], k))
                                      for k in range(renda.estados)])
            direita = beta_r * (c_prox ** -par.theta) @ renda.P[j]
            erro = np.abs(direita ** (-1 / par.theta) / c[interior] - 1)
            self.assertLess(erro.max(), 2e-3, msg=f"estado {j}")

    def test_restricao_de_endividamento(self):
        est, _ = economia_calibrada()
        m = np.linspace(1e-4, 0.05, 20)
        for j in range(est.renda.estados):
            c = est.politica.consumo(m, np.full(m.size, j))
            self.assertTrue(np.all(est.par.periodo * c <= m + 1e-12))


class TestEquilibrio(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.est, cls.alvos = economia_calibrada()

    def test_calibracao_reproduz_os_alvos(self):
        est = self.est
        self.assertAlmostEqual(est.K / est.y, self.alvos.capital_produto, places=10)
        self.assertAlmostEqual(est.par.gasto / est.y, self.alvos.gasto_pib, places=10)
        self.assertAlmostEqual(est.distribuicao.media / est.K, 1, places=6)
        self.assertAlmostEqual(est.transferencia, 0.0, places=10)
        self.assertLess(est.r, est.par.r_limite())   # poupança precaucional

    def test_distribuicao(self):
        massa = self.est.distribuicao.massa
        self.assertAlmostEqual(massa.sum(), 1.0, places=10)
        np.testing.assert_allclose(massa.sum(axis=0), self.est.renda.pi, atol=1e-10)
        self.assertLess(massa[-50:].sum(), 1e-8)   # a grade de riqueza basta

    def test_histograma_e_estacionario_para_as_familias_simuladas(self):
        # Preços fixos: 20 mil famílias sorteadas do histograma e simuladas por 400
        # trimestres mantêm a riqueza média e a massa de cada estado. (Partindo de
        # longe, a convergência leva milhares de trimestres: os ricos acumulam
        # devagar, com o juro perto do limite.)
        est = self.est
        par, renda, pol = est.par, est.renda, est.politica
        rng = np.random.default_rng(1)
        N = 20_000
        dist = est.distribuicao
        sorteio = rng.choice(dist.massa.size, size=N, p=dist.massa.ravel() / dist.massa.sum())
        a, j = dist.grade_a[sorteio // renda.estados], sorteio % renda.estados
        acumulada = np.cumsum(renda.P, axis=1)
        medias = []
        for _ in range(400):
            j = np.minimum((rng.random(N)[:, None] > acumulada[j]).sum(axis=1), renda.estados - 1)
            m = (1 + est.r * par.periodo) * a + par.periodo * pol.renda[j]
            a = (m - par.periodo * pol.consumo(m, j)) * par.fator_crescimento
            medias.append(a.mean())
        self.assertAlmostEqual(np.mean(medias) / dist.media, 1, delta=0.02)
        np.testing.assert_allclose(np.bincount(j, minlength=renda.estados) / N, renda.pi, atol=0.01)

    def test_equilibrio_recupera_o_capital_calibrado(self):
        est = self.est
        novo = F.equilibrio(est.par, est.renda, K_inicial=est.K * 1.02)
        self.assertAlmostEqual(novo.K / est.K, 1, places=5)

    def test_imposto_maior_reduz_o_capital(self):
        est = self.est
        novo = F.equilibrio(replace(est.par, tau_k=est.par.tau_k + 0.0085), est.renda, K_inicial=est.K)
        self.assertLess(novo.K, est.K)
        self.assertGreater(novo.transferencia, 0.0)


class TestTabela(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.est, _ = economia_calibrada()
        est = cls.est
        cls.perfil = (1 - est.par.tau_w) * est.renda.z
        cls.tabela = F.TabelaPoliticas(est.par, est.renda, cls.perfil, r_exatos=(est.r,))

    def test_no_exato_igual_a_politica_de_equilibrio(self):
        est = self.est
        m = np.linspace(0.01, 40, 300)
        for j in range(est.renda.estados):
            jj = np.full(m.size, j)
            direto = est.politica.consumo(m, jj)
            tabela = self.tabela.consumo(m, jj, est.r, est.w)
            np.testing.assert_allclose(tabela, direto, rtol=2e-3)

    def test_entre_nos_perto_da_solucao_direta(self):
        est = self.est
        r = est.r - 0.004
        direta = F.resolver_politica(est.par, est.renda, r, self.perfil, F.Grades().poupanca())
        m = np.linspace(0.05, 30, 200)
        for j in (0, 4, 8):
            jj = np.full(m.size, j)
            np.testing.assert_allclose(self.tabela.consumo_unitario(m, jj, r), direta.consumo(m, jj),
                                       rtol=0.01)

    def test_homogeneidade_no_salario(self):
        m, j = np.array([2.0, 5.0]), np.array([0, 3])
        self.assertTrue(np.allclose(self.tabela.consumo(2 * m, j, self.est.r, 2.0),
                                    2 * self.tabela.consumo(m, j, self.est.r, 1.0)))


if __name__ == "__main__":
    unittest.main()
