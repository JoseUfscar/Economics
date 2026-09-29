# ABM 2: sem leiloeiro

O [ABM 1](../abm1_com_leiloeiro/README.md) sem o leiloeiro: 200 firmas que
fixam preços e salários, um mercado de trabalho com busca e um mercado de bens
em que cada família compra de poucos fornecedores. As famílias, a calibração e
as regras de expectativas são as mesmas do ABM 1. O desemprego, a margem das
firmas, o salário real e o retorno do capital resultam das decisões dos
agentes.

O modelo é usado na previsão fora da amostra desta pasta
([`../README.md`](../README.md)), em que o par dele no equilíbrio geral é o
[modelo com margem e busca](../dsge_busca/README.md), e nos experimentos da
[Lei 15.270](../../../../Politicas/Lei-15270/README.md#no-abm-sem-leiloeiro).

## A economia

No ABM 1, os preços vêm de um leiloeiro walrasiano. Em `descentralizada.py`,
cada mercado passa a funcionar pelas decisões dos agentes:

| Mercado | Quem decide | Como |
|---|---|---|
| Trabalho | 200 firmas heterogêneas em produtividade | cada firma abre vagas quando quer mais gente e demite quando quer menos; o desempregado se candidata a firmas com vagas, atraído pelo salário; o desemprego é o que sobra |
| Salários | as firmas | quem não preenche a maior parte das vagas oferece mais; quem passa dois anos sem dificuldade oferece menos (Lengnick, 2013); o salário revisto parte do salário médio do mercado: quem sobe paga pelo menos a média, quem corta, no máximo a média |
| Bens | as famílias, com 3 fornecedores cada | compram do mais barato para o mais caro; a firma sem estoque raciona; quem é racionado procura outra firma e, de vez em quando, troca de fornecedor |
| Preços | as firmas | margem sobre o custo unitário, revista com probabilidade 0,75 por trimestre (a frequência de reajustes no Brasil, Gouvea, 2007); a margem sobe quando falta estoque e desce quando sobra |
| Produção e capital | as firmas | quadro ajustado aos poucos pelo estoque; investimento que repõe a depreciação e o crescimento de tendência e fecha 3% por trimestre da distância até o capital de custo mínimo, com o custo do capital dado pelo retorno que as famílias esperam |
| Riqueza | um fundo, dono das firmas | o retorno das famílias é o lucro realizado, e não o produto marginal |

O desempregado recebe do governo a mesma fração da renda do seu tipo que no
Aiyagari, mas não produz, e os fluxos de emprego vêm da mesma cadeia
trimestral da PNAD. Se sobram vagas, o emprego segue exatamente essa cadeia;
se faltam, o desemprego sobe. A referência é o equilíbrio walrasiano com
esses fundamentos: como os desempregados ficam fora da produção, o capital é
4% menor que no ABM 1, e o juro e o salário são os mesmos.

A contabilidade fecha a cada trimestre: a riqueza das famílias mais o saldo
do governo é o capital mais o valor dos estoques, e o produto é consumo mais
investimento mais gasto do governo mais a variação dos estoques. As regras
das firmas vêm da literatura de ABM macroeconômico (Lengnick, 2013; Delli
Gatti et al., 2011), convertidas para trimestres. O único parâmetro calibrado
com dados é a velocidade de ajuste do capital, 3% por trimestre: com ela, o
desvio-padrão do crescimento trimestral da FBCF na história de 1996 a 2013
guiada pelos dados fica em 3,6 p.p., contra 3,5 p.p. nas Contas Nacionais
(com 10% por trimestre, seria 12 p.p.). O período termina antes da primeira
origem da avaliação de previsões.

## Como o modelo chegou a essa forma

As primeiras versões eram instáveis, e cada problema estava ligado a uma
regra das firmas. A regra de salários de Lengnick sobe o salário sempre que
falta gente, e com busca sempre falta alguém; com margem fixa, o salário real
crescia sem limite, porque o preço repassa só a parte do trabalho no custo.
Firmas que estimavam a demanda só pelas vendas não percebiam a demanda que
deixavam de atender e ficavam presas num racionamento permanente. Quando o
investimento comprava antes das famílias, o racionamento virava poupança
forçada, que virava mais capital, derrubava o juro e aumentava a demanda. E
firmas que ajustavam o quadro de uma vez levavam a economia ao desemprego de
100%.

A versão atual ajusta o quadro aos poucos, deixa a margem subir quando falta
produto, dá prioridade às famílias no mercado de bens e mede a demanda pelas
vendas mais o que ficou sem atender. Duas mudanças vieram depois, ao preparar
o modelo para a previsão. Na regra de Lengnick, o salário de cada firma era
um passeio aleatório, e a dispersão entre firmas passava de 8% e ainda subia
depois de 300 anos; agora o salário revisto parte da média do mercado, e a
dispersão se estabiliza em cerca de 5%. E a firma repunha só a depreciação,
de modo que, com crescimento, o capital ficava abaixo do alvo numa proporção
que dependia da velocidade de ajuste; agora ela repõe também o crescimento
de tendência, e o capital de longo prazo não depende da velocidade.

## Longo prazo, sem choques agregados

300 anos sem choques agregados, com 20 mil famílias e quatro sementes por
regra. A tabela mostra a média das sementes depois dos 100 primeiros anos
(`resultados/mercados_longo_prazo.csv`) e, entre parênteses, o erro-padrão
entre elas quando ele passa de 0,01 (`resultados/mercados_longo_prazo_erro_padrao.csv`):

| | Walrasiano / PNAD | Aprendizado | Heurísticas | Atenção limitada |
|---|---|---|---|---|
| Produto (referência = 1) | 1 | 0,96 | 0,96 | 0,96 |
| Capital | 1 | 0,87 (0,01) | 0,86 | 0,85 |
| Salário real | 1 | 0,90 | 0,89 | 0,89 |
| Juro líquido | 10,24% | 10,55% | 10,61% | 10,75% |
| Desemprego | 9,7% | 10,2% (0,2) | 10,0% | 10,1% (0,1) |
| Margem sobre o custo | 0 | 10,3% | 10,4% | 10,5% (0,1) |
| Participação do trabalho | 54,9% | 50,7% | 50,8% | 50,7% |
| Procura há até 1 ano / 1 a 2 anos / mais de 2 | 64 / 14 / 22% | 63 / 15 / 23% | 63 / 14 / 22% | 63 / 15 / 23% |
| Famílias que não acham o produto em algum fornecedor | 0 | 43% | 42% | 43% |
| Desvio do crescimento anual do produto | — | 1,5 p.p. (0,2) | 1,4 p.p. | 1,5 p.p. (0,1) |
| Desvio do desemprego | — | 0,84 p.p. (0,62) | 0,25 p.p. | 0,38 p.p. (0,20) |

![Produto, desemprego e margem sem leiloeiro](figuras/mercados_longo_prazo.png)

O desemprego fica em 10,0% a 10,2%, contra 9,7% na PNAD, e a distribuição do
tempo de procura bate com a da PNAD (tabela 1616 do IBGE). Parte disso vem da
calibração, porque a busca reproduz a cadeia da PNAD quando sobram vagas; os
0,3 a 0,5 p.p. a mais vêm das demissões e das vagas que ficam abertas.

As firmas cobram margens de cerca de 10% sobre o custo, porque as famílias
comparam poucos fornecedores e descobrem devagar as firmas mais baratas. O
salário real fica 10% a 11% abaixo do walrasiano, a participação do trabalho
cai de 55% para 51%, e o capital, que as firmas dimensionam pelo custo, fica
13% a 15% abaixo. O produto cai menos, cerca de 4%, porque a produção migra
para as firmas mais produtivas. O juro fica 0,3 a 0,5 p.p. acima do
walrasiano: o retorno do fundo é o lucro realizado, e a poupança das famílias
se ajusta para que o capital renda o que elas exigem.

Mesmo sem choques agregados, o produto oscila em ondas longas, e o
crescimento anual tem desvio de 1,4 a 1,5 p.p., cerca de metade dos 2,7 p.p.
do PIB brasileiro desde 1997. Em 10 das 12 simulações, o desemprego quase não
se mexe (desvio de 0,2 a 0,3 p.p., contra 2,9 p.p. na PNAD), e não há lei de
Okun nem curva de Beveridge. Nas outras duas, ambas com a mesma semente, uma
com aprendizado e outra com atenção limitada, aparecem crises de desemprego.
Na mais forte, com aprendizado, depois de décadas de aumento do capital, as
firmas cortam o quadro, as vagas quase desaparecem, e o desemprego chega a
26% perto do ano 280, ainda acima de 17% no fim dos 300 anos. Na outra, chega
a 17%. Essas crises são raras, mas mostram que o modelo pode gerar ciclos de
desemprego sem nenhum choque externo.

### Sensibilidade

Com aprendizado, média de quatro sementes nos últimos 100 de 150 anos
(`resultados/mercados_sensibilidade.csv`, que traz também os erros-padrão,
de no máximo 0,01 no produto e no capital e 0,04 p.p. no desemprego). A
linha de base difere um pouco da tabela anterior, que usa 300 anos:

| Variante | Produto | Capital | Salário real | Desemprego | Margem |
|---|---|---|---|---|---|
| Base | 0,95 | 0,84 | 0,88 | 10,0% | 10,6% |
| Margem máxima de 10% (em vez de 15%) | 0,97 | 0,89 | 0,93 | 9,9% | 7,5% |
| Margem máxima de 25% | 0,91 | 0,74 | 0,80 | 10,3% | 16,0% |
| Revisão de preço com probabilidade 0,5 | 0,95 | 0,84 | 0,88 | 10,0% | 10,7% |
| Passo do salário de 1,5% ou de 6% | 0,94–0,96 | 0,82–0,85 | 0,87–0,90 | 10,0% | 10,3–10,9% |
| Procura de fornecedor 0,1 ou 0,5 | 0,94–0,96 | 0,83–0,85 | 0,88–0,89 | 10,0% | 10,1–10,5% |
| 100 ou 400 firmas | 0,94–0,96 | 0,83–0,84 | 0,88–0,89 | 9,9–10,2% | 10,5–10,7% |
| Depreciação do estoque de 2% ou 10% | 0,94–0,97 | 0,82–0,87 | 0,87–0,91 | 10,0–10,1% | 9,6–11,5% |

O desemprego e o juro quase não dependem das regras. A margem depende de uma
só: fica em cerca de dois terços do teto que as firmas se permitem. O modelo
mostra a direção em que o poder de mercado empurra salários e capital, mas não
fixa o tamanho dele; para isso, o teto teria de ser calibrado com margens
medidas nos dados.

## Verificação

Os 21 testes (`test_*.py`) conferem que, a cada trimestre, a riqueza das
famílias mais o saldo do governo é o capital mais os estoques e o produto é a
soma das demandas mais a variação dos estoques; que, com vagas sobrando, a
busca reproduz a cadeia de emprego da PNAD; que nenhuma firma vende mais do
que tem; e que, sem receita nova, mudar a forma de devolução não muda nada
(só a receita da reforma segue os pesos da devolução). Na história guiada
pelos dados, o ABM 2 reproduz o PIB e o gasto observados com erro de
$10^{-14}$ e a taxa de desemprego da PNAD com erro médio de 0,05 p.p., e
achar a separação que dá o desemprego observado não altera os números
aleatórios do resto do trimestre.

## Previsão fora da amostra

Em cada origem, só com o que se sabia naquela data
(`previsao_descentralizada.py`), o modelo passa por cinco etapas:

1. a mesma calibração do ABM 1 (dados anuais até dois anos antes, PNAD até a
   origem, tendência pelo PIB trimestral até a origem), com os
   desempregados fora da produção;
2. 100 anos de aquecimento sem choques, a partir da referência walrasiana,
   para que margens, estoques, capital e crenças cheguem ao regime do próprio
   ABM;
3. a história de 1996 até a origem, reproduzindo o PIB (pelo crescimento da
   produtividade), o gasto do governo e, desde 2012, a taxa de desemprego da
   PNAD dessazonalizada só com os dados até a origem (pela probabilidade de
   separação do trimestre);
4. um AR(1) para cada um dos três choques, com resíduos correlacionados;
5. 200 simulações de T+1 a T+8, com choques antitéticos.

O modelo prevê o crescimento acumulado de PIB, consumo, FBCF e consumo do
governo e a variação do desemprego. A tabela mostra o RMSE relativo ao AR(1)
em 8 trimestres, com a amostra toda e sem as janelas da pandemia (em negrito,
diferença significativa a 5% pelo teste de Diebold-Mariano; com †, também
depois da correção de Holm para as comparações de todos os modelos):

| Modelo | PIB | PIB sem pandemia | Consumo | Consumo sem pandemia | FBCF | FBCF sem pandemia | Desemprego | Desemprego sem pandemia |
|---|---|---|---|---|---|---|---|---|
| Equilíbrio geral com busca (tend. trimestral) | 0,97 | 1,03 | 0,95 | 1,04 | 1,09 | 1,12 | 0,72 | 0,75 |
| ABM 2: crenças fixas | 0,98 | 1,00 | 0,95 | 0,98 | **1,06** | 1,04 | 0,77 | 0,88 |
| ABM 2: aprendizado | 0,95 | 0,96 | 0,95 | 0,97 | 1,05 | 1,06 | 0,75 | 0,83 |
| ABM 2: heurísticas | 1,04 | **1,08** | 1,09 | **1,26** | **1,60**† | **1,56**† | 0,90 | 0,92 |
| ABM 2: informação rígida | 0,90 | 0,96 | 0,91 | 0,97 | 0,99 | 1,04 | 0,82 | 0,95 |
| ABM 2: atenção limitada | 0,97 | **1,05**† | **1,23** | 1,35 | **1,60** | 1,57 | 0,79 | 0,89 |

![ABM 2 e equilíbrio geral com busca](../figuras/rmse_abm2_sem_pandemia.png)

Com crenças fixas, aprendizado e informação rígida, o ABM 2 fica no nível do
par ou um pouco melhor. Com informação rígida, é o modelo de menor erro para o
consumo na amostra toda de h = 3 a h = 8 (de 9% a 14% menos que o AR(1)) e
para o PIB de h = 6 a h = 8 (8% a 10% menos). Sem a pandemia, erra menos que o
par na FBCF (1,04 a 1,06 vez o AR(1) em 8 trimestres, contra 1,12). Nenhuma
dessas diferenças é significativa.

No desemprego, o ganho aparece em dois anos. Em 8 trimestres, o ABM 2 com
aprendizado erra 25% menos que o AR(1) (17% sem a pandemia), e o equilíbrio
geral com busca, 28% menos (25%), o menor erro entre os modelos. Os dois
trazem o desemprego de volta à média da PNAD, enquanto as referências
extrapolam a tendência recente. Em um ano, só o equilíbrio geral com busca
erra menos que o AR(1) (8% menos); o ABM 2 fica no nível dele ou pior, e em um
trimestre o AR(1) é o melhor. Nenhuma dessas diferenças é significativa.

Com heurísticas e com atenção limitada, o ABM 2 é instável. O retorno do
capital é o lucro realizado do fundo, que oscila de um trimestre para outro,
e essas regras o levam quase direto às crenças; o custo do capital das firmas
e o consumo oscilam junto, e os erros na FBCF ficam de 56% a 84% maiores que
os do AR(1) em 4 e 8 trimestres. Com heurísticas, as famílias ainda trocam de
regra em bloco. No ABM 1, em que o retorno é o produto marginal, as mesmas
regras dão os melhores resultados para a FBCF.

As tabelas completas e as previsões registradas para 2026-2028 estão no
[README da previsão](../README.md).

## Como rodar

Da pasta `Econometria/`, com as dependências de `Python/requirements.txt`:

```bash
python Python/macroeconomia/Forecast/Brasil/2013T4-2026T2/abm2_sem_leiloeiro/experimentos_mercados.py   # longo prazo e sensibilidade (cerca de 10 minutos)
python Python/macroeconomia/Forecast/Brasil/2013T4-2026T2/comparacao.py --processos 4 --modelos abm2_eq abm2_apr abm2_heu abm2_inf abm2_aten
python -m unittest discover -s Python/macroeconomia/Forecast/Brasil/2013T4-2026T2/abm2_sem_leiloeiro -v
```

## Arquivos

| Arquivo | Conteúdo |
|---|---|
| `descentralizada.py` | a economia sem leiloeiro: firmas, preços, salários, busca, mercado de bens e fundo; a referência walrasiana com os mesmos fundamentos |
| `previsao_descentralizada.py` | o ABM no protocolo de previsão: aquecimento, história que reproduz PIB, gasto e desemprego, choques e réplicas |
| `experimentos_mercados.py` | longo prazo sem choques agregados e sensibilidade às regras das firmas |
| `test_*.py` | 21 testes |
| `resultados/`, `figuras/` | tabelas e figuras |

As famílias e as regras de expectativas vêm de `../abm1_com_leiloeiro/`.

## Limitações e próximos passos

O retorno das famílias é o lucro realizado do fundo, que oscila de um
trimestre para outro, e as regras de heurísticas e de atenção limitada o
levam quase direto às crenças e ao custo do capital das firmas. Suavizar o
retorno que entra nas crenças, ou dar às firmas um custo do capital de longo
prazo, é o próximo ajuste.

Na história guiada pelos dados, os dois ABMs explicam a queda do PIB pelo
crescimento da produtividade, e o ABM 2 explica o desemprego pela separação.
Numa recessão, a produtividade cai, o capital por unidade de eficiência sobe
e o retorno do capital cai. No ABM 2 com heurísticas, as famílias que levam o
retorno corrente às crenças baixam o custo do capital das firmas, e o
investimento do modelo sobe na recessão de 2015 e cai depois, justamente
quando nos dados ele se recuperava. Falta o canal de demanda e de crédito que
fez o investimento brasileiro cair em 2015-2016, e faltam também a entrada e
a saída de firmas e a política monetária, que fazem o desemprego brasileiro
oscilar muito mais do que no modelo.

A margem que aparece depende do teto que as firmas se permitem, e a
tecnologia é calibrada pela participação do trabalho medida nos dados, que
já inclui as margens da economia; com a margem do modelo, a participação cai
para 51%. Calibrar o teto com margens medidas no Brasil e recalibrar a
tecnologia são extensões naturais.

Depois disso, a ideia é levar os dois ABMs e o equilíbrio geral para vários
setores com a matriz insumo-produto e as Tabelas de Recursos e Usos do IBGE
(agregadas em cerca de 12 setores). No equilíbrio geral, firmas heterogêneas
com variedades CES e uma rede de insumos calibrada na matriz do IBGE, como em
Bernard, Moxnes e Saito (2019) e Baqaee e Farhi (2019), determinam o fluxo de
cada família para cada firma e de cada firma para cada fornecedor, e a matriz
de contabilidade social sai completa. No ABM, firmas por setor, mercados
descentralizados, um banco e um livro-razão de partidas dobradas, no espírito
dos modelos *stock-flow consistent* (Godley e Lavoie, 2007; Caiani et al.,
2016) e do ABM da Áustria de Poledna et al. (2023), fazem de todo agregado
uma soma de linhas do livro. Com isso dá para comparar a rede densa de
transações do equilíbrio com a rede esparsa que aparece no ABM, e as duas com
a matriz do IBGE.

As famílias formam as políticas com o risco de desemprego da PNAD, e não com
o que vivem na simulação; a tabela de políticas supõe o perfil de
transferências do estado estacionário; e as regras de crenças fixas e de
atenção limitada conhecem o equilíbrio por definição.

## Referências

- Baqaee, D. R. e Farhi, E. (2019). The Macroeconomic Impact of Microeconomic Shocks: Beyond Hulten's Theorem. *Econometrica*, 87(4), 1155-1203.
- Bernard, A. B., Moxnes, A. e Saito, Y. U. (2019). Production Networks, Geography, and Firm Performance. *Journal of Political Economy*, 127(2), 639-688.
- Caiani, A., Godin, A., Caverzasi, E., Gallegati, M., Kinsella, S. e Stiglitz, J. E. (2016). Agent Based-Stock Flow Consistent Macroeconomics: Towards a Benchmark Model. *Journal of Economic Dynamics and Control*, 69, 375-408.
- Delli Gatti, D., Desiderio, S., Gaffeo, E., Cirillo, P. e Gallegati, M. (2011). *Macroeconomics from the Bottom-up*. Springer.
- Godley, W. e Lavoie, M. (2007). *Monetary Economics: An Integrated Approach to Credit, Money, Income, Production and Wealth*. Palgrave Macmillan.
- Gouvea, S. (2007). Price Rigidity in Brazil: Evidence from CPI Micro Data. Banco Central do Brasil, *Working Paper Series*, 143.
- Lengnick, M. (2013). Agent-Based Macroeconomics: A Baseline Model. *Journal of Economic Behavior & Organization*, 86, 102-120.
- Poledna, S., Miess, M. G., Hommes, C. e Rabitsch, K. (2023). Economic Forecasting with an Agent-Based Model. *European Economic Review*, 151, 104306.
- As referências das regras de expectativas estão no [README do ABM 1](../abm1_com_leiloeiro/README.md#referências).
