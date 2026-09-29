"""
Testes dos experimentos distributivos (experimentos_ha.py), com grades mais
grossas que as do script para rodar em poucos segundos.
"""
import tempfile
import unittest
from pathlib import Path

import numpy as np

from aiyagari import Grade, grade_temporal
from experimentos_ha import (VARIANTES, desigualdade, economia_ha, figura_grupos,
                             ganho_por_decil_de_riqueza, reforma, resumo_bem_estar)


class TestExperimentosHA(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = economia_ha(Grade(a_max=150.0, pontos=200, curvatura=2.0))
        t = grade_temporal(150.0, 50)
        cls.reformas = {nome: reforma(cls.base.eq0, cls.base.choque, pesos, nome, t=t)
                        for nome, pesos in VARIANTES.items()}
        cls.resumos = {nome: resumo_bem_estar(cls.base.eq0, ref).set_index("grupo")
                       for nome, ref in cls.reformas.items()}

    def test_desigualdade_do_modelo_e_dos_dados(self):
        tab = desigualdade(self.base.eq0).set_index("momento")
        self.assertTrue(np.all((tab.modelo > 0) & (tab.modelo < 1)))
        self.assertAlmostEqual(tab.loc["Gini da renda", "modelo"],
                               tab.loc["Gini da renda", "dados"], delta=0.1)
        # Limitação conhecida: o modelo concentra muito menos riqueza que os dados.
        self.assertLess(tab.loc["10% mais ricos: parcela da riqueza", "modelo"], 0.6)

    def test_devolucao_uniforme_favorece_os_pobres(self):
        r = self.resumos["uniforme"]
        self.assertGreater(r.loc["50% com menor renda", "ganho médio (%)"], 0)
        self.assertLess(r.loc["10% com maior renda", "ganho médio (%)"], 0)
        self.assertGreater(r.loc["todos", "ganha (%)"], 50)
        decis = ganho_por_decil_de_riqueza(self.base.eq0, self.reformas["uniforme"].lam)
        self.assertGreater(decis[0], decis[-1])

    def test_isencao_favorece_o_grupo_intermediario(self):
        r = self.resumos["isenção"]
        self.assertGreater(r.loc["40% seguintes", "ganho médio (%)"], 0)
        self.assertLess(r.loc["50% com menor renda", "ganho médio (%)"], 0)
        self.assertLess(r.loc["10% com maior renda", "ganho médio (%)"], 0)

    def test_total_e_media_dos_grupos(self):
        eq0 = self.base.eq0
        massas = eq0.m.reshape(eq0.m.shape[0], 3, 3).sum(axis=(0, 2))
        for r in self.resumos.values():
            grupos = r.drop(index="todos")
            self.assertAlmostEqual(massas @ grupos["ganho médio (%)"].to_numpy(),
                                   r.loc["todos", "ganho médio (%)"], places=10)
            self.assertTrue(np.all((r["ganha (%)"] >= 0) & (r["ganha (%)"] <= 100)))

    def test_capital_cai_como_no_modelo_representativo(self):
        for ref in self.reformas.values():
            queda = 100 * (ref.eq1.K / self.base.eq0.K - 1)
            self.assertAlmostEqual(queda, -1.46, delta=0.15)

    def test_figura_dos_grupos(self):
        resumos = {nome: r.reset_index() for nome, r in self.resumos.items()}
        with tempfile.TemporaryDirectory() as pasta:
            destino = Path(pasta) / "grupos.png"
            figura_grupos(resumos, -0.084, destino)
            self.assertGreater(destino.stat().st_size, 10_000)


if __name__ == "__main__":
    unittest.main()
