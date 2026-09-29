"""Testes da economia sem leiloeiro. Rode da pasta Econometria/:

    python -m unittest discover -s Python/macroeconomia/Forecast/Brasil/2013T4-2026T2/abm2_sem_leiloeiro -v
"""
import sys
import unittest
from dataclasses import replace
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))   # macroeconomia/
import caminhos  # noqa: E402,F401

import descentralizada as DC  # noqa: E402
import expectativas as X  # noqa: E402
import familias as F  # noqa: E402
from comum import economia_base as economia_com_leiloeiro  # noqa: E402
from experimentos_mercados import economia_base  # noqa: E402


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.eco, cls.aumento = economia_base()
        cls.cal = cls.eco.cal


class TestReferencia(Base):
    def test_desempregados_recebem_do_governo_e_nao_produzem(self):
        est, renda = self.cal.est, self.cal.renda
        L, B = F.trabalho_e_beneficio(renda, DC.desempregados(renda))
        self.assertAlmostEqual(L + B, 1.0)
        desempregados = renda.pi[DC.desempregados(renda)].sum()
        self.assertAlmostEqual(desempregados, 0.097, delta=0.001)   # desocupação da PNAD
        self.assertAlmostEqual(est.transferencia, 0.0, places=10)   # orçamento fecha com tau_w
        R, w, y = F.precos(est.par, est.K, L)
        self.assertAlmostEqual(est.K / y, 2.272, places=3)          # K/Y dos dados
        self.assertAlmostEqual(est.distribuicao.media / est.K, 1.0, places=6)

    def test_mesmo_juro_e_salario_que_com_leiloeiro(self):
        # K/L e, portanto, r e w são os mesmos; só o capital cai com o trabalho.
        cal_leiloeiro, _ = economia_com_leiloeiro()
        self.assertAlmostEqual(self.cal.est.r, cal_leiloeiro.est.r, places=10)
        self.assertAlmostEqual(self.cal.est.w, cal_leiloeiro.est.w, places=10)
        L = self.eco.trabalho_referencia
        self.assertAlmostEqual(self.cal.est.K / cal_leiloeiro.est.K, L, places=10)


class TestFluxos(Base):
    def test_com_vagas_sobrando_o_emprego_segue_a_cadeia_da_pnad(self):
        rng = np.random.default_rng(0)
        N = 60_000
        empregador = np.full(N, -1)
        curta = np.arange(N) < N // 2
        eficiencia = np.full(N, 1.0 / N)
        vagas = np.full(10, 1.0)
        contratados, _ = DC._buscar(empregador, curta, eficiencia, vagas, np.ones(10), self.eco, rng,
                                    np.ones(N, dtype=bool))
        P = self.cal.renda.P
        self.assertAlmostEqual(np.mean(empregador[curta] >= 0), P[DC.CURTA, DC.EMPREGADO], delta=0.01)
        self.assertAlmostEqual(np.mean(empregador[~curta] >= 0), P[DC.LONGA, DC.EMPREGADO], delta=0.01)
        self.assertEqual(contratados, int(np.sum(empregador >= 0)))

    def test_sem_vagas_ninguem_e_contratado_e_quem_acabou_de_sair_espera(self):
        rng = np.random.default_rng(1)
        empregador = np.full(100, -1)
        contratados, _ = DC._buscar(empregador, np.ones(100, dtype=bool), np.full(100, 0.01),
                                    np.zeros(5), np.ones(5), self.eco, rng, np.ones(100, dtype=bool))
        self.assertEqual(contratados, 0)
        contratados, _ = DC._buscar(empregador, np.ones(100, dtype=bool), np.full(100, 0.01),
                                    np.ones(5), np.ones(5), self.eco, rng, np.zeros(100, dtype=bool))
        self.assertEqual(contratados, 0)

    def test_vagas_limitam_as_contratacoes(self):
        rng = np.random.default_rng(2)
        N = 1000
        empregador = np.full(N, -1)
        vagas = np.array([0.05, 0.0, 0.02])
        DC._buscar(empregador, np.ones(N, dtype=bool), np.full(N, 1.0 / N), vagas, np.ones(3),
                   self.eco, rng, np.ones(N, dtype=bool))
        contratados = np.bincount(empregador[empregador >= 0], minlength=3) / N
        self.assertEqual(contratados[1], 0.0)
        # Aceita enquanto há vaga: passa no máximo uma pessoa.
        np.testing.assert_array_less(contratados, vagas + 1.0 / N + 1e-12)
        np.testing.assert_array_less(vagas - 1e-12, contratados + 1.0 / N)

    def test_demissoes_nao_passam_do_pedido(self):
        rng = np.random.default_rng(3)
        empregador = np.repeat(np.arange(4), 25)
        eficiencia = rng.uniform(0.5, 1.5, 100) / 100
        reducao = np.array([0.0, 0.05, 0.10, 1.0])
        demitidos = DC._demitir(empregador, eficiencia, reducao, rng)
        cortado = np.bincount(empregador[demitidos], eficiencia[demitidos], 4)
        np.testing.assert_array_less(cortado, reducao + 1e-15)
        self.assertEqual(cortado[0], 0.0)
        self.assertAlmostEqual(cortado[3], eficiencia[empregador == 3].sum())   # a firma inteira


