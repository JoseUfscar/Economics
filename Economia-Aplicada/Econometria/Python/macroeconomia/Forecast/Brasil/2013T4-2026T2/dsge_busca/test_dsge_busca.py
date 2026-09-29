"""Testes do equilíbrio geral com margem e busca. Rode da pasta Econometria/:

    python -m unittest discover -s Python/macroeconomia/Forecast/Brasil/2013T4-2026T2/dsge_busca -v
"""
import sys
import unittest
from dataclasses import replace
from pathlib import Path

import numpy as np
from scipy.linalg import expm

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))   # macroeconomia/
import caminhos  # noqa: E402,F401

import dsge  # noqa: E402
import dsge_busca as B  # noqa: E402
import protocolo  # noqa: E402
from calibracao import calcular_alvos, carregar_dados  # noqa: E402
from calibracao_renda import calibrar_desemprego, carregar_pnad, renda_brasil  # noqa: E402
from espaco_estados import ModeloLinear, filtrar, simular  # noqa: E402


def calibrada():
    anuais = carregar_dados()
    e = protocolo.estrutura_na_origem(anuais, 202504)
    t = B.Trabalho.da_pnad(calibrar_desemprego(carregar_pnad()[0]))
    alvos = calcular_alvos(anuais, protocolo.INICIO_CALIBRACAO, 2023)
    return replace(e, rho=B.rho_para_capital_produto(e, t, alvos.capital_produto)), t, alvos


class TestEstadoEstacionario(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.e, cls.t, cls.alvos = calibrada()
        cls.ee = B.estado_estacionario(cls.e, cls.t)

    def test_alvos(self):
        ee, e, t = self.ee, self.e, self.t
        self.assertAlmostEqual(ee.k / ee.pib, self.alvos.capital_produto, places=10)
        self.assertAlmostEqual(ee.gasto / ee.pib, e.gasto_pib, places=12)
        self.assertAlmostEqual(1 - ee.N, t.desemprego, places=12)
        # O fluxo de entrada no emprego repõe as separações.
        f = ee.chi * ee.theta ** (1 - t.eta)
        self.assertAlmostEqual(f * (1 - ee.N), t.separacao * ee.N, places=12)
        self.assertAlmostEqual(ee.chi * ee.theta ** -t.eta, t.preenchimento, places=12)
        # Contratar custa 14% do salário de um trimestre.
        self.assertAlmostEqual(ee.custo_vaga / t.preenchimento, t.custo_contratacao * e.periodo * ee.w,
                               places=12)
        self.assertAlmostEqual(ee.pib, ee.c + ee.investimento + ee.gasto, places=12)

    def test_margem_reduz_a_participacao_do_trabalho(self):
        participacao = self.ee.w * self.ee.N / self.ee.y
        self.assertAlmostEqual(participacao, (1 - self.e.alpha) * self.ee.omega / (1 + self.t.margem),
                               places=12)
        self.assertLess(participacao, 1 - self.e.alpha)

    def test_sem_margem_o_capital_por_ocupado_e_o_do_modelo_sem_busca(self):
        t0 = replace(self.t, margem=0.0)
        e0 = replace(self.e, rho=0.07)
        ee = B.estado_estacionario(e0, t0)
        self.assertAlmostEqual(ee.k / ee.N, dsge.estado_estacionario(e0).k, places=10)
        self.assertAlmostEqual(ee.r, dsge.estado_estacionario(e0).r, places=12)

    def test_equacoes_zeram_no_estado_estacionario(self):
        x0 = B._ponto(self.ee)
        for rigidez in (0.0, 0.8):
            residuos = B._equacoes(self.e, self.t, self.ee, B.Choques(rigidez=rigidez), x0, x0)
            np.testing.assert_allclose(residuos, 0, atol=1e-12)


class TestSeparacaoDaPNAD(unittest.TestCase):
    def test_mesma_cadeia_trimestral_do_abm(self):
        d = calibrar_desemprego(carregar_pnad()[0])
        t = B.Trabalho.da_pnad(d)
        P = expm(np.asarray(renda_brasil().gerador)[:3, :3] * 0.25)   # um tipo: empregado, curta, longa
        self.assertAlmostEqual(t.separacao, P[0, 1] + P[0, 2], places=10)
        self.assertAlmostEqual(t.desemprego, d.taxa)


class TestDinamica(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.e, cls.t, _ = calibrada()

    def resposta(self, choques, indice, tamanho, trimestres=12):
        sol = B.resolver(self.e, self.t, choques)
        x = np.zeros(B.PREDETERMINADAS)
        x[indice] = tamanho
        caminho = []
        for _ in range(trimestres):
            caminho.append(sol.niveis @ x)
            x = sol.P @ x
        return np.array(caminho)

    def test_estavel_para_qualquer_rigidez(self):
        for rigidez in (0.0, 0.5, 0.9, 0.98):
            sol = B.resolver(self.e, self.t, B.Choques(rigidez=rigidez))
            self.assertLess(np.max(np.abs(np.linalg.eigvals(sol.P))), 1)

    def test_separacao_aumenta_o_desemprego(self):
        caminho = self.resposta(B.Choques(), 6, 0.2)
        self.assertGreater(caminho[0, 4], 0.003)
        self.assertLess(caminho[0, 0], 0)

    def test_salario_rigido_faz_a_produtividade_mexer_no_desemprego(self):
        flexivel = self.resposta(B.Choques(rigidez=0.0), 4, 0.01)
        rigido = self.resposta(B.Choques(rigidez=0.9), 4, 0.01)
        self.assertLess(rigido[4, 4], -0.004)                     # ~0,9 p.p. a menos em um ano
        self.assertLess(abs(flexivel[4, 4]), abs(rigido[4, 4]) / 5)


class TestEspacoDeEstados(unittest.TestCase):
    def test_sem_desemprego_e_o_modelo_das_contas_nacionais(self):
        # Com a coluna do desemprego vazia, a verossimilhança é a do modelo só
        # com as quatro séries das Contas Nacionais.
        e, t, _ = calibrada()
        sol = B.resolver(e, t, B.Choques(rigidez=0.7))
        m = B.espaco_estados(sol, [0.5, 0.8, 2.0, 1.0, 0.1])
        y = simular(m, 40, np.random.default_rng(1))
        y[:, 4] = np.nan
        quatro = ModeloLinear(m.c, m.T, m.Q, m.d[:4], m.Z[:4], m.H[:4, :4])
        self.assertAlmostEqual(filtrar(m, y).log_verossimilhanca,
                               filtrar(quatro, y[:, :4]).log_verossimilhanca, places=8)

    def test_observacoes_sem_tendencia_no_desemprego(self):
        e, t, _ = calibrada()
        m = B.espaco_estados(B.resolver(e, t, B.Choques()), np.ones(5))
        np.testing.assert_allclose(m.d[:4], 100 * (e.g + e.n) * e.periodo)
        self.assertEqual(m.d[4], 0.0)


if __name__ == "__main__":
    unittest.main()
