# Previsão fora da amostra: Brasil, 2013T4-2026T2

Compara modelos de equilíbrio geral e modelos baseados em agentes,
calibrados para o Brasil, com modelos estatísticos simples na tarefa mais
direta que existe para um modelo macroeconômico: prever dados que ele não
viu. As origens das previsões vão de 2013T4 a 2026T2, com dados desde 1996.

| Pasta | Modelo |
|---|---|
| [`referencias/`](referencias/README.md) | média histórica, AR(1) e VAR(1) |
| [`dsge/`](dsge/README.md) | equilíbrio geral estocástico: o Ramsey com governo de [`Politicas/Lei-15270/equilibrio_geral/`](../../../Politicas/Lei-15270/equilibrio_geral/README.md), com choques |
| [`dsge_busca/`](dsge_busca/README.md) | o mesmo com margem, busca no mercado de trabalho e salário rígido |
| [`abm1_com_leiloeiro/`](abm1_com_leiloeiro/README.md) | ABM com 20 mil famílias e leiloeiro walrasiano |
| [`abm2_sem_leiloeiro/`](abm2_sem_leiloeiro/README.md) | ABM sem leiloeiro: firmas, preços, salários e busca |

O protocolo comum (`protocolo.py`, `avaliacao.py`, `espaco_estados.py`), a
comparação (`comparacao.py`), os resultados e as figuras ficam nesta pasta.

São quatro modelos estruturais, em dois pares com os mesmos fundamentos:

| | Com leiloeiro ou equilíbrio | Sem leiloeiro |
|---|---|---|
| Sem desemprego nem margem | equilíbrio geral (`dsge/`) | ABM 1, com leiloeiro (`abm1_com_leiloeiro/`) |
| Com desemprego de busca e margem de 10% | equilíbrio geral com busca (`dsge_busca/`) | ABM 2, sem leiloeiro (`abm2_sem_leiloeiro/`) |

Dentro de cada linha, a diferença entre os dois mede o que muda quando os
preços deixam de vir de um equilíbrio e passam a sair das decisões dos
agentes. O par de baixo prevê também o desemprego.

## Protocolo

- **Dados:** Contas Nacionais Trimestrais do IBGE, de 1996T1 a 2026T2
  (índices de volume com ajuste sazonal). As variáveis são o crescimento
  trimestral de PIB, consumo das famílias, FBCF e consumo do governo e, desde
  2012, a variação da taxa de desemprego da PNAD Contínua (tabela 4099),
  dessazonalizada por decomposição clássica: média móvel centrada 2x4 e um
  fator fixo por trimestre do ano. Os fatores usam a amostra inteira, como a
  dessazonalização das Contas Nacionais que o IBGE publica hoje.
- **Origens:** de 2013T4 a 2026T1, uma por trimestre. Em cada origem T, cada
  modelo é reestimado só com os dados até T (janela crescente desde 1996) e
  prevê o crescimento acumulado de T+1 a T+h, para h = 1 a 8 trimestres.
- **Calibração sem olhar o futuro:** a parte estrutural dos modelos usa só
  dados anuais até o ano de T menos 2, porque PWT, Ipea e IBGE saem com
  defasagem, e o ABM usa a PNAD só até T. Testes conferem que alterar
  qualquer dado posterior à origem não muda nenhuma previsão.
- **Medidas:** erro quadrático médio (RMSE) relativo ao AR(1); CRPS, que
  avalia a previsão de densidade inteira; cobertura do intervalo de 90%; e o
  teste de Diebold e Mariano com a correção de Harvey, Leybourne e Newbold
  (1997) para amostras pequenas.

São 50 origens com realizado em h = 1 e 43 em h = 8. Como a pandemia domina
qualquer medida de erro, todos os resultados aparecem também sem as janelas
de previsão que tocam 2020T2 a 2020T4.

## Modelos

**Referências**, estimadas por mínimos quadrados em cada origem:

- **média histórica** do crescimento (passeio aleatório com deriva no nível);
- **AR(1)** para cada variável;
- **VAR(1)** com as quatro variáveis das Contas Nacionais.

