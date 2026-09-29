"""Testes do experimento da Lei 15.270/2025 no ABM com leiloeiro. Rode da pasta Econometria/:

    python -m unittest discover -s Python/macroeconomia/Politicas/Lei-15270/abm1_com_leiloeiro -v
"""
import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))   # macroeconomia/
import caminhos  # noqa: E402,F401

import expectativas as X  # noqa: E402
import lei_com_leiloeiro as XA  # noqa: E402
import transicao  # noqa: E402


class TestLei(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cal0, cls.aumento = XA.economia_base()
        cls.reformas = {nome: XA.reformada(cls.cal0, cls.aumento, pesos)
                        for nome, pesos in XA.DEVOLUCOES.items()}

    def test_novo_estado_estacionario_igual_ao_do_aiyagari_continuo(self):
        # Duas soluções independentes do mesmo modelo: grade endógena trimestral
        # e HJB em tempo contínuo (equilibrio_geral/aiyagari.py).
        for devolucao, cal1 in self.reformas.items():
            variacao = 100 * (cal1.est.K / self.cal0.est.K - 1)
            self.assertAlmostEqual(variacao, XA.HA_CAPITAL[devolucao], delta=0.05, msg=devolucao)

    def test_receita_nova_volta_como_transferencia(self):
        for cal1 in self.reformas.values():
            self.assertGreater(cal1.est.transferencia, 0)
            self.assertAlmostEqual(cal1.par.tau_w, self.cal0.par.tau_w)
            self.assertAlmostEqual(cal1.par.gasto, self.cal0.par.gasto)

    def test_numeros_aleatorios_comuns(self):
        # Sem reforma dos dois lados, a diferença de bem-estar é exatamente zero.
        for fabrica in (X.Equilibrio, X.Heuristicas, X.InformacaoRigida):
            _, b0, tipo = XA.simular(self.cal0, self.cal0, fabrica(), 12, semente=3)
            _, b1, _ = XA.simular(self.cal0, self.cal0, fabrica(), 12, semente=3)
            np.testing.assert_array_equal(b0, b1)
            tabela = XA.resumo_bem_estar(b1, b0, tipo, self.cal0.par.theta)
            np.testing.assert_allclose(tabela["ganho médio (%)"], 0.0)

    def test_aprendizado_parte_das_crencas_antigas(self):
        regra = X.Aprendizado()
        rng = np.random.default_rng(0)
        cal1 = self.reformas["uniforme"]
        regra.iniciar(10, cal1.est.r, cal1.est.w, rng)
        regra.herdar(self.cal0.est.r, self.cal0.est.w)
        self.assertEqual((regra.r_hat, regra.w_hat), (self.cal0.est.r, self.cal0.est.w))


class TestPrevisaoPerfeita(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cal0, cls.aumento = XA.economia_base()
        cls.cal1 = XA.reformada(cls.cal0, cls.aumento, None)
        cls.base = transicao.previsao_perfeita(cls.cal0, cls.cal0, 120, 4000, semente=2)
        cls.reforma = transicao.previsao_perfeita(cls.cal0, cls.cal1, 120, 4000, semente=2)

    def test_ponto_fixo(self):
        # As famílias, seguindo as políticas encontradas, produzem o caminho suposto.
        for pp in (self.base, self.reforma):
            np.testing.assert_allclose(pp.agregados.K.to_numpy(), pp.K, rtol=1e-4)

    def test_sem_reforma_o_capital_fica_parado(self):
        K = self.base.K
        self.assertLess(np.max(np.abs(K / K[0] - 1)), 0.01)

    def test_reforma_reduz_o_capital_aos_poucos(self):
        desvio = self.reforma.K / self.base.K - 1
        self.assertAlmostEqual(desvio[0], 0.0, places=12)   # o capital inicial é dado
        self.assertLess(desvio[-1], desvio[20])
        self.assertLess(desvio[-1], -0.005)
        self.assertGreater(desvio[-1], -0.0145 - 0.005)   # não passa do longo prazo

    def test_isencao_tira_dos_pobres_e_da_ao_grupo_intermediario(self):
        # Com a devolução só aos empregados do grupo intermediário, a metade mais
        # pobre perde (arca com a queda do salário sem receber nada) e o grupo
        # intermediário ganha, como no Aiyagari contínuo; com qualquer semente.
        cal_isencao = XA.reformada(self.cal0, self.aumento, XA.DEVOLUCOES["isenção"])
        for semente in (2, 11):
            base = transicao.previsao_perfeita(self.cal0, self.cal0, 80, 3000, semente)
            reforma = transicao.previsao_perfeita(self.cal0, cal_isencao, 80, 3000, semente)
            tabela = XA.resumo_bem_estar(reforma.bem_estar, base.bem_estar, base.tipo_inicial,
                                         self.cal0.par.theta).set_index("grupo")
            self.assertLess(tabela.loc[XA.TIPOS[0], "ganho médio (%)"], 0)
            self.assertGreater(tabela.loc[XA.TIPOS[1], "ganho médio (%)"], 0)
            self.assertLess(tabela.loc[XA.TIPOS[2], "ganho médio (%)"], 0)

    def test_politica_final_e_a_do_novo_estado_estacionario(self):
        m = np.linspace(0.1, 30, 50)
        j = np.zeros(50, dtype=int)
        ultima = self.reforma.politicas[-1].consumo(m, j)
        np.testing.assert_allclose(ultima, self.cal1.est.politica.consumo(m, j), rtol=0.02)


if __name__ == "__main__":
    unittest.main()
