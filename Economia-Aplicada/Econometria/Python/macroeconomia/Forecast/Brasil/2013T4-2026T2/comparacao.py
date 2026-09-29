"""
Avaliação fora da amostra: modelos de equilíbrio geral e ABMs contra média,
AR(1) e VAR(1), com o protocolo de protocolo.py, e previsões registradas a
partir do último trimestre com dados.

Rode a partir da pasta Econometria/:

    python Python/macroeconomia/Forecast/Brasil/2013T4-2026T2/comparacao.py --processos 4
    python Python/macroeconomia/Forecast/Brasil/2013T4-2026T2/comparacao.py --modelos eg_busca abm2_apr   # só alguns
    python Python/macroeconomia/Forecast/Brasil/2013T4-2026T2/comparacao.py --sem-reestimar     # só tabelas e figuras

Com --modelos, as previsões dos outros modelos vêm de resultados/previsoes.csv.
Chaves:
  media, ar1, var1                  referências estatísticas
  eg, eg_trim                       equilíbrio geral (dsge/), tendência anual ou trimestral
  eg_busca, eg_busca_trim           equilíbrio geral com margem e busca (dsge_busca/)
  abm_eq, abm_apr, abm_heu,         ABM 1, com leiloeiro (abm1_com_leiloeiro/), uma
  abm_inf, abm_aten                 chave por regra de expectativas
  abm2_eq, abm2_apr, abm2_heu,      ABM 2, sem leiloeiro (abm2_sem_leiloeiro/)
  abm2_inf, abm2_aten
Com --processos, as origens se dividem entre processos. Os tempos por origem,
num núcleo: segundos para as referências, meio minuto a um minuto e meio
para cada equilíbrio geral e meio minuto para cada variante de ABM.

Os resultados vão para resultados/ e as figuras para figuras/, nesta pasta.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import protocolo  # põe as pastas dos modelos no caminho de importação
from avaliacao import resumo
from calibracao import aumento_tau_k_lei, calcular_alvos, calibrar
from experimentos import (ANUNCIO, AZUL, LARANJA, TINTA, TINTA_2, VIGENCIA, _estilo, _virgula,
                          choque_tau_k)
from modelo import estado_estacionario

PASTA = Path(__file__).resolve().parent
PRIMEIRA_ORIGEM = 201304
# O desemprego só é avaliado a partir das origens com três anos de PNAD
# (desde 2012T1). Antes disso, a dessazonalização feita só com o passado se
# apoia em oito a onze trimestres, e o AR(1) da variação, estimado com menos
# de dez pontos, chega a ser explosivo (em 2013T4, coeficiente de -2,4).
PRIMEIRA_ORIGEM_DESEMPREGO = 201404
PANDEMIA = (202002, 202004)   # trimestres da queda e da recuperação mais bruscas
NOMES = {"pib": "PIB", "consumo": "Consumo das famílias", "investimento": "FBCF",
         "governo": "Consumo do governo", "desemprego": "Desemprego (variação, p.p.)"}
CORES_EG = {"Média": TINTA_2, "VAR(1)": LARANJA, "Equilíbrio geral": AZUL,
            "Equilíbrio geral, tendência trimestral": "#104281"}
CORES_BUSCA = {"Média": TINTA_2, "Equilíbrio geral, tendência trimestral": AZUL,
               "Equilíbrio geral com busca": "#5dade2",
               "Equilíbrio geral com busca, tendência trimestral": "#104281"}

REGISTRO = {
    "media": lambda anuais: protocolo.ModeloReferencia("Média", protocolo.referencias.media,
                                                       protocolo.VARIAVEIS),
    "ar1": lambda anuais: protocolo.ModeloReferencia("AR(1)", protocolo.referencias.ar1,
                                                     protocolo.VARIAVEIS),
    "var1": lambda anuais: protocolo.ModeloReferencia("VAR(1)", protocolo.referencias.var1),
    "eg": lambda anuais: protocolo.ModeloDSGE(anuais),
    "eg_trim": lambda anuais: protocolo.ModeloDSGE(anuais, "trimestral"),
    "eg_busca": lambda anuais: protocolo.ModeloDSGEBusca(anuais),
    "eg_busca_trim": lambda anuais: protocolo.ModeloDSGEBusca(anuais, "trimestral"),
}
# A calibração de cada ABM numa origem serve às cinco regras de expectativas.
_CALIBRACOES_ABM: dict = {}
_ECONOMIAS_ABM2: dict = {}


def _abm(chave):
    def construir(anuais):
        import previsao_abm
        return previsao_abm.ModeloABM(anuais, chave, cache=_CALIBRACOES_ABM)
    return construir


def _abm2(chave):
    def construir(anuais):
        import previsao_descentralizada
        return previsao_descentralizada.ModeloDescentralizado(anuais, chave, cache=_ECONOMIAS_ABM2)
    return construir


REGRAS_ABM = {"eq": "crenças fixas", "apr": "aprendizado", "heu": "heurísticas",
              "inf": "informação rígida", "aten": "atenção limitada"}
for _chave in REGRAS_ABM:
    REGISTRO[f"abm_{_chave}"] = _abm(f"abm_{_chave}")
for _chave in REGRAS_ABM:
    REGISTRO[f"abm2_{_chave}"] = _abm2(f"abm2_{_chave}")
_CORES_REGRAS = (TINTA, LARANJA, "#1baf7a", "#8e44ad", "#c0392b")
CORES_ABM = {"Equilíbrio geral, tendência trimestral": AZUL,
             **{f"ABM 1: {nome}": cor for nome, cor in zip(REGRAS_ABM.values(), _CORES_REGRAS)}}
CORES_ABM2 = {"Equilíbrio geral com busca, tendência trimestral": AZUL,
              **{f"ABM 2: {nome}": cor for nome, cor in zip(REGRAS_ABM.values(), _CORES_REGRAS)}}
# Nomes antigos do ABM com leiloeiro em resultados/previsoes.csv.
NOMES_ANTIGOS = {f"ABM: {nome}": f"ABM 1: {nome}" for nome in REGRAS_ABM.values()}
# Ficam fora das previsões registradas: no ABM 2, essas duas regras levam o
# lucro realizado do fundo quase direto às crenças e ao custo do capital, e
# as previsões de consumo e FBCF oscilam demais para serem levadas a sério
# (ver o README do ABM 2). Continuam na avaliação fora da amostra.
SEM_REGISTRO = ("ABM 2: heurísticas", "ABM 2: atenção limitada")


def somar_trimestres(trimestre: int, k: int) -> int:
    ano, q = divmod(trimestre, 100)
    total = ano * 4 + (q - 1) + k
    return (total // 4) * 100 + total % 4 + 1


def sem_pandemia(previsoes: pd.DataFrame) -> pd.DataFrame:
    """Tira as previsões cuja janela (origem, origem + h] toca 2020T2-2020T4."""
    fim = [somar_trimestres(o, h) for o, h in zip(previsoes.origem, previsoes.h)]
    inicio = [somar_trimestres(o, 1) for o in previsoes.origem]
    toca = (np.array(inicio) <= PANDEMIA[1]) & (np.array(fim) >= PANDEMIA[0])
    return previsoes[~toca]


def janela_de_avaliacao(previsoes: pd.DataFrame) -> pd.DataFrame:
    """Tira as previsões do desemprego feitas antes de PRIMEIRA_ORIGEM_DESEMPREGO."""
    cedo = (previsoes.variavel == protocolo.DESEMPREGO) & (previsoes.origem < PRIMEIRA_ORIGEM_DESEMPREGO)
    return previsoes[~cedo]


def tabela_horizontes(avaliacao: pd.DataFrame, coluna: str, horizontes=(1, 4, 8)) -> pd.DataFrame:
    t = avaliacao[avaliacao.h.isin(horizontes)].pivot_table(
        index=["variavel", "modelo"], columns="h", values=coluna, sort=False)
    t.columns = [f"h={h}" for h in t.columns]
    return t


def efeito_lei(horizonte: int, origem: int) -> pd.DataFrame:
    """
    Efeito da Lei 15.270/2025 no crescimento acumulado depois da origem, pelo
    modelo contínuo de equilibrio_geral: diferença, em p.p., entre o caminho
    com o aumento de tau_k anunciado em 15/03/2025 e o caminho sem mudança.
    """
    dados = protocolo.carregar_dados()
    alvos = calcular_alvos(dados)
    eco, pol = calibrar(alvos)
    traj = choque_tau_k(eco, pol, aumento_tau_k_lei(alvos, dados), VIGENCIA - ANUNCIO)
    ee = estado_estacionario(eco, pol)

    def desvio(trimestre):   # desvio em log, no meio do trimestre, desde o anúncio
        ano, q = divmod(trimestre, 100)
        tab = traj.tabela(ano + (q - 0.5) / 4 - ANUNCIO)
        return 100 * np.log(np.array([tab.y[0] / ee.y, tab.c[0] / ee.c,
                                      tab.investimento[0] / (ee.y - ee.c - pol.gasto), 1.0]))

    base = desvio(origem)
    linhas = [desvio(somar_trimestres(origem, h)) - base for h in range(1, horizonte + 1)]
    return pd.DataFrame(linhas, columns=list(protocolo.SERIES), index=range(1, horizonte + 1))


def figura_rmse(avaliacao: pd.DataFrame, destino: Path, titulo: str, cores=None) -> None:
    cores = CORES_EG if cores is None else cores
    _estilo()
    com_modelo = avaliacao[avaliacao.modelo.isin(list(cores)) & (avaliacao.modelo != "Média")]
    variaveis = [v for v in NOMES if (com_modelo.variavel == v).any()]
    colunas = 2 if len(variaveis) <= 4 else 3
    fig, eixos = plt.subplots(2, colunas, figsize=(4.5 * colunas, 6.2), sharex=True, squeeze=False)
    for ax in eixos.ravel()[len(variaveis):]:
        ax.set_visible(False)
    for ax, variavel in zip(eixos.ravel(), variaveis):
        dados = avaliacao[avaliacao.variavel == variavel]
        ax.axhline(1, color=TINTA, linewidth=1)
        for modelo, cor in cores.items():
            linha = dados[dados.modelo == modelo].sort_values("h")
            ax.plot(linha.h, linha.rmse_relativo, color=cor, marker="o", markersize=3.5, label=modelo)
        ax.set_title(NOMES[variavel])
        ax.set_xticks(range(1, protocolo.HORIZONTE + 1))
        ax.tick_params(labelbottom=True)
        _virgula(ax)
    for ax in eixos[1]:
        ax.set_xlabel("horizonte (trimestres)")
    for ax in eixos[:, 0]:
        ax.set_ylabel("RMSE relativo ao AR(1)")
    alcas, rotulos = eixos[0, 0].get_legend_handles_labels()
    fig.legend(alcas, rotulos, loc="lower center", ncol=3, fontsize=8)
    fig.suptitle(titulo, x=0.01, ha="left", fontsize=10.5, fontweight="bold", color=TINTA)
    fig.tight_layout(rect=(0, 0.08 if len(cores) > 3 else 0.05, 1, 1))
    fig.savefig(destino)
    plt.close(fig)


def figura_pib(previsoes: pd.DataFrame, destino: Path, h: int = 4) -> None:
    """Crescimento do PIB em h trimestres: realizado e previsto, por data-alvo."""
    _estilo()
    p = previsoes[(previsoes.variavel == "pib") & (previsoes.h == h)].dropna(subset=["realizado"])
    alvo = [somar_trimestres(o, h) for o in p.origem]
    p = p.assign(x=[a // 100 + (a % 100 - 0.5) / 4 for a in alvo])
    fig, ax = plt.subplots(figsize=(8, 4.4))
    real = p[p.modelo == "AR(1)"]
    ax.plot(real.x, real.realizado, color=TINTA, label="realizado")
    for modelo, cor in (("Equilíbrio geral", AZUL), ("AR(1)", LARANJA)):
        m = p[p.modelo == modelo]
        ax.plot(m.x, m.previsto, color=cor, label=f"previsto: {modelo}")
        if modelo == "Equilíbrio geral":
            ax.fill_between(m.x, m.previsto - 1.645 * m.dp, m.previsto + 1.645 * m.dp,
                            color=cor, alpha=0.15, linewidth=0, label="intervalo de 90%")
    ax.axhline(0, color=TINTA_2, linewidth=0.8)
    ax.set(xlabel="data-alvo", ylabel="% em quatro trimestres")
    ax.set_title(f"PIB: crescimento acumulado em {h} trimestres, previsto {h} trimestres antes")
    ax.legend(loc="lower left")
    _virgula(ax)
    fig.tight_layout()
    fig.savefig(destino)
    plt.close(fig)


def rotulo(trimestre: int) -> str:
    return f"{trimestre // 100}T{trimestre % 100}"


def relatorio(previsoes: pd.DataFrame) -> None:
    """Tabelas, previsões registradas e figuras a partir de resultados/previsoes.csv."""
    pasta_res, pasta_fig = PASTA / "resultados", PASTA / "figuras"
    pasta_fig.mkdir(exist_ok=True)
    lista = sorted(previsoes.origem.unique())
    fora = janela_de_avaliacao(previsoes[previsoes.origem < lista[-1]])   # a última origem não tem realizado
    completa, filtrada = resumo(fora), resumo(sem_pandemia(fora))
    completa.to_csv(pasta_res / "avaliacao.csv", index=False, float_format="%.6g")
    filtrada.to_csv(pasta_res / "avaliacao_sem_pandemia.csv", index=False, float_format="%.6g")

    with pd.option_context("display.width", 140, "display.float_format", "{:.3f}".format):
        for nome, tabela in (("todas as origens", completa), ("sem a pandemia", filtrada)):
            print(f"\nRMSE relativo ao AR(1), {nome} (abaixo de 1 = melhor que o AR(1)):")
            print(tabela_horizontes(tabela, "rmse_relativo"))
            print(f"\nCRPS relativo ao AR(1), {nome}:")
            print(tabela_horizontes(tabela, "crps_relativo"))
            print(f"\np-valor contra o AR(1), {nome} (Diebold-Mariano; Clark-West para média e VAR(1)):")
            print(tabela_horizontes(tabela[tabela.modelo != "AR(1)"], "p_teste"))
            print(f"\no mesmo, com a correção de Holm entre os modelos, {nome}:")
            print(tabela_horizontes(tabela[tabela.modelo != "AR(1)"], "p_holm"))
            print(f"\nCobertura do intervalo de 90%, {nome}:")
            print(tabela_horizontes(tabela, "cobertura_90"))

    # Os modelos com as médias da amostra contra a própria média: o que a dinâmica acrescenta.
    estruturais = [m for m in previsoes.modelo.unique()
                   if m.startswith("ABM") or m.endswith("tendência trimestral")]
    if estruturais:
        for nome, dados, arquivo in (("todas as origens", fora, "contra_media.csv"),
                                     ("sem a pandemia", sem_pandemia(fora), "contra_media_sem_pandemia.csv")):
            contra = resumo(dados[dados.modelo.isin(estruturais + ["Média"])], referencia="Média")
            contra.to_csv(pasta_res / arquivo, index=False, float_format="%.6g")
            contra = contra[contra.modelo != "Média"]
            with pd.option_context("display.width", 140, "display.float_format", "{:.3f}".format):
                print(f"\nRMSE relativo à média histórica, {nome}:")
                print(tabela_horizontes(contra, "rmse_relativo"))
                print(f"p-valor de Diebold-Mariano contra a média histórica, {nome}:")
                print(tabela_horizontes(contra, "p_teste"))

    ultima = lista[-1]
    registrada = previsoes[(previsoes.origem == ultima) & ~previsoes.modelo.isin(SEM_REGISTRO)]
    registrada = registrada.drop(columns="realizado").copy()
    registrada["alvo"] = [somar_trimestres(ultima, h) for h in registrada.h]
    lei = efeito_lei(protocolo.HORIZONTE, ultima)
    registrada["efeito_lei"] = [lei.loc[h, v] if m.startswith("Equilíbrio geral") and v in lei else 0.0
                                for m, v, h in zip(registrada.modelo, registrada.variavel, registrada.h)]
    registrada["previsto_com_lei"] = registrada.previsto + registrada.efeito_lei
    registrada.to_csv(pasta_res / f"previsao_registrada_{ultima}.csv", index=False, float_format="%.6g")
    print(f"\nPrevisões registradas a partir de {rotulo(ultima)} (crescimento acumulado, %):")
    print(registrada[registrada.h.isin([2, 6])].pivot_table(
        index=["variavel", "modelo"], columns="alvo", values="previsto", sort=False).round(2))
    print("Efeito da Lei 15.270/2025 no acumulado (p.p., modelo contínuo):")
    print(lei.loc[[2, 6]].round(3))

    figura_rmse(completa, pasta_fig / "rmse_relativo.png",
                f"Erro de previsão relativo ao AR(1), origens {rotulo(lista[0])} a {rotulo(lista[-2])}")
    figura_rmse(filtrada, pasta_fig / "rmse_relativo_sem_pandemia.png",
                "Erro de previsão relativo ao AR(1), sem as janelas da pandemia")
    figura_pib(previsoes, pasta_fig / "previsoes_pib.png")
    grupos = (("rmse_abm", "ABM 1 e equilíbrio geral", CORES_ABM),
              ("rmse_abm2", "ABM 2 e equilíbrio geral com busca", CORES_ABM2),
              ("rmse_busca", "Equilíbrio geral com e sem busca", CORES_BUSCA))
    for arquivo, titulo, cores in grupos:
        if previsoes.modelo.isin([m for m in cores if m != "Média"][1:]).any():
            figura_rmse(completa, pasta_fig / f"{arquivo}.png",
                        f"{titulo}: erro relativo ao AR(1), todas as origens", cores)
            figura_rmse(filtrada, pasta_fig / f"{arquivo}_sem_pandemia.png",
                        f"{titulo}: erro relativo ao AR(1), sem a pandemia", cores)
    contra_realizado(fora).to_csv(pasta_res / "previsoes_contra_realizado.csv", index=False,
                                  float_format="%.4g")
    print(f"\nResultados em {pasta_res} e figuras em {pasta_fig}")


def contra_realizado(previsoes: pd.DataFrame) -> pd.DataFrame:
    """O realizado e a previsão pontual de cada modelo, lado a lado, por origem, variável e horizonte."""
    largo = previsoes.pivot_table(index=["origem", "variavel", "h"], columns="modelo",
                                  values="previsto", sort=False)
    realizado = previsoes.groupby(["origem", "variavel", "h"], sort=False).realizado.first()
    return largo.join(realizado).reset_index()[
        ["origem", "variavel", "h", "realizado", *largo.columns]].dropna(subset=["realizado"])


def _rodar(tarefa) -> tuple[pd.DataFrame, list]:
    """Os modelos de `chaves` em algumas origens: previsões e parâmetros estimados."""
    chaves, lista = tarefa
    dados, anuais = protocolo.carregar_tudo()
    modelos = [REGISTRO[c](anuais) for c in chaves]
    previsoes = protocolo.avaliar(dados, anuais, lista, modelos, progresso=True)
    parametros = [{"modelo": m.nome, "origem": o, **vars(est.choques),
                   **{f"erro_{v}": s for v, s in zip(getattr(m, "variaveis", protocolo.SERIES),
                                                     est.erros_medida)},
                   "log_verossimilhanca": est.log_verossimilhanca}
                  for m in modelos if isinstance(m, protocolo.ModeloDSGE)
                  for o, est in m.estimativas.items()]
    return previsoes, parametros


def ler_previsoes(arquivo: Path) -> pd.DataFrame:
    return pd.read_csv(arquivo).replace({"modelo": NOMES_ANTIGOS})


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description="Avaliação fora da amostra.")
    parser.add_argument("--primeira", type=int, default=PRIMEIRA_ORIGEM)
    parser.add_argument("--ultima", type=int, default=None)
    parser.add_argument("--modelos", nargs="+", choices=list(REGISTRO),
                        help="estima só estes modelos e junta com resultados/previsoes.csv")
    parser.add_argument("--processos", type=int, default=1,
                        help="divide as origens entre estes processos")
    parser.add_argument("--sem-reestimar", action="store_true",
                        help="refaz tabelas e figuras a partir de resultados/previsoes.csv")
    args = parser.parse_args(argv)
    pasta_res = PASTA / "resultados"
    if args.sem_reestimar:
        relatorio(ler_previsoes(pasta_res / "previsoes.csv"))
        return

    dados, _ = protocolo.carregar_tudo()
    lista = protocolo.origens(dados, args.primeira, args.ultima)
    chaves = args.modelos or list(REGISTRO)
    print(f"{len(lista)} origens, de {rotulo(lista[0])} a {rotulo(lista[-1])}; "
          f"dados até {rotulo(dados.index[-1])}; modelos: {', '.join(chaves)}")
    if args.processos > 1:
        # Origens alternadas: cada processo pega origens do começo e do fim da
        # amostra, que têm históricos de tamanhos diferentes.
        partes = [(chaves, lista[i::args.processos]) for i in range(args.processos)]
        with ProcessPoolExecutor(args.processos) as executor:
            resultados = list(executor.map(_rodar, partes))
    else:
        resultados = [_rodar((chaves, lista))]
    previsoes = pd.concat([r[0] for r in resultados]).sort_values("origem", kind="stable")
    parametros = [linha for r in resultados for linha in r[1]]

    pasta_res.mkdir(exist_ok=True)
    arquivo = pasta_res / "previsoes.csv"
    if args.modelos and arquivo.exists():
        anteriores = ler_previsoes(arquivo)
        anteriores = anteriores[~anteriores.modelo.isin(previsoes.modelo.unique())]
        previsoes = pd.concat([anteriores, previsoes], ignore_index=True)
    previsoes.to_csv(arquivo, index=False, float_format="%.6g")

    if parametros:
        novos = pd.DataFrame(parametros).sort_values(["modelo", "origem"], kind="stable")
        arquivo = pasta_res / "parametros_dsge.csv"
        if args.modelos and arquivo.exists():
            anteriores = pd.read_csv(arquivo)
            if "modelo" not in anteriores:
                anteriores.insert(0, "modelo", "Equilíbrio geral")
            novos = pd.concat([anteriores[~anteriores.modelo.isin(novos.modelo)], novos])
        novos.to_csv(arquivo, index=False, float_format="%.6g")
    relatorio(previsoes)


if __name__ == "__main__":
    main()
