# ABM 1: com leiloeiro

Uma economia com 20 mil famílias simuladas uma a uma, trimestre a trimestre,
com a mesma microfundamentação e a mesma calibração do modelo de Aiyagari de
[`Politicas/Lei-15270/equilibrio_geral/`](../../../../Politicas/Lei-15270/equilibrio_geral/README.md).
Duas coisas mudam. As famílias podem formar expectativas de várias formas,
da previsão perfeita às regras de racionalidade limitada da literatura
recente. E nenhuma condição de equilíbrio é imposta ao longo do caminho: os
agregados são somas de decisões individuais. Os preços ainda vêm de um
leiloeiro walrasiano; o [ABM 2](../abm2_sem_leiloeiro/README.md) tira o
leiloeiro.

O modelo é usado em três lugares: na avaliação de previsões fora da amostra
desta pasta ([`../README.md`](../README.md)); nos experimentos da Lei
15.270/2025 com famílias que não são plenamente racionais
([`Politicas/Lei-15270/`](../../../../Politicas/Lei-15270/README.md)); e em
dois exercícios próprios, descritos abaixo: a convergência a partir de longe
do equilíbrio e as regras de previsão que as famílias escolhem de 1996 a
2026.

## A economia

A cada trimestre:

1. a poupança do trimestre anterior vira riqueza por membro, descontado o
   crescimento da produtividade e da população;
2. cada família sorteia o novo estado de renda pela cadeia de Markov
   calibrada com a PNAD Contínua: três tipos permanentes (50% com menor renda,
   40% seguintes, 10% com maior renda) e três situações (empregado,
   desempregado de curta e de longa duração);
3. um leiloeiro walrasiano fixa os preços dos fatores: $K$ é a riqueza média,
   $L$ a produtividade média, e a firma competitiva paga
   $r = (1-\tau_k)(\alpha Y/K - \delta)$ e $w = (1-\alpha)Y/L$;
4. o governo gasta $G$, cobra $\tau_k$ e $\tau_w$ e devolve o saldo como
   transferência;
5. cada família atualiza as crenças e escolhe quanto consumir;
6. o que sobra é poupado, e o investimento é $I = Y - C - G$.

Toda família resolve o problema de consumo e poupança com utilidade CRRA e
sem endividamento, pela equação de Euler

$$
c_t^{-\theta} = e^{-\rho/4}\,(1 + r_{t+1}/4)\,e^{-\theta g/4}\,E_t\!\left[c_{t+1}^{-\theta}\right],
$$

resolvida pelo método da grade endógena (Carroll, 2006). As regras de
expectativas diferem no que a família supõe sobre os juros e os salários
futuros. Com crenças $(r^e, w^e)$, ela age como se esses preços fossem durar
para sempre (*anticipated utility*, Kreps, 1998) e usa a política ótima para
eles, pré-calculada numa tabela de crenças de juro. Como na economia do
Aiyagari, o desempregado continua produzindo a fração da renda que recebe.

## Regras de expectativas

| Regra | Hipótese | Referência | Parâmetro |
|---|---|---|---|
| Previsão perfeita | conhece o caminho futuro de preços, consistente com as escolhas de todos (expectativas racionais sem risco agregado) | benchmark neoclássico | — |
| Crenças fixas | crê que os preços do estado estacionário valem para sempre (a regra "fundamentalista") | Brock e Hommes (1997) | — |
| Aprendizado | atualiza as crenças com ganho constante: $r^e \leftarrow r^e + \gamma (r - r^e)$ | Evans e Honkapohja (2001); Milani (2007) | $\gamma = 0{,}02$ |
| Heurísticas | escolhe entre as regras fundamentalista, de aprendizado e ingênua (preços atuais); cada família sorteia uma regra com probabilidades logit do erro passado de cada uma, que é o mesmo para todas | Brock e Hommes (1997); Anufriev e Hommes (2012) | intensidade 1, memória 0,7 |
| Atualização esporádica | a cada trimestre, 25% das famílias adotam a previsão corrente do aprendizado; as outras mantêm a que tinham | Carroll (2003), com a rigidez de Mankiw e Reis (2002) | $\lambda = 0{,}25$ |
| Atenção limitada | percebe só 85% do desvio dos preços em relação ao estado estacionário | Gabaix (2020) | $\bar m = 0{,}85$ |

