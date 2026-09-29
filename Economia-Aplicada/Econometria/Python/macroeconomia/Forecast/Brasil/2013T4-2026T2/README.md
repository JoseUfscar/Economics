# Previsão fora da amostra: Brasil, 2013T4-2026T2

Modelos de equilíbrio geral e modelos baseados em agentes, calibrados para o
Brasil, comparados com modelos estatísticos simples na previsão de dados que
eles não viram. As origens das previsões vão de 2013T4 a 2026T2, com dados
desde 1996.

| Pasta | Modelo |
|---|---|
| [`referencias/`](referencias/README.md) | média histórica, AR(1) e VAR(1) |
| [`dsge/`](dsge/README.md) | equilíbrio geral estocástico: o Ramsey com governo de [`Politicas/Lei-15270/equilibrio_geral/`](../../../Politicas/Lei-15270/equilibrio_geral/README.md), com choques |
| [`dsge_busca/`](dsge_busca/README.md) | o mesmo com margem, busca no mercado de trabalho e salário rígido |
| [`abm1_com_leiloeiro/`](abm1_com_leiloeiro/README.md) | ABM com 20 mil famílias e leiloeiro walrasiano |
| [`abm2_sem_leiloeiro/`](abm2_sem_leiloeiro/README.md) | ABM sem leiloeiro: firmas, preços, salários e busca |

O protocolo comum (`protocolo.py`, `avaliacao.py`, `espaco_estados.py`), a
comparação (`comparacao.py`), os resultados e as figuras ficam nesta pasta.

Os quatro modelos estruturais formam dois pares com a mesma calibração:

| | Equilíbrio geral (agente representativo, linearizado) | Modelo baseado em agentes |
|---|---|---|
| Sem desemprego nem margem | equilíbrio geral (`dsge/`) | ABM 1, com leiloeiro (`abm1_com_leiloeiro/`) |
| Com desemprego de busca e margem de 10% | equilíbrio geral com busca (`dsge_busca/`) | ABM 2, sem leiloeiro (`abm2_sem_leiloeiro/`) |

Dentro de cada par, os modelos diferem em várias coisas ao mesmo tempo:
famílias heterogêneas contra agente representativo, solução não linear contra
linearizada, regras de expectativas, a forma de estimar os choques (máxima
verossimilhança no equilíbrio geral; um AR(1) para cada choque inferido da
história nos ABMs) e as séries observadas (as quatro das Contas Nacionais no
equilíbrio geral; só o PIB, o gasto e, no ABM 2, o desemprego nos ABMs). No
par de baixo, só o ABM 2 tira o leiloeiro. A comparação mostra como cada
modelo prevê, mas não isola o efeito de uma dessas diferenças. O par de baixo
prevê também o desemprego.

## Protocolo

- **Dados.** Contas Nacionais Trimestrais do IBGE, de 1996T1 a 2026T2 (índices
  de volume com ajuste sazonal). As variáveis são o crescimento trimestral de
  PIB, consumo das famílias, FBCF e consumo do governo e, desde 2012, a
  variação da taxa de desemprego da PNAD Contínua (tabela 4099). A PNAD não
  tem ajuste sazonal oficial; em cada origem, a taxa é dessazonalizada por
  decomposição clássica (média móvel centrada 2x4 e um fator fixo por
  trimestre do ano) só com os dados até a origem. O realizado, com que as
  previsões são comparadas, é a taxa dessazonalizada com a amostra inteira.
- **Origens.** De 2013T4 a 2026T1, uma por trimestre. Em cada origem T, cada
  modelo é reestimado só com os dados até T (janela crescente desde 1996) e
  prevê o crescimento acumulado de T+1 a T+h, para h = 1 a 8 trimestres. O
  desemprego é avaliado a partir de 2014T4, quando há três anos de PNAD; antes
  disso, a dessazonalização e as estimativas se apoiam em menos de doze
  trimestres (em 2013T4, o AR(1) da variação do desemprego sai explosivo).
- **Calibração.** A parte estrutural dos modelos usa só dados anuais até o
  ano de T menos 2, porque PWT, Ipea e IBGE saem com defasagem, e os ABMs usam
  a PNAD só até T. Testes conferem que alterar qualquer dado posterior à
  origem, inclusive a PNAD sem ajuste, não muda nenhuma previsão.
