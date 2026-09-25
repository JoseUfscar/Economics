"""
Baixa as séries anuais do Brasil usadas na calibração do modelo de equilíbrio
geral (Python/macroeconomia/equilibrio_geral) e grava dados/brasil/brasil_anual.csv.

Fontes:
  - Penn World Table 11.0 (Feenstra, Inklaar e Timmer), pelas séries que o
    FRED (Federal Reserve Bank of St. Louis) republica;
  - Ipea, estoque de capital fixo (DIMAC), pela API do Ipeadata;
  - IBGE, Sistema de Contas Nacionais, pela API do Ipeadata.

Rode a partir da pasta Econometria/ (precisa de internet):

    python3 dados/brasil/baixar_dados.py

O CSV gerado fica versionado, então o resto do projeto roda sem internet.
"""
import io
import json
import time
import urllib.request
from pathlib import Path

import pandas as pd

FRED = {  # coluna: código no FRED (Penn World Table 11.0)
    "pib_real_pwt": "RGDPNABRA666NRUG",       # PIB a preços nacionais constantes de 2021
    "capital_real_pwt": "RKNANPBRA666NRUG",   # estoque de capital a preços nacionais de 2021
    "parcela_trabalho": "LABSHPBRA156NRUG",   # participação do trabalho na renda (labsh)
    "ocupados": "EMPENGBRA148NRUG",           # pessoas ocupadas (milhões)
    "populacao": "POPTTLBRA148NRUG",          # população (milhões)
    "capital_humano": "HCIYISBRA066NRUG",     # índice de capital humano
    "horas_por_ocupado": "AVHWPEBRA065NRUG",  # horas anuais médias por ocupado
}

IPEADATA = {  # coluna: código no Ipeadata (valores em R$ milhões)
    "capital_liquido": "DIMAC_CFELCTOT",      # Ipea: estoque líquido de capital fixo (R$ de 2025)
    "depreciacao": "DIMAC_CFDPRTOT",          # Ipea: depreciação do capital fixo (R$ de 2025)
    "investimento_bruto": "DIMAC_CFINVBRTOT", # Ipea: investimento bruto (R$ de 2025)
    "capital_produto": "DIMAC_CFRCP",         # Ipea: relação capital-produto
    "pib_nominal": "SCN10_PIBN10",            # IBGE: PIB a preços de mercado (R$ correntes)
    "consumo_governo": "SCN10_CFGGN10",       # IBGE: consumo final do governo (R$ correntes)
    "consumo_familias": "SCN10_CFPPNEXC10",   # IBGE: consumo final das famílias (R$ correntes)
    "fbcf_nominal": "SCN10_FBKFN10",          # IBGE: formação bruta de capital fixo (R$ correntes)
}

DESTINO = Path("dados/brasil/brasil_anual.csv")


def _baixar(url: str, tentativas: int = 3) -> bytes:
    for tentativa in range(tentativas):
        try:
            with urllib.request.urlopen(url, timeout=60) as resposta:
                return resposta.read()
        except OSError:
            if tentativa == tentativas - 1:
                raise
            time.sleep(2 ** tentativa)


def serie_fred(codigo: str) -> pd.Series:
    tabela = pd.read_csv(io.BytesIO(_baixar(
        f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={codigo}")))
    anos = pd.to_datetime(tabela.iloc[:, 0]).dt.year
    return pd.Series(pd.to_numeric(tabela.iloc[:, 1], errors="coerce").to_numpy(), index=anos)


def serie_ipeadata(codigo: str) -> pd.Series:
    url = f"https://www.ipeadata.gov.br/api/odata4/ValoresSerie(SERCODIGO='{codigo}')"
    valores = json.loads(_baixar(url))["value"]
    return pd.Series({int(v["VALDATA"][:4]): v["VALVALOR"] for v in valores}, dtype=float)


def main() -> None:
    colunas = {nome: serie_fred(cod) for nome, cod in FRED.items()}
    colunas |= {nome: serie_ipeadata(cod) for nome, cod in IPEADATA.items()}
    tabela = pd.DataFrame(colunas).sort_index().rename_axis("ano")
    tabela = tabela.loc[1950:].dropna(how="all")
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    tabela.to_csv(DESTINO, float_format="%.10g")
    print(f"{DESTINO}: {len(tabela)} anos ({tabela.index.min()}-{tabela.index.max()})")


if __name__ == "__main__":
    main()