A média e o AR(1) preveem também o desemprego, com a amostra que ele tem
(desde 2012). O VAR(1) não, porque perderia 16 anos das outras séries.

**Equilíbrio geral** (`dsge/`). É o modelo de Ramsey com governo da parte 1 de
`Politicas/Lei-15270/equilibrio_geral/`, escrito em tempo discreto trimestral e
com três choques:

- **tendência:** o crescimento da produtividade do trabalho oscila em torno de
  $g$, $\log \Gamma_t = g/4 + u_t$, com $u_t$ AR(1). É o choque permanente de
  Aguiar e Gopinath (2007), que pesa muito nos ciclos de economias emergentes;
- **produtividade transitória:** $Y_t = e^{z_t} K_t^\alpha (A_t L_t)^{1-\alpha}$,
  com $z_t$ AR(1);
- **gasto público:** $G_t/(A_t L_t) = \bar g\, e^{s_t}$, com $s_t$ AR(1).

A família escolhe o consumo pela equação de Euler

$$
x_t^{-\theta} = e^{-\rho/4}\, E_t\!\left[x_{t+1}^{-\theta}\left(1 + \tfrac14 (1-\tau_k)(R_{t+1} - \delta)\right)\right],
$$

com $x = C/L$. Quando o período tende a zero, o estado estacionário e a
velocidade de convergência tendem exatamente aos de `modelo.py` (há um teste
para isso). O modelo é linearizado em logaritmos e resolvido pelo método de
Klein (2000).

Os parâmetros estruturais ($\alpha$, $\delta$, $n$, $g$, $\tau_k$, $G/Y$,
$\theta = 2$ e $\rho$ para reproduzir $K/Y$) vêm da mesma calibração anual de
`Politicas/Lei-15270/equilibrio_geral/calibracao.py`, refeita em cada origem. Os seis parâmetros
dos choques e os quatro erros de medida são estimados por máxima
verossimilhança, com o filtro de Kalman.

**Equilíbrio geral, tendência trimestral.** O mesmo modelo, com duas
mudanças que isolam a dinâmica do erro de tendência: o crescimento de
tendência $g + n$ passa a reproduzir o crescimento médio do PIB trimestral até
a origem (em vez da tendência anual desde 2000), e cada série tem a própria
média de crescimento (o gasto real, por exemplo, cresce menos que o PIB nos
dados, porque o preço relativo dos serviços públicos sobe). Com as mesmas
médias que a média histórica, a comparação entre os dois mede só o que a
dinâmica do modelo acrescenta.

**Equilíbrio geral com busca** (`dsge_busca/`). O mesmo modelo com os
fundamentos do ABM sem leiloeiro:

- **margem:** concorrência monopolística com margem de 10% sobre o custo
  marginal, a que emerge no ABM 2. Capital e trabalho recebem o produto
  marginal dividido por 1,10; a tecnologia ($\alpha$) é a mesma, então a
  participação do trabalho cai para 50%, como no ABM 2. $\rho$ é recalibrado
  para reproduzir o $K/Y$ com a margem;
- **busca:** o emprego é uma variável de estado,
  $N_t = (1-s_t)N_{t-1} + f_t(1-N_{t-1})$, e quem acabou de perder o emprego
  espera o trimestre seguinte, como no ABM. A separação $s$ e o desemprego de
  longo prazo vêm da mesma cadeia trimestral da PNAD do ABM, calibrada até a
  origem; $f$ sai de uma função de encontro com elasticidade 0,5, e as
  firmas abrem vagas até o custo de contratar (14% do salário de um
  trimestre, Silva e Toledo, 2009; vaga preenchida com probabilidade 0,7
  por trimestre) igualar o valor do trabalhador;
- **salário rígido:** o salário acompanha a tendência da produtividade, mas
  só se ajusta aos poucos ao produto marginal,
  $\log w_t = \gamma(\log w_{t-1} - u_t) + (1-\gamma)\log(\omega\,\mathrm{PMgL}_t)$
  (Hall, 2005; Blanchard e Galí, 2010). É o papel da regra de salários do
  ABM. A rigidez $\gamma$ é estimada;
