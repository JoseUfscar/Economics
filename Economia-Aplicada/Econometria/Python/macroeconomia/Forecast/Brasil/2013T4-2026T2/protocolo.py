"""
Protocolo comum da avaliação fora da amostra.

Em cada origem T (um trimestre), cada modelo usa apenas o que se conheceria
em T:
  - dados trimestrais até T (Contas Nacionais Trimestrais, IBGE);
  - dados anuais até o ano de T menos 2, para a calibração estrutural do
    modelo de equilíbrio geral (PWT, Ipea e IBGE saem com defasagem).
Os parâmetros são reestimados a cada origem (janela crescente desde 1996) e
cada modelo prevê o crescimento acumulado de PIB, consumo das famílias, FBCF
e consumo do governo de T+1 a T+h, h = 1..8, com média e desvio-padrão. Os
modelos que têm desemprego (o equilíbrio geral com busca e o ABM sem
leiloeiro) e as referências univariadas preveem também a variação da taxa
de desemprego de T a T+h, em p.p., com a PNAD Contínua (desde 2012).
"""
from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))   # macroeconomia/
import caminhos  # noqa: E402

from calibracao import TAU_K_BRUTO, aliquota_liquida, calcular_alvos, carregar_dados  # noqa: E402
from calibracao_renda import calibrar_desemprego, carregar_pnad  # noqa: E402

import dsge  # noqa: E402
import dsge_busca  # noqa: E402
import referencias  # noqa: E402
from espaco_estados import filtrar, prever_acumulado  # noqa: E402

DADOS_TRIMESTRAIS = caminhos.DADOS / "contas_trimestrais.csv"
DADOS_PNAD = DADOS_TRIMESTRAIS.with_name("pnad_trimestral.csv")
SERIES = {"pib": "volume_pib", "consumo": "volume_consumo_familias",
          "investimento": "volume_fbcf", "governo": "volume_consumo_governo"}
DESEMPREGO = "desemprego"              # variação da taxa, em p.p.
TAXA_DESEMPREGO = "taxa_desemprego"    # nível, em %
VARIAVEIS = (*SERIES, DESEMPREGO)
HORIZONTE = 8
DEFASAGEM_ANUAL = 2
INICIO_CALIBRACAO = 2000
THETA = 2.0


def carregar_crescimento(caminho: Path = DADOS_TRIMESTRAIS) -> pd.DataFrame:
    """Crescimento trimestral em %, 100 * Delta log do índice de volume dessazonalizado."""
    volume = pd.read_csv(caminho, index_col="trimestre")[list(SERIES.values())]
    crescimento = 100 * np.log(volume).diff().dropna()
    crescimento.columns = list(SERIES)
    return crescimento


def dessazonalizar(serie: pd.Series) -> pd.Series:
    """
    Decomposição clássica aditiva de uma série trimestral: a tendência é a
    média móvel centrada 2x4, e o fator de cada trimestre do ano é a média
    do desvio em relação a ela, com soma zero. Os fatores usam a amostra
    inteira, como os das Contas Nacionais dessazonalizadas pelo IBGE que os
    outros dados usam (a safra atual).
    """
    pesos = np.array([1, 2, 2, 2, 1]) / 8
    tendencia = pd.Series(np.convolve(serie.to_numpy(), pesos, mode="same"), index=serie.index)
    tendencia.iloc[:2] = tendencia.iloc[-2:] = np.nan
    trimestre = serie.index % 100
    fator = (serie - tendencia).groupby(trimestre).mean()
    fator -= fator.mean()
    return serie - fator.loc[trimestre].to_numpy()


def carregar_taxa_desemprego(caminho: Path = DADOS_PNAD) -> pd.Series:
    """Taxa de desemprego dessazonalizada da PNAD Contínua, em %."""
    taxa = pd.read_csv(caminho, index_col="trimestre").taxa_desocupacao
    return dessazonalizar(taxa).rename(TAXA_DESEMPREGO)


def carregar_observaveis() -> pd.DataFrame:
    """
    As quatro séries das Contas Nacionais, a variação do desemprego (vazia
    antes de 2012T2) e, para os modelos que reproduzem o nível, a própria
    taxa (vazia antes de 2012T1).
    """
    taxa = carregar_taxa_desemprego()
    return carregar_crescimento().join(taxa.diff().rename(DESEMPREGO)).join(taxa)


