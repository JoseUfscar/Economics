"""
Baixa as Contas Nacionais Trimestrais (IBGE) usadas na avaliação de
previsões fora da amostra (Python/macroeconomia/Forecast/Brasil/2013T4-2026T2/).

    dados/brasil/contas_trimestrais.csv  índices de volume com ajuste sazonal
                                         e valores a preços correntes do PIB,
                                         consumo das famílias, consumo do
                                         governo e FBCF

Fonte: API do SIDRA (tabelas 1621 e 1846). Rode a partir da pasta
Econometria/ (precisa de internet):

    python3 dados/brasil/baixar_trimestrais.py
"""
import json
import time
import urllib.request
from pathlib import Path

import pandas as pd

PASTA = Path("dados/brasil")

COMPONENTES = {  # categoria da classificação 11255: sufixo da coluna
    "90707": "pib",
    "93404": "consumo_familias",
    "93405": "consumo_governo",
    "93406": "fbcf",
}


def _sidra(caminho: str, tentativas: int = 3) -> pd.DataFrame:
    url = "https://apisidra.ibge.gov.br/values/" + caminho
    for tentativa in range(tentativas):
        try:
            with urllib.request.urlopen(url, timeout=90) as resposta:
                linhas = json.loads(resposta.read())
            break
        except OSError:
            if tentativa == tentativas - 1:
                raise
            time.sleep(2 ** tentativa)
    tabela = pd.DataFrame(linhas[1:])
    tabela["V"] = pd.to_numeric(tabela["V"], errors="coerce")
    return tabela


def _componentes(tabela: int, variavel: int, prefixo: str) -> pd.DataFrame:
    dados = _sidra(f"t/{tabela}/n1/all/v/{variavel}/p/all/c11255/" + ",".join(COMPONENTES))
    largura = dados.pivot(index="D3C", columns="D4C", values="V")
    largura = largura.rename(columns={c: prefixo + s for c, s in COMPONENTES.items()})
    return largura[[prefixo + s for s in COMPONENTES.values()]]


def main() -> None:
    volume = _componentes(1621, 584, "volume_")    # índice encadeado, média 1995 = 100
    nominal = _componentes(1846, 585, "nominal_")  # R$ milhões correntes
    trimestral = volume.join(nominal)
    trimestral.index = trimestral.index.astype(int).rename("trimestre")
    trimestral.sort_index().to_csv(PASTA / "contas_trimestrais.csv")
    print(f"contas_trimestrais.csv: {len(trimestral)} trimestres "
          f"({trimestral.index.min()} a {trimestral.index.max()})")


if __name__ == "__main__":
    main()