- **quarto choque:** a taxa de separação, AR(1), que dá ao desemprego uma
  fonte própria de variação, como a separação que o ABM usa para reproduzir
  a PNAD.

São nove parâmetros de choques e rigidez e cinco erros de medida, por
máxima verossimilhança. O desemprego entra como observação faltante antes de
2012. Tem as mesmas duas versões de tendência.

**ABM 1, com leiloeiro** (`abm1_com_leiloeiro/`). As cinco variantes de
expectativas do [modelo baseado em agentes](abm1_com_leiloeiro/README.md), com famílias heterogêneas cujo estado
na origem sai de uma simulação da história desde 1996 guiada pelos dados, e
previsões por 200 simulações.

**ABM 2, sem leiloeiro** (`abm2_sem_leiloeiro/`). A economia
com 200 firmas que fixam preços e salários, busca por emprego e mercado de
bens com fornecedores, com as mesmas cinco regras de expectativas. Em cada
origem: a mesma calibração do ABM 1, com os desempregados fora da produção;
100 anos de aquecimento sem choques, para que margens, estoques, capital e
crenças cheguem ao regime do próprio ABM; a história de 1996 até a origem,
reproduzindo o PIB (pelo crescimento da produtividade), o gasto do governo
e, desde 2012, a taxa de desemprego da PNAD (pela probabilidade de
separação do trimestre); AR(1) dos três choques; e 200 simulações.

## Resultados

RMSE relativo ao AR(1): abaixo de 1, o modelo errou menos que o AR(1). Em
negrito, as diferenças significativas a 5% pelo teste de Diebold-Mariano.
As tabelas completas, com todos os horizontes e o CRPS, estão em
`resultados/avaliacao.csv` e `resultados/avaliacao_sem_pandemia.csv`, e as
previsões de cada modelo ao lado do realizado, em
`resultados/previsoes_contra_realizado.csv`.

### Equilíbrio geral contra as referências

| Variável | Modelo | h=1 | h=4 | h=8 | h=1 sem pandemia | h=4 sem pandemia | h=8 sem pandemia |
|---|---|---|---|---|---|---|---|
| PIB | Média | 0,88 | 0,90 | 0,95 | 1,07 | 1,05 | 1,03 |
| PIB | VAR(1) | 1,15 | 1,13 | 1,07 | 0,92 | 0,95 | 0,97 |
| PIB | Equilíbrio geral | 0,85 | 0,95 | 1,05 | **1,11** | 1,16 | 1,16 |
| Consumo das famílias | Média | 0,88 | 0,92 | 0,95 | **1,08** | 1,05 | 1,03 |
| Consumo das famílias | VAR(1) | 1,11 | 1,09 | 1,05 | 0,95 | 0,95 | 0,98 |
| Consumo das famílias | Equilíbrio geral | 0,88 | 0,92 | 0,97 | **1,08** | 1,06 | 1,07 |
| FBCF | Média | 0,96 | 1,01 | 1,02 | 1,04 | 1,09 | 1,06 |
| FBCF | VAR(1) | 1,25 | 1,38 | 1,20 | 0,90 | 0,94 | 0,96 |
| FBCF | Equilíbrio geral | 0,94 | 1,03 | 1,05 | 1,04 | 1,13 | 1,10 |
| Consumo do governo | Média | 0,96 | 1,00 | 0,99 | **0,88** | 0,96 | **0,97** |
| Consumo do governo | VAR(1) | 1,15 | **1,04** | 1,03 | **1,18** | 1,06 | 1,05 |
| Consumo do governo | Equilíbrio geral | 0,93 | 1,16 | 1,38 | 0,95 | 1,28 | 1,49 |
| PIB | Equilíbrio geral, tendência trimestral | 0,83 | 0,88 | 0,94 | 1,03 | 1,03 | 1,02 |
| Consumo das famílias | Equilíbrio geral, tendência trimestral | 0,88 | 0,91 | 0,95 | 1,07 | 1,04 | 1,04 |
| FBCF | Equilíbrio geral, tendência trimestral | 0,93 | 1,00 | 1,02 | 1,02 | 1,08 | 1,05 |
| Consumo do governo | Equilíbrio geral, tendência trimestral | **0,88** | **0,89** | **0,92** | **0,85** | **0,88** | 0,92 |