- **Medidas.** Erro quadrático médio (RMSE) relativo ao AR(1); CRPS, que
  avalia a previsão de densidade inteira; cobertura do intervalo de 90%; o
  teste de Diebold e Mariano (1995), com a correção de Harvey, Leybourne e
  Newbold (1997) para amostras pequenas; e, para a média e o VAR(1), que estão
  aninhados com o AR(1), o teste de Clark e West (2007). Como cada tabela
  compara muitos modelos, os p-valores também são corrigidos pelo método de
  Holm (1979) entre os modelos de cada variável e horizonte.

São 50 origens com realizado em h = 1 e 43 em h = 8 (46 e 39 no
desemprego). Como a pandemia domina qualquer medida de erro, todos os
resultados aparecem também sem as janelas de previsão que tocam 2020T2 a
2020T4. Os dados são os revisados de hoje, e não os que existiam em cada
origem; o efeito disso pode ser diferente entre os modelos, porque eles usam
séries e defasagens diferentes.

## Modelos

As referências são estimadas por mínimos quadrados em cada origem: a média
histórica do crescimento (passeio aleatório com deriva no nível), um AR(1)
para cada variável e um VAR(1) com as quatro variáveis das Contas Nacionais.
A média e o AR(1) preveem também o desemprego, com a amostra que ele tem
(desde 2012). O VAR(1) não, porque perderia 16 anos das outras séries.

O equilíbrio geral (`dsge/`) é o modelo de Ramsey com governo da parte 1 de
`Politicas/Lei-15270/equilibrio_geral/`, em tempo discreto trimestral e com
três choques. O crescimento da produtividade do trabalho oscila em torno de
$g$, $\log \Gamma_t = g/4 + u_t$, com $u_t$ AR(1), o choque permanente de
Aguiar e Gopinath (2007); a produtividade transitória entra como
$Y_t = e^{z_t} K_t^\alpha (A_t L_t)^{1-\alpha}$, com $z_t$ AR(1); e o gasto
público, como $G_t/(A_t L_t) = \bar g\, e^{s_t}$, com $s_t$ AR(1). A família
escolhe o consumo pela equação de Euler

$$
x_t^{-\theta} = e^{-\rho/4}\, E_t\!\left[x_{t+1}^{-\theta}\left(1 + \tfrac14 (1-\tau_k)(R_{t+1} - \delta)\right)\right],
$$

com $x = C/L$. Quando o período tende a zero, o estado estacionário e a
velocidade de convergência tendem aos de `modelo.py` (há um teste para isso).
O modelo é linearizado em logaritmos e resolvido pelo método de Klein (2000).
Os parâmetros estruturais ($\alpha$, $\delta$, $n$, $g$, $\tau_k$, $G/Y$,
$\theta = 2$ e $\rho$ para reproduzir $K/Y$) vêm da calibração anual de
`Politicas/Lei-15270/equilibrio_geral/calibracao.py`, refeita em cada origem.
Os seis parâmetros dos choques e os quatro erros de medida são estimados por
máxima verossimilhança, com o filtro de Kalman.

Na versão com tendência trimestral, o crescimento de tendência $g + n$ passa
a reproduzir o crescimento médio do PIB trimestral até a origem, em vez da
tendência anual desde 2000, e cada série tem a própria média de crescimento
(o gasto real, por exemplo, cresce menos que o PIB nos dados, porque o preço
relativo dos serviços públicos sobe). Com as mesmas médias que a média
histórica, a comparação entre os dois mede o que a dinâmica do modelo
acrescenta.

O equilíbrio geral com busca (`dsge_busca/`) acrescenta ao modelo a margem de
10% sobre o custo marginal que aparece no ABM 2, busca no mercado de trabalho,
$N_t = (1-s_t)N_{t-1} + f_t(1-N_{t-1})$, com a separação e o desemprego de
longo prazo da mesma cadeia trimestral da PNAD do ABM, e um salário rígido,
$\log w_t = \gamma(\log w_{t-1} - u_t) + (1-\gamma)\log(\omega\,\mathrm{PMgL}_t)$
(Hall, 2005; Blanchard e Galí, 2010), com a rigidez $\gamma$ estimada. As
firmas abrem vagas até o custo de contratar (14% do salário de um trimestre,
Silva e Toledo, 2009; vaga preenchida com probabilidade 0,7 por trimestre,
den Haan, Ramey e Watson, 2000) igualar o valor do trabalhador. Um quarto
choque, na taxa de separação, dá ao desemprego uma fonte própria de variação.
São nove parâmetros de choques e rigidez e cinco erros de medida, por máxima
verossimilhança; o desemprego entra como observação faltante antes de 2012.
Como a tecnologia é a mesma dos outros modelos, a margem reduz a participação
do trabalho para cerca de 50%, abaixo dos 54,9% dos dados.