A atualização esporádica aparece nos resultados como "informação rígida". Em
Mankiw e Reis (2002), quem atualiza passa a ter expectativas racionais; aqui,
passa a ter a previsão do aprendizado adaptativo, como os domicílios de
Carroll (2003), que copiam a previsão dos profissionais. Por isso ela se
comporta como o aprendizado, só que mais devagar. As crenças fixas e a
atenção limitada ancoram as crenças no estado estacionário, que as famílias
conhecem, inclusive o novo, logo depois de uma reforma.

A previsão perfeita é resolvida como um ponto fixo (`transicao.py`): dado um
caminho para o capital, a política de cada trimestre sai da grade endógena
de trás para frente, as famílias a seguem, e o capital que elas acumulam
atualiza o caminho até coincidir.

## Verificação

Com previsão perfeita, o ABM reproduz o Aiyagari contínuo. No experimento da
[Lei 15.270](../../../../Politicas/Lei-15270/README.md), o novo estado
estacionário tem capital −1,45% com devolução uniforme e −1,41% com isenção,
os números de `Politicas/Lei-15270/equilibrio_geral/`, por duas soluções
independentes (grade endógena trimestral com histograma aqui; HJB e
Kolmogorov em tempo contínuo lá). Os ganhos de bem-estar por grupo ficam a
até 0,06 p.p. dos do modelo contínuo (por exemplo, +0,53% contra +0,58% para
os 50% com menor renda na devolução uniforme). A diferença vem de o ABM
medir a utilidade que cada família de fato obtém com os seus sorteios de
renda, em trimestres, e o contínuo, a utilidade esperada.

Os 40 testes (`test_*.py`) conferem também:

- a política sem risco contra a fórmula fechada do consumo com renda
  constante, e a equação de Euler, com erro menor que 0,2% fora da grade;
- que 20 mil famílias sorteadas da distribuição estacionária a mantêm por
  400 trimestres, e que o histograma das famílias sorteadas preserva a massa,
  a riqueza média e o peso de cada tipo;
- que $Y = C + I + G$ e o orçamento do governo fecham a cada trimestre, e que
  a poupança agregada é o capital mais o investimento líquido;
- que a história guiada pelos dados reproduz o PIB e o gasto observados com
  erro de $10^{-14}$, e que mudar qualquer dado posterior à origem (PIB,
  dados anuais, PNAD) não muda nenhuma previsão;
- que, com previsão perfeita pelo histograma, o caminho fica no equilíbrio
  com erro menor que $10^{-6}$, e as famílias simuladas seguem o caminho do
  contínuo por 20 anos com erro menor que 0,5%;
- que a população inicial tem o número exato de famílias em cada estado de
  renda. Um sorteio simples erra a oferta de trabalho em cerca de 1% (o tipo
  de maior renda produz 4 vezes a média), o que cria um déficit público
  inexistente no modelo e, na devolução por isenção, inverte o sinal do
  efeito sobre os mais pobres.

## Convergência a partir de longe do equilíbrio

Nos experimentos da lei, a economia parte do equilíbrio estacionário. Em
`convergencia.py`, ela parte de longe dele: a renda de cada família está no
estado estacionário, mas a riqueza não. São quatro partidas (capital 50%
abaixo, capital 50% acima, a mesma riqueza para todos e 1% das famílias com
toda a riqueza) e o próprio equilíbrio como controle, sem reforma e sem
choques agregados, por 1.000 anos. As crenças começam dos preços que as
famílias observam no primeiro trimestre, de modo que quem aprende não sabe
onde fica o equilíbrio.

