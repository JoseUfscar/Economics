"""Testes da economia simulada, das expectativas e da previsão. Rode da pasta Econometria/:

    python -m unittest discover -s Python/macroeconomia/Forecast/Brasil/2013T4-2026T2/abm1_com_leiloeiro -v
"""
import copy
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))   # macroeconomia/
import caminhos  # noqa: E402,F401

import economia as E  # noqa: E402
import expectativas as X  # noqa: E402
import previsao_abm as PA  # noqa: E402
import protocolo  # noqa: E402
from calibracao_renda import carregar_pnad  # noqa: E402
from test_familias import economia_calibrada  # noqa: E402


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.est, cls.alvos = economia_calibrada()
        cls.cal = E.preparar(cls.est)
        cls.crescimento, cls.anuais = protocolo.carregar_tudo()


class TestPasso(Base):
    def test_contabilidade(self):
        rng = np.random.default_rng(0)
        estado = E.estado_inicial(self.cal, X.Aprendizado(), 5000, rng)
        par = self.cal.par
        for _ in range(5):
            poupanca_anterior = estado.s.mean()
            novo, reg = E.passo(self.cal, estado, rng, log_gamma=0.004, crescimento_gasto=0.01)
            K = poupanca_anterior * np.exp(-0.004 - par.n * par.periodo)
            self.assertAlmostEqual(reg["K"], K)
            self.assertAlmostEqual(reg["y"], reg["C"] + reg["I"] + reg["G"])
            # A poupança agregada é o capital mais o investimento líquido do trimestre.
            self.assertAlmostEqual(novo.s.mean(), K + par.periodo * (reg["I"] - par.delta * K), places=12)
            # O orçamento do governo fecha: a transferência é a receita menos o gasto.
            R = par.alpha * reg["y"] / K
            receita = par.tau_k * (R - par.delta) * K + par.tau_w * reg["w"] * reg["trabalho"]
            self.assertAlmostEqual(reg["transferencia"], receita - reg["G"])
            estado = novo

    def test_estado_estacionario_e_ponto_de_repouso(self):
        # Sem choques agregados e com crenças de equilíbrio, o capital fica no calibrado.
        rng = np.random.default_rng(1)
        estado = E.estado_inicial(self.cal, X.Equilibrio(), 20_000, rng)
        par = self.cal.par
        Ks = []
        for _ in range(200):
            estado, reg = E.passo(self.cal, estado, rng, log_gamma=par.g * par.periodo, gasto=par.gasto)
            Ks.append(reg["K"])
        self.assertAlmostEqual(np.mean(Ks[100:]) / self.est.K, 1, delta=0.02)
        self.assertAlmostEqual(reg["r"] / self.est.r, 1, delta=0.05)

    def test_populacao_inicial_estratificada(self):
        # Oferta de trabalho e capital iniciais iguais aos do equilíbrio, qualquer que seja a semente.
        for semente in (0, 11, 23):
            estado = E.estado_inicial(self.cal, X.Equilibrio(), 4000, np.random.default_rng(semente))
            self.assertAlmostEqual(self.cal.renda.z[estado.j].mean(), 1.0, delta=1e-3)
            K = estado.s.mean() * self.cal.par.fator_crescimento
            self.assertAlmostEqual(K / self.est.K, 1.0, delta=2e-3)
        np.testing.assert_array_equal(E.contagens(np.array([0.5, 0.3, 0.2]), 7), [4, 2, 1])

    def test_reprodutivel(self):
        amostra = self.crescimento.loc[:200504]
        _, h1 = E.historia(self.cal, amostra, X.Heuristicas(), 3000, semente=5)
        _, h2 = E.historia(self.cal, amostra, X.Heuristicas(), 3000, semente=5)
        pd.testing.assert_frame_equal(h1, h2)


class TestHistoria(Base):
    def test_reproduz_pib_e_gasto_observados(self):
        amostra = self.crescimento.loc[:201504]
        for regra in (X.Equilibrio(), X.Heuristicas(), X.InformacaoRigida()):
            _, h = E.historia(self.cal, amostra, regra, 4000)
            np.testing.assert_allclose(100 * np.diff(h.log_y), amostra.pib, atol=1e-9)
            np.testing.assert_allclose(100 * np.diff(h.log_G), amostra.governo, atol=1e-9)

    def test_consumo_emerge_e_acompanha_os_dados(self):
        _, h = E.historia(self.cal, self.crescimento, X.Equilibrio(), 20_000)
        consumo = 100 * np.diff(h.log_C)
        self.assertGreater(np.corrcoef(consumo, self.crescimento.consumo)[0, 1], 0.5)