![RMSE relativo ao AR(1)](figuras/rmse_relativo.png)

O que os números dizem:

1. **Quase nada é significativo.** Com 50 origens, só diferenças grandes
   seriam detectáveis. A exceção é o equilíbrio geral com tendência
   trimestral no consumo do governo, 8% a 15% melhor que o AR(1).
2. **A pandemia inverte o ranking.** Com ela, o AR(1) e o VAR(1) sofrem porque
   extrapolam a queda de 2020T2 e a recuperação seguinte; a média e o
   equilíbrio geral, que voltam logo à tendência, erram menos. Sem ela, o
   VAR(1) passa a ser o melhor e o equilíbrio geral erra de 6% a 16% mais que o
   AR(1) no PIB e no consumo, com diferença significativa em h = 1.
3. **A maior parte da desvantagem do equilíbrio geral vem da tendência.**
   Todos os modelos superestimaram o crescimento desde 2014, mas ele mais: sem
   a pandemia, o viés médio no PIB em 8 trimestres é de −3,4 p.p., contra −2,7
   do AR(1). A
   tendência do modelo sai da calibração anual (3,6% a 3,8% ao ano nas origens
   de 2013 a 2016, com dados de 2000 em diante), enquanto as referências usam
   a média desde 1996. Com a tendência trimestral, o mesmo modelo passa a ser
   o melhor na amostra completa para o PIB (17% a 6% menos erro que o AR(1)
   de h = 1 a h = 8) e, sem a pandemia, erra só 2% a 3% mais que o AR(1).
   Contra a média histórica, que tem as mesmas médias, ele erra 1% a 5%
   menos no PIB: a dinâmica estrutural acrescenta pouco, mas acrescenta.
4. **O crescimento balanceado custa caro no consumo do governo.** O modelo
   obriga o gasto real a crescer no ritmo do PIB, mas nos dados ele cresceu
   1,7% ao ano, contra 2,3% do PIB: o preço relativo dos serviços públicos
   sobe. Daí o viés de −4,0 p.p. em 8 trimestres, sem a pandemia (AR(1): −1,6).
   Com a média própria de cada série, o problema some e o consumo do governo
   passa a ser a variável em que o modelo mais ganha.
5. **Os intervalos de 90% cobrem menos do que deveriam em horizontes longos**
   em todos os modelos (74% a 81% para o PIB em h = 8). O equilíbrio geral fica
   no nível da média histórica.
6. **Os parâmetros dos choques mudam quando 2020T2 entra na amostra.** A
   persistência do choque de gasto cai de 0,99 para −0,04, e a do choque de
   tendência, de 0,57 para −0,35 (`resultados/parametros_dsge.csv`). Um
   trimestre em que todas as séries caem de 8% a 17% pesa muito numa
   verossimilhança normal. No equilíbrio geral com busca, a rigidez do
   salário estimada cai de 0,45–0,62 para zero.

![PIB: crescimento em quatro trimestres, realizado e previsto](figuras/previsoes_pib.png)

### Os quatro modelos estruturais

RMSE relativo ao AR(1), com a amostra toda e sem as janelas da pandemia, em
4 trimestres:

| Modelo | PIB | PIB sem pandemia | Consumo | Consumo sem pandemia | FBCF | FBCF sem pandemia | Desemprego | Desemprego sem pandemia |
|---|---|---|---|---|---|---|---|---|
| Média | 0,90 | 1,05 | 0,92 | 1,05 | 1,01 | 1,09 | 1,06 | 1,23 |
| VAR(1) | 1,13 | 0,95 | 1,09 | 0,95 | 1,38 | 0,94 | — | — |
| Equilíbrio geral (tend. trimestral) | 0,88 | 1,03 | 0,91 | 1,04 | 0,99 | 1,08 | — | — |
| Equilíbrio geral com busca (tend. trimestral) | 0,92 | 1,05 | 0,92 | 1,04 | 1,08 | 1,15 | 0,95 | 0,97 |
| ABM 1: crenças fixas | 1,02 | 1,00 | 0,98 | 0,96 | 1,09 | 1,08 | — | — |
| ABM 1: aprendizado | 1,03 | 1,02 | 0,99 | 1,00 | 1,14 | 1,06 | — | — |
| ABM 1: heurísticas | 0,99 | 0,95 | 0,99 | 1,13 | 1,33 | 0,82 | — | — |
| ABM 1: informação rígida | 1,03 | 1,03 | 0,99 | 0,98 | 1,16 | 1,11 | — | — |
| ABM 1: atenção limitada | 0,99 | 0,95 | 0,93 | 0,99 | 1,29 | 0,99 | — | — |
| ABM 2: crenças fixas | 0,98 | 0,99 | 0,95 | 0,98 | 1,10 | 1,03 | 0,98 | 1,09 |
| ABM 2: aprendizado | 0,96 | **1,08** | 0,93 | 1,00 | 1,09 | 1,12 | 0,89 | 0,96 |
| ABM 2: heurísticas | 1,01 | **1,12** | 1,07 | 1,32 | **1,57** | **1,80** | 1,04 | 1,14 |
| ABM 2: informação rígida | 0,91 | 1,03 | 0,88 | 0,97 | 1,05 | 1,07 | 1,00 | 1,12 |
| ABM 2: atenção limitada | 1,00 | **1,20** | 1,13 | **1,35** | **1,54** | **1,76** | 1,05 | 1,18 |

Em 8 trimestres:

| Modelo | PIB | PIB sem pandemia | Consumo | Consumo sem pandemia | FBCF | FBCF sem pandemia | Desemprego | Desemprego sem pandemia |
|---|---|---|---|---|---|---|---|---|
| Média | 0,95 | 1,03 | 0,95 | 1,03 | 1,02 | 1,06 | 0,95 | 1,08 |
| VAR(1) | 1,07 | 0,97 | 1,05 | 0,98 | 1,20 | 0,96 | — | — |
| Equilíbrio geral (tend. trimestral) | 0,94 | 1,02 | 0,95 | 1,04 | 1,01 | 1,05 | — | — |
| Equilíbrio geral com busca (tend. trimestral) | 0,97 | 1,05 | 0,95 | 1,04 | 1,10 | 1,14 | 0,81 | 0,87 |
| ABM 1: crenças fixas | 1,02 | 1,01 | 0,97 | 0,96 | 1,08 | 1,07 | — | — |
| ABM 1: aprendizado | 1,04 | 1,03 | 1,00 | 1,01 | 1,15 | **1,05** | — | — |
| ABM 1: heurísticas | 1,00 | 0,96 | 1,02 | 1,11 | 1,17 | 0,85 | — | — |
| ABM 1: informação rígida | 1,04 | 1,04 | 1,00 | 0,99 | **1,17** | 1,08 | — | — |
| ABM 1: atenção limitada | 1,00 | 0,96 | 0,96 | 1,00 | 1,18 | 0,98 | — | — |
| ABM 2: crenças fixas | 0,97 | 0,96 | 0,95 | 0,98 | 1,04 | 1,03 | 0,78 | 0,89 |
| ABM 2: aprendizado | **0,95** | 0,99 | 0,94 | 0,98 | 1,07 | **1,08** | 0,76 | 0,86 |
| ABM 2: heurísticas | 1,07 | **1,07** | **1,15** | 1,25 | **1,68** | **1,71** | 1,00 | 1,00 |
| ABM 2: informação rígida | 0,94 | 0,99 | 0,90 | 0,97 | 1,03 | 1,06 | 0,82 | 0,93 |
| ABM 2: atenção limitada | 1,01 | 1,11 | 1,14 | **1,26** | **1,45** | **1,47** | 0,85 | 0,98 |

O desemprego é a variação da taxa entre a origem e o alvo; a referência é o
AR(1) dela. O consumo do governo é exógeno nos ABMs e fica fora da tabela.

![ABM 2 e equilíbrio geral com busca, sem a pandemia](figuras/rmse_abm2_sem_pandemia.png)

1. **Nenhum modelo domina.** Quase nenhuma diferença é significativa, e o
   melhor modelo muda com a variável, o horizonte e a pandemia.
