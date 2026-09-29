# Economics

Este repositório reúne modelos econômicos quantitativos e econométricos
escritos para serem lidos, e não apenas executados, de modo que cada modelo
vem acompanhado do código, dos dados que utiliza e de uma explicação do que
está sendo estimado, o que permite acompanhar o raciocínio do começo ao fim.

A maior parte do material está em [`Economia-Aplicada/`](Economia-Aplicada/README.md)
e se organiza em quatro frentes. A primeira é a econometria aplicada, com as
mesmas técnicas implementadas em R, Python, Julia e C sobre os mesmos dados,
de forma que os coeficientes precisam coincidir entre as linguagens e cada
implementação serve de conferência para as demais. A segunda é um estudo
sobre a tributação da renda do capital no Brasil em equilíbrio geral, em
tempo contínuo, calibrado com dados reais e acompanhado de uma nota técnica.
A terceira leva a mesma economia para modelos baseados em agentes, com 20 mil
famílias simuladas uma a uma e expectativas que vão da previsão perfeita à
racionalidade limitada, em versões com e sem leiloeiro walrasiano. A quarta
compara esses dois tipos de modelo com modelos estatísticos na previsão das
Contas Nacionais Trimestrais e do desemprego, sempre com a informação que
existia em cada data.

Os modelos de macroeconomia ficam em duas pastas, uma dedicada ao estudo da
lei, [`Politicas/Lei-15270/`](Economia-Aplicada/Econometria/Python/macroeconomia/Politicas/Lei-15270/README.md),
e outra à previsão, [`Forecast/Brasil/2013T4-2026T2/`](Economia-Aplicada/Econometria/Python/macroeconomia/Forecast/Brasil/2013T4-2026T2/README.md).

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

Os exemplos econométricos usam dados sintéticos gerados com semente fixa e
processo gerador conhecido, como um ATT de 3,0 no DID e um beta de 1,2 no
CAPM, o que permite verificar se o estimador recupera o parâmetro verdadeiro.
As dependências foram mantidas no mínimo, já que R e Julia usam apenas a
biblioteca padrão, o C usa somente `libc` e `libm`, com o OLS resolvido à mão
por Gauss-Jordan, e o Python se limita a numpy, pandas, scipy, statsmodels e
matplotlib.

### Tributação do capital no Brasil

O projeto em [`Politicas/Lei-15270/`](Economia-Aplicada/Econometria/Python/macroeconomia/Politicas/Lei-15270/README.md)
mede os efeitos de um aumento da tributação da renda do capital do tamanho
previsto na Lei 15.270/2025, com parâmetros calibrados a partir da PWT 11.0,
do Ipea e do IBGE. Com agente representativo, o aumento de 0,85 p.p. na
alíquota efetiva reduz o capital em 1,46% e o PIB e os salários em 0,66% no
longo prazo, enquanto a receita de longo prazo fica em 90% da estática. O
modelo trata choques inesperados, anunciados e temporários e inclui uma
estimação estrutural avaliada por Monte Carlo. Quando as famílias passam a
ser heterogêneas, com risco de desemprego e desigualdade de renda calibrados
pela PNAD Contínua, o resultado agregado quase não se altera, mas a
distribuição muda bastante, e a metade mais pobre pode sair ganhando ou
perdendo conforme a forma como a receita é devolvida.

![Transição após o aumento da tributação do capital](Economia-Aplicada/Econometria/Python/macroeconomia/Politicas/Lei-15270/equilibrio_geral/figuras/lei_15270.png)

A derivação completa, os algoritmos e a discussão dos resultados estão na
[nota técnica](Economia-Aplicada/Econometria/Python/macroeconomia/Politicas/Lei-15270/equilibrio_geral/nota_tecnica.pdf),
e a versão em Julia resolve o mesmo modelo por outro algoritmo (*reverse
shooting*) e chega aos mesmos números até a sexta casa decimal.

### Modelos baseados em agentes

O [ABM](Economia-Aplicada/Econometria/Python/macroeconomia/Forecast/Brasil/2013T4-2026T2/abm1_com_leiloeiro/README.md)
tem 20 mil famílias com o mesmo problema de consumo e poupança do modelo de
Aiyagari, em trimestres, e cinco formas de formar expectativas, que são a
previsão perfeita, o aprendizado adaptativo, as heurísticas com troca de
Brock e Hommes, a informação rígida de Mankiw e Reis e a atenção limitada de
Gabaix. Com previsão perfeita, o ABM reproduz o modelo contínuo, tanto na
queda de longo prazo do capital com a Lei 15.270/2025 (−1,45%) quanto nos
ganhos e perdas de bem-estar de cada grupo, com dois métodos de solução
independentes. Com racionalidade limitada, quem ganha e quem perde continua o
mesmo, mas o tamanho dos efeitos muda, e com aprendizado o capital oscila em
ciclos longos antes de chegar ao novo equilíbrio e o ganho de bem-estar
encolhe cerca de um terço.