Com previsão perfeita, a convergência vem da construção, porque o caminho de
preços termina no estado estacionário. Ela é calculada para um contínuo de
famílias, pelo histograma, e não para as 20 mil. Com famílias simuladas
seguindo um caminho de preços dado, o ruído de amostragem se acumula: quem
não reage aos preços realizados torna o equilíbrio instável, e o desvio
dobra mais ou menos a cada 20 anos. Com expectativas racionais, a
estabilidade vem de cada família refazer os planos. Nas outras regras, o
caminho resulta só das decisões.

A tabela mostra os anos até o capital entrar de vez na faixa de ±1% do
equilíbrio (entre parênteses, a faixa percorrida) e o capital depois de
1.000 anos, em relação ao de equilíbrio:

| Regra | Partindo 50% abaixo | Partindo 50% acima | Depois de 1.000 anos, todas as partidas |
|---|---|---|---|
| Previsão perfeita | 66 (0,50 a 1,00) | 62 (1,00 a 1,50) | 1,000 (1,007 partindo de 1% com tudo) |
| Crenças fixas | nunca | nunca | 1,84 |
| Aprendizado | 171 (0,50 a 1,23) | 224 (0,73 a 1,50) | 0,997 a 1,005 |
| Heurísticas | 118 (0,50 a 1,02) | 46 (0,99 a 1,50) | 0,997 a 1,004 |
| Informação rígida | 165 (0,50 a 1,25) | 155 (0,70 a 1,50) | 1,001 a 1,005 |
| Atenção limitada | 59 (0,50 a 1,01) | 50 (1,00 a 1,50) | 0,997 a 1,002 |

A segunda tabela traz o Gini da riqueza depois de 1.000 anos (no equilíbrio,
0,52) e a distância de Kolmogorov-Smirnov até a distribuição estacionária (a
maior diferença entre as funções de distribuição):

| Regra | Riqueza igual: Gini | Riqueza igual: distância | 1% com tudo: Gini | 1% com tudo: distância | Controle: distância |
|---|---|---|---|---|---|
| Previsão perfeita | 0,50 | 0,027 | 0,59 | 0,081 | 0,000 |
| Crenças fixas | 0,35 | 0,62 | 0,35 | 0,62 | 0,62 |
| Aprendizado | 0,50 | 0,038 | 0,58 | 0,067 | 0,013 |
| Heurísticas | 0,50 | 0,040 | 0,56 | 0,047 | 0,017 |
| Informação rígida | 0,50 | 0,040 | 0,58 | 0,071 | 0,018 |
| Atenção limitada | 0,50 | 0,037 | 0,56 | 0,051 | 0,012 |

![Convergência a partir de longe do equilíbrio](figuras/convergencia.png)

Com aprendizado, heurísticas, informação rígida e atenção limitada, o capital
volta ao equilíbrio de todas as partidas. O aprendizado e a informação
rígida, que dependem só do passado, passam do ponto em ciclos longos e
amortecidos. Partindo de 50% abaixo, o juro fica alto por anos, as famílias
passam a acreditar nele e poupam demais, e o capital chega a 1,23 vez o de
equilíbrio antes de voltar; levam de 155 a 225 anos para se acertar. As
heurísticas e a atenção limitada, que ancoram parte das crenças no
equilíbrio, chegam em 46 a 118 anos, às vezes mais rápido que a previsão
perfeita.

Com crenças fixas, a economia vai para outro ponto de repouso, o mesmo para
todas as partidas, inclusive a do próprio equilíbrio: capital 1,84 vez o de
equilíbrio e Gini de 0,35. Nesse ponto, o juro líquido fica 4,2 p.p. abaixo
do que as famílias acreditam, e elas continuam poupando para um juro que não
vem. O ponto de repouso é estável, mas não é o equilíbrio de expectativas
racionais.