class TestMercadoDeBens(unittest.TestCase):
    def test_racionamento_e_ordem_de_compra(self):
        # A família 0 prefere a firma 0 (mais barata), que tem pouco estoque.
        fornecedores = np.array([[1, 0, 2], [3, 2, 1]])
        p = np.array([1.0, 1.2, 1.5, 1.3])
        estoque = np.array([0.1, 10.0, 10.0, 10.0])   # por família (N = 2)
        orcamento = np.array([1.0, 0.6])
        gasto, quantidade, vendas, gasto_inst, qtd_inst, racionou, demanda = DC._mercado_de_bens(
            orcamento, fornecedores, p, estoque, 0.3, np.ones(4))
        # Família 0: pede 1 unidade à firma 0, que tem 0,1 x 2 = 0,2 para ela; o resto vai à firma 1.
        self.assertAlmostEqual(quantidade[0], 0.2 + (1.0 - 0.2) / 1.2)
        self.assertEqual(racionou[0], 0)
        self.assertAlmostEqual(quantidade[1], 0.6 / 1.2)              # a mais barata das suas
        np.testing.assert_allclose(gasto, orcamento)                 # sobra estoque: todos gastam tudo
        np.testing.assert_array_less(vendas, estoque + 1e-15)
        self.assertAlmostEqual(gasto_inst, 0.3)
        self.assertAlmostEqual(vendas @ p, gasto.mean() + gasto_inst)
        np.testing.assert_allclose(demanda, vendas)                   # ninguém ficou sem nada

    def test_demanda_nao_atendida_sem_dupla_contagem(self):
        fornecedores = np.array([[0, 1], [0, 1], [1, 0]])
        p = np.ones(2)
        estoque = np.array([0.2, 0.1])
        orcamento = np.ones(3)
        gasto, _, vendas, gasto_inst, _, _, demanda = DC._mercado_de_bens(
            orcamento, fornecedores, p, estoque, 0.5, np.ones(2))
        np.testing.assert_allclose(vendas, estoque)                   # tudo vendido
        self.assertEqual(gasto_inst, 0.0)                             # as famílias vêm primeiro
        falta_familias = (orcamento - gasto).mean()
        self.assertAlmostEqual(demanda.sum() - vendas.sum(), falta_familias + 0.5)


class TestUltimaRodada(unittest.TestCase):
    def test_quem_ficou_sem_nada_procura_outra_firma(self):
        fornecedores = np.array([[0, 1], [0, 1]])
        p = np.ones(3)
        estoque = np.array([0.0, 0.0, 5.0])   # os fornecedores estão sem estoque
        orcamento = np.array([1.0, 2.0])
        sem, qtd_sem, *_ = DC._mercado_de_bens(orcamento, fornecedores, p, estoque, 0.0, np.ones(3))
        np.testing.assert_array_equal(qtd_sem, 0.0)
        com, qtd_com, vendas, *_ = DC._mercado_de_bens(orcamento, fornecedores, p, estoque, 0.0, np.ones(3),
                                                       np.random.default_rng(0))
        np.testing.assert_allclose(qtd_com, orcamento)
        self.assertAlmostEqual(vendas[2], orcamento.mean())


