"""Testes dos dados e do protocolo fora da amostra. Rode da pasta Econometria/:

    python -m unittest discover -s Python/macroeconomia/Forecast/Brasil/2013T4-2026T2 -v
"""
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))   # macroeconomia/
import caminhos  # noqa: E402,F401

import dsge  # noqa: E402
import protocolo  # noqa: E402
from calibracao import calcular_alvos  # noqa: E402
from comparacao import efeito_lei, sem_pandemia, somar_trimestres  # noqa: E402


class TestDados(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.crescimento, cls.anuais = protocolo.carregar_tudo()

    def test_trimestres_contiguos_e_sem_lacunas(self):
        indice = list(self.crescimento.index)
        self.assertEqual(indice[0], 199602)
        self.assertEqual(indice, [somar_trimestres(indice[0], k) for k in range(len(indice))])
        self.assertFalse(self.crescimento[list(protocolo.SERIES)].isna().any().any())
        # O desemprego começa com a PNAD Contínua e não tem lacunas depois.
        for coluna, inicio in ((protocolo.DESEMPREGO, 201202), (protocolo.TAXA_DESEMPREGO, 201201)):
            serie = self.crescimento[coluna]
            self.assertEqual(serie.first_valid_index(), inicio)
            self.assertFalse(serie.loc[inicio:].isna().any())

    def test_desemprego_dessazonalizado(self):
        taxa = self.crescimento[protocolo.TAXA_DESEMPREGO].dropna()
        variacao = self.crescimento[protocolo.DESEMPREGO].dropna()
        np.testing.assert_allclose(variacao.to_numpy(), np.diff(taxa.to_numpy()))
        # Os fatores somam zero no ano e a média da taxa não muda.
        bruta = pd.read_csv(protocolo.DADOS_PNAD, index_col="trimestre").taxa_desocupacao
        fator = (bruta - taxa).groupby(bruta.index % 100).mean()
        self.assertAlmostEqual(fator.sum(), 0.0, places=10)
        self.assertGreater(fator.loc[1], 0.3)    # o primeiro trimestre tem desemprego sazonalmente alto
        self.assertLess(fator.loc[4], -0.3)

    def test_dessazonalizar_tira_sazonalidade_pura(self):
        indice = [somar_trimestres(201201, k) for k in range(40)]
        tendencia = np.linspace(7.0, 12.0, 40)
        sazonal = np.tile([0.6, 0.1, -0.2, -0.5], 10)
        limpa = protocolo.dessazonalizar(pd.Series(tendencia + sazonal, index=indice))
        np.testing.assert_allclose(limpa.to_numpy(), tendencia, atol=1e-10)

    def test_crescimento_e_diferenca_do_log(self):
        volume = pd.read_csv(protocolo.DADOS_TRIMESTRAIS, index_col="trimestre")
        esperado = 100 * np.log(volume.volume_pib.loc[201001] / volume.volume_pib.loc[200904])
        self.assertAlmostEqual(self.crescimento.pib.loc[201001], esperado)

    def test_tendencia_trimestral_reproduz_o_crescimento_medio(self):
        media = self.crescimento.pib.loc[:201603].mean()
        e = protocolo.estrutura_na_origem(self.anuais, 201603, crescimento_pib=media)
        self.assertAlmostEqual(100 * (e.g + e.n) * e.periodo, media)
        ee = dsge.estado_estacionario(e)
        self.assertAlmostEqual(ee.k / ee.y, calcular_alvos(self.anuais, 2000, 2014).capital_produto,
                               places=10)

    def test_estrutura_usa_dados_anuais_ate_dois_anos_antes(self):
        e = protocolo.estrutura_na_origem(self.anuais, 201603)
        alvos = calcular_alvos(self.anuais, 2000, 2014)
        self.assertAlmostEqual(e.alpha, alvos.alpha)
        self.assertAlmostEqual(e.n, alvos.n)
        ee = dsge.estado_estacionario(e)
        self.assertAlmostEqual(ee.k / ee.y, alvos.capital_produto, places=10)
        # Mudar os anos seguintes não muda nada.
        alterado = self.anuais.copy()
        alterado.loc[2015:] *= 1.7
        self.assertEqual(protocolo.estrutura_na_origem(alterado, 201603), e)


class TestSemOlharOFuturo(unittest.TestCase):
    """A previsão numa origem não pode depender de nenhum dado posterior a ela."""

    def test_previsoes_iguais_com_futuro_alterado(self):
        crescimento, anuais = protocolo.carregar_tudo()
        origem = 201304
        alterado = crescimento.copy()
        alterado.loc[alterado.index > origem] += 5.0
        anuais_alterados = anuais.copy()
        anuais_alterados.loc[2012:] *= 0.5
        colunas = ["variavel", "h", "previsto", "dp"]
        for construir in (lambda a: protocolo.modelos_padrao(a)[:3],
                          lambda a: [protocolo.ModeloDSGE(a)],
                          lambda a: [protocolo.ModeloDSGE(a, "trimestral")],
                          lambda a: [protocolo.ModeloDSGEBusca(a, "trimestral")]):
            for modelo, modelo_alt in zip(construir(anuais), construir(anuais_alterados)):
                original = protocolo.prever_na_origem(modelo, crescimento, origem)
                mudado = protocolo.prever_na_origem(modelo_alt, alterado, origem)
                pd.testing.assert_frame_equal(original[colunas], mudado[colunas])
                # O realizado, esse sim, vem do futuro.
                self.assertFalse(np.allclose(original.realizado, mudado.realizado))

    def test_pnad_bruta_alterada_depois_da_origem(self):
        # Mudar a PNAD sem ajuste depois da origem muda a taxa dessazonalizada
        # com a amostra inteira também antes dela, mas não o que os modelos veem.
        origem = 201604
        crescimento = protocolo.carregar_crescimento()
        bruta = protocolo.carregar_taxa_bruta()
        alterada = bruta.copy()
        alterada.loc[alterada.index > origem] += np.tile([3.0, -2.0, 1.0, 0.5], 40)[:(alterada.index > origem).sum()]
        dados, dados_alt = (protocolo.observaveis(crescimento, b) for b in (bruta, alterada))
        cheia = dados.loc[:origem, protocolo.TAXA_DESEMPREGO]
        self.assertFalse(np.allclose(cheia, dados_alt.loc[:origem, protocolo.TAXA_DESEMPREGO]))
        visto = protocolo.ate_a_origem(dados, origem)
        pd.testing.assert_frame_equal(visto, protocolo.ate_a_origem(dados_alt, origem))
        np.testing.assert_allclose(visto[protocolo.TAXA_DESEMPREGO].dropna(),
                                   protocolo.dessazonalizar(bruta.loc[:origem]))
        _, anuais = protocolo.carregar_tudo()
        colunas = ["variavel", "h", "previsto", "dp"]
        # Uma instância nova para cada previsão: o modelo com busca guarda a
        # estimativa anterior como ponto de partida.
        for construir in (lambda: protocolo.ModeloReferencia("AR(1)", protocolo.referencias.ar1,
                                                             protocolo.VARIAVEIS),
                          lambda: protocolo.ModeloDSGEBusca(anuais, "trimestral")):
            original = protocolo.prever_na_origem(construir(), dados, origem)
            mudado = protocolo.prever_na_origem(construir(), dados_alt, origem)
            pd.testing.assert_frame_equal(original[colunas], mudado[colunas])

    def test_realizado_e_o_crescimento_acumulado(self):
        crescimento, anuais = protocolo.carregar_tudo()
        modelo = protocolo.modelos_padrao(anuais)[0]
        p = protocolo.prever_na_origem(modelo, crescimento, 201904)
        pib = p[p.variavel == "pib"].set_index("h").realizado
        self.assertAlmostEqual(pib.loc[4], crescimento.pib.loc[202001:202004].sum())
        # A média e o AR(1) também preveem o desemprego: o realizado é a
        # variação da taxa entre a origem e o alvo.
        u = p[p.variavel == "desemprego"].set_index("h").realizado
        taxa = crescimento[protocolo.TAXA_DESEMPREGO]
        self.assertAlmostEqual(u.loc[4], taxa.loc[202004] - taxa.loc[201904])
        self.assertNotIn("desemprego", set(protocolo.prever_na_origem(
            protocolo.modelos_padrao(anuais)[2], crescimento, 201904).variavel))   # o VAR(1) não


class TestAuxiliares(unittest.TestCase):
    def test_somar_trimestres(self):
        self.assertEqual(somar_trimestres(202604, 1), 202701)
        self.assertEqual(somar_trimestres(202601, -1), 202504)
        self.assertEqual(somar_trimestres(201902, 8), 202102)

    def test_sem_pandemia_tira_janelas_que_tocam_2020(self):
        p = pd.DataFrame({"origem": [201904, 201904, 202001, 202004, 201802],
                          "h": [1, 8, 1, 1, 6]})
        restante = sem_pandemia(p)
        # 201904 h=1 cobre 2020T1 (fica); h=8 cobre 2020T2-T4 (sai); 202001 h=1 é
        # 2020T2 (sai); 202004 h=1 é 2021T1 (fica); 201802 h=6 vai até 2019T4 (fica).
        self.assertEqual(list(restante.index), [0, 3, 4])

    def test_efeito_da_lei_pequeno_e_negativo_no_pib(self):
        efeito = efeito_lei(8, 202602)
        self.assertTrue((efeito.pib < 0).all())
        self.assertTrue((efeito.abs() < 0.2).all().all())
        np.testing.assert_allclose(efeito.governo, 0.0)


if __name__ == "__main__":
    unittest.main()