Partindo da mesma riqueza para todos, o Gini sobe de 0 para 0,50 em 1.000
anos, só com os choques de renda e a poupança precaucional, e na mesma
velocidade em todas as regras, inclusive a previsão perfeita. Essa velocidade
é dada pelo processo de renda. A distribuição converge muito mais devagar que
o capital: o capital se acerta em décadas, e a distribuição, em séculos.
Partindo de 1% com toda a riqueza, nem em 1.000 anos ela chega (Gini de 0,56
a 0,59), e o capital fica mais de 1% acima do equilíbrio por 540 a 890 anos.
No controle, as 20 mil famílias ficam a uma distância de 0,012 a 0,018 da
distribuição estacionária, que é o piso do ruído de amostragem; partindo de
50% abaixo ou acima, todas as regras chegam a esse piso.

Quando as crenças começam nos preços do equilíbrio, e não nos observados, o
destino é o mesmo e o caminho muda. Partindo de 50% abaixo, quem aprende
começa acreditando no salário do equilíbrio, mais alto que o verdadeiro, e
gasta; o capital cai até 0,35 antes de subir (`resultados/convergencia.csv`).

## As regras escolhidas de 1996 a 2026

Com as heurísticas (`heuristicas.py`), o ABM percorre a história brasileira
desde 1996, reproduzindo o PIB e o gasto observados, e a fração de famílias
em cada regra acompanha o erro recente de cada uma. O estado estacionário que
a regra fundamentalista usa é o da calibração com os dados de 2000 a 2023,
de modo que, nos primeiros anos, ela sabe um pouco do futuro.

![Regras escolhidas pelas famílias](figuras/heuristicas.png)

Nos anos de juros estáveis, de 1999 a 2005, a regra fundamentalista divide as
famílias com o aprendizado. A partir de 2006 a regra ingênua passa a
dominar, com duas interrupções em que o aprendizado e a regra
fundamentalista voltam (2010 e 2014-2015). Depois da recessão de 2015-2016,
quando o juro líquido cai e não volta, a regra ingênua fica com quase todas
as famílias por quase dez anos, porque a regra que aposta na volta ao
estado estacionário erra sempre na mesma direção. Em 2025, com os preços
mais estáveis, o aprendizado volta a ganhar espaço.

## Previsão fora da amostra

Em cada origem, o ABM é calibrado só com o que se sabia naquela data (dados
anuais até dois anos antes, PNAD até a origem, tendência pelo PIB trimestral
até a origem) e percorre a história desde 1996, reproduzindo o PIB e o gasto
observados. Isso fixa, na origem, a distribuição de riqueza, os estados de
renda e as crenças das famílias. Dois AR(1), um para o crescimento da
produtividade inferida e outro para o do gasto, com choques correlacionados,
dão os choques futuros, e 200 simulações (com choques antitéticos) dão a
previsão e a incerteza. É o desenho de Poledna, Miess, Hommes e Rabitsch
(2023) para o ABM da Áustria.

Como a produtividade é escolhida para reproduzir o PIB observado, a previsão
do PIB do ABM é, em boa parte, a de um AR(1) para essa produtividade. O que o
modelo acrescenta vem do capital e das decisões de consumo, e aparece mais no
consumo e na FBCF.

RMSE relativo ao AR(1), sem as janelas da pandemia (abaixo de 1, o modelo
errou menos; em negrito, diferença significativa a 5% pelo teste de
Diebold-Mariano):

| Modelo | PIB h=1 | PIB h=4 | PIB h=8 | Consumo h=1 | Consumo h=4 | FBCF h=1 | FBCF h=2 | FBCF h=4 |
|---|---|---|---|---|---|---|---|---|
| VAR(1) | 0,92 | 0,95 | 0,97 | 0,95 | 0,95 | 0,90 | 0,87 | 0,94 |
| Equilíbrio geral, tendência trimestral | 1,03 | 1,03 | 1,02 | 1,07 | 1,04 | 1,01 | 1,02 | 1,08 |
| ABM 1: crenças fixas | 1,00 | 1,00 | 1,01 | 0,96 | 0,96 | 0,98 | 1,03 | 1,08 |
| ABM 1: aprendizado | 1,00 | 1,02 | 1,03 | 1,00 | 1,00 | 0,98 | 1,00 | 1,06 |
| ABM 1: heurísticas | 0,97 | 0,95 | 0,96 | 1,19 | 1,13 | 0,89 | **0,82** | 0,82 |
| ABM 1: informação rígida | 1,01 | 1,03 | 1,04 | 0,99 | 0,98 | 1,02 | 1,05 | 1,11 |
| ABM 1: atenção limitada | 0,97 | 0,95 | 0,96 | 1,00 | 0,99 | 0,92 | 0,94 | 0,99 |