def ano_de(trimestre: int) -> int:
    return trimestre // 100


def estrutura_na_origem(anuais: pd.DataFrame, origem: int, theta: float = THETA,
                        periodo: float = 0.25, crescimento_pib: float | None = None) -> dsge.Estrutura:
    """
    Calibração anual com dados até ano(origem) - DEFASAGEM_ANUAL. Com
    `crescimento_pib` (média trimestral em %, até a origem), a tendência g + n
    passa a reproduzir esse crescimento, em vez da tendência anual desde 2000.
    """
    ultimo = int(anuais.pib_real_pwt.dropna().index.max())
    fim = min(ano_de(origem) - DEFASAGEM_ANUAL, ultimo)
    alvos = calcular_alvos(anuais, INICIO_CALIBRACAO, fim)
    tau_k = aliquota_liquida(TAU_K_BRUTO, alvos.alpha, alvos.delta, alvos.capital_produto)
    g = alvos.g if crescimento_pib is None else crescimento_pib / 100 / periodo - alvos.n
    e = dsge.Estrutura(alpha=alvos.alpha, delta=alvos.delta, rho=0.0, theta=theta, n=alvos.n,
                       g=g, tau_k=tau_k, gasto_pib=alvos.gasto_pib, periodo=periodo)
    return replace(e, rho=dsge.rho_para_capital_produto(e, alvos.capital_produto))


class ModeloDSGE:
    """
    tendencia = "anual": crescimento balanceado g + n da calibração anual,
    comum às quatro séries (o modelo como está em Politicas/Lei-15270/equilibrio_geral/);
    tendencia = "trimestral": g + n reproduz o crescimento médio do PIB até a
    origem e cada série tem a própria média, o que isola a dinâmica do modelo
    do erro de tendência.
    """

    def __init__(self, anuais: pd.DataFrame, tendencia: str = "anual"):
        if tendencia not in ("anual", "trimestral"):
            raise ValueError("tendencia deve ser 'anual' ou 'trimestral'")
        self.anuais, self.tendencia = anuais, tendencia
        self.nome = ("Equilíbrio geral" if tendencia == "anual"
                     else "Equilíbrio geral, tendência trimestral")
        self.anterior = None   # estimativa da origem anterior, usada como partida
        self.estimativas = {}

    def distribuicao(self, y: np.ndarray, origem: int):
        medias = None
        if self.tendencia == "trimestral":
            medias = y.mean(axis=0)
            e = estrutura_na_origem(self.anuais, origem, crescimento_pib=medias[0])
        else:
            e = estrutura_na_origem(self.anuais, origem)
        partidas = dsge.PARTIDAS
        if self.anterior is not None:
            partidas = ((self.anterior.choques, self.anterior.erros_medida),) + partidas
        est = dsge.estimar(e, y, partidas, medias)
        self.anterior = self.estimativas[origem] = est
        modelo = est.modelo
        filtrado = filtrar(modelo, y)
        return modelo, filtrado.media, filtrado.cov


class ModeloDSGEBusca(ModeloDSGE):
    """
    O equilíbrio geral com margem e busca (dsge_busca.py), com as mesmas duas
    tendências de ModeloDSGE. O mercado de trabalho vem da PNAD até a origem
    (desemprego médio e a cadeia de separação), e rho reproduz o K/Y com a
    margem. Prevê também a variação do desemprego.
    """

    variaveis = VARIAVEIS

    def __init__(self, anuais: pd.DataFrame, tendencia: str = "anual", pnad=None):
        super().__init__(anuais, tendencia)
        self.nome = ("Equilíbrio geral com busca" if tendencia == "anual"
                     else "Equilíbrio geral com busca, tendência trimestral")
        self.pnad = carregar_pnad() if pnad is None else pnad

    def estrutura(self, origem: int, crescimento_pib: float | None = None):
        e = estrutura_na_origem(self.anuais, origem, crescimento_pib=crescimento_pib)
        trabalho = dsge_busca.Trabalho.da_pnad(calibrar_desemprego(self.pnad[0].loc[:origem]))
        ultimo = int(self.anuais.pib_real_pwt.dropna().index.max())
        alvos = calcular_alvos(self.anuais, INICIO_CALIBRACAO,
                               min(ano_de(origem) - DEFASAGEM_ANUAL, ultimo))
        rho = dsge_busca.rho_para_capital_produto(e, trabalho, alvos.capital_produto)
        return replace(e, rho=rho), trabalho

    def distribuicao(self, y: np.ndarray, origem: int):
        medias = None
        if self.tendencia == "trimestral":
            # Cada série das Contas Nacionais com a própria média; o desemprego
            # não tem tendência.
            medias = np.r_[np.nanmean(y[:, :-1], axis=0), 0.0]
            e, trabalho = self.estrutura(origem, crescimento_pib=medias[0])
        else:
            e, trabalho = self.estrutura(origem)
        partidas = dsge_busca.PARTIDAS
        if self.anterior is not None:
            partidas = ((self.anterior.choques, self.anterior.erros_medida),) + partidas
        est = dsge_busca.estimar(e, trabalho, y, partidas, medias)
        self.anterior = self.estimativas[origem] = est
        modelo = est.modelo
        filtrado = filtrar(modelo, y)
        return modelo, filtrado.media, filtrado.cov