O [ABM 1](abm1_com_leiloeiro/README.md) entra com as cinco regras de
expectativas; o estado das famílias na origem sai de uma simulação da
história desde 1996 guiada pelos dados, e a previsão, de 200 simulações. O
[ABM 2](abm2_sem_leiloeiro/README.md) usa a mesma calibração, com os
desempregados fora da produção, 100 anos de aquecimento sem choques e uma
história que reproduz também a taxa de desemprego desde 2012.

## Resultados

As tabelas mostram o RMSE relativo ao AR(1): abaixo de 1, o modelo errou
menos que o AR(1). Em negrito, as diferenças significativas a 5% pelo teste
de Diebold-Mariano; com †, as que continuam significativas depois da
correção de Holm. Para a média e o VAR(1), a marca ᶜ indica que o teste de
Clark-West rejeita, a 5%, que o modelo maior (o AR(1) contra a média; o
VAR(1) contra o AR(1)) não acrescenta nada. As tabelas completas, com todos
os horizontes, o CRPS e os p-valores, estão em `resultados/avaliacao.csv` e
`resultados/avaliacao_sem_pandemia.csv`, e as previsões de cada modelo ao
lado do realizado, em `resultados/previsoes_contra_realizado.csv`.

### Equilíbrio geral contra as referências

| Variável | Modelo | h=1 | h=4 | h=8 | h=1 sem pandemia | h=4 sem pandemia | h=8 sem pandemia |
|---|---|---|---|---|---|---|---|
| PIB | Média | 0,88 | 0,90 | 0,95 | 1,07ᶜ | 1,05 | 1,03 |
| PIB | VAR(1) | 1,15 | 1,13 | 1,07 | 0,92ᶜ | 0,95 | 0,97 |
| PIB | Equilíbrio geral | 0,85 | 0,95 | 1,05 | **1,11** | 1,16 | 1,16 |
| Consumo das famílias | Média | 0,88 | 0,92 | 0,95 | 1,08ᶜ | 1,05 | 1,03 |
| Consumo das famílias | VAR(1) | 1,11 | 1,09 | 1,05 | 0,95ᶜ | 0,95ᶜ | 0,98 |
| Consumo das famílias | Equilíbrio geral | 0,88 | 0,92 | 0,97 | **1,08** | 1,06 | 1,07 |
| FBCF | Média | 0,96 | 1,01 | 1,02 | 1,04 | 1,09 | 1,06 |
| FBCF | VAR(1) | 1,25 | 1,38 | 1,20 | 0,90ᶜ | 0,94 | 0,96ᶜ |
| FBCF | Equilíbrio geral | 0,94 | 1,03 | 1,05 | 1,04 | 1,13 | 1,10 |
| Consumo do governo | Média | 0,96 | 1,00 | 0,99 | 0,88 | 0,96 | 0,97 |
| Consumo do governo | VAR(1) | 1,15 | 1,04 | 1,03 | 1,18 | 1,06 | 1,05 |
| Consumo do governo | Equilíbrio geral | 0,93 | 1,16 | 1,38 | 0,95 | 1,28 | 1,49 |
| PIB | Equilíbrio geral, tendência trimestral | 0,83 | 0,88 | 0,94 | 1,03 | 1,03 | 1,02 |
| Consumo das famílias | Equilíbrio geral, tendência trimestral | 0,88 | 0,91 | 0,95 | 1,07 | 1,04 | 1,04 |
| FBCF | Equilíbrio geral, tendência trimestral | 0,93 | 1,00 | 1,02 | 1,02 | 1,08 | 1,05 |
| Consumo do governo | Equilíbrio geral, tendência trimestral | **0,88** | **0,89** | **0,92** | **0,85** | **0,88** | 0,92 |

