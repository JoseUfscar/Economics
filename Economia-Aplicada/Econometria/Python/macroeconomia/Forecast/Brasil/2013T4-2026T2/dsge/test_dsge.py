"""Testes do modelo de equilíbrio geral estocástico. Rode da pasta Econometria/:

    python -m unittest discover -s Python/macroeconomia/Forecast/Brasil/2013T4-2026T2/dsge -v
"""
import sys
import unittest
from dataclasses import replace
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))   # macroeconomia/
import caminhos  # noqa: E402,F401

import dsge  # noqa: E402
from calibracao import calcular_alvos, calibrar, carregar_dados  # noqa: E402
from espaco_estados import simular  # noqa: E402
from modelo import estado_estacionario as estacionario_continuo  # noqa: E402


def estrutura_calibrada(periodo=0.25):
    alvos = calcular_alvos(carregar_dados())
    eco, pol = calibrar(alvos)
    e = dsge.Estrutura(eco.alpha, eco.delta, eco.rho, eco.theta, eco.n, eco.g, pol.tau_k,
                       alvos.gasto_pib, periodo)
    return e, eco, pol, alvos


class TestBrockMirman(unittest.TestCase):
    """Log, depreciação total e período de um ano: K' = alpha beta Y é exato."""

    def test_politica_exata(self):
        a, rho = 0.36, 0.05
        e = dsge.Estrutura(alpha=a, delta=1.0, rho=rho, theta=1.0, n=0.0, g=0.0,
                           tau_k=0.0, gasto_pib=0.0, periodo=1.0)
        sol = dsge.resolver(e, dsge.Choques(rho_u=0.4, rho_z=0.8, rho_s=0.3))
        ee = sol.ee
        # kappa' = alpha beta e^z kappa^alpha e^{-alpha u}; c = (1 - alpha beta) y.
        np.testing.assert_allclose(sol.P[0], [a, -a, 1.0, 0.0], atol=1e-10)
        np.testing.assert_allclose(sol.F[0], [a, -a, 1.0, 0.0], atol=1e-10)
        self.assertAlmostEqual(ee.kappa, a * np.exp(-rho) * ee.y, places=12)
        self.assertAlmostEqual(ee.c, (1 - a * np.exp(-rho)) * ee.y, places=12)
        np.testing.assert_allclose(sol.P[1:, 1:], np.diag([0.4, 0.8, 0.3]), atol=1e-12)


class TestLimiteContinuo(unittest.TestCase):
    """Com período curto, o modelo discreto converge para modelo.py."""

    def test_estado_estacionario_e_convergencia(self):
        e, eco, pol, _ = estrutura_calibrada(periodo=1e-4)
        sol = dsge.resolver(e, dsge.Choques())
        c = estacionario_continuo(eco, pol)
        self.assertAlmostEqual(sol.ee.k / c.k, 1, places=4)
        self.assertAlmostEqual(sol.ee.c / c.c, 1, places=4)
        velocidade = np.log(sol.P[0, 0]) / e.periodo
        self.assertAlmostEqual(velocidade / c.lambda_estavel, 1, places=4)
        # dlog c / dlog k no braço estável: F contra a inclinação do contínuo.
        self.assertAlmostEqual(sol.F[0, 0] / (c.inclinacao * c.k / c.c), 1, places=4)

    def test_erro_de_discretizacao_diminui_com_o_periodo(self):
        e, eco, pol, _ = estrutura_calibrada()
        c = estacionario_continuo(eco, pol)
        erros = [abs(dsge.estado_estacionario(replace(e, periodo=p)).k / c.k - 1)
                 for p in (0.25, 0.025, 0.0025)]
        self.assertTrue(erros[0] > 5 * erros[1] > 25 * erros[2])


class TestCalibracao(unittest.TestCase):
    def test_rho_reproduz_capital_produto(self):
        e, *_, alvos = estrutura_calibrada()
        e = replace(e, rho=dsge.rho_para_capital_produto(e, alvos.capital_produto))
        ee = dsge.estado_estacionario(e)
        self.assertAlmostEqual(ee.k / ee.y, alvos.capital_produto, places=10)
        self.assertAlmostEqual(ee.gasto / ee.y, alvos.gasto_pib, places=12)
        self.assertAlmostEqual(ee.c + ee.investimento + ee.gasto, ee.y, places=12)