class ModeloReferencia:
    def __init__(self, nome: str, estimador, variaveis=tuple(SERIES)):
        self.nome, self.estimador, self.variaveis = nome, estimador, tuple(variaveis)

    def distribuicao(self, y: np.ndarray, origem: int):
        return (self.estimador(y), *referencias.estado_final(y))


def modelos_padrao(anuais: pd.DataFrame) -> list:
    return [ModeloReferencia("Média", referencias.media, VARIAVEIS),
            ModeloReferencia("AR(1)", referencias.ar1, VARIAVEIS),
            ModeloReferencia("VAR(1)", referencias.var1),
            ModeloDSGE(anuais),
            ModeloDSGE(anuais, "trimestral")]


def prever_na_origem(modelo, dados: pd.DataFrame, origem: int,
                     horizonte: int = HORIZONTE) -> pd.DataFrame:
    """
    Previsões de um modelo em uma origem, com o realizado quando já existe.
    Cada modelo prevê as variáveis de `modelo.variaveis` (as quatro das
    Contas Nacionais, se não disser nada); o desemprego, onde falta, entra
    como dado faltante.
    """
    variaveis = list(getattr(modelo, "variaveis", SERIES))
    amostra = dados.loc[:origem]
    if amostra.index[-1] != origem:
        raise ValueError(f"origem {origem} fora dos dados")
    if hasattr(modelo, "prever"):   # modelos simulados, como o ABM
        medias, variancias = modelo.prever(amostra, origem, horizonte)
    else:
        linear, media, cov = modelo.distribuicao(amostra[variaveis].to_numpy(), origem)
        medias, variancias = prever_acumulado(linear, media, cov, horizonte)
    futuro = dados[variaveis].iloc[len(amostra):len(amostra) + horizonte]
    realizado = np.full((horizonte, len(variaveis)), np.nan)
    realizado[:len(futuro)] = futuro.cumsum().to_numpy()
    linhas = []
    for h in range(horizonte):
        for j, variavel in enumerate(variaveis):
            linhas.append({"origem": origem, "modelo": modelo.nome, "variavel": variavel,
                           "h": h + 1, "previsto": medias[h, j], "dp": np.sqrt(variancias[h, j]),
                           "realizado": realizado[h, j]})
    return pd.DataFrame(linhas)


def origens(crescimento: pd.DataFrame, primeira: int, ultima: int | None = None) -> list[int]:
    indice = crescimento.index
    ultima = indice[-1] if ultima is None else ultima
    return [int(t) for t in indice if primeira <= t <= ultima]


def avaliar(crescimento: pd.DataFrame, anuais: pd.DataFrame, lista_origens, modelos=None,
            progresso: bool = False) -> pd.DataFrame:
    modelos = modelos_padrao(anuais) if modelos is None else modelos
    partes = []
    for origem in lista_origens:
        for modelo in modelos:
            partes.append(prever_na_origem(modelo, crescimento, origem))
        if progresso:
            print(f"  origem {origem} concluída", flush=True)
    return pd.concat(partes, ignore_index=True)


def carregar_tudo():
    """Observáveis trimestrais (com o desemprego) e dados anuais."""
    return carregar_observaveis(), carregar_dados()