Algumas propriedades emergem da interação entre as famílias. Ao percorrer o
período de 1996 a 2026 guiadas pelos dados, elas abandonam a regra que aposta
na volta ao passado depois da recessão de 2015-2016, e, partindo de situações
distantes do equilíbrio, como o capital pela metade, a riqueza igual para
todos ou 1% das famílias com toda a riqueza, o capital volta sozinho ao
equilíbrio com aprendizado, heurísticas, informação rígida e atenção
limitada, enquanto a desigualdade reaparece. Com crenças fixas no estado
estacionário a economia segue para outro ponto de repouso, com 84% a mais de
capital. Numa [versão sem leiloeiro](Economia-Aplicada/Econometria/Python/macroeconomia/Forecast/Brasil/2013T4-2026T2/abm2_sem_leiloeiro/README.md),
com 200 firmas que fixam preços e salários, busca por emprego e compras em
poucos fornecedores, o desemprego emerge em 10% (9,7% na PNAD), as firmas
passam a cobrar margens de 10% sobre o custo, o salário real fica 10% menor e
o produto oscila sem nenhum choque agregado.

![Bem-estar por grupo com cada regra de expectativas](Economia-Aplicada/Econometria/Python/macroeconomia/Politicas/Lei-15270/abm1_com_leiloeiro/figuras/lei_bem_estar.png)

### Previsão fora da amostra

A [avaliação](Economia-Aplicada/Econometria/Python/macroeconomia/Forecast/Brasil/2013T4-2026T2/README.md)
reestima cada modelo em 50 trimestres, de 2013 a 2026, apenas com os dados
disponíveis em cada data, e compara as previsões de 1 a 8 trimestres com o
que de fato aconteceu. Os modelos formam dois pares com os mesmos
fundamentos, o equilíbrio geral estocástico contra o ABM com leiloeiro e o
equilíbrio geral com margem e busca no mercado de trabalho contra o ABM sem
leiloeiro, e este segundo par prevê também o desemprego. Na amostra completa,
o melhor modelo para o PIB é o equilíbrio geral estocástico com a tendência
dos dados trimestrais, o melhor para o consumo é o ABM sem leiloeiro com
informação rígida e, fora da pandemia, o ABM com leiloeiro e heurísticas é o
que melhor prevê o investimento. No desemprego, os dois modelos com busca
erram de 13% a 24% menos que um AR(1) em dois anos, porque trazem a taxa de
volta à média da PNAD, ao passo que, sem leiloeiro, as regras de expectativas
que reagem demais ao retorno realizado do capital tornam o investimento
instável e pioram as previsões. Quase nenhuma dessas diferenças é
estatisticamente significativa com a amostra disponível, e as previsões para
2026-2028 ficam registradas para serem conferidas quando o IBGE divulgar os
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

Dentro de cada linguagem, os modelos ficam separados por área, em
`macroeconometria/`, `microeconometria/`, `financas/`,
`trabalho_desenvolvimento/` e `macroeconomia/`.

## Como rodar

Todos os scripts leem os dados por caminho relativo, e por isso os comandos
devem ser executados a partir da pasta `Econometria/`.

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

Os comandos dos modelos de macroeconomia, que cobrem calibração,
experimentos, previsões e testes, estão no
[README de `macroeconomia/`](Economia-Aplicada/Econometria/Python/macroeconomia/README.md)
e nos das pastas de cada modelo, e cada pasta de linguagem tem também seu
próprio README, com mais detalhes.

## Dados

Os dados sintéticos (`macro_series.csv`, `painel.csv`, `financas.csv` e
`did.csv`) são gerados por `dados/gerar_dados.py`, e o processo gerador de
cada um está descrito em [`dados/README.md`](Economia-Aplicada/Econometria/dados/README.md).
Os dados do Brasil reúnem séries da Penn World Table 11.0, do Ipea, para o
estoque de capital, e do IBGE, com as Contas Nacionais anuais e trimestrais e
a PNAD Contínua. Os arquivos ficam versionados para que tudo rode sem
internet, junto com os scripts que os baixam, e as fontes, unidades e códigos
de cada série estão em [`dados/brasil/README.md`](Economia-Aplicada/Econometria/dados/brasil/README.md).

## Adicionando um modelo

Cada modelo deve ocupar um arquivo na pasta da área correspondente, com um
nome que diga o que ele é (`var.py`, `garch.jl`, `logit.R`) e um cabeçalho
curto com a equação estimada e o comando para rodar, usando sempre que
possível os dados de `dados/`, para que o resultado possa ser comparado com o
das outras linguagens.

## Autor

José Oliveira, [@JoseUfscar](https://github.com/JoseUfscar)
