"""Testes do modelo de Aiyagari em tempo contínuo (aiyagari.py)."""
import unittest
from dataclasses import replace

import numpy as np

from aiyagari import (Governo, Grade, Renda, calibrar_rho, distribuicao, equilibrio,
                      ganho_bem_estar, gini, grade_temporal, parcela_topo, precos,
                      renda_dois_estados, resolver_familias, transicao)
from calibracao import calcular_alvos, calibrar, carregar_dados
from modelo import Economia

SEM_RISCO = Renda(z=(1.0,), intensidades=((0.0,),))
RISCO = renda_dois_estados(0.5, 1.0, 1 / 9)


class TestFamilias(unittest.TestCase):
    def test_sem_risco_segue_a_regra_de_consumo_do_modelo_representativo(self):
        # Sem risco e com r_liq > rho + theta g, a restrição nunca aperta e
        # c = m (a + y / r_til), com r_til = r_liq - n - g e m = r_til - (r_til - beta)/theta.
        eco, grade, renda_trabalho, r_liq = Economia(), Grade(a_max=40, pontos=2000), 1.0, 0.09
        fam = resolver_familias(eco, SEM_RISCO, grade, r_liq, np.array([renda_trabalho]))
        r_til = r_liq - eco.n - eco.g
        m = r_til - (r_til - eco.beta) / eco.theta
        a = grade.a
        exato = m * (a + renda_trabalho / r_til)
        metade = a < 15
        np.testing.assert_allclose(fam.c[metade, 0], exato[metade], rtol=2e-3)

    def test_sem_risco_e_r_igual_a_rho_mais_theta_g_nao_ha_poupanca(self):
        eco, grade = Economia(), Grade(a_max=20, pontos=400)
        r_liq = eco.rho + eco.theta * eco.g
        fam = resolver_familias(eco, SEM_RISCO, grade, r_liq, np.array([1.0]))
        self.assertLess(np.max(np.abs(fam.poupanca)), 1e-6)

    def test_gerador_e_distribuicao(self):
        eco, grade = Economia(rho=0.06), Grade(a_max=40, pontos=500)
        fam = resolver_familias(eco, RISCO, grade, 0.05, np.asarray(RISCO.z))
        np.testing.assert_allclose(np.asarray(fam.A.sum(axis=1)).ravel(), 0, atol=1e-10)
        m = distribuicao(fam.A, grade, RISCO)
        self.assertTrue(np.all(m >= 0))
        self.assertAlmostEqual(m.sum(), 1.0, places=12)
        residuo = fam.A.T @ m.ravel(order="F")
        self.assertLess(np.max(np.abs(residuo)), 1e-10)
        # A massa em cada estado de renda é a distribuição estacionária da cadeia.
        np.testing.assert_allclose(m.sum(axis=0), RISCO.estacionaria, atol=1e-10)