![RMSE relativo ao AR(1)](figuras/rmse_relativo.png)

Com 50 origens, só diferenças grandes seriam detectáveis, e quase nenhuma
aparece. A exceção pelo teste de Diebold-Mariano é o equilíbrio geral com
tendência trimestral no consumo do governo, 8% a 15% melhor que o AR(1), mas
nenhuma diferença desta tabela continua significativa depois da correção de
Holm.

A pandemia inverte o ranking. Com ela, o AR(1) e o VAR(1) sofrem porque
extrapolam a queda de 2020T2 e a recuperação seguinte; a média e o equilíbrio
geral, que voltam logo à tendência, erram menos. Sem ela, o VAR(1) passa a ser
o melhor nos horizontes curtos, e o teste de Clark-West indica que ele
acrescenta informação ao AR(1) no PIB, no consumo e na FBCF em um trimestre.
O equilíbrio geral erra de 6% a 16% mais que o AR(1) no PIB e no consumo.

A maior parte da desvantagem do equilíbrio geral vem da tendência. Todos os
modelos superestimaram o crescimento desde 2014, mas ele mais: sem a
pandemia, o viés médio no PIB em 8 trimestres é de −3,4 p.p., contra −2,7 do
AR(1). A tendência do modelo sai da calibração anual (3,6% a 3,8% ao ano nas
origens de 2013 a 2016, com dados de 2000 em diante), enquanto as referências
usam a média desde 1996. Com a tendência trimestral, o mesmo modelo passa a
ser o melhor na amostra completa para o PIB de h = 1 a h = 5 (17% a 9% menos
erro que o AR(1)) e, sem a pandemia, erra só 2% a 3% mais que o AR(1).
Contra a média histórica, que tem as mesmas médias, ele erra de 1% a 5% menos
no PIB.

O crescimento balanceado custa caro no consumo do governo. O modelo obriga o
gasto real a crescer no ritmo do PIB, mas nos dados ele cresceu 1,7% ao ano,
contra 2,3% do PIB, porque o preço relativo dos serviços públicos sobe. Daí o
viés de −4,0 p.p. em 8 trimestres, sem a pandemia (AR(1): −1,6). Com a média
própria de cada série, o problema desaparece, e o consumo do governo passa a
ser a variável em que o modelo mais ganha.

Os intervalos de 90% cobrem menos do que deveriam em horizontes longos em
todos os modelos (de 70% a 81% do PIB realizado em h = 8). E os parâmetros
dos choques mudam quando 2020T2 entra na amostra: a persistência do choque de
gasto cai de 0,99 para −0,04, e a do choque de tendência, de 0,57 para −0,35
(`resultados/parametros_dsge.csv`), porque um trimestre em que todas as
séries caem de 8% a 17% pesa muito numa verossimilhança normal. No equilíbrio
geral com busca, a rigidez do salário estimada cai de cerca de 0,5 para zero.

![PIB: crescimento em quatro trimestres, realizado e previsto](figuras/previsoes_pib.png)

### Os quatro modelos estruturais

RMSE relativo ao AR(1), com a amostra toda e sem as janelas da pandemia, em
4 trimestres:

| Modelo | PIB | PIB sem pandemia | Consumo | Consumo sem pandemia | FBCF | FBCF sem pandemia | Desemprego | Desemprego sem pandemia |
|---|---|---|---|---|---|---|---|---|
| Média | 0,90 | 1,05 | 0,92 | 1,05 | 1,01 | 1,09 | 1,03 | 1,22ᶜ |
| VAR(1) | 1,13 | 0,95 | 1,09 | 0,95ᶜ | 1,38 | 0,94 | — | — |
| Equilíbrio geral (tend. trimestral) | 0,88 | 1,03 | 0,91 | 1,04 | 0,99 | 1,08 | — | — |
| Equilíbrio geral com busca (tend. trimestral) | 0,91 | 1,04 | 0,91 | 1,04 | 1,07 | 1,14 | 0,92 | 0,95 |
| ABM 1: crenças fixas | 1,02 | 1,00 | 0,98 | 0,96 | 1,09 | 1,08 | — | — |
| ABM 1: aprendizado | 1,03 | 1,02 | 0,99 | 1,00 | 1,14 | 1,06 | — | — |
| ABM 1: heurísticas | 0,99 | 0,95 | 0,99 | 1,13 | 1,33 | 0,82 | — | — |
| ABM 1: informação rígida | 1,03 | 1,03 | 0,99 | 0,98 | 1,16 | 1,11 | — | — |
| ABM 1: atenção limitada | 0,99 | 0,95 | 0,93 | 0,99 | 1,29 | 0,99 | — | — |
| ABM 2: crenças fixas | 0,94 | 1,03 | 0,94 | 0,98 | 1,13 | 1,07 | 1,04 | 1,18 |
| ABM 2: aprendizado | 0,95 | 1,00 | 0,95 | 0,99 | 1,13 | 1,10 | 0,99 | 1,14 |
| ABM 2: heurísticas | 1,03 | **1,17** | 1,09 | **1,35** | **1,57** | **1,82** | 1,05 | 1,17 |
| ABM 2: informação rígida | 0,91 | 1,03 | 0,89 | 0,97 | 1,01 | 1,05 | 1,02 | 1,17 |
| ABM 2: atenção limitada | 0,94 | 1,05 | 1,19 | **1,43** | **1,67**† | **1,84** | 1,03 | 1,17 |

