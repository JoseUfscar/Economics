"""Testes do ABM sem leiloeiro na previsão fora da amostra. Rode da pasta Econometria/:

    python -m unittest discover -s Python/macroeconomia/Forecast/Brasil/2013T4-2026T2/abm2_sem_leiloeiro -v
"""
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))   # macroeconomia/
import caminhos  # noqa: E402,F401

import previsao_descentralizada as PD  # noqa: E402
import descentralizada as DC  # noqa: E402
import economia as E  # noqa: E402
import expectativas as X  # noqa: E402
import protocolo  # noqa: E402
from calibracao_renda import carregar_pnad  # noqa: E402

ORIGEM = 201504


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dados, cls.anuais = protocolo.carregar_tudo()
        cls.pnad = carregar_pnad()
        cls.amostra = cls.dados.loc[:ORIGEM]
        cls.eco = PD.economia_na_origem(cls.anuais, cls.pnad, cls.amostra, ORIGEM)


class TestHistoria(Base):
    def test_reproduz_pib_gasto_e_desemprego(self):
        _, hist = PD.historia(self.eco, self.amostra, X.Aprendizado(), 16000, semente=1, aquecimento=40)
        pib = np.diff(np.log(hist.y) + hist.log_X)
        np.testing.assert_allclose(100 * pib, self.amostra.pib.to_numpy()[1:], atol=1e-9)
        gasto = np.diff(np.log(hist.G_pedido) + hist.log_X)
        np.testing.assert_allclose(100 * gasto, self.amostra.governo.to_numpy()[1:], atol=1e-9)
        alvo = self.amostra[protocolo.TAXA_DESEMPREGO]
        com_pnad = alvo.notna()
        erro = 100 * hist.desemprego[com_pnad] - alvo[com_pnad]
        # A separação é achada com os números aleatórios do trimestre, mas o
        # desemprego muda aos saltos com ela, e sobra um erro que depende do
        # caminho da simulação. Com 16 mil famílias, o erro médio fica entre
        # 0,04 e 0,08 p.p. nas sementes 1 a 10; com 4 mil, entre 0,10 e 0,26,
        # e uma diferença de arredondamento entre máquinas bastava para
        # passar do limite.
        self.assertLess(erro.abs().mean(), 0.15)
        # Antes da PNAD, a separação é a da cadeia calibrada.
        antes = hist.probabilidade_separacao[~com_pnad]
        np.testing.assert_allclose(antes, self.eco.fluxos.separacao)

    def test_separacao_pedida_nao_gasta_numeros_aleatorios(self):
        # Achar a separação que dá o desemprego pedido não muda o sorteio do
        # resto do trimestre: com a separação achada, o trimestre é o mesmo.
        rng = np.random.default_rng(2)
        e = DC.estado_inicial(self.eco, X.Aprendizado(), 3000, rng)
        par = self.eco.cal.par
        estado = rng.bit_generator.state
        _, com_alvo = DC.trimestre(self.eco, e, rng, par.g * par.periodo, par.gasto, desemprego_alvo=0.12)
        rng.bit_generator.state = estado
        _, direto = DC.trimestre(self.eco, e, rng, par.g * par.periodo, par.gasto,
                                 separacao=com_alvo["probabilidade_separacao"])
        self.assertTrue(pd.Series(com_alvo).equals(pd.Series(direto)))
        self.assertAlmostEqual(com_alvo["desemprego"], 0.12, delta=0.002)


class TestExogenos(unittest.TestCase):
    def test_serie_que_comeca_depois(self):
        rng = np.random.default_rng(3)
        x = np.zeros((80, 3))
        for t in range(1, 80):
            x[t] = np.array([0.1, 0.0, -0.2]) + np.array([0.5, -0.3, 0.8]) * x[t - 1] + rng.normal(size=3)
        lacunas = x.copy()
        lacunas[:50, 2] = np.nan
        ex = E.Exogenos.de_series(lacunas)
        so_duas = E.Exogenos.de_series(x[:, :2])
        np.testing.assert_allclose(ex.c[:2], so_duas.c)
        np.testing.assert_allclose(ex.phi[:2], so_duas.phi)
        curta = E.Exogenos.de_series(x[50:, 2:])
        self.assertAlmostEqual(ex.phi[2], curta.phi[0])
        # A covariância usa só os trimestres em que as três têm resíduo.
        residuos = np.column_stack([x[51:, j] - ex.c[j] - ex.phi[j] * x[50:-1, j] for j in range(3)])
        np.testing.assert_allclose(ex.L @ ex.L.T, residuos.T @ residuos / (len(residuos) - 2))
        # O ABM com leiloeiro continua com a mesma estimativa de antes.
        antigo = E.Exogenos.estimar(x[:, 0], x[:, 1])
        np.testing.assert_allclose(antigo.L, so_duas.L)

    def test_limite_da_persistencia(self):
        x = np.cumsum(np.random.default_rng(4).normal(size=(40, 1)), axis=0)   # passeio aleatório
        ex = E.Exogenos.de_series(x, limite_phi=0.9)
        self.assertLessEqual(abs(ex.phi[0]), 0.9)


class TestPrevisao(Base):
    def test_sem_olhar_o_futuro_e_formato(self):
        alterado = self.dados.copy()
        alterado.loc[alterado.index > ORIGEM] += 5.0
        previsoes = []
        for dados in (self.dados, alterado):
            modelo = PD.ModeloDescentralizado(self.anuais, "abm2_apr", pnad=self.pnad, N=2000,
                                              replicas=4, aquecimento=20)
            previsoes.append(protocolo.prever_na_origem(modelo, dados, ORIGEM))
        colunas = ["variavel", "h", "previsto", "dp"]
        pd.testing.assert_frame_equal(previsoes[0][colunas], previsoes[1][colunas])
        self.assertEqual(set(previsoes[0].variavel), set(protocolo.VARIAVEIS))
        self.assertEqual(len(previsoes[0]), 5 * protocolo.HORIZONTE)
        self.assertTrue(np.isfinite(previsoes[0].previsto).all())


if __name__ == "__main__":
    unittest.main()
