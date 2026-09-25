"""
Baixa séries da PNAD Contínua (IBGE) usadas na calibração do risco de renda
do modelo de Aiyagari (Python/macroeconomia/equilibrio_geral/aiyagari.py).

    dados/brasil/pnad_trimestral.csv  taxa de desocupação e tempo de procura
    dados/brasil/pnad_anual.csv       massa de rendimento do trabalho por
                                      faixa de percentil e Gini da renda

Fonte: API do SIDRA (tabelas 4099, 1616, 7543 e 7435). Rode a partir da
pasta Econometria/ (precisa de internet):

    python3 dados/brasil/baixar_pnad.py
"""
import json
import time
import urllib.request
from pathlib import Path

import pandas as pd

PASTA = Path("dados/brasil")

PROCURA = {  # categoria da tabela 1616: coluna
    "31827": "procura_menos_de_1_mes",
    "31828": "procura_1_mes_a_1_ano",
    "31829": "procura_1_a_2_anos",
    "101227": "procura_2_anos_ou_mais",
}

FAIXAS = {  # categoria da tabela 7543: coluna (% da massa de rendimento do trabalho)
    "49286": "massa_ate_p10",
    "49287": "massa_p10_p20",
    "49288": "massa_p20_p30",
    "49289": "massa_p30_p40",
    "49290": "massa_p40_p50",
    "49291": "massa_p50_p60",
    "49292": "massa_p60_p70",
    "49293": "massa_p70_p80",
    "49294": "massa_p80_p90",
    "49296": "massa_p90_p95",
    "49297": "massa_p95_p99",
    "49298": "massa_acima_p99",
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


def main() -> None:
    desocupacao = _sidra("t/4099/n1/all/v/4099/p/all")
    trimestral = pd.DataFrame({"taxa_desocupacao": desocupacao.set_index("D3C")["V"]})
    procura = _sidra("t/1616/n1/all/v/4110/p/all/c1965/" + ",".join(PROCURA))
    procura = procura.pivot(index="D3C", columns="D4C", values="V").rename(columns=PROCURA)
    trimestral = trimestral.join(procura[list(PROCURA.values())])
    trimestral.index = trimestral.index.astype(int).rename("trimestre")

    faixas = _sidra("t/7543/n1/all/v/10848/p/all/c1043/" + ",".join(FAIXAS))
    anual = faixas.pivot(index="D3C", columns="D4C", values="V").rename(columns=FAIXAS)
    anual = anual[list(FAIXAS.values())]
    gini = _sidra("t/7435/n1/all/v/10681/p/all").set_index("D3C")["V"]
    anual["gini_renda_domiciliar_pc"] = gini
    anual.index = anual.index.astype(int).rename("ano")

    trimestral.sort_index().to_csv(PASTA / "pnad_trimestral.csv")
    anual.sort_index().to_csv(PASTA / "pnad_anual.csv")
    print(f"pnad_trimestral.csv: {len(trimestral)} trimestres; pnad_anual.csv: {len(anual)} anos")


if __name__ == "__main__":
    main()
