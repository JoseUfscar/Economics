"""Testes das referências estatísticas e das medidas de acurácia. Rode da pasta Econometria/:

    python -m unittest discover -s Python/macroeconomia/Forecast/Brasil/2013T4-2026T2/referencias -v
"""
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import integrate, stats
from statsmodels.tsa.api import VAR
from statsmodels.tsa.ar_model import AutoReg

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))   # macroeconomia/
import caminhos  # noqa: E402,F401

import referencias  # noqa: E402
from avaliacao import clark_west, crps_normal, diebold_mariano, holm, resumo  # noqa: E402


def serie_var(n=200, seed=0):
    rng = np.random.default_rng(seed)
    Phi = np.array([[0.5, 0.1, 0.0], [0.2, 0.3, 0.1], [0.0, -0.2, 0.4]])
    y = np.zeros((n, 3))
    for t in range(1, n):
        y[t] = np.array([0.5, 0.2, -0.1]) + Phi @ y[t - 1] + rng.normal(size=3)
    return y


class TestReferencias(unittest.TestCase):
    def test_var1_igual_ao_statsmodels(self):
        y = serie_var()
        m = referencias.var1(y)
        ajuste = VAR(y).fit(1, trend="c")
        np.testing.assert_allclose(m.c, ajuste.intercept, atol=1e-10)
        np.testing.assert_allclose(m.T, ajuste.coefs[0], atol=1e-10)
        np.testing.assert_allclose(m.Q, ajuste.sigma_u, atol=1e-10)

    def test_ar1_igual_ao_statsmodels(self):
        y = serie_var(seed=1)
        m = referencias.ar1(y)
        for j in range(3):
            ajuste = AutoReg(y[:, j], lags=1, trend="c").fit()
            np.testing.assert_allclose([m.c[j], m.T[j, j]], ajuste.params, atol=1e-10)
            residuo = ajuste.resid
            self.assertAlmostEqual(m.Q[j, j], residuo @ residuo / (len(residuo) - 2), places=10)

    def test_media(self):
        y = serie_var(seed=2)
        m = referencias.media(y)
        np.testing.assert_allclose(m.c, y.mean(axis=0))
        np.testing.assert_allclose(m.T, 0)

    def test_serie_que_comeca_depois(self):
        # A terceira série só existe nos últimos 60 trimestres: média e AR(1)
        # dela usam só esses, e as outras não mudam.
        y = serie_var(seed=8)
        lacunas = y.copy()
        lacunas[:-60, 2] = np.nan
        for estimador in (referencias.media, referencias.ar1):
            com, sem = estimador(lacunas), estimador(y)
            curta = estimador(y[-60:, 2:])
            np.testing.assert_allclose(com.c[:2], sem.c[:2])
            np.testing.assert_allclose(np.diag(com.T)[:2], np.diag(sem.T)[:2])
            self.assertAlmostEqual(com.c[2], curta.c[0])
            self.assertAlmostEqual(com.T[2, 2], curta.T[0, 0])
            self.assertAlmostEqual(com.Q[2, 2], curta.Q[0, 0])


class TestCRPS(unittest.TestCase):
    def test_formula_fechada_igual_a_integral(self):
        for media, dp, y in ((0.0, 1.0, 0.3), (1.0, 2.5, -2.0), (-0.5, 0.4, 1.7)):
            abaixo, _ = integrate.quad(lambda x: stats.norm.cdf(x, media, dp) ** 2, -np.inf, y)
            acima, _ = integrate.quad(lambda x: stats.norm.sf(x, media, dp) ** 2, y, np.inf)
            numerica = abaixo + acima
            self.assertAlmostEqual(float(crps_normal(media, dp, y)), numerica, places=6)

    def test_sem_incerteza_vira_erro_absoluto(self):
        self.assertAlmostEqual(float(crps_normal(1.0, 1e-9, 3.5)), 2.5, places=6)


class TestDieboldMariano(unittest.TestCase):
    def test_antissimetrico(self):
        rng = np.random.default_rng(3)
        e1, e2 = rng.normal(size=60), 1.3 * rng.normal(size=60)
        dm12, p12 = diebold_mariano(e1, e2, 2)
        dm21, p21 = diebold_mariano(e2, e1, 2)
        self.assertAlmostEqual(dm12, -dm21)
        self.assertAlmostEqual(p12, p21)

    def test_correcao_hln_para_h_1(self):
        rng = np.random.default_rng(4)
        e1, e2 = rng.normal(size=40), rng.normal(size=40)
        d = e1**2 - e2**2
        n = d.size
        dm_puro = d.mean() / np.sqrt(np.var(d) / n)
        self.assertAlmostEqual(diebold_mariano(e1, e2, 1)[0], dm_puro * np.sqrt((n - 1) / n))

    def test_tamanho_sob_a_hipotese_nula(self):
        rng = np.random.default_rng(5)
        rejeicoes = [diebold_mariano(rng.normal(size=50), rng.normal(size=50), 1)[1] < 0.05
                     for _ in range(2000)]
        self.assertTrue(0.03 < np.mean(rejeicoes) < 0.07)

    def test_detecta_diferenca_grande(self):
        rng = np.random.default_rng(6)
        dm, p = diebold_mariano(rng.normal(size=80), 2 * rng.normal(size=80), 1)
        self.assertLess(dm, 0)
        self.assertLess(p, 0.01)