class TestSolucao(unittest.TestCase):
    def setUp(self):
        e, *_ = estrutura_calibrada()
        self.e = e
        self.ch = dsge.Choques(rho_u=0.4, sigma_u=0.01, rho_z=0.9, sigma_z=0.01,
                               rho_s=0.8, sigma_s=0.02)
        self.sol = dsge.resolver(e, self.ch)

    def test_linearizacao_tem_erro_de_segunda_ordem(self):
        # Com a política linear, os resíduos das equações caem com o quadrado do desvio.
        ee = self.sol.ee
        x_ee = np.array([np.log(ee.kappa), 0, 0, 0])
        direcao = np.array([0.5, 0.3, -0.4, 0.6])
        residuos = []
        for eps in (1e-2, 1e-3):
            x = eps * direcao
            x1 = self.sol.P @ x
            atual = np.concatenate([x_ee + x, [np.log(ee.c) + self.sol.F[0] @ x]])
            prox = np.concatenate([x_ee + x1, [np.log(ee.c) + self.sol.F[0] @ x1]])
            residuos.append(np.max(np.abs(dsge._equacoes(self.e, ee, self.ch, prox, atual))))
        self.assertLess(residuos[1], residuos[0] / 50)

    def test_choque_permanente_desloca_o_nivel_em_toda_a_economia(self):
        # u de 1% sem persistência: PIB, consumo, FBCF e gasto acabam 1% acima.
        sol = dsge.resolver(self.e, replace(self.ch, rho_u=0.0))
        m = dsge.espaco_estados(sol, [0.1] * 4)
        xi = np.zeros(8)
        xi[1] = 0.01
        acumulado = m.Z @ xi
        for _ in range(3000):
            xi = m.T @ xi
            acumulado = acumulado + m.Z @ xi
        np.testing.assert_allclose(acumulado, 1.0, atol=1e-6)

    def test_choque_transitorio_nao_muda_o_nivel_de_longo_prazo(self):
        m = dsge.espaco_estados(self.sol, [0.1] * 4)
        for posicao in (2, 3):   # z e s
            xi = np.zeros(8)
            xi[posicao] = 0.01
            acumulado = m.Z @ xi
            for _ in range(3000):
                xi = m.T @ xi
                acumulado = acumulado + m.Z @ xi
            np.testing.assert_allclose(acumulado, 0.0, atol=1e-6)

    def test_crescimento_medio_e_o_do_equilibrio_balanceado(self):
        m = dsge.espaco_estados(self.sol, [0.1] * 4)
        np.testing.assert_allclose(m.d + m.Z @ m.media_estacionaria,
                                   100 * (self.e.g + self.e.n) * self.e.periodo)

    def test_medias_proprias_de_cada_serie(self):
        # Na variante com tendência trimestral, cada série converge para a própria média.
        medias = np.array([0.5, 0.6, 0.4, 0.3])
        m = dsge.espaco_estados(self.sol, [0.1] * 4, medias)
        np.testing.assert_allclose(m.d + m.Z @ m.media_estacionaria, medias)
        from espaco_estados import prever_acumulado
        xi = np.zeros(8)
        xi[2] = 0.02
        acumulado, _ = prever_acumulado(m, xi, np.zeros((8, 8)), 3000)
        np.testing.assert_allclose(np.diff(acumulado[-2:], axis=0)[0], medias, atol=1e-8)

    def test_sem_solucao_unica_levanta_erro(self):
        A = np.eye(2)
        B = np.diag([1.5, 2.0])   # duas raízes instáveis e uma variável predeterminada
        with self.assertRaises(ValueError):
            dsge.resolver_klein(A, B, 1)


class TestEstimacao(unittest.TestCase):
    def test_recupera_parametros_em_dados_simulados(self):
        # Média de 4 amostras de 800 trimestres. Em 8 amostras, os desvios-padrão
        # das estimativas foram 0,055 (rho_u), 0,007 (rho_z) e 0,08 (rho_s), e as
        # tolerâncias abaixo ficam em torno de 3 desvios-padrão da média.
        e, *_ = estrutura_calibrada()
        verdade = dsge.Choques(rho_u=0.3, sigma_u=0.008, rho_z=0.9, sigma_z=0.01,
                               rho_s=0.7, sigma_s=0.015)
        erros = np.array([0.3, 0.5, 1.5, 0.8])
        m = dsge.espaco_estados(dsge.resolver(e, verdade), erros)
        estimativas = []
        for semente in range(4):
            y = simular(m, 800, np.random.default_rng(semente))
            est = dsge.estimar(e, y, partidas=dsge.PARTIDAS[:1])
            self.assertGreaterEqual(est.log_verossimilhanca,
                                    dsge.log_verossimilhanca(e, verdade, erros, y))
            estimativas.append(est)
        for nome, tolerancia in (("rho_u", 0.09), ("rho_z", 0.012), ("rho_s", 0.12)):
            media = np.mean([getattr(est.choques, nome) for est in estimativas])
            self.assertAlmostEqual(media, getattr(verdade, nome), delta=tolerancia, msg=nome)
        for nome in ("sigma_u", "sigma_z", "sigma_s"):
            media = np.mean([getattr(est.choques, nome) for est in estimativas])
            self.assertAlmostEqual(media / getattr(verdade, nome), 1, delta=0.1, msg=nome)
        np.testing.assert_allclose(np.mean([est.erros_medida for est in estimativas], axis=0),
                                   erros, rtol=0.1)


if __name__ == "__main__":
    unittest.main()
