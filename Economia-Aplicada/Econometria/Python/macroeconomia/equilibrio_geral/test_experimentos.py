"""Testes dos experimentos de política com o modelo calibrado."""
import tempfile
import unittest
from pathlib import Path

import numpy as np

from calibracao import aumento_tau_k_lei, calibrar
from experimentos import (curva_laffer, economia_calibrada, efeitos, figura_lei,
                          figura_outros_choques)


class TestExperimentos(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dados, cls.alvos, cls.eco, cls.pol = economia_calibrada()
        cls.lei = aumento_tau_k_lei(cls.alvos, cls.dados)
        cls.resultado = efeitos(cls.eco, cls.pol, cls.lei, antecedencia=0.8)

    def test_sinais_dos_efeitos_da_lei(self):
        r = self.resultado
        self.assertLess(r["capital (%)"], r["PIB e salário (%)"])
        self.assertLess(r["PIB e salário (%)"], 0)
        self.assertLess(r["receita de longo prazo (% PIB)"], r["receita estática (% PIB)"])
        self.assertGreater(r["receita de longo prazo (% PIB)"], 0)
        self.assertLess(r["bem-estar, surpresa (%)"], 0)
        self.assertAlmostEqual(r["bem-estar, surpresa (%)"], r["bem-estar, anunciado (%)"], delta=0.01)

    def test_receita_estatica_bate_com_a_estimativa_oficial(self):
        # Por construção, o choque reproduz R$ 34,12 bi sobre o PIB do último ano.
        pib_bi = self.dados.pib_nominal.dropna().iloc[-1] / 1e3
        self.assertAlmostEqual(self.resultado["receita estática (% PIB)"],
                               100 * 34.12 / pib_bi, delta=0.01)

    def test_longo_prazo_nao_depende_de_theta_quando_rho_e_recalibrado(self):
        outro_eco, outro_pol = calibrar(self.alvos, theta=4.0)
        outro = efeitos(outro_eco, outro_pol, self.lei, antecedencia=0.8)
        for chave in ("capital (%)", "PIB e salário (%)", "consumo (%)"):
            self.assertAlmostEqual(outro[chave], self.resultado[chave], places=9)
        self.assertNotAlmostEqual(outro["bem-estar, surpresa (%)"],
                                  self.resultado["bem-estar, surpresa (%)"], places=3)

    def test_curva_de_laffer_tem_pico_acima_da_aliquota_atual(self):
        curva = curva_laffer(self.eco, self.pol, np.linspace(0, 0.95, 96))
        pico = curva.tau_k[curva.receita_pib_inicial.idxmax()]
        self.assertTrue(self.pol.tau_k < pico < 0.95)

    def test_figuras_sao_geradas(self):
        with tempfile.TemporaryDirectory() as pasta:
            figura_lei(self.eco, self.pol, self.lei, Path(pasta) / "lei.png")
            figura_outros_choques(self.eco, self.pol, Path(pasta) / "outros.png")
            for nome in ("lei.png", "outros.png"):
                self.assertGreater((Path(pasta) / nome).stat().st_size, 10_000)


if __name__ == "__main__":
    unittest.main()
