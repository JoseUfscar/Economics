# Dados anuais do Brasil

Séries reais usadas na calibração do modelo de equilíbrio geral
(`Python/macroeconomia/equilibrio_geral/`). O arquivo `brasil_anual.csv` é
gerado por `baixar_dados.py` e fica versionado, para que o projeto rode sem
internet e com números reproduzíveis. Para atualizar:

```
python3 dados/brasil/baixar_dados.py
```

Última extração: setembro de 2026 (PWT até 2023; Ipea e IBGE até 2025).

## Colunas

| coluna | descrição | unidade | fonte (código) |
|---|---|---|---|
| `pib_real_pwt` | PIB a preços nacionais constantes | milhões de US$ de 2021 | PWT 11.0 `rgdpna` (FRED `RGDPNABRA666NRUG`) |
| `capital_real_pwt` | estoque de capital a preços nacionais constantes | milhões de US$ de 2021 | PWT 11.0 `rnna` (FRED `RKNANPBRA666NRUG`) |
| `parcela_trabalho` | participação da renda do trabalho no PIB | fração | PWT 11.0 `labsh` (FRED `LABSHPBRA156NRUG`) |
| `ocupados` | pessoas ocupadas | milhões | PWT 11.0 `emp` (FRED `EMPENGBRA148NRUG`) |
| `populacao` | população | milhões | PWT 11.0 `pop` (FRED `POPTTLBRA148NRUG`) |
| `capital_humano` | índice de capital humano | índice | PWT 11.0 `hc` (FRED `HCIYISBRA066NRUG`) |
| `horas_por_ocupado` | horas anuais médias por ocupado | horas | PWT 11.0 `avh` (FRED `AVHWPEBRA065NRUG`) |
| `capital_liquido` | estoque líquido de capital fixo | R$ milhões de 2025 | Ipea (Ipeadata `DIMAC_CFELCTOT`) |
| `depreciacao` | depreciação do capital fixo | R$ milhões de 2025 | Ipea (Ipeadata `DIMAC_CFDPRTOT`) |
| `investimento_bruto` | investimento bruto em capital fixo | R$ milhões de 2025 | Ipea (Ipeadata `DIMAC_CFINVBRTOT`) |
| `capital_produto` | relação capital-produto | razão | Ipea (Ipeadata `DIMAC_CFRCP`) |
| `pib_nominal` | PIB a preços de mercado | R$ milhões correntes | IBGE, SCN (Ipeadata `SCN10_PIBN10`) |
| `consumo_governo` | consumo final do governo | R$ milhões correntes | IBGE, SCN (Ipeadata `SCN10_CFGGN10`) |
| `consumo_familias` | consumo final das famílias | R$ milhões correntes | IBGE, SCN (Ipeadata `SCN10_CFPPNEXC10`) |
| `fbcf_nominal` | formação bruta de capital fixo | R$ milhões correntes | IBGE, SCN (Ipeadata `SCN10_FBKFN10`) |

## PNAD Contínua (`pnad_trimestral.csv` e `pnad_anual.csv`)

Gerados por `baixar_pnad.py` (API do SIDRA/IBGE), para calibrar o risco de
renda do modelo de Aiyagari:

```
python3 dados/brasil/baixar_pnad.py
```

| arquivo | coluna | descrição | tabela SIDRA |
|---|---|---|---|
| trimestral | `taxa_desocupacao` | taxa de desocupação, 14 anos ou mais (%) | 4099 |
| trimestral | `procura_*` | distribuição dos desocupados por tempo de procura de trabalho (%): menos de 1 mês, 1 mês a 1 ano, 1 a 2 anos, 2 anos ou mais | 1616 |
| anual | `massa_*` | distribuição da massa de rendimento habitual do trabalho por faixa de percentil dos ocupados (%) | 7543 |
| anual | `gini_renda_domiciliar_pc` | índice de Gini do rendimento domiciliar per capita | 7435 |

Série trimestral de 2012T1 a 2026T2; anual de 2012 a 2025.

## Observações

- A Penn World Table é baixada pelas séries que o FRED republica, porque o
  repositório oficial (Dataverse) bloqueia downloads automáticos. Os valores
  são os mesmos da PWT 11.0.
- Nas séries do IBGE, os anos anteriores ao Plano Real aparecem em reais
  convertidos e por isso são minúsculos; a calibração usa só 2000 em diante.
- O estoque de capital do Ipea é a referência para K/Y e depreciação, pois é
  compatível com as Contas Nacionais do IBGE. O da PWT fica no arquivo para
  comparação: ele inclui outra composição de ativos e gera K/Y bem maior.

## Referências

- Feenstra, R. C., Inklaar, R. e Timmer, M. P. (2015). The Next Generation of
  the Penn World Table. *American Economic Review*, 105(10), 3150-3182.
  Dados: PWT 11.0, Groningen Growth and Development Centre, 2025.
- Ipea. Estoque de capital fixo no Brasil. Ipeadata, séries DIMAC.
- IBGE. Sistema de Contas Nacionais. Ipeadata, séries SCN10.
