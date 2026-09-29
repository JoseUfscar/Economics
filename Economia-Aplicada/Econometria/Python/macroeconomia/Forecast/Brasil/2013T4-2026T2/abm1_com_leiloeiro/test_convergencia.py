"""Testes do experimento de convergência do ABM. Rode da pasta Econometria/:

    python -m unittest discover -s Python/macroeconomia/Forecast/Brasil/2013T4-2026T2/abm1_com_leiloeiro -v
"""
import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))   # macroeconomia/
import caminhos  # noqa: E402,F401

import convergencia as CV  # noqa: E402
import economia as E  # noqa: E402
import expectativas as X  # noqa: E402
import transicao  # noqa: E402
from comum import economia_base  # noqa: E402


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cal, _ = economia_base()
        cls.referencia = CV.Referencia(cls.cal)


class TestMedidas(Base):
    def test_gini_e_topo(self):
        self.assertAlmostEqual(CV.gini(np.full(10, 3.0)), 0.0)
        self.assertAlmostEqual(CV.gini([0, 0, 0, 1]), 0.75)
        self.assertAlmostEqual(CV.participacao_topo(np.arange(1, 11), 0.1), 10 / 55)

    def test_gini_do_histograma_e_o_das_familias_sorteadas(self):
        rng = np.random.default_rng(4)
        estado = E.estado_inicial(self.cal, X.Equilibrio(), 20_000, rng)
        a = estado.s * self.cal.par.fator_crescimento
        self.assertAlmostEqual(CV.gini(a), self.referencia.gini, delta=0.005)

    def test_distancia(self):
        rng = np.random.default_rng(5)
        a = E.estado_inicial(self.cal, X.Equilibrio(), 20_000, rng).s * self.cal.par.fator_crescimento
        self.assertLess(self.referencia.distancia(a), 0.01)
        self.assertGreater(self.referencia.distancia(0.5 * a), 0.2)
        self.assertGreater(self.referencia.distancia(np.full_like(a, a.mean())), 0.5)

    def test_anos_ate_convergir(self):
        K = np.concatenate([np.linspace(0.5, 0.995, 80), np.ones(400)])
        self.assertAlmostEqual(CV.anos_ate_convergir(K), 79 / 4)
        self.assertEqual(CV.anos_ate_convergir(np.ones(100)), 0.0)
        self.assertTrue(np.isnan(CV.anos_ate_convergir(np.full(100, 1.05))))


class TestPartidas(Base):
    def populacao(self, partida, regra=None, semente=3, **kw):
        regra = X.Equilibrio() if regra is None else regra
        return CV.populacao(self.cal, CV.PARTIDAS[partida], regra, 5000, np.random.default_rng(semente), **kw)

    def test_riqueza_fora_do_lugar_e_renda_no_estado_estacionario(self):
        controle = self.populacao(CV.CONTROLE)
        esperado = {"capital 50% abaixo": 0.5, "capital 50% acima": 1.5,
                    "riqueza igual para todos": 1.0, "1% com toda a riqueza": 1.0}
        for partida, fator in esperado.items():
            estado = self.populacao(partida)
            np.testing.assert_array_equal(estado.j, controle.j)
            self.assertAlmostEqual(estado.s.mean() / controle.s.mean(), fator, places=12)
        self.assertAlmostEqual(CV.gini(self.populacao("riqueza igual para todos").s), 0.0)
        concentrada = self.populacao("1% com toda a riqueza").s
        self.assertEqual(np.count_nonzero(concentrada), 50)

    def test_crencas_partem_dos_precos_observados(self):
        r_eq = self.cal.est.r
        aprende = X.Aprendizado()
        estado = self.populacao("capital 50% abaixo", aprende)
        r0, w0 = CV.precos_iniciais(self.cal, estado)
        self.assertGreater(r0, r_eq + 0.02)   # pouco capital: juro bem mais alto
        self.assertLess(w0, self.cal.est.w)
        self.assertEqual((aprende.r_hat, aprende.w_hat), (r0, w0))
        rigida = X.InformacaoRigida()
        self.populacao("capital 50% abaixo", rigida)
        np.testing.assert_array_equal(rigida.r_i, r0)
        # A regra que ancora no estado estacionário continua ancorada.
        atencao = X.AtencaoLimitada()
        self.populacao("capital 50% abaixo", atencao)
        self.assertEqual(atencao.r_eq, r_eq)
        # Sem crenças observadas, quem aprende começa do equilíbrio.
        aprende = X.Aprendizado()
        self.populacao("capital 50% abaixo", aprende, crencas_observadas=False)
        self.assertEqual(aprende.r_hat, r_eq)