Em 8 trimestres:

| Modelo | PIB | PIB sem pandemia | Consumo | Consumo sem pandemia | FBCF | FBCF sem pandemia | Desemprego | Desemprego sem pandemia |
|---|---|---|---|---|---|---|---|---|
| Média | 0,95 | 1,03 | 0,95 | 1,03 | 1,02 | 1,06 | 0,86 | 0,96ᶜ† |
| VAR(1) | 1,07 | 0,97 | 1,05 | 0,98 | 1,20 | 0,96ᶜ | — | — |
| Equilíbrio geral (tend. trimestral) | 0,94 | 1,02 | 0,95 | 1,04 | 1,01 | 1,05 | — | — |
| Equilíbrio geral com busca (tend. trimestral) | 0,97 | 1,03 | 0,95 | 1,04 | 1,09 | 1,12 | 0,72 | 0,75 |
| ABM 1: crenças fixas | 1,02 | 1,01 | 0,97 | 0,96 | 1,08 | 1,07 | — | — |
| ABM 1: aprendizado | 1,04 | 1,03 | 1,00 | 1,01 | 1,15 | **1,05** | — | — |
| ABM 1: heurísticas | 1,00 | 0,96 | 1,02 | 1,11 | 1,17 | 0,85 | — | — |
| ABM 1: informação rígida | 1,04 | 1,04 | 1,00 | 0,99 | **1,17** | 1,08 | — | — |
| ABM 1: atenção limitada | 1,00 | 0,96 | 0,96 | 1,00 | 1,18 | 0,98 | — | — |
| ABM 2: crenças fixas | 0,98 | 1,00 | 0,95 | 0,98 | **1,06** | 1,04 | 0,77 | 0,88 |
| ABM 2: aprendizado | 0,95 | 0,96 | 0,95 | 0,97 | 1,05 | 1,06 | 0,75 | 0,83 |
| ABM 2: heurísticas | 1,04 | **1,08** | 1,09 | **1,26** | **1,60**† | **1,56**† | 0,90 | 0,92 |
| ABM 2: informação rígida | 0,90 | 0,96 | 0,91 | 0,97 | 0,99 | 1,04 | 0,82 | 0,95 |
| ABM 2: atenção limitada | 0,97 | **1,05**† | **1,23** | 1,35 | **1,60** | 1,57 | 0,79 | 0,89 |

O desemprego é a variação da taxa entre a origem e o alvo; a referência é o
AR(1) dela. O consumo do governo é exógeno nos ABMs e fica fora da tabela.

![ABM 2 e equilíbrio geral com busca, sem a pandemia](figuras/rmse_abm2_sem_pandemia.png)

Nenhum modelo domina: o melhor muda com a variável, o horizonte e a amostra,
e quase nenhuma diferença é significativa. Na amostra completa, o equilíbrio
geral com tendência trimestral é o melhor para o PIB até h = 5, e o ABM 2 com
informação rígida, de h = 6 a h = 8; para o consumo, o ABM 2 com informação
rígida é o melhor de h = 3 a h = 8 (11% menos erro que o AR(1) em 4
trimestres e 9% menos em 8). Sem a pandemia, o VAR(1) é o melhor para o PIB e
o consumo nos horizontes curtos, e o ABM 1 com heurísticas é o melhor para a
FBCF em todos os horizontes.

