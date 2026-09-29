# Economics

Modelos econômicos quantitativos e econométricos, com o código, os dados que
eles usam e uma explicação do que está sendo estimado, para que dê para
acompanhar o raciocínio do começo ao fim.

A maior parte do material está em
[`Economia-Aplicada/`](Economia-Aplicada/README.md) e se divide em quatro
frentes:

- **Econometria aplicada.** As mesmas técnicas implementadas em R, Python,
  Julia e C, rodando sobre os mesmos dados. Como os coeficientes têm que bater
  entre as linguagens, uma implementação serve de conferência para a outra.
- **Equilíbrio geral em tempo contínuo.** Um estudo sobre a tributação da
  renda do capital no Brasil, calibrado com dados reais e com uma nota técnica
  em LaTeX.
- **Modelos baseados em agentes.** A mesma economia com 20 mil famílias
  simuladas uma a uma, com expectativas que vão da previsão perfeita à
  racionalidade limitada, com e sem leiloeiro.
- **Previsão fora da amostra.** Os dois tipos de modelo contra modelos
  estatísticos, prevendo as Contas Nacionais Trimestrais e o desemprego sem
  olhar o futuro.

Os modelos de macroeconomia se dividem em duas pastas:
[`Politicas/Lei-15270/`](Economia-Aplicada/Econometria/Python/macroeconomia/Politicas/Lei-15270/README.md),
com o estudo da lei, e
[`Forecast/Brasil/2013T4-2026T2/`](Economia-Aplicada/Econometria/Python/macroeconomia/Forecast/Brasil/2013T4-2026T2/README.md),
com a previsão.

## O que tem aqui

### Econometria em quatro linguagens

| Área | Modelo | R | Python | Julia | C |
|---|---|:-:|:-:|:-:|:-:|
| Macroeconometria | AR(1) por OLS | ✓ | ✓ | ✓ | ✓ |
| Microeconometria | Painel com efeitos fixos (LSDV) | ✓ | ✓ | ✓ | ✓ |
| Finanças | CAPM | ✓ | ✓ | ✓ | ✓ |
| Avaliação de política | Diferença-em-diferenças | ✓ | ✓ | ✓ | ✓ |
| Macroeconomia | Ramsey–Cass–Koopmans com governo | | ✓ | ✓ | |
| Macroeconomia | Aiyagari (famílias heterogêneas) | | ✓ | | |
| Macroeconomia | Equilíbrio geral estocástico (filtro de Kalman) | | ✓ | | |
| Macroeconomia | Equilíbrio geral com margem e busca no mercado de trabalho | | ✓ | | |
| Macroeconomia | Modelos baseados em agentes, com e sem leiloeiro | | ✓ | | |

Os exemplos econométricos usam datasets sintéticos gerados com seed fixa, com
o processo gerador conhecido (por exemplo, um ATT de 3,0 no DID e um beta de
1,2 no CAPM). Assim dá para ver se o estimador recupera o parâmetro verdadeiro.

As dependências foram mantidas no mínimo: R e Julia usam só a biblioteca
padrão, o C usa apenas `libc` e `libm` (o OLS é resolvido à mão, por
Gauss-Jordan), e o Python usa numpy, pandas, scipy, statsmodels e matplotlib.

### Tributação do capital no Brasil

O projeto em
[`Politicas/Lei-15270/`](Economia-Aplicada/Econometria/Python/macroeconomia/Politicas/Lei-15270/README.md)
mede os efeitos de um aumento da tributação da renda do capital do tamanho
previsto na Lei 15.270/2025, com parâmetros calibrados a partir da PWT 11.0,
do Ipea e do IBGE.

Com agente representativo, o aumento de 0,85 p.p. na alíquota efetiva reduz o
capital de longo prazo em 1,46% e o PIB e os salários em 0,66%, e a receita de
longo prazo fica em 90% da estática. O modelo trata choques inesperados,
anunciados e temporários e inclui uma estimação estrutural com Monte Carlo.
Esses números provavelmente superestimam a queda do capital, porque um quarto
da receita nova vem de não residentes e boa parte do resto vem da tributação
de dividendos, e a nota técnica discute por quê.