class TestAninhadosEHolm(unittest.TestCase):
    def test_holm_contra_statsmodels(self):
        from statsmodels.stats.multitest import multipletests
        p = np.array([0.01, 0.04, 0.03, 0.2, 0.0005])
        np.testing.assert_allclose(holm(p), multipletests(p, method="holm")[1])
        com_nan = holm(np.array([0.01, np.nan, 0.04]))
        self.assertTrue(np.isnan(com_nan[1]))
        np.testing.assert_allclose(com_nan[[0, 2]], multipletests([0.01, 0.04], method="holm")[1])

    def test_clark_west_tem_tamanho_certo_onde_o_dm_rejeita_de_menos(self):
        # Sob H0 o modelo grande (AR(1) estimado) tem coeficiente zero: a média
        # é o modelo certo. Rejeições unilaterais a 10% a favor do grande.
        rng = np.random.default_rng(11)
        cw, dm = [], []
        for _ in range(300):
            y = rng.normal(size=140)
            p_peq, p_gr, real = [], [], []
            for t in range(60, 139):
                x, z = y[:t - 1], y[1:t]
                b = np.polyfit(x, z, 1)
                p_peq.append(y[:t].mean())
                p_gr.append(b[1] + b[0] * y[t - 1])
                real.append(y[t])
            real, p_peq, p_gr = map(np.array, (real, p_peq, p_gr))
            estat, p_cw = clark_west(real - p_peq, real - p_gr, p_peq, p_gr, 1)
            cw.append(p_cw < 0.10)
            d, _ = diebold_mariano(real - p_gr, real - p_peq, 1)
            dm.append(d < -1.29)
        self.assertGreater(np.mean(cw), 0.05)
        self.assertLess(np.mean(cw), 0.16)
        self.assertLess(np.mean(dm), np.mean(cw) / 2)

    def test_resumo_usa_clark_west_nos_aninhados(self):
        rng = np.random.default_rng(3)
        linhas = []
        for origem in range(40):
            real = rng.normal()
            for modelo, ruido in (("AR(1)", 1.0), ("Média", 1.1), ("VAR(1)", 0.9), ("Outro", 0.8)):
                linhas.append({"origem": origem, "modelo": modelo, "variavel": "pib", "h": 1,
                               "previsto": real + ruido * rng.normal(), "dp": 1.0, "realizado": real})
        tabela = resumo(pd.DataFrame(linhas)).set_index("modelo")
        self.assertTrue(np.isnan(tabela.loc["Outro", "p_valor_cw"]))
        self.assertEqual(tabela.loc["Outro", "p_teste"], tabela.loc["Outro", "p_valor"])
        for modelo in ("Média", "VAR(1)"):
            self.assertFalse(np.isnan(tabela.loc[modelo, "p_valor_cw"]))
            self.assertEqual(tabela.loc[modelo, "p_teste"], tabela.loc[modelo, "p_valor_cw"])
        outros = tabela.drop(index="AR(1)")
        np.testing.assert_allclose(outros.p_holm, holm(outros.p_teste.to_numpy()))


class TestResumo(unittest.TestCase):
    def test_referencia_tem_razao_um_e_outros_comparam_nas_mesmas_origens(self):
        rng = np.random.default_rng(7)
        linhas = []
        for origem in range(30):
            real = rng.normal()
            for modelo, ruido in (("AR(1)", 1.0), ("Outro", 0.5)):
                linhas.append({"origem": origem, "modelo": modelo, "variavel": "pib", "h": 1,
                               "previsto": real + ruido * rng.normal(), "dp": ruido,
                               "realizado": real})
        tabela = resumo(pd.DataFrame(linhas)).set_index("modelo")
        self.assertAlmostEqual(tabela.loc["AR(1)", "rmse_relativo"], 1.0)
        self.assertLess(tabela.loc["Outro", "rmse_relativo"], 1.0)
        self.assertEqual(tabela.loc["Outro", "n"], 30)

    def test_cobertura_do_intervalo(self):
        # Erros de 0, 1 e 3 desvios-padrão: dois dos três dentro do intervalo de 90%.
        linhas = [{"origem": o, "modelo": "AR(1)", "variavel": "pib", "h": 1,
                   "previsto": 0.0, "dp": 1.0, "realizado": r}
                  for o, r in enumerate([0.0, 1.0, -3.0])]
        tabela = resumo(pd.DataFrame(linhas))
        self.assertAlmostEqual(tabela.cobertura_90.iloc[0], 2 / 3)


if __name__ == "__main__":
    unittest.main()