![ABM e equilíbrio geral contra o AR(1)](../figuras/rmse_abm_sem_pandemia.png)

Sem a pandemia, as regras que olham os preços correntes preveem melhor. Com
heurísticas e com atenção limitada, o ABM erra de 3% a 6% menos que o AR(1)
no PIB, e com heurísticas erra de 11% a 20% menos na FBCF, o melhor resultado
entre os modelos para o investimento. Contra a média histórica, que usa as
mesmas médias, a vantagem chega a 28% na FBCF. Só a diferença na FBCF em
h = 2 é significativa pelo teste de Diebold-Mariano, e ela deixa de ser
quando se corrige para as comparações de todos os modelos com o AR(1)
(correção de Holm).

Cada regra acerta uma variável. As heurísticas preveem bem o investimento e
mal o consumo (19% pior que o AR(1) em h = 1); as crenças fixas preveem bem o
consumo (4% melhor) e mal o investimento. Quando as famílias reagem aos
preços correntes, o consumo fica suave demais e o investimento absorve os
choques; quando não reagem, acontece o contrário.

Com a pandemia, o ABM perde. Os choques de produtividade seguem um AR(1), que
extrapola a queda de 2020 e a recuperação seguinte, e as regras que olham os
preços correntes transformam isso em oscilações grandes do investimento. Na
amostra completa, o melhor modelo para o PIB nos primeiros cinco horizontes é
o equilíbrio geral com tendência trimestral.

A incerteza também depende da regra. Sem a pandemia, os intervalos de 90% do
ABM com aprendizado, informação rígida e crenças fixas cobrem de 61% a 76% da
FBCF realizada, conforme o horizonte; os das heurísticas e da atenção
limitada cobrem de 82% a 100% da FBCF, mas de 62% a 80% do consumo.