Com famílias heterogêneas, com risco de desemprego e desigualdade de renda
calibrados pela PNAD Contínua, o resultado agregado quase não muda, e a forma
de devolver a receita decide quem ganha. Devolvida igual para todos, a metade
mais pobre ganha 0,58% do consumo; devolvida só ao grupo intermediário, como a
isenção do imposto de renda da lei, perde 0,42%.

![Transição após o aumento da tributação do capital](Economia-Aplicada/Econometria/Python/macroeconomia/Politicas/Lei-15270/equilibrio_geral/figuras/lei_15270.png)

A derivação completa, os algoritmos e a discussão dos resultados estão na
[nota técnica](Economia-Aplicada/Econometria/Python/macroeconomia/Politicas/Lei-15270/equilibrio_geral/nota_tecnica.pdf).
A versão em Julia resolve o mesmo modelo por outro algoritmo (*reverse
shooting*) e chega aos mesmos números até a 6ª casa decimal.

### Modelos baseados em agentes

O [ABM com leiloeiro](Economia-Aplicada/Econometria/Python/macroeconomia/Forecast/Brasil/2013T4-2026T2/abm1_com_leiloeiro/README.md)
tem 20 mil famílias com o mesmo problema de consumo e poupança do Aiyagari, em
trimestres, e cinco formas de formar expectativas: previsão perfeita,
aprendizado adaptativo, heurísticas com troca (Brock e Hommes), atualização
esporádica da informação (Carroll) e atenção limitada (Gabaix).

Com previsão perfeita, ele reproduz o modelo contínuo: a queda de longo prazo
do capital com a Lei 15.270/2025 é a mesma (−1,45%), e os ganhos e perdas de
bem-estar por grupo ficam a até 0,06 p.p. dos do Aiyagari, por um método de
solução independente. Com racionalidade limitada, quem ganha e quem perde não
muda, e o tamanho sim: com aprendizado, o capital oscila em ciclos longos antes
de chegar ao novo equilíbrio, e o ganho de bem-estar encolhe cerca de um
terço. Partindo de longe do equilíbrio (capital pela metade, riqueza igual
para todos, 1% com tudo), o capital volta sozinho a ele com aprendizado,
heurísticas, informação rígida e atenção limitada, e a desigualdade
reaparece; com crenças fixas no estado estacionário, a economia vai para
outro ponto de repouso, com 84% a mais de capital. Percorrendo 1996-2026
guiadas pelos dados, as famílias abandonam depois da recessão de 2015-2016 a
regra que aposta na volta ao estado estacionário.

Na [versão sem leiloeiro](Economia-Aplicada/Econometria/Python/macroeconomia/Forecast/Brasil/2013T4-2026T2/abm2_sem_leiloeiro/README.md),
com 200 firmas que fixam preços e salários, mercado de trabalho com busca e
compras em poucos fornecedores, o desemprego fica em 10% (9,7% na PNAD), as
firmas cobram margens de 10% sobre o custo, o salário real fica 10% a 11%
menor que no equilíbrio walrasiano, e o produto oscila mesmo sem choques
externos. Em raras simulações, o modelo também produz crises de desemprego
profundas.

![Bem-estar por grupo com cada regra de expectativas](Economia-Aplicada/Econometria/Python/macroeconomia/Politicas/Lei-15270/abm1_com_leiloeiro/figuras/lei_bem_estar.png)

### Previsão fora da amostra

A [avaliação](Economia-Aplicada/Econometria/Python/macroeconomia/Forecast/Brasil/2013T4-2026T2/README.md)
reestima cada modelo em 50 trimestres, de 2013 a 2026, só com os dados
disponíveis em cada data, e compara as previsões de 1 a 8 trimestres com o que
aconteceu. São dois equilíbrios gerais (um deles com margem e busca no
mercado de trabalho, que prevê também o desemprego), os dois ABMs e três
referências estatísticas.