class TestTrimestre(Base):
    def test_populacao_inicial(self):
        rng = np.random.default_rng(4)
        e = DC.estado_inicial(self.eco, X.Aprendizado(), 5000, rng)
        fator = self.cal.par.fator_crescimento
        # A riqueza das famílias é o capital mais os estoques.
        self.assertAlmostEqual(e.s.mean() + e.governo, e.k.sum() + e.p @ e.x, places=12)
        self.assertAlmostEqual(e.s.mean() * fator / self.cal.est.K, 1.0, delta=0.01)
        l = DC.trabalho_das_firmas(e, self.eco.eficiencia[e.tipo] / e.N, self.eco.comp.firmas)
        self.assertAlmostEqual(l.sum() / self.eco.trabalho_referencia, 1.0, delta=0.005)
        self.assertTrue(np.all(l > 0))
        self.assertAlmostEqual(np.mean(e.empregador < 0), 0.097, delta=0.002)

    def test_contabilidade_de_cada_trimestre(self):
        rng = np.random.default_rng(5)
        e = DC.estado_inicial(self.eco, X.Aprendizado(), 4000, rng)
        par = self.cal.par
        for _ in range(12):
            governo_antes = e.governo
            fator = np.exp(-par.g * par.periodo - par.n * par.periodo)
            e, reg = DC.trimestre(self.eco, e, rng, par.g * par.periodo, par.gasto)
            # Riqueza das famílias + saldo do governo = capital + estoques.
            self.assertAlmostEqual(e.s.mean() + e.governo, e.k.sum() + e.p @ e.x, places=12)
            # O governo gasta o que arrecada: a transferência fecha o orçamento.
            T = par.tau_w * (reg["salarios"] + reg["beneficio"]) - reg["beneficio"] - par.gasto \
                + governo_antes * fator / par.periodo
            self.assertAlmostEqual(reg["transferencia"], T, places=12)
            self.assertAlmostEqual(reg["y"], reg["C"] + reg["I"] + reg["G"] + reg["dX"], places=12)
            self.assertTrue(np.all(e.x >= -1e-15))
            self.assertAlmostEqual(reg["desemprego"], np.mean(e.empregador < 0))
            self.assertTrue(np.all((e.empregador >= -1) & (e.empregador < self.eco.comp.firmas)))
            margem = e.margem
            self.assertTrue(np.all((margem >= self.eco.comp.margem_minima - 1e-12)
                                   & (margem <= self.eco.comp.margem_maxima + 1e-12)))

    def test_estavel_e_perto_da_referencia(self):
        # Sem choques agregados, a economia fica em torno de um ponto de repouso:
        # desemprego perto do da PNAD e juro perto do de equilíbrio.
        rng = np.random.default_rng(6)
        e = DC.estado_inicial(self.eco, X.Aprendizado(), 5000, rng)
        _, h = DC.simular(self.eco, e, rng, 4 * 60)
        final = h.iloc[-80:].mean()
        self.assertAlmostEqual(final.desemprego, 0.10, delta=0.03)
        self.assertAlmostEqual(final.r, self.cal.est.r, delta=0.015)
        self.assertGreater(final.K / self.cal.est.K, 0.7)
        self.assertLess(final.K / self.cal.est.K, 1.1)
        self.assertGreater(final.margem_alvo, 0.0)                    # a margem emerge positiva
        # Muitas famílias acham algum fornecedor sem estoque, mas quase todas
        # terminam o trimestre comprando o que queriam em outra firma.
        self.assertLess(final.racionadas, 0.6)
        self.assertLess(final.sem_comprar_tudo, 0.01)

    def test_salario_revisto_parte_da_media(self):
        # Salários bem dispersos. Se todas as firmas cortam, nenhuma fica acima
        # da média paga; se todas sobem, nenhuma fica abaixo dela.
        rng = np.random.default_rng(8)
        e = DC.estado_inicial(self.eco, X.Aprendizado(), 4000, rng)
        comp, par = self.eco.comp, self.cal.par
        e = replace(e, w=e.w * np.exp(0.2 * rng.standard_normal(e.w.size)))
        l = DC.trabalho_das_firmas(e, self.eco.eficiencia[e.tipo] / e.N, comp.firmas)
        casos = {"corta": replace(e, quadro_alvo=np.zeros_like(l),
                                  sem_vaga=np.full(l.size, comp.paciencia_salario)),
                 "sobe": replace(e, quadro_alvo=3 * l)}
        for nome, inicio in casos.items():
            novo, registro = DC.trimestre(self.eco, inicio, np.random.default_rng(9),
                                          par.g * par.periodo, par.gasto)
            razao = np.log(novo.w.max() / novo.w.min())
            passo = comp.passo_salario
            if nome == "corta":   # max <= média e min >= min(w)(1 - passo)
                limite = np.log(registro["w"] / (e.w.min() * (1 - passo)))
            else:                 # min >= média e max <= max(w)(1 + passo)
                limite = np.log(e.w.max() * (1 + passo) / registro["w"])
            self.assertLessEqual(razao, limite + 1e-12, nome)
            self.assertLess(razao, 0.7 * np.log(e.w.max() / e.w.min()), nome)

    def test_so_a_receita_nova_segue_os_pesos_da_reforma(self):
        # Sem receita nova, trocar os pesos da devolução para só o grupo
        # intermediário não muda nada: o resto do orçamento continua dividido
        # igualmente entre todos.
        pesos = np.array([0, 0, 0, 1, 0, 0, 0, 0, 0], dtype=float)   # a devolução por isenção da lei
        cal1 = replace(self.cal, pesos=pesos / (self.cal.renda.pi @ pesos))
        eco1 = replace(self.eco, cal=cal1, tau_k_base=self.cal.par.tau_k)
        historias = []
        for eco in (self.eco, eco1):
            rng = np.random.default_rng(8)
            e = DC.estado_inicial(self.eco, X.Aprendizado(), 2000, rng)
            _, h = DC.simular(eco, e, rng, 12)
            historias.append(h)
        np.testing.assert_array_equal(historias[1].to_numpy(), historias[0].to_numpy())

    def test_numeros_aleatorios_comuns(self):
        historias = []
        for _ in range(2):
            rng = np.random.default_rng(7)
            e = DC.estado_inicial(self.eco, X.Aprendizado(), 2000, rng)
            _, h = DC.simular(self.eco, e, rng, 8)
            historias.append(h)
        np.testing.assert_array_equal(historias[0].to_numpy(), historias[1].to_numpy())


class TestComportamento(unittest.TestCase):
    def test_parametros_validos(self):
        comp = DC.Comportamento()
        self.assertLess(comp.margem_minima, 0)
        self.assertGreater(comp.margem_maxima, 0)
        self.assertLess(comp.estoque_baixo, comp.estoque_alto)
        self.assertEqual(replace(comp, firmas=10).firmas, 10)


if __name__ == "__main__":
    unittest.main()