2. **Pôr margem e busca no equilíbrio geral não melhora as Contas
   Nacionais.** Com a tendência trimestral e a amostra toda, o RMSE do
   modelo com busca é de 3% a 7% maior que o do sem busca no PIB e de 9% a
   12% maior na FBCF, de 1 a 8 trimestres. O que ele acrescenta é o
   desemprego.
3. **O desemprego é onde os modelos com busca ganham.** Em um trimestre,
   nada bate o AR(1), porque o desemprego é muito persistente. Em um e dois
   anos, os dois modelos com busca erram menos que o AR(1) e que a média:
   em 8 trimestres, 24% menos com o ABM 2 com aprendizado e 19% menos com o
   equilíbrio geral com busca (14% e 13% sem a pandemia), sem significância.
   A razão é a mesma nos dois: eles trazem o desemprego de volta à média da
   PNAD, e as referências extrapolam a tendência recente. O viés em 8
   trimestres, sem a pandemia, é de +0,07 p.p. no equilíbrio geral com
   busca e de −0,23 no ABM 2 com aprendizado, contra −0,99 no AR(1).
4. **Sem leiloeiro, com as regras que não reagem demais, o ABM 2 fica no
   nível do par dele.** Com crenças fixas, aprendizado e informação rígida,
   ele erra mais ou menos o mesmo que o equilíbrio geral com busca no PIB e
   um pouco menos no consumo: com informação rígida, 12% menos que o AR(1)
   em 4 trimestres e 10% menos em 8, o melhor de todos os modelos com a
   amostra toda. No desemprego em dois anos, com crenças fixas e
   aprendizado, erra um pouco menos que o par; na FBCF sem a pandemia, de
   1,03 a 1,12 vezes o AR(1), contra 1,14 a 1,15 do par.
5. **Com heurísticas e atenção limitada, o ABM 2 é instável.** São os piores
   modelos para a FBCF, com erros 45% a 80% maiores que os do AR(1),
   significativos, em 4 e 8 trimestres. No ABM 2, o retorno do capital é o lucro realizado do
   fundo, que oscila de um trimestre para outro, e essas duas regras o levam
   quase direto às crenças: o custo do capital das firmas e o consumo
   oscilam junto. Com heurísticas, as famílias ainda trocam de regra em
   bloco (todas passam para a regra ingênua e, poucos trimestres depois,
   para a fundamentalista). No ABM 1, com o retorno dado pelo produto
   marginal, as mesmas regras dão os melhores resultados para a FBCF sem a
   pandemia.
6. **Os intervalos de 90% do desemprego cobrem de 66% a 74%** dos realizados
   em 4 trimestres, nos modelos com busca e no AR(1): a incerteza sobre o
   desemprego é subestimada por todos.

![Equilíbrio geral com e sem busca](figuras/rmse_busca.png)