O consumo do governo é exógeno no ABM e segue o mesmo AR(1) da referência,
então a comparação para ele não informa nada. O ABM sem leiloeiro está no
[README dele](../abm2_sem_leiloeiro/README.md#previsão-fora-da-amostra). As
tabelas completas estão em [`../resultados/`](../resultados/), e as previsões
registradas para 2026-2028, em
[`../README.md`](../README.md#previsões-registradas).

## Como rodar

Da pasta `Econometria/`, com as dependências de `Python/requirements.txt`:

```bash
python Python/macroeconomia/Forecast/Brasil/2013T4-2026T2/abm1_com_leiloeiro/convergencia.py   # partidas fora do equilíbrio (cerca de meia hora)
python Python/macroeconomia/Forecast/Brasil/2013T4-2026T2/abm1_com_leiloeiro/heuristicas.py    # regras escolhidas, 1996-2026
python Python/macroeconomia/Forecast/Brasil/2013T4-2026T2/comparacao.py --processos 4 --modelos abm_eq abm_apr abm_heu abm_inf abm_aten
python -m unittest discover -s Python/macroeconomia/Forecast/Brasil/2013T4-2026T2/abm1_com_leiloeiro -v
```

## Arquivos

| Arquivo | Conteúdo |
|---|---|
| `familias.py` | problema das famílias: grade endógena, histograma estacionário, calibração de $\rho$, equilíbrio e tabela de políticas por crença de juro |
| `expectativas.py` | regras de formação de expectativas |
| `economia.py` | a economia com leiloeiro: população inicial, trimestre com leiloeiro e governo, história guiada pelos dados e previsão por simulação |
| `transicao.py` | transição com previsão perfeita (ponto fixo), com as famílias simuladas ou com o histograma |
| `comum.py` | calibração com a amostra anual inteira e cores das regras nas figuras, usadas aqui e nos experimentos da lei |
| `previsao_abm.py` | o ABM no protocolo de previsão fora da amostra |
| `convergencia.py` | partidas fora do equilíbrio: o capital e a distribuição da riqueza voltam sozinhos? |
| `heuristicas.py` | as regras de previsão que as famílias escolhem de 1996 a 2026 |
| `test_*.py` | 40 testes |
| `resultados/`, `figuras/` | tabelas e figuras |

## Limitações

Na história guiada pelos dados, os dois ABMs explicam a queda do PIB pelo
crescimento da produtividade (e o ABM 2 explica o desemprego pela
separação). Numa recessão, a produtividade cai, o capital por unidade de
eficiência sobe e o retorno do capital cai. Falta o canal de demanda e de
crédito que fez o investimento brasileiro cair em 2015-2016.

As expectativas racionais estão implementadas só para transições sem risco
agregado. Com choques agregados, o benchmark racional exigiria o método de
Krusell e Smith (1998). Os parâmetros comportamentais vêm da literatura e
não foram estimados; estimá-los pelo método dos momentos simulados, com os
dados de expectativas do Focus e da FGV, é uma extensão natural.

Como no Aiyagari, a riqueza é menos concentrada que nos dados, e partindo de
longe a distribuição leva séculos para se estabilizar. As famílias formam as
políticas com o risco de desemprego da PNAD, e não com o que vivem na
simulação, e a tabela de políticas supõe o perfil de transferências do
estado estacionário.

## Referências

- Anufriev, M. e Hommes, C. (2012). Evolutionary Selection of Individual Expectations and Aggregate Outcomes in Asset Pricing Experiments. *American Economic Journal: Microeconomics*, 4(4), 35-64.
- Brock, W. A. e Hommes, C. H. (1997). A Rational Route to Randomness. *Econometrica*, 65(5), 1059-1095.
- Carroll, C. D. (2003). Macroeconomic Expectations of Households and Professional Forecasters. *Quarterly Journal of Economics*, 118(1), 269-298.
- Carroll, C. D. (2006). The Method of Endogenous Gridpoints for Solving Dynamic Stochastic Optimization Problems. *Economics Letters*, 91(3), 312-320.
- Diebold, F. X. e Mariano, R. S. (1995). Comparing Predictive Accuracy. *Journal of Business & Economic Statistics*, 13(3), 253-263.
- Evans, G. W. e Honkapohja, S. (2001). *Learning and Expectations in Macroeconomics*. Princeton University Press.
- Gabaix, X. (2020). A Behavioral New Keynesian Model. *American Economic Review*, 110(8), 2271-2327.
- Holm, S. (1979). A Simple Sequentially Rejective Multiple Test Procedure. *Scandinavian Journal of Statistics*, 6(2), 65-70.
- Kreps, D. M. (1998). Anticipated Utility and Dynamic Choice. Em Jacobs, D. P., Kalai, E. e Kamien, M. I. (orgs.), *Frontiers of Research in Economic Theory*. Cambridge University Press, 242-274.
- Krusell, P. e Smith, A. A. (1998). Income and Wealth Heterogeneity in the Macroeconomy. *Journal of Political Economy*, 106(5), 867-896.
- Mankiw, N. G. e Reis, R. (2002). Sticky Information versus Sticky Prices: A Proposal to Replace the New Keynesian Phillips Curve. *Quarterly Journal of Economics*, 117(4), 1295-1328.
- Milani, F. (2007). Expectations, Learning and Macroeconomic Persistence. *Journal of Monetary Economics*, 54(7), 2065-2082.
- Poledna, S., Miess, M. G., Hommes, C. e Rabitsch, K. (2023). Economic Forecasting with an Agent-Based Model. *European Economic Review*, 151, 104306.
- Young, E. R. (2010). Solving the Incomplete Markets Model with Aggregate Uncertainty Using the Krusell-Smith Algorithm and Non-Stochastic Simulations. *Journal of Economic Dynamics and Control*, 34(1), 36-41.