Na amostra completa, o melhor modelo para o PIB é o equilíbrio geral
estocástico com a tendência dos dados trimestrais, até cinco trimestres, e o
ABM sem leiloeiro com informação rígida em horizontes mais longos; para o
consumo, é esse mesmo ABM. Sem a pandemia, o VAR(1) é o melhor para o PIB e o
consumo nos horizontes curtos, e o ABM com leiloeiro e heurísticas, para o
investimento. No desemprego, na amostra completa, os modelos com busca erram
de 25% a 28% menos que um AR(1) em dois anos, porque trazem o desemprego de
volta à média da PNAD.
Sem leiloeiro, as regras de expectativas que reagem demais ao retorno
realizado do capital tornam o investimento instável e as previsões ruins.

Quase nenhuma diferença é estatisticamente significativa com essa amostra,
e menos ainda depois de corrigir para as muitas comparações. As previsões para
2026-2028 ficam registradas, para serem conferidas quando o IBGE divulgar os
dados.

## Estrutura

```
Economia-Aplicada/
└── Econometria/
    ├── R/          # base R, sem pacotes externos
    ├── Python/     # inclui macroeconomia/: Politicas/Lei-15270/ e Forecast/Brasil/2013T4-2026T2/
    ├── Julia/      # biblioteca padrão
    ├── C/          # C puro, com OLS próprio em comum/
    └── dados/      # datasets sintéticos + dados reais do Brasil (brasil/)
```

Dentro de cada linguagem, os modelos ficam separados por área:
`macroeconometria/`, `microeconometria/`, `financas/`,
`trabalho_desenvolvimento/` e `macroeconomia/`.

## Como rodar

Todos os scripts leem os dados por caminho relativo, então os comandos devem
ser executados a partir da pasta `Econometria/`:

```bash
git clone https://github.com/JoseUfscar/Economics.git
cd Economics/Economia-Aplicada/Econometria
```

**Python**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r Python/requirements.txt
python3 Python/macroeconometria/ar1.py
```

Para reproduzir os resultados dos modelos de macroeconomia até a última casa,
use as versões exatas de `Python/requirements-versoes.txt`. Os testes desses
modelos rodam a cada push, pelo GitHub Actions.

**R**

```bash
Rscript R/microeconometria/painel_fe.R
```

**Julia** (testado na 1.10)

```bash
julia Julia/financas/capm.jl
```

**C**

```bash
make -C C
./C/bin/diff_in_diff
```

Os comandos dos modelos de macroeconomia (calibração, experimentos,
previsões e testes) estão no
[README de `macroeconomia/`](Economia-Aplicada/Econometria/Python/macroeconomia/README.md)
e nos das pastas de cada modelo. Cada pasta de linguagem também tem seu
próprio README, com mais detalhes.

## Dados

- **Sintéticos:** `macro_series.csv`, `painel.csv`, `financas.csv` e
  `did.csv`, gerados por `dados/gerar_dados.py`. O processo gerador de cada
  um está descrito em
  [`dados/README.md`](Economia-Aplicada/Econometria/dados/README.md).
- **Brasil:** séries da Penn World Table 11.0, do Ipea (estoque de capital) e
  do IBGE (Contas Nacionais anuais e trimestrais e PNAD Contínua). Os CSVs
  ficam versionados para que tudo rode sem internet, e os scripts de download
  estão junto. Fontes, unidades e códigos de cada série em
  [`dados/brasil/README.md`](Economia-Aplicada/Econometria/dados/brasil/README.md).

## Adicionando um modelo

- Um arquivo por modelo, na pasta da área correspondente, com um nome que diga
  o que ele é (`var.py`, `garch.jl`, `logit.R`).
- Um cabeçalho curto com a equação estimada e o comando para rodar.
- Sempre que possível, usar os dados de `dados/`, para que o resultado possa
  ser comparado com as outras linguagens.

## Citação

Os dados de citação estão em [`CITATION.cff`](CITATION.cff).

## Autor

José Oliveira, [@JoseUfscar](https://github.com/JoseUfscar)
