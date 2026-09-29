"""Testes da calibração para o Brasil (usam o CSV versionado em dados/brasil/)."""
import unittest

import numpy as np

from calibracao import (TAU_K_BRUTO, aliquota_liquida, aumento_tau_k_lei, calcular_alvos,
                        calibrar, carregar_dados, momentos)
from modelo import estado_estacionario


class TestCalibracao(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dados = carregar_dados()
        cls.alvos = calcular_alvos(cls.dados)
        cls.eco, cls.pol = calibrar(cls.alvos)
        cls.ee = estado_estacionario(cls.eco, cls.pol)

    def test_dados_cobrem_o_periodo(self):
        colunas = ["parcela_trabalho", "ocupados", "pib_real_pwt", "capital_liquido",
                   "depreciacao", "capital_produto", "pib_nominal", "consumo_governo"]
        self.assertFalse(self.dados.loc[1999:2023, colunas].isna().any().any())

    def test_estado_estacionario_reproduz_os_alvos(self):
        self.assertAlmostEqual(self.ee.k / self.ee.y, self.alvos.capital_produto, places=10)
        self.assertAlmostEqual(self.pol.gasto / self.ee.y, self.alvos.gasto_pib, places=10)
        self.assertAlmostEqual(self.ee.r, self.eco.rho + self.eco.theta * self.eco.g, places=12)

    def test_conversao_da_aliquota_preserva_a_receita(self):
        a = self.alvos
        retorno = a.alpha / a.capital_produto
        tau = aliquota_liquida(TAU_K_BRUTO, a.alpha, a.delta, a.capital_produto)
        self.assertAlmostEqual(tau * (retorno - a.delta), TAU_K_BRUTO * retorno, places=12)
        self.assertAlmostEqual(tau, self.pol.tau_k, places=12)

    def test_parametros_economicamente_plausiveis(self):
        self.assertTrue(0.35 < self.eco.alpha < 0.55)
        self.assertTrue(0.03 < self.eco.delta < 0.09)
        self.assertTrue(0 < self.eco.g < 0.03 and 0 < self.eco.n < 0.03)
        self.assertTrue(0 < self.eco.rho < 0.15)
        self.assertGreater(self.eco.beta, 0)
        self.assertLess(self.ee.lambda_estavel, 0)

    def test_momentos_nao_usados_ficam_proximos(self):
        tab = momentos(self.alvos, self.eco, self.pol).set_index("momento")
        np.testing.assert_allclose(tab.modelo, tab.dados, atol=0.03)

    def test_choque_da_lei_e_pequeno_e_positivo(self):
        choque = aumento_tau_k_lei(self.alvos, self.dados)
        self.assertTrue(0.002 < choque < 0.02)


if __name__ == "__main__":
    unittest.main()