Os resultados do ABM 1 estão no [README dele](abm1_com_leiloeiro/README.md#previsão-fora-da-amostra),
e os do ABM 2, no [dele](abm2_sem_leiloeiro/README.md#previsão-fora-da-amostra).

![ABM 1 e equilíbrio geral, sem a pandemia](figuras/rmse_abm_sem_pandemia.png)

## Previsões registradas

Previsões feitas com os dados até 2026T2, gravadas em
`resultados/previsao_registrada_202602.csv` para serem comparadas com os
dados que o IBGE ainda vai divulgar. Crescimento acumulado desde 2026T2, em
%, e variação da taxa de desemprego desde 2026T2 (5,3%), em p.p.:

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
| ABM 2: heurísticas | 0,40 | 2,69 | 7,39 | 8,80 | 15,84 | +0,55 | +1,90 |
| ABM 2: informação rígida | 2,72 | 3,03 | 1,39 | 4,10 | −3,83 | +0,73 | +2,43 |
| ABM 2: atenção limitada | 3,14 | 4,84 | −1,05 | −6,85 | −35,16 | +0,86 | +2,08 |

Com o desemprego no menor nível da série, os modelos com busca preveem que
ele suba: o equilíbrio geral, 0,5 p.p. até 2027T4; o ABM 2, de 1,9 a 2,7
p.p. com quatro das cinco regras. As previsões do ABM 2 com heurísticas e
com atenção limitada para consumo e FBCF não são críveis, pelo motivo do
item 5 acima: em 2026T2, a economia com atenção limitada está no meio de um
surto de investimento, com os estoques pela metade, e a com heurísticas
passa, na simulação, a ter todas as famílias com a regra ingênua.

O arquivo traz também o desvio-padrão de cada previsão, que é grande (4 a
7 p.p. para o PIB até 2027T4, 1,4 a 3,8 p.p. para o desemprego), e a coluna
`efeito_lei`: o efeito da Lei 15.270/2025 pelo modelo contínuo de
`Politicas/Lei-15270/equilibrio_geral/`, com o aumento de $\tau_k$ anunciado
em março de 2025. Ele é pequeno nesse horizonte, −0,05 p.p. no PIB e −0,08
p.p. no consumo até 2027T4, porque o capital se ajusta devagar.

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
cerca de meio minuto para cada variante de ABM. Tudo, com 4 núcleos, leva
de 2 a 3 horas.

Os dados trimestrais ficam em [`dados/brasil/`](../../../../../dados/brasil/README.md),
com o script que os baixa.

## Arquivos

| Arquivo ou pasta | Conteúdo |
|---|---|
| `protocolo.py` | dados, dessazonalização do desemprego, calibração em cada origem e previsões sem olhar o futuro |
| `espaco_estados.py` | filtro de Kalman (com observações faltantes) e previsão do crescimento acumulado, comuns aos modelos lineares |
| `avaliacao.py` | RMSE, CRPS, cobertura e teste de Diebold-Mariano |
| `comparacao.py` | roda o protocolo, em paralelo se pedido, e grava os resultados e as figuras |
| `referencias/` | média, AR(1) e VAR(1) |
| `dsge/` | equilíbrio geral estocástico: estado estacionário, linearização, solução de Klein, espaço de estados e máxima verossimilhança |
| `dsge_busca/` | o mesmo com margem, busca, salário rígido e choque de separação |
| `abm1_com_leiloeiro/`, `abm2_sem_leiloeiro/` | os dois ABMs, com os próprios experimentos e testes |
| `test_*.py` (aqui e em cada pasta) | 49 testes nas pastas de referências, DSGEs e protocolo: solução exata de Brock-Mirman, limite contínuo, precisão da linearização, estado estacionário e dinâmica do modelo com busca, verossimilhança do Kalman contra a normal multivariada e com dados faltantes, recuperação dos parâmetros em dados simulados, comparação com o `statsmodels`, dessazonalização, CRPS e tamanho do teste de Diebold-Mariano, e ausência de dados do futuro |
| `resultados/` | previsões, avaliações contra o AR(1) e contra a média histórica, parâmetros estimados por origem, previsões lado a lado com o realizado (`previsoes_contra_realizado.csv`) e previsões registradas |
| `figuras/` | erros relativos por horizonte e previsões do PIB |

## Limitações

- Os dados são os revisados de hoje, não os que existiam em cada origem. Isso
  favorece um pouco todos os modelos, por igual.
- Nenhum modelo tem setor externo; a diferença entre o PIB e a soma de
  consumo, FBCF e gasto fica nos erros de medida (no ABM 2, na variação dos
  estoques). O primeiro equilíbrio geral e o ABM 1 também não têm
  desemprego.
- O desemprego só existe desde 2012: nas primeiras origens, a média e o
  AR(1) do desemprego são estimados com menos de dez trimestres, e o
  equilíbrio geral com busca tem pouca informação sobre a rigidez do
  salário.
- O desemprego de longo prazo dos modelos com busca é a média da PNAD até a
  origem. Quando o desemprego fica muito tempo longe dela, como em 2016-2021
  e desde 2023, os dois modelos preveem que ele volte.
- Todos os modelos supõem choques normais, e a pandemia está longe disso.
- A série de consumo do governo tem um salto atípico no começo, −16% em
  1996T4 e +12% em 1997T1, que entra em todas as amostras.
- Com 50 origens, os testes têm pouco poder: só diferenças grandes aparecem
  como significativas.
