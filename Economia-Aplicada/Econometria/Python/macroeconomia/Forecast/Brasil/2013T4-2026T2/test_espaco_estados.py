"""Testes do filtro de Kalman e da previsão acumulada. Rode da pasta Econometria/:

    python -m unittest discover -s Python/macroeconomia/Forecast/Brasil/2013T4-2026T2 -v
"""
import unittest

import numpy as np
from scipy.stats import multivariate_normal

from espaco_estados import ModeloLinear, filtrar, prever_acumulado, simular


def modelo_exemplo(seed=0):
    rng = np.random.default_rng(seed)
    T = np.array([[0.7, 0.2, 0.0], [0.0, 0.5, 0.1], [0.1, 0.0, -0.3]])
    B = rng.normal(size=(3, 3)) * 0.5
    Z = rng.normal(size=(2, 3))
    return ModeloLinear(c=np.array([0.1, -0.2, 0.05]), T=T, Q=B @ B.T, d=np.array([0.5, 1.0]),
                        Z=Z, H=np.diag([0.3, 0.2]))


class TestKalman(unittest.TestCase):
    def test_verossimilhanca_igual_a_normal_multivariada_direta(self):
        m = modelo_exemplo()
        n = 12
        y = simular(m, n, np.random.default_rng(1))
        # Covariância conjunta de (y_1, ..., y_n) com o estado estacionário.
        P0 = m.cov_estacionaria
        a0 = m.media_estacionaria
        k = 2
        media = np.tile(m.d + m.Z @ a0, n)
        cov = np.zeros((n * k, n * k))
        for t in range(n):
            for s in range(t, n):
                bloco = m.Z @ np.linalg.matrix_power(m.T, s - t) @ P0 @ m.Z.T
                if s == t:
                    bloco = bloco + m.H
                cov[s * k:(s + 1) * k, t * k:(t + 1) * k] = bloco
                cov[t * k:(t + 1) * k, s * k:(s + 1) * k] = bloco.T
        direta = multivariate_normal(media, cov).logpdf(y.ravel())
        self.assertAlmostEqual(filtrar(m, y).log_verossimilhanca, direta, places=8)

    def test_estado_observado_sem_erro(self):
        # Z = I e H = 0: o estado filtrado é a última observação, sem incerteza.
        m = ModeloLinear(c=np.zeros(2), T=np.diag([0.5, 0.2]), Q=np.eye(2), d=np.zeros(2),
                         Z=np.eye(2), H=np.zeros((2, 2)))
        y = simular(m, 5, np.random.default_rng(2))
        f = filtrar(m, y)
        np.testing.assert_allclose(f.media, y[-1], atol=1e-10)
        np.testing.assert_allclose(f.cov, 0, atol=1e-10)

    def test_dado_faltante(self):
        # Sem a segunda série no começo, o filtro é o do modelo só com a
        # primeira nesses trimestres e o do modelo completo depois.
        m = modelo_exemplo(6)
        y = simular(m, 20, np.random.default_rng(7))
        lacunas = y.copy()
        lacunas[:8, 1] = np.nan
        so_primeira = ModeloLinear(m.c, m.T, m.Q, m.d[:1], m.Z[:1], m.H[:1, :1])
        inicio = filtrar(so_primeira, y[:8, :1])
        # Continua do estado previsto para o nono trimestre.
        a = m.c + m.T @ inicio.media
        P = m.T @ inicio.cov @ m.T.T + m.Q
        resto = filtrar(m, y[8:], a, P)
        completo = filtrar(m, lacunas)
        self.assertAlmostEqual(completo.log_verossimilhanca,
                               inicio.log_verossimilhanca + resto.log_verossimilhanca, places=10)
        np.testing.assert_allclose(completo.media, resto.media)
        # Um trimestre inteiro sem dados só propaga o estado.
        vazio = y.copy()
        vazio[5] = np.nan
        sem = filtrar(m, np.delete(y, 5, axis=0)[:5])
        a = m.c + m.T @ (m.c + m.T @ sem.media)
        P = m.T @ (m.T @ sem.cov @ m.T.T + m.Q) @ m.T.T + m.Q
        depois = filtrar(m, y[6:], a, P)
        self.assertAlmostEqual(filtrar(m, vazio).log_verossimilhanca,
                               sem.log_verossimilhanca + depois.log_verossimilhanca, places=10)


class TestPrevisaoAcumulada(unittest.TestCase):
    def test_media_e_variancia_batem_com_simulacao(self):
        m = modelo_exemplo(3)
        rng = np.random.default_rng(4)
        media0 = np.array([0.3, -0.1, 0.2])
        cov0 = 0.2 * np.eye(3)
        medias, variancias = prever_acumulado(m, media0, cov0, 6)
        sorteios = 40_000
        xi = rng.multivariate_normal(media0, cov0, size=sorteios)
        soma = np.zeros((sorteios, 2))
        acumulado = []
        L, LH = np.linalg.cholesky(m.Q), np.linalg.cholesky(m.H)
        for _ in range(6):
            xi = m.c + xi @ m.T.T + rng.normal(size=(sorteios, 3)) @ L.T
            soma = soma + m.d + xi @ m.Z.T + rng.normal(size=(sorteios, 2)) @ LH.T
            acumulado.append(soma.copy())
        acumulado = np.array(acumulado)
        erro_media = np.sqrt(variancias / sorteios)
        self.assertTrue(np.all(np.abs(acumulado.mean(axis=1) - medias) < 5 * erro_media))
        np.testing.assert_allclose(acumulado.var(axis=1), variancias, rtol=0.03)

    def test_primeiro_passo(self):
        m = modelo_exemplo(5)
        media0, cov0 = np.array([1.0, 0.0, -1.0]), np.eye(3)
        medias, variancias = prever_acumulado(m, media0, cov0, 1)
        np.testing.assert_allclose(medias[0], m.d + m.Z @ (m.c + m.T @ media0))
        V = m.Z @ (m.T @ cov0 @ m.T.T + m.Q) @ m.Z.T + m.H
        np.testing.assert_allclose(variancias[0], np.diag(V))


if __name__ == "__main__":
    unittest.main()