class TestEquilibrio(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.alvos = calcular_alvos(carregar_dados())
        cls.eco_ra, cls.pol_ra = calibrar(cls.alvos)
        cls.eco, cls.gov = calibrar_rho(cls.eco_ra, RISCO, Governo(tau_k=cls.pol_ra.tau_k),
                                        cls.alvos.capital_produto, cls.alvos.gasto_pib)
        cls.eq = equilibrio(cls.eco, RISCO, cls.gov)

    def test_calibracao_reproduz_K_Y_com_rho_acima_do_representativo(self):
        self.assertAlmostEqual(self.eq.K / self.eq.Y, self.alvos.capital_produto, places=6)
        # A poupança precaucional exige famílias mais impacientes para o mesmo K/Y.
        self.assertGreater(self.eco.rho, self.eco_ra.rho)
        self.assertLess(self.eq.r_liq, self.eco.rho + self.eco.theta * self.eco.g)

    def test_contabilidade(self):
        eq, eco = self.eq, self.eco
        self.assertAlmostEqual(np.sum(eq.grade.a[:, None] * eq.m), eq.K, places=6)
        recursos = eq.C + self.gov.gasto + (eco.delta + eco.n + eco.g) * eq.K
        self.assertAlmostEqual(recursos / eq.Y, 1.0, places=6)
        # Na calibração, tau_k e tau_w financiam exatamente o gasto.
        r, w = precos(eco, eq.K)
        self.assertAlmostEqual(self.gov.tau_k * r * eq.K + self.gov.tau_w * w, self.gov.gasto, places=8)
        np.testing.assert_allclose(eq.transferencia, 0.0, atol=1e-8)
        self.assertLess(eq.m[eq.grade.a > 40].sum(), 1e-10)

    def test_grade_nao_uniforme_da_o_mesmo_equilibrio(self):
        outro = equilibrio(self.eco, RISCO, self.gov, Grade(pontos=500, curvatura=2.0))
        self.assertAlmostEqual(outro.K / self.eq.K, 1.0, delta=2e-3)

    def test_mais_risco_reduz_os_juros(self):
        arriscada = renda_dois_estados(0.3, 1.0, 1 / 9)
        outro = equilibrio(self.eco, arriscada, self.gov)
        self.assertLess(outro.r, self.eq.r)
        self.assertGreater(outro.K, self.eq.K)

    def test_transferencia_focalizada(self):
        gov = replace(self.gov, tau_k=self.gov.tau_k + 0.02, pesos=(1.0, 0.0))
        eq = equilibrio(self.eco, RISCO, gov)
        pi = RISCO.estacionaria
        self.assertGreater(eq.transferencia[0], 0)
        self.assertEqual(eq.transferencia[1], 0)
        r, w = precos(self.eco, eq.K)
        receita = gov.tau_k * r * eq.K + gov.tau_w * w - gov.gasto
        self.assertAlmostEqual(pi @ eq.transferencia, receita, places=8)


class TestTransicao(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        alvos = calcular_alvos(carregar_dados())
        eco, pol = calibrar(alvos)
        cls.grade = Grade(a_max=60, pontos=250, curvatura=2.0)
        cls.eco, cls.gov = calibrar_rho(eco, RISCO, Governo(tau_k=pol.tau_k),
                                        alvos.capital_produto, alvos.gasto_pib, cls.grade)
        cls.eq0 = equilibrio(cls.eco, RISCO, cls.gov, cls.grade)
        cls.gov1 = replace(cls.gov, tau_k=cls.gov.tau_k + 0.05)
        cls.eq1 = equilibrio(cls.eco, RISCO, cls.gov1, cls.grade)
        cls.t = grade_temporal(150.0, 80)
        cls.tr = transicao(cls.eq0, cls.gov1, cls.eq1, t=cls.t)

    def test_sem_mudanca_de_politica_a_economia_fica_parada(self):
        tr = transicao(self.eq0, self.gov, self.eq0, t=self.t)
        np.testing.assert_allclose(tr.K, self.eq0.K, rtol=1e-6)
        lam = ganho_bem_estar(tr.V0, self.eq0.familias.V, self.eco.theta)
        self.assertLess(np.max(np.abs(lam)), 1e-6)

    def test_caminho_vai_do_estado_inicial_ao_final(self):
        tr = self.tr
        self.assertAlmostEqual(tr.K[0], self.eq0.K, places=8)
        self.assertAlmostEqual(tr.K[-1] / self.eq1.K, 1.0, delta=1e-3)
        # O capital cai monotonamente (o fim do horizonte numérico fica de fora).
        self.assertTrue(np.all(np.diff(tr.K[tr.t <= 100]) < 1e-9))
        np.testing.assert_allclose(tr.m.sum(axis=(1, 2)), 1.0, atol=1e-10)

    def test_quem_ganha_e_quem_perde(self):
        lam = ganho_bem_estar(self.tr.V0, self.eq0.familias.V, self.eco.theta)
        # Com a receita devolvida igualmente, os pobres ganham e os ricos perdem.
        self.assertGreater(lam[0, 0], 0)
        self.assertLess(lam[-1, 1], 0)
        self.assertTrue(np.all(np.diff(lam[:, 1]) < 1e-12))   # ganho cai com a riqueza


class TestDesigualdade(unittest.TestCase):
    def test_gini_e_parcelas(self):
        valores = np.array([1.0, 2.0, 3.0, 4.0])
        self.assertAlmostEqual(gini(valores, np.array([0, 1.0, 0, 0])), 0.0)
        self.assertAlmostEqual(gini(np.array([0.0, 1.0]), np.array([0.5, 0.5])), 0.5)
        self.assertAlmostEqual(gini(valores, np.ones(4)), 0.25)
        self.assertAlmostEqual(parcela_topo(valores, np.ones(4), 0.25), 0.4)
        self.assertAlmostEqual(parcela_topo(valores, np.ones(4), 0.5), 0.7)


if __name__ == "__main__":
    unittest.main()