Pôr margem e busca no equilíbrio geral não melhora a previsão das Contas
Nacionais. Com a tendência trimestral e a amostra toda, o RMSE do modelo com
busca é de 3% a 7% maior que o do modelo sem busca no PIB e de 7% a 12% maior
na FBCF, de 1 a 8 trimestres. O que ele acrescenta é o desemprego.

No desemprego, os modelos com busca ganham em dois anos. Em um trimestre, o
AR(1) é o melhor, porque o desemprego é muito persistente. Em 8 trimestres, o
equilíbrio geral com busca erra 28% menos que o AR(1) (25% sem a pandemia),
o menor erro entre os modelos, e o ABM 2 com aprendizado, 25% menos (17%),
sem significância. Em um ano, só o equilíbrio geral com busca erra menos que
o AR(1) (8% menos). A razão é a mesma nos dois modelos: eles trazem o
desemprego de volta à média da PNAD, e as referências extrapolam a tendência
recente. Sem a pandemia, o viés em 8 trimestres é de −0,64 p.p. no equilíbrio
geral com busca e de −1,34 p.p. no ABM 2 com aprendizado, contra −2,34 p.p.
no AR(1).

Com crenças fixas, aprendizado e informação rígida, o ABM 2 fica no nível do
par ou um pouco melhor no PIB e no consumo, e, sem a pandemia, erra menos que
ele na FBCF (de 1,04 a 1,10 vez o AR(1), contra 1,12 a 1,14). Com heurísticas
e atenção limitada, o ABM 2 é instável: são os piores modelos para a FBCF, com
erros de 56% a 84% maiores que os do AR(1) em 4 e 8 trimestres, e algumas
dessas diferenças continuam significativas depois da correção de Holm. O
retorno do capital do ABM 2 é o lucro realizado do fundo, que oscila de um
trimestre para outro, e essas duas regras o levam quase direto às crenças: o
custo do capital das firmas e o consumo oscilam junto. Com heurísticas, as
famílias ainda trocam de regra em bloco (todas passam para a regra ingênua e,
poucos trimestres depois, para a fundamentalista). No ABM 1, com o retorno
dado pelo produto marginal, as mesmas regras dão os melhores resultados para
a FBCF sem a pandemia.

Os intervalos de 90% do desemprego cobrem de 65% a 77% dos realizados em 4
trimestres, nos modelos com busca e no AR(1) (70%): a incerteza sobre o
desemprego é subestimada por todos.

![Equilíbrio geral com e sem busca](figuras/rmse_busca.png)

