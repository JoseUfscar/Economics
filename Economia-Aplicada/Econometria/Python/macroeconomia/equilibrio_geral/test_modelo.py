"""
Testes econômicos e numéricos do modelo. Rode a partir da pasta Econometria/:

    python -m unittest discover -s Python/macroeconomia/equilibrio_geral -v
"""
import unittest

import numpy as np

from modelo import (Economia, Politica, estado_estacionario, fluxos_anuais,
                    ganho_bem_estar, receita_estacionaria, resolver_transicao)

ECO = Economia()
BASE = Politica(tau_k=0.25, gasto=0.2)
MAIS_IMPOSTO = Politica(tau_k=0.30, gasto=0.2)


def campo(eco, pol, k, c):
    dk = k**eco.alpha - c - pol.gasto - (eco.delta + eco.n + eco.g) * k
    dc = c * ((1 - pol.tau_k) * (eco.alpha * k ** (eco.alpha - 1) - eco.delta)
              - eco.rho - eco.theta * eco.g) / eco.theta
    return np.array([dk, dc])


class TestEstadoEstacionario(unittest.TestCase):
    def test_sem_governo_coincide_com_formula_fechada(self):
        ee = estado_estacionario(ECO)
        m = ECO.delta + ECO.rho + ECO.theta * ECO.g
        self.assertAlmostEqual(ee.k, (ECO.alpha / m) ** (1 / (1 - ECO.alpha)), places=12)
        self.assertAlmostEqual(ee.k, 4.016397590517025, places=11)
        self.assertAlmostEqual(ee.c, 1.2609054253865568, places=11)
        self.assertAlmostEqual(ee.lambda_estavel, -0.09457031657589857, places=11)

    def test_euler_e_restricao_de_recursos(self):
        ee = estado_estacionario(ECO, BASE)
        r = (1 - BASE.tau_k) * (ECO.alpha * ee.k ** (ECO.alpha - 1) - ECO.delta)
        self.assertAlmostEqual(r, ECO.rho + ECO.theta * ECO.g, places=12)
        self.assertAlmostEqual(ee.r, r, places=12)
        self.assertAlmostEqual(
            ee.y, ee.c + BASE.gasto + (ECO.delta + ECO.n + ECO.g) * ee.k, places=12)

    def test_efeitos_de_longo_prazo_da_politica(self):
        base = estado_estacionario(ECO, BASE)
        self.assertLess(estado_estacionario(ECO, MAIS_IMPOSTO).k, base.k)
        # O gasto desloca consumo um a um e não muda k*; tau_c constante é neutro.
        sem_gasto = estado_estacionario(ECO, Politica(tau_k=0.25))
        self.assertAlmostEqual(sem_gasto.k, base.k, places=12)
        self.assertAlmostEqual(sem_gasto.c - base.c, BASE.gasto, places=12)
        com_tau_c = estado_estacionario(ECO, Politica(tau_k=0.25, tau_c=0.2, gasto=0.2))
        self.assertAlmostEqual(com_tau_c.c, base.c, places=12)

    def test_ponto_de_sela_e_direcao_estavel(self):
        ee = estado_estacionario(ECO, BASE)
        a = ECO.alpha * ee.k ** (ECO.alpha - 1) - (ECO.delta + ECO.n + ECO.g)
        b = ee.c * (1 - BASE.tau_k) * ECO.alpha * (ECO.alpha - 1) * ee.k ** (ECO.alpha - 2) / ECO.theta
        jac = np.array([[a, -1.0], [b, 0.0]])
        np.testing.assert_allclose(np.sort(np.linalg.eigvals(jac)),
                                   [ee.lambda_estavel, ee.lambda_instavel], atol=1e-12)
        self.assertLess(ee.lambda_estavel, 0)
        self.assertGreater(ee.lambda_instavel, 0)
        v = np.array([1.0, ee.inclinacao])
        np.testing.assert_allclose(jac @ v, ee.lambda_estavel * v, atol=1e-12)

    def test_parametros_invalidos(self):
        for kwargs in ({"alpha": 1.0}, {"theta": 0.0}, {"delta": -0.1},
                       {"rho": 0.01, "n": 0.02, "theta": 1.0, "g": 0.0}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                Economia(**kwargs)
        with self.assertRaises(ValueError):
            Politica(tau_k=1.0)
        with self.assertRaises(ValueError):
            estado_estacionario(ECO, Politica(gasto=5.0))


class TestTransicao(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ee0 = estado_estacionario(ECO, BASE)
        cls.ee1 = estado_estacionario(ECO, MAIS_IMPOSTO)
        cls.inesperado = resolver_transicao(ECO, cls.ee0.k, MAIS_IMPOSTO)
        cls.anunciado = resolver_transicao(ECO, cls.ee0.k, [(0, BASE), (2.0, MAIS_IMPOSTO)])

    def test_trajetoria_resolve_o_sistema_diferencial(self):
        ee = estado_estacionario(ECO)
        traj = resolver_transicao(ECO, 0.7 * ee.k, Politica())
        self.assertAlmostEqual(traj.avaliar(0.0)[0], 0.7 * ee.k, places=9)
        h = 1e-4
        for t in (0.5, 3.0, 10.0, 40.0):
            derivada = (np.array(traj.avaliar(t + h)) - np.array(traj.avaliar(t - h))) / (2 * h)
            np.testing.assert_allclose(derivada, campo(ECO, Politica(), *traj.avaliar(t)),
                                       rtol=1e-5, atol=1e-7)
        np.testing.assert_allclose(traj.avaliar(traj.fim), (ee.k, ee.c), rtol=1e-6)

    def test_horizonte_numerico_nao_altera_a_solucao(self):
        curto = resolver_transicao(ECO, self.ee0.k, MAIS_IMPOSTO, horizonte=100)
        longo = resolver_transicao(ECO, self.ee0.k, MAIS_IMPOSTO, horizonte=250)
        t = np.array([0.0, 1.0, 5.0, 20.0, 60.0])
        np.testing.assert_allclose(curto.avaliar(t), longo.avaliar(t), rtol=1e-6)

    def test_choque_inesperado_consumo_salta_e_capital_cai(self):
        k, c = self.inesperado.avaliar(np.linspace(0, 100, 201))
        self.assertGreater(c[0], self.ee0.c)
        self.assertTrue(np.all(np.diff(k) < 0))
        self.assertTrue(np.all(np.diff(c) < 0))
        self.assertAlmostEqual(k[-1], self.ee1.k, delta=1e-3 * self.ee1.k)

    def test_choque_anunciado_consumo_continuo_na_vigencia(self):
        antes, depois = self.anunciado.avaliar(2.0 - 1e-9), self.anunciado.avaliar(2.0)
        np.testing.assert_allclose(antes, depois, rtol=1e-7)
        k0, c0 = self.anunciado.avaliar(0.0)
        self.assertGreater(c0, self.ee0.c)
        self.assertLess(c0, self.inesperado.avaliar(0.0)[1])

    def test_antecedencia_maior_reduz_o_salto_inicial(self):
        saltos = [resolver_transicao(ECO, self.ee0.k, [(0, BASE), (ta, MAIS_IMPOSTO)]).avaliar(0.0)[1]
                  - self.ee0.c for ta in (0.5, 2.0, 10.0)]
        self.assertTrue(saltos[0] > saltos[1] > saltos[2] > 0)

    def test_aumento_anunciado_de_tau_c_gera_salto_na_vigencia(self):
        novo = Politica(tau_k=0.25, tau_c=0.10, gasto=0.2)
        traj = resolver_transicao(ECO, self.ee0.k, [(0, BASE), (3.0, novo)])
        razao = traj.avaliar(3.0 - 1e-9)[1] / traj.avaliar(3.0)[1]
        self.assertAlmostEqual(razao, 1.10 ** (1 / ECO.theta), places=7)
        # Com tau_c constante no longo prazo, a economia volta ao mesmo k*.
        self.assertAlmostEqual(traj.avaliar(traj.fim)[0], self.ee0.k, delta=1e-4)

    def test_choque_temporario_de_gasto_volta_ao_estado_inicial(self):
        alto = Politica(tau_k=0.25, gasto=0.25)
        traj = resolver_transicao(ECO, self.ee0.k, [(0, alto), (5.0, BASE)])
        self.assertLess(traj.avaliar(0.0)[1], self.ee0.c)
        self.assertLess(traj.avaliar(5.0)[0], self.ee0.k)
        np.testing.assert_allclose(traj.avaliar(traj.fim), (self.ee0.k, self.ee0.c), rtol=1e-5)


class TestContabilidadeEBemEstar(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ee0 = estado_estacionario(ECO, BASE)
        cls.traj = resolver_transicao(ECO, cls.ee0.k, [(0, BASE), (2.5, MAIS_IMPOSTO)])

    def test_identidades_anuais(self):
        tab = fluxos_anuais(self.traj, 6)
        np.testing.assert_allclose(tab.Y, tab.C + tab.G + tab.I, rtol=0, atol=1e-12)
        capital_anterior = self.ee0.k
        for linha in tab.itertuples():
            # K(j) - K(j-1) = investimento bruto do ano - depreciação do ano
            self.assertAlmostEqual(linha.K_fim - capital_anterior,
                                   linha.I - ECO.delta * linha.K_medio, delta=1e-6)
            capital_anterior = linha.K_fim

    def test_orcamento_das_familias_reproduz_a_restricao_de_recursos(self):
        t = np.array([1.0, 2.0, 4.0, 15.0])
        tab = self.traj.tabela(t)
        tau_c = np.array([p.tau_c for p in self.traj.politica(t)])
        renda = tab.r * tab.k + tab.salario + tab.transferencia
        dk_familia = renda - (1 + tau_c) * tab.c - (ECO.n + ECO.g) * tab.k
        dk_recursos = tab.y - tab.c - tab.gasto - (ECO.delta + ECO.n + ECO.g) * tab.k
        np.testing.assert_allclose(dk_familia, dk_recursos, atol=1e-12)

    def test_bem_estar(self):
        sem_mudanca = resolver_transicao(ECO, self.ee0.k, BASE)
        self.assertAlmostEqual(ganho_bem_estar(sem_mudanca, self.ee0, ECO), 0.0, places=9)
        self.assertLess(ganho_bem_estar(self.traj, self.ee0, ECO), 0)
        corte = resolver_transicao(ECO, self.ee0.k, Politica(tau_k=0.0, gasto=0.2))
        self.assertGreater(ganho_bem_estar(corte, self.ee0, ECO), 0)

    def test_bem_estar_com_utilidade_logaritmica(self):
        eco = Economia(theta=1.0)
        ee0 = estado_estacionario(eco, BASE)
        sem_mudanca = resolver_transicao(eco, ee0.k, BASE)
        self.assertAlmostEqual(ganho_bem_estar(sem_mudanca, ee0, eco), 0.0, places=9)
        mais = resolver_transicao(eco, ee0.k, MAIS_IMPOSTO)
        perto = Economia(theta=1.0 + 1e-6)
        mais_perto = resolver_transicao(perto, estado_estacionario(perto, BASE).k, MAIS_IMPOSTO)
        self.assertAlmostEqual(ganho_bem_estar(mais, ee0, eco),
                               ganho_bem_estar(mais_perto, estado_estacionario(perto, BASE), perto),
                               places=6)

    def test_curva_de_laffer_de_longo_prazo(self):
        # Em nível a receita tem pico interior, pois k* -> 0 quando tau_k -> 1;
        # como fração do PIB ela só cresce, porque a base encolhe junto com y.
        aliquotas = np.linspace(0, 0.98, 50)
        receitas = [receita_estacionaria(ECO, Politica(tau_k=t)) for t in aliquotas]
        nivel = [r["capital"] for r in receitas]
        pico = int(np.argmax(nivel))
        self.assertEqual(nivel[0], 0.0)
        self.assertTrue(0 < pico < len(aliquotas) - 1)
        self.assertTrue(np.all(np.diff([r["capital_pib"] for r in receitas]) > 0))


if __name__ == "__main__":
    unittest.main()
