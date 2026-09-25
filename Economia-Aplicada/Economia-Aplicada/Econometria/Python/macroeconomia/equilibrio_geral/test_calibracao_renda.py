"""Testes da calibração do processo de renda com a PNAD Contínua."""
import unittest

import numpy as np

from calibracao_renda import (COLUNAS_PROCURA, GRUPOS, calibrar_desemprego, carregar_pnad,
                              parcelas_mistura, produtividade_dos_tipos, renda_brasil)


class TestCalibracaoRenda(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.trimestral, cls.anual = carregar_pnad()
        cls.desemprego = calibrar_desemprego(cls.trimestral)
        cls.renda = renda_brasil(pnad=(cls.trimestral, cls.anual))

    def test_mistura_reproduz_as_faixas_de_tempo_de_procura(self):
        d = self.desemprego
        observado = self.trimestral.loc[201201:202504, COLUNAS_PROCURA].mean().to_numpy()
        np.testing.assert_allclose(parcelas_mistura(d.p_curto, d.f_curto, d.f_longo),
                                   observado / observado.sum(), atol=1e-8)
        self.assertGreater(d.f_curto, 1.0)
        self.assertLess(d.f_longo, 1.0)

    def test_cadeia_de_markov_reproduz_a_desocupacao(self):
        pi, q = self.renda.estacionaria, self.renda.gerador
        np.testing.assert_allclose(pi @ q, 0.0, atol=1e-12)
        self.assertAlmostEqual(pi.sum(), 1.0, places=12)
        desempregados = pi.reshape(3, 3)[:, 1:].sum()
        self.assertAlmostEqual(desempregados, self.desemprego.taxa, places=10)
        self.assertAlmostEqual(pi @ np.asarray(self.renda.z), 1.0, places=12)

    def test_tipos_reproduzem_a_massa_de_rendimento(self):
        massas, produtividade = produtividade_dos_tipos(self.anual)
        np.testing.assert_allclose(massas, [0.5, 0.4, 0.1])
        parcelas = massas * produtividade
        dados = [self.anual.loc[2012:2025, faixas].sum(axis=1).mean()
                 for _, faixas in GRUPOS.values()]
        np.testing.assert_allclose(parcelas, np.array(dados) / sum(dados), rtol=1e-12)
        z = np.asarray(self.renda.z).reshape(3, 3)
        np.testing.assert_allclose(z[:, 1] / z[:, 0], 0.4)
        np.testing.assert_allclose(z[:, 0] / z[1, 0], produtividade / produtividade[1])


if __name__ == "__main__":
    unittest.main()
