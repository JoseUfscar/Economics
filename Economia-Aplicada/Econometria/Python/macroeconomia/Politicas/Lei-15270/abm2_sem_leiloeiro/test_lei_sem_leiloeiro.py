"""Testes do experimento da lei no ABM sem leiloeiro. Rode da pasta Econometria/:

    python -m unittest discover -s Python/macroeconomia/Politicas/Lei-15270/abm2_sem_leiloeiro -v
"""
import sys
import unittest
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))   # macroeconomia/
import caminhos  # noqa: E402,F401

import descentralizada as DC  # noqa: E402
import expectativas as X  # noqa: E402
from experimentos_mercados import economia_base  # noqa: E402
from lei_sem_leiloeiro import _economia_da_lei  # noqa: E402

N_TESTE, AQUECIMENTO_TESTE, TRIMESTRES_TESTE = 1500, 8, 12


class TestLeiSemLeiloeiro(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.eco, _ = economia_base()

    def test_sem_reforma_continua_o_aquecimento(self):
        # A cópia sem reforma é a mesma economia que roda direto, sem parar.
        _, saida = _economia_da_lei((self.eco, {}, 5, TRIMESTRES_TESTE, AQUECIMENTO_TESTE, N_TESTE))
        rng = np.random.default_rng(5)
        e = DC.estado_inicial(self.eco, X.Aprendizado(), N_TESTE, rng)
        _, direto = DC.simular(self.eco, e, rng, AQUECIMENTO_TESTE + TRIMESTRES_TESTE)
        pd.testing.assert_frame_equal(saida["sem reforma"][0],
                                      direto.iloc[AQUECIMENTO_TESTE:].reset_index(drop=True))

    def test_pesos_sem_receita_nova_nao_mudam_nada(self):
        # Uma "reforma" que só troca os pesos da devolução, sem aumentar a
        # alíquota, deixa tudo igual: só a receita nova seguiria os pesos.
        cal = self.eco.cal
        pesos = np.array([0, 0, 0, 1, 0, 0, 0, 0, 0], dtype=float)
        so_pesos = replace(self.eco, cal=replace(cal, pesos=pesos / (cal.renda.pi @ pesos)),
                           tau_k_base=cal.par.tau_k)
        _, saida = _economia_da_lei((self.eco, {"isenção": so_pesos}, 6, TRIMESTRES_TESTE,
                                     AQUECIMENTO_TESTE, N_TESTE))
        (h0, b0, tipo0), (h1, b1, tipo1) = saida["sem reforma"], saida["isenção"]
        pd.testing.assert_frame_equal(h0, h1)
        np.testing.assert_array_equal(b0, b1)
        np.testing.assert_array_equal(tipo0, tipo1)


if __name__ == "__main__":
    unittest.main()