Os resultados do ABM 1 estão no [README dele](abm1_com_leiloeiro/README.md#previsão-fora-da-amostra),
e os do ABM 2, no [dele](abm2_sem_leiloeiro/README.md#previsão-fora-da-amostra).

![ABM 1 e equilíbrio geral, sem a pandemia](figuras/rmse_abm_sem_pandemia.png)

## Previsões registradas

Previsões feitas com os dados até 2026T2, gravadas em
`resultados/previsao_registrada_202602.csv` para serem comparadas com os
dados que o IBGE ainda vai divulgar. Crescimento acumulado desde 2026T2, em
%, e variação da taxa de desemprego desde 2026T2 (5,3%, dessazonalizada), em
p.p. O ABM 2 com heurísticas e com atenção limitada fica de fora: pelo motivo
descrito acima, as previsões de consumo e FBCF dessas duas regras oscilam
demais para serem levadas a sério (na última origem, uma delas previa queda
de 35% na FBCF em seis trimestres).

| Modelo | PIB até 2026T4 | PIB até 2027T4 | Consumo até 2026T4 | Consumo até 2027T4 | FBCF até 2027T4 | Desemprego até 2026T4 | Desemprego até 2027T4 |
|---|---|---|---|---|---|---|---|
| Média | 1,14 | 3,42 | 1,23 | 3,70 | 3,17 | −0,08 | −0,23 |
| AR(1) | 1,13 | 3,39 | 1,21 | 3,63 | 3,23 | −0,31 | −0,63 |
| VAR(1) | 1,23 | 3,49 | 1,37 | 3,78 | 3,04 | — | — |
| Equilíbrio geral | 0,97 | 2,93 | 0,98 | 2,92 | 2,61 | — | — |
| Equilíbrio geral, tendência trimestral | 1,06 | 3,24 | 1,15 | 3,45 | 2,94 | — | — |
| Equilíbrio geral com busca | 1,11 | 2,96 | 0,99 | 2,94 | 2,71 | −0,04 | +0,49 |
| Equilíbrio geral com busca, tendência trimestral | 1,23 | 3,32 | 1,17 | 3,49 | 3,20 | −0,03 | +0,50 |
| ABM 1: crenças fixas | 1,14 | 3,35 | 1,10 | 3,28 | 3,95 | — | — |
| ABM 1: aprendizado | 0,86 | 2,49 | 1,04 | 3,03 | 0,38 | — | — |
| ABM 1: heurísticas | 0,95 | 3,07 | 1,33 | 3,89 | 0,43 | — | — |
| ABM 1: informação rígida | 0,84 | 2,45 | 1,08 | 3,15 | −0,16 | — | — |
| ABM 1: atenção limitada | 1,11 | 3,27 | 1,09 | 3,33 | 3,14 | — | — |
| ABM 2: crenças fixas | 1,51 | 3,49 | 1,16 | 3,56 | 1,12 | −0,66 | +0,25 |
| ABM 2: aprendizado | 0,40 | 2,17 | 1,22 | 3,74 | 1,07 | +1,22 | +2,72 |
| ABM 2: informação rígida | 2,72 | 3,03 | 1,39 | 4,10 | −3,83 | +0,73 | +2,43 |

Com o desemprego no menor nível da série, os modelos com busca preveem que
ele suba até 2027T4: 0,5 p.p. no equilíbrio geral com busca, 2,4 e 2,7 p.p.
no ABM 2 com informação rígida e com aprendizado e 0,3 p.p. com crenças
fixas. O arquivo traz também o desvio-padrão de cada previsão, que é grande
(de 4 a 7 p.p. para o PIB até 2027T4 e de 1,4 a 3,8 p.p. para o
desemprego), e a coluna `efeito_lei`: o efeito da Lei 15.270/2025 pelo modelo
contínuo de `Politicas/Lei-15270/equilibrio_geral/`, com o aumento de
$\tau_k$ anunciado em março de 2025. Ele é pequeno nesse horizonte, −0,05
p.p. no PIB e −0,08 p.p. no consumo até 2027T4, porque o capital se ajusta
devagar.

## Como rodar

Da pasta `Econometria/`, com as dependências de `Python/requirements.txt`:

```bash
python Python/macroeconomia/Forecast/Brasil/2013T4-2026T2/comparacao.py --processos 4    # tudo, com 4 núcleos
python Python/macroeconomia/Forecast/Brasil/2013T4-2026T2/comparacao.py --modelos eg_busca abm2_apr   # só alguns modelos
python Python/macroeconomia/Forecast/Brasil/2013T4-2026T2/comparacao.py --sem-reestimar  # só tabelas e figuras
python Python/macroeconomia/rodar_testes.py Forecast   # os testes de todas as pastas da previsão
```

As chaves dos modelos são `media`, `ar1`, `var1`, `eg`, `eg_trim`,
`eg_busca`, `eg_busca_trim`, `abm_eq`, `abm_apr`, `abm_heu`, `abm_inf`,
`abm_aten` (ABM 1) e `abm2_eq`, `abm2_apr`, `abm2_heu`, `abm2_inf`,
`abm2_aten` (ABM 2). Com `--modelos`, as previsões dos outros vêm de
`resultados/previsoes.csv`. Por origem, num núcleo: segundos para as
referências, de meio minuto a um minuto e meio para cada equilíbrio geral e
cerca de meio minuto para cada variante de ABM. Tudo, com 4 núcleos, leva de
2 a 3 horas.

Os dados trimestrais ficam em [`dados/brasil/`](../../../../../dados/brasil/README.md),
com o script que os baixa.

## Arquivos

| Arquivo ou pasta | Conteúdo |
|---|---|
| `protocolo.py` | dados, dessazonalização do desemprego só com o passado, calibração em cada origem e previsões sem olhar o futuro |
| `espaco_estados.py` | filtro de Kalman (com observações faltantes) e previsão do crescimento acumulado, comuns aos modelos lineares |
| `avaliacao.py` | RMSE, CRPS, cobertura e testes de Diebold-Mariano, Clark-West e Holm |
| `comparacao.py` | roda o protocolo, em paralelo se pedido, e grava os resultados e as figuras |
| `referencias/` | média, AR(1) e VAR(1) |
| `dsge/` | equilíbrio geral estocástico: estado estacionário, linearização, solução de Klein, espaço de estados e máxima verossimilhança |
| `dsge_busca/` | o mesmo com margem, busca, salário rígido e choque de separação |
| `abm1_com_leiloeiro/`, `abm2_sem_leiloeiro/` | os dois ABMs, com os próprios experimentos e testes |
| `test_*.py` (aqui e em cada pasta) | 54 testes nas pastas de referências, DSGEs e protocolo: solução exata de Brock-Mirman, limite contínuo, precisão da linearização, estado estacionário e dinâmica do modelo com busca, verossimilhança do Kalman contra a normal multivariada e com dados faltantes, recuperação dos parâmetros em dados simulados, comparação com o `statsmodels`, dessazonalização, CRPS, tamanho dos testes de Diebold-Mariano e Clark-West, correção de Holm e ausência de dados do futuro |
| `resultados/` | previsões, avaliações contra o AR(1) e contra a média histórica, parâmetros estimados por origem, previsões lado a lado com o realizado (`previsoes_contra_realizado.csv`) e previsões registradas |
| `figuras/` | erros relativos por horizonte e previsões do PIB |

## Limitações

Nenhum modelo tem setor externo. A diferença entre o PIB e a soma de
consumo, FBCF e gasto fica nos erros de medida (no ABM 2, na variação dos
estoques). O primeiro equilíbrio geral e o ABM 1 também não têm desemprego, e
o desemprego de longo prazo dos modelos com busca é a média da PNAD até a
origem; quando o desemprego fica muito tempo longe dela, como em 2016-2021 e
desde 2023, os dois modelos preveem que ele volte. Todos os modelos supõem
choques normais, e a pandemia está longe disso. A série de consumo do governo
tem um salto atípico no começo, −16% em 1996T4 e +12% em 1997T1, que entra em
todas as amostras. E a referência mais exigente para o Brasil, as
expectativas do Focus, ainda não está na comparação.

## Referências

- Aguiar, M. e Gopinath, G. (2007). Emerging Market Business Cycles: The Cycle Is the Trend. *Journal of Political Economy*, 115(1), 69-102.
- Blanchard, O. e Galí, J. (2010). Labor Markets and Monetary Policy: A New Keynesian Model with Unemployment. *American Economic Journal: Macroeconomics*, 2(2), 1-30.
- Clark, T. E. e West, K. D. (2007). Approximately Normal Tests for Equal Predictive Accuracy in Nested Models. *Journal of Econometrics*, 138(1), 291-311.
- den Haan, W. J., Ramey, G. e Watson, J. (2000). Job Destruction and Propagation of Shocks. *American Economic Review*, 90(3), 482-498.
- Diebold, F. X. e Mariano, R. S. (1995). Comparing Predictive Accuracy. *Journal of Business & Economic Statistics*, 13(3), 253-263.
- Gneiting, T. e Raftery, A. E. (2007). Strictly Proper Scoring Rules, Prediction, and Estimation. *Journal of the American Statistical Association*, 102(477), 359-378.
- Hall, R. E. (2005). Employment Fluctuations with Equilibrium Wage Stickiness. *American Economic Review*, 95(1), 50-65.
- Harvey, D., Leybourne, S. e Newbold, P. (1997). Testing the Equality of Prediction Mean Squared Errors. *International Journal of Forecasting*, 13(2), 281-291.
- Holm, S. (1979). A Simple Sequentially Rejective Multiple Test Procedure. *Scandinavian Journal of Statistics*, 6(2), 65-70.
- Klein, P. (2000). Using the Generalized Schur Form to Solve a Multivariate Linear Rational Expectations Model. *Journal of Economic Dynamics and Control*, 24(10), 1405-1423.
- Silva, J. I. e Toledo, M. (2009). Labor Turnover Costs and the Cyclical Behavior of Vacancies and Unemployment. *Macroeconomic Dynamics*, 13(S1), 76-96.