class TestExpectativas(unittest.TestCase):
    def setUp(self):
        self.rng = np.random.default_rng(0)

    def test_equilibrio_e_ingenua(self):
        e = X.Equilibrio()
        e.iniciar(10, 0.1, 1.0, self.rng)
        self.assertEqual(e.atualizar(0.2, 3.0, self.rng), (0.1, 1.0))
        i = X.Ingenua()
        i.iniciar(10, 0.1, 1.0, self.rng)
        self.assertEqual(i.atualizar(0.2, 3.0, self.rng), (0.2, 3.0))

    def test_aprendizado_converge_com_o_ganho(self):
        a = X.Aprendizado(ganho=0.1)
        a.iniciar(10, 0.0, 1.0, self.rng)
        for k in range(1, 30):
            r, w = a.atualizar(1.0, 2.0, self.rng)
            self.assertAlmostEqual(r, 1 - 0.9**k)
            self.assertAlmostEqual(w, 2 - 0.9**k)

    def test_atencao_limitada(self):
        for m, esperado in ((0.0, 0.1), (1.0, 0.3), (0.5, 0.2)):
            a = X.AtencaoLimitada(m)
            a.iniciar(10, 0.1, 1.0, self.rng)
            self.assertAlmostEqual(a.atualizar(0.3, 1.0, self.rng)[0], esperado)

    def test_informacao_rigida_atualiza_uma_fracao(self):
        regra = X.InformacaoRigida(X.Ingenua(), lam=0.25)
        regra.iniciar(100_000, 0.1, 1.0, self.rng)
        r, _ = regra.atualizar(0.2, 1.0, self.rng)
        self.assertAlmostEqual(np.mean(r == 0.2), 0.25, delta=0.01)
        r, _ = regra.atualizar(0.3, 1.0, self.rng)
        # Quem não reviu mantém a informação antiga.
        self.assertAlmostEqual(np.mean(r == 0.1), 0.75**2, delta=0.01)
        self.assertAlmostEqual(np.mean(r == 0.2), 0.75 * 0.25, delta=0.01)

    def test_heuristicas_sem_intensidade_dividem_igualmente(self):
        h = X.Heuristicas(intensidade=0.0)
        h.iniciar(30_000, 0.1, 1.0, self.rng)
        for t in range(20):
            h.atualizar(0.1 + 0.01 * np.sin(t), 1.0, self.rng)
        np.testing.assert_allclose(h.fracoes, 1 / 3)
        self.assertAlmostEqual(np.mean(h.escolha == 0), 1 / 3, delta=0.02)

    def test_heuristicas_premiam_a_regra_que_acerta(self):
        # Preços constantes e diferentes do equilíbrio suposto: a regra ingênua
        # acerta sempre e deve dominar; a fundamentalista erra e deve perder espaço.
        h = X.Heuristicas(intensidade=1.0)
        h.iniciar(1000, 0.08, 1.0, self.rng)
        for _ in range(40):
            h.atualizar(0.10, 1.05, self.rng)
        nomes = [r.nome for r in h.regras]
        self.assertAlmostEqual(h.fracoes.sum(), 1.0)
        self.assertGreater(h.fracoes[nomes.index("ingênua")], 0.9)
        self.assertLess(h.fracoes[nomes.index("fundamentalista")], 0.01)


class TestExogenos(unittest.TestCase):
    def test_recupera_o_processo(self):
        rng = np.random.default_rng(3)
        x = np.zeros((5000, 2))
        L = np.array([[0.01, 0.0], [0.004, 0.02]])
        for t in range(1, 5000):
            x[t] = np.array([0.002, 0.003]) + np.array([0.3, -0.2]) * x[t - 1] + L @ rng.standard_normal(2)
        ex = E.Exogenos.estimar(x[:, 0], x[:, 1])
        np.testing.assert_allclose(ex.phi, [0.3, -0.2], atol=0.04)
        np.testing.assert_allclose(ex.L @ ex.L.T, L @ L.T, rtol=0.1, atol=1e-6)

    def test_choques_antiteticos(self):
        ex = E.Exogenos(np.zeros(2), np.array([0.5, 0.5]), np.eye(2), np.zeros(2))
        e = np.random.default_rng(0).standard_normal((6, 2))
        np.testing.assert_allclose(ex.simular(6, choques=e), -ex.simular(6, choques=-e))


class TestPrevisao(Base):
    def test_sem_olhar_o_futuro(self):
        origem = 201504
        trimestral, anual = carregar_pnad()
        alterado = self.crescimento.copy()
        alterado.loc[alterado.index > origem] += 4.0
        anuais_alt = self.anuais.copy()
        anuais_alt.loc[2014:] *= 0.6
        pnad_alt = (trimestral.copy(), anual.copy())
        pnad_alt[0].loc[pnad_alt[0].index > origem, :] *= 1.5
        pnad_alt[1].loc[2015:, :] *= 1.3
        colunas = ["variavel", "h", "previsto", "dp"]
        for chave in ("abm_eq", "abm_heu"):
            original = PA.ModeloABM(self.anuais, chave, (trimestral, anual), N=2000, replicas=6)
            mudado = PA.ModeloABM(anuais_alt, chave, pnad_alt, N=2000, replicas=6)
            p1 = protocolo.prever_na_origem(original, self.crescimento, origem)
            p2 = protocolo.prever_na_origem(mudado, alterado, origem)
            pd.testing.assert_frame_equal(p1[colunas], p2[colunas])

    def test_previsao_de_crescimento_acumulado(self):
        amostra = self.crescimento.loc[:201904]
        estado, h = E.historia(self.cal, amostra, X.Equilibrio(), 4000)
        ex = E.Exogenos.estimar(h.log_gamma.iloc[1:].to_numpy(), amostra.governo.to_numpy() / 100)
        # Sem choques e com gasto crescendo à média, o gasto acumulado é a soma das médias.
        ex_det = E.Exogenos(ex.c, ex.phi, np.zeros((2, 2)), ex.ultimo)
        sim = E.prever(self.cal, copy.deepcopy(estado), h.iloc[-1][E.NIVEIS].to_numpy(float),
                       ex_det, 8, 2, semente=0)
        trajetoria = ex_det.simular(8, choques=np.zeros((8, 2)))
        np.testing.assert_allclose(sim[0, :, 3], 100 * np.cumsum(trajetoria[:, 1]), atol=1e-9)
        # O estado passado não é alterado pela previsão.
        estado2, _ = E.historia(self.cal, amostra, X.Equilibrio(), 4000)
        np.testing.assert_array_equal(estado.s, estado2.s)


if __name__ == "__main__":
    unittest.main()