class TestConvergencia(Base):
    def simular(self, regra, partida, anos, N=5000, semente=7):
        rng = np.random.default_rng(semente)
        estado = CV.populacao(self.cal, CV.PARTIDAS[partida], regra, N, rng)
        return CV.trajetoria(self.cal, estado, rng, 4 * anos)

    def test_aprendizado_volta_ao_equilibrio_sem_conhece_lo(self):
        K, anual = self.simular(X.Aprendizado(), "capital 50% acima", 300)
        self.assertAlmostEqual(K[-40:].mean(), 1.0, delta=0.02)
        # A desigualdade também reaparece partindo da igualdade.
        _, anual = self.simular(X.Aprendizado(), "riqueza igual para todos", 200)
        self.assertLess(anual.gini.iloc[0], 0.1)
        self.assertGreater(anual.gini.iloc[-1], 0.15)

    def test_crencas_fixas_tem_outro_ponto_de_repouso(self):
        # Com as crenças do equilíbrio para sempre, o capital vai para o mesmo
        # lugar partindo de baixo ou de cima, e esse lugar não é o equilíbrio.
        finais = [self.simular(X.Equilibrio(), partida, 400)[0][-40:].mean()
                  for partida in ("capital 50% abaixo", "capital 50% acima")]
        self.assertGreater(min(finais), 1.5)
        self.assertAlmostEqual(finais[0] / finais[1], 1.0, delta=0.03)


class TestPrevisaoPerfeitaContinua(Base):
    def test_histograma_das_familias(self):
        rng = np.random.default_rng(6)
        estado = CV.populacao(self.cal, CV.PARTIDAS["1% com toda a riqueza"], X.Equilibrio(), 5000, rng)
        grade = transicao.grade_para(self.cal, estado)
        self.assertGreater(grade[-1], estado.s.max())   # ninguém fica fora da grade
        massa = transicao.histograma(self.cal, estado, grade)
        self.assertAlmostEqual(massa.sum(), 1.0, places=12)
        a = estado.s * self.cal.par.fator_crescimento
        self.assertAlmostEqual(grade @ massa.sum(axis=1), a.mean(), places=10)
        renda = self.cal.renda
        for tipo in np.unique(renda.tipo):
            no_tipo = renda.tipo == tipo
            self.assertAlmostEqual(massa[:, no_tipo].sum(), np.mean(no_tipo[estado.j]), places=12)

    def test_estado_estacionario_e_ponto_fixo(self):
        dist = self.cal.est.distribuicao
        self.assertAlmostEqual(self.referencia.distancia_histograma(dist.grade_a, dist.massa.sum(axis=1)), 0.0)
        caminho = transicao.previsao_perfeita_histograma(self.cal, dist.massa, dist.grade_a, 200)
        self.assertEqual(caminho.iteracoes, 1)
        self.assertLess(np.max(np.abs(caminho.K / self.cal.est.K - 1)), 1e-6)
        seguinte = transicao.avancar(self.cal, caminho.politicas[0], dist.grade_a, dist.massa)
        self.assertAlmostEqual(seguinte.sum(), 1.0, places=12)

    def test_medidas_do_histograma_e_das_familias(self):
        dist = self.cal.est.distribuicao
        riqueza = dist.massa.sum(axis=1)
        rng = np.random.default_rng(9)
        a = E.estado_inicial(self.cal, X.Equilibrio(), 20_000, rng).s * self.cal.par.fator_crescimento
        self.assertAlmostEqual(CV.topo_histograma(dist.grade_a, riqueza), CV.participacao_topo(a), delta=0.005)
        # Metade com 1 e metade com 0: os 10% mais ricos têm 0,1 de 0,5.
        self.assertAlmostEqual(CV.topo_histograma(np.array([0.0, 1.0]), np.array([0.5, 0.5]), 0.1), 0.2)
        # 5% com toda a riqueza: os 10% mais ricos têm tudo.
        self.assertAlmostEqual(CV.topo_histograma(np.array([0.0, 10.0]), np.array([0.95, 0.05]), 0.1), 1.0)

    def test_parte_de_longe_e_chega_por_construcao(self):
        rng = np.random.default_rng(2)
        estado = CV.populacao(self.cal, CV.PARTIDAS["capital 50% abaixo"], X.Equilibrio(), 20_000, rng,
                              crencas_observadas=False)
        grade = transicao.grade_para(self.cal, estado, pontos=400)
        caminho = transicao.previsao_perfeita_histograma(
            self.cal, transicao.histograma(self.cal, estado, grade), grade, 400)
        K = caminho.K / self.cal.est.K
        self.assertAlmostEqual(K[0], 0.5, delta=0.001)
        self.assertGreater(np.min(np.diff(K)), -1e-6)   # sobe sem oscilar
        self.assertAlmostEqual(K[-1], 1.0, delta=0.01)
        # As famílias simuladas seguem o caminho do contínuo por algumas
        # décadas; depois o ruído de amostragem se acumula.
        K_familias, _ = CV.trajetoria(self.cal, estado, rng, 80, caminho.politicas)
        self.assertLess(np.max(np.abs(K_familias - K[:80])), 0.005)


if __name__ == "__main__":
    unittest.main()
