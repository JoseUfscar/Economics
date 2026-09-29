"""Testes da estimação sintética de rho e theta."""
import unittest

import numpy as np
import pandas as pd

from calibracao import calcular_alvos, calibrar, carregar_dados
from estimacao import SIGMA, adicionar_ruido, estimar, monte_carlo, resumo_monte_carlo, simular


class TestEstimacao(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.eco, cls.pol = calibrar(calcular_alvos(carregar_dados()))
        cls.verdade = simular(cls.eco, cls.pol)

    def test_simulacao_tem_duas_transicoes_de_25_anos(self):
        self.assertEqual(len(self.verdade), 50)
        self.assertEqual(set(self.verdade.trajetoria), {1, 2})
        self.assertTrue(np.all(self.verdade[["C", "K"]].to_numpy() > 0))

    def test_ruido_reprodutivel_e_independente_entre_variaveis(self):
        a = adicionar_ruido(self.verdade, SIGMA, np.random.default_rng(1))
        b = adicionar_ruido(self.verdade, SIGMA, np.random.default_rng(1))
        np.testing.assert_array_equal(a.C_obs, b.C_obs)
        # Correlação amostral entre os erros de C e K numa amostra grande.
        grande = pd.DataFrame({"C": np.ones(20_000), "K": np.ones(20_000)})
        ruido = adicionar_ruido(grande, SIGMA, np.random.default_rng(2))
        e_c, e_k = np.log(ruido.C_obs), np.log(ruido.K_obs)
        self.assertLess(abs(np.corrcoef(e_c, e_k)[0, 1]), 0.03)
        self.assertAlmostEqual(e_c.std(), SIGMA, delta=0.0005)

    def test_sem_ruido_recupera_os_parametros(self):
        exato = self.verdade.assign(C_obs=self.verdade.C, K_obs=self.verdade.K)
        est = estimar(exato, self.eco, self.pol)
        self.assertAlmostEqual(est["rho"], self.eco.rho, delta=1e-4)
        self.assertAlmostEqual(est["theta"], self.eco.theta, delta=1e-2)
        self.assertLess(est["objetivo"], 1e-3)

    def test_monte_carlo_pequeno_tem_erros_padrao_coerentes(self):
        mc = monte_carlo(self.eco, self.pol, replicas=12, semente=7)
        resumo = resumo_monte_carlo(mc, self.eco).set_index("parametro")
        for nome in ("rho", "theta"):
            linha = resumo.loc[nome]
            # O viés é pequeno frente ao erro-padrão, e o erro-padrão médio
            # tem a mesma ordem de grandeza da dispersão das estimativas.
            self.assertLess(abs(linha.vies), 1.5 * linha.ep_medio)
            self.assertTrue(0.4 < linha.dp_estimativas / linha.ep_medio < 2.5)


if __name__ == "__main__":
    unittest.main()
