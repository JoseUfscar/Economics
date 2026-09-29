# ABM 1 com leiloeiro

Este modelo simula uma economia com 20 mil famílias, uma a uma e trimestre a
trimestre, construída sobre a mesma microfundamentação neoclássica do modelo
de Aiyagari de [`Politicas/Lei-15270/equilibrio_geral/`](../../../../Politicas/Lei-15270/equilibrio_geral/README.md)
e com a mesma calibração para o Brasil. A diferença está na forma como as
famílias formam expectativas, que vai das expectativas racionais à
racionalidade limitada da literatura recente, e no fato de que nenhum
equilíbrio é imposto ao longo do caminho, já que os agregados são apenas a
soma das decisões individuais. Os preços, no entanto, ainda vêm de um
leiloeiro walrasiano, que o [ABM 2](../abm2_sem_leiloeiro/README.md) retira.

O modelo serve a três perguntas. A primeira é se o ABM prevê melhor que o
equilíbrio geral, avaliada no protocolo fora da amostra desta pasta de
previsão ([`../README.md`](../README.md)), a segunda é se a Lei 15.270/2025
tem os mesmos efeitos distributivos quando as famílias não são plenamente
racionais, tratada em [`Politicas/Lei-15270/`](../../../../Politicas/Lei-15270/README.md),
e a terceira é o que emerge da interação entre as famílias, em particular a
convergência a partir de situações distantes do equilíbrio e as regras de
previsão que elas escolhem ao longo da história brasileira recente.

## A economia

A cada trimestre, a poupança do trimestre anterior se transforma em riqueza
por membro, descontado o crescimento da produtividade e da população, e cada
família sorteia seu novo estado de renda pela cadeia de Markov calibrada com
a PNAD Contínua, que combina três tipos permanentes (os 50% com menor renda,
os 40% seguintes e os 10% com maior renda) com três situações no mercado de
trabalho (empregado, desempregado de curta duração e desempregado de longa
duração). Um leiloeiro walrasiano fixa então os preços que equilibram os
mercados de fatores, com $K$ igual à riqueza média e $L$ à produtividade
média, de modo que a firma competitiva paga $r = (1-\tau_k)(\alpha Y/K - \delta)$
e $w = (1-\alpha)Y/L$. O governo gasta $G$, cobra $\tau_k$ e $\tau_w$ e
devolve o saldo como transferência, cada família atualiza suas crenças e
decide quanto consumir, e o que sobra é poupado, com o investimento dado por
$I = Y - C - G$.

Toda família resolve o problema de consumo e poupança com utilidade CRRA e
sem endividamento, segundo a equação de Euler

$$
c_t^{-\theta} = e^{-\rho/4}\,(1 + r_{t+1}/4)\,e^{-\theta g/4}\,E_t\!\left[c_{t+1}^{-\theta}\right],
$$

resolvida pelo método da grade endógena (Carroll, 2006). O que muda de uma
etapa da microfundamentação para outra é o que a família supõe sobre os juros
e os salários futuros, e com crenças $(r^e, w^e)$ ela age como se essas
crenças fossem durar para sempre, no espírito da *anticipated utility* de
Kreps (1998), usando a política ótima correspondente, pré-calculada numa
tabela indexada pela crença de juro.

## Etapas da microfundamentação

| Etapa | Hipótese | Referência | Parâmetro |
|---|---|---|---|
| Previsão perfeita | conhece o caminho futuro de preços, consistente com as escolhas de todos (expectativas racionais sem risco agregado) | benchmark neoclássico | — |
| Crenças fixas | crê que os preços do estado estacionário valem para sempre (a regra "fundamentalista") | Brock e Hommes (1997) | — |
| Aprendizado | atualiza as crenças com ganho constante, $r^e \leftarrow r^e + \gamma (r - r^e)$ | Evans e Honkapohja (2001); Milani (2007) | $\gamma = 0{,}02$ |
| Heurísticas | cada família escolhe entre as regras fundamentalista, de aprendizado e ingênua (preços atuais), por um logit do erro passado de cada uma | Brock e Hommes (1997); Anufriev e Hommes (2012) | intensidade 1, memória 0,7 |
| Informação rígida | só 25% das famílias atualizam a informação a cada trimestre | Mankiw e Reis (2002); Carroll (2003) | $\lambda = 0{,}25$ |
| Atenção limitada | percebe só 85% do desvio dos preços em relação ao estado estacionário | Gabaix (2020) | $\bar m = 0{,}85$ |

A previsão perfeita é resolvida como um ponto fixo em `transicao.py`, em que,
dado um caminho para o capital, a política de cada trimestre sai da grade
endógena de trás para frente, as famílias a seguem e o capital que elas
acumulam atualiza o caminho, até que os dois coincidam.

## Verificação

Com previsão perfeita, o ABM reproduz o Aiyagari contínuo, porque no
experimento da [Lei 15.270](../../../../Politicas/Lei-15270/README.md) o novo
estado estacionário depois do aumento de $\tau_k$ tem capital 1,45% menor com
devolução uniforme e 1,41% menor com isenção, os mesmos números obtidos em
`Politicas/Lei-15270/equilibrio_geral/` por um método independente, com
grade endógena trimestral e histograma aqui e equações de HJB e Kolmogorov em
tempo contínuo lá, e os ganhos de bem-estar por grupo também coincidem. Sem
risco, a política coincide com a fórmula fechada do consumo com renda
constante, e a equação de Euler vale com erro menor que 0,2% em pontos fora
da grade. As 20 mil famílias sorteadas da distribuição estacionária mantêm
essa distribuição por 400 trimestres, a identidade $Y = C + I + G$ e o
orçamento do governo fecham a cada trimestre e a poupança agregada é igual ao
capital mais o investimento líquido.

Na história guiada pelos dados, o ABM reproduz o PIB e o gasto observados com
erro de $10^{-14}$, e mudar qualquer dado posterior à origem, seja o PIB, os
dados anuais ou a PNAD, não altera nenhuma previsão. A previsão perfeita
calculada pelo histograma permanece no equilíbrio com erro menor que
$10^{-6}$ quando parte da distribuição estacionária, o histograma das famílias
sorteadas preserva a massa, a riqueza média e o peso de cada tipo, e as
famílias simuladas seguem o caminho do contínuo por 20 anos com erro menor
que 0,5%. Por fim, a população inicial é estratificada, com o número exato de
famílias em cada estado de renda, porque um sorteio simples erra a oferta de
trabalho em cerca de 1%, já que o tipo de maior renda produz quatro vezes a
média, o que cria um déficit público inexistente no modelo e, na devolução
por isenção, chega a inverter o sinal do efeito sobre os mais pobres, algo que
um teste impede de voltar. Ao todo são 40 testes (`test_*.py`).

## O equilíbrio é imposto ou emergente?

Nos experimentos da Lei 15.270 a economia parte do equilíbrio estacionário,
mas em `convergencia.py` ela parte de longe dele, com a renda de cada família
no estado estacionário e a riqueza fora do lugar. São quatro partidas, com o
capital 50% abaixo, o capital 50% acima, a mesma riqueza para todos e 1% das
famílias com toda a riqueza, além do próprio equilíbrio como controle, sem
reforma e sem choques agregados, ao longo de 1.000 anos. As crenças começam
dos preços que as famílias observam no primeiro trimestre, de modo que quem
aprende não sabe onde fica o equilíbrio.

Com previsão perfeita, a convergência é imposta, porque o caminho de preços
termina no estado estacionário por construção, e ela é calculada para um
contínuo de famílias, pelo histograma, e não para as 20 mil. Com famílias
simuladas seguindo um caminho de preços dado, o ruído de amostragem se
acumula, já que quem não reage aos preços realizados torna o equilíbrio
instável e o desvio dobra mais ou menos a cada 20 anos, o que mostra que a
estabilidade do equilíbrio com expectativas racionais vem de cada família
refazer seus planos, e não do comportamento em si. Nas outras regras, nada é
imposto.

A tabela seguinte mostra quantos anos o capital leva para entrar de vez na
faixa de ±1% em torno do equilíbrio, com a faixa percorrida entre parênteses,
e o capital depois de 1.000 anos em relação ao de equilíbrio.

| Regra | Partindo 50% abaixo | Partindo 50% acima | Depois de 1.000 anos, todas as partidas |
|---|---|---|---|
| Previsão perfeita | 66 (0,50 a 1,00) | 62 (1,00 a 1,50) | 1,000 (1,007 partindo de 1% com tudo) |
| Crenças fixas | nunca | nunca | 1,84 |
| Aprendizado | 171 (0,50 a 1,23) | 224 (0,73 a 1,50) | 0,997 a 1,005 |
| Heurísticas | 118 (0,50 a 1,02) | 46 (0,99 a 1,50) | 0,997 a 1,004 |
| Informação rígida | 165 (0,50 a 1,25) | 155 (0,70 a 1,50) | 1,001 a 1,005 |
| Atenção limitada | 59 (0,50 a 1,01) | 50 (1,00 a 1,50) | 0,997 a 1,002 |

A distribuição da riqueza é resumida pelo Gini depois de 1.000 anos, que no
equilíbrio vale 0,52, e pela distância de Kolmogorov-Smirnov até a
distribuição estacionária, a maior diferença entre as duas funções de
distribuição.

| Regra | Riqueza igual: Gini | Riqueza igual: distância | 1% com tudo: Gini | 1% com tudo: distância | Controle: distância |
|---|---|---|---|---|---|
| Previsão perfeita | 0,50 | 0,027 | 0,59 | 0,081 | 0,000 |
| Crenças fixas | 0,35 | 0,62 | 0,35 | 0,62 | 0,62 |
| Aprendizado | 0,50 | 0,038 | 0,58 | 0,067 | 0,013 |
| Heurísticas | 0,50 | 0,040 | 0,56 | 0,047 | 0,017 |
| Informação rígida | 0,50 | 0,040 | 0,58 | 0,071 | 0,018 |
| Atenção limitada | 0,50 | 0,037 | 0,56 | 0,051 | 0,012 |

![Convergência a partir de longe do equilíbrio](figuras/convergencia.png)

Com racionalidade limitada, o equilíbrio emerge, e com aprendizado,
heurísticas, informação rígida e atenção limitada o capital volta ao
equilíbrio a partir de todas as partidas sem que nada o imponha. O aprendizado
e a informação rígida, que dependem apenas do passado, ultrapassam o ponto em
ciclos longos e amortecidos, porque, partindo de 50% abaixo, o juro fica alto
por anos, as famílias passam a acreditar nele e poupam demais, e o capital
chega a 1,23 vez o de equilíbrio antes de voltar, levando de 155 a 225 anos
para se acertar. As heurísticas e a atenção limitada, que ancoram parte das
crenças no equilíbrio, chegam em 46 a 118 anos, às vezes mais depressa que a
previsão perfeita.

Com crenças fixas a economia vai para outro lugar, e de todas as partidas,
inclusive do próprio equilíbrio, o capital segue para 1,84 vez o de equilíbrio
e o Gini para 0,35. Trata-se de um ponto de repouso estável, o mesmo para
todas as partidas, que emerge das decisões mas não é o equilíbrio de
expectativas racionais, já que nele o juro líquido fica 4,2 p.p. abaixo do que
as famílias acreditam e elas poupam para sempre à espera de um juro que nunca
vem, o que mostra que emergir não garante chegar ao equilíbrio certo.

A desigualdade também emerge, e partindo da riqueza igual para todos o Gini
sobe de 0 para 0,50 em 1.000 anos, apenas com os choques de renda e a poupança
precaucional, na mesma velocidade em todas as regras e inclusive com
previsão perfeita, o que indica que essa velocidade é determinada pelo
processo de renda e não pelas expectativas. A distribuição, aliás, converge
muito mais devagar que o capital, que se acerta em décadas enquanto ela leva
séculos, e partindo de 1% com toda a riqueza nem em 1.000 anos ela chega ao
equilíbrio (Gini de 0,56 a 0,59), com o capital acima do equilíbrio em mais de
1% por 540 a 890 anos. Com um número finito de famílias a distribuição nunca
chega exatamente, e no controle as 20 mil famílias ficam a uma distância de
0,012 a 0,018 da distribuição estacionária, que é o piso dado pelo ruído de
amostragem e é alcançado pelas regras partindo de 50% abaixo ou acima.

Quando as crenças começam nos preços do equilíbrio, e não nos observados, o
destino é o mesmo, mas o caminho muda, porque partindo de 50% abaixo quem
aprende começa acreditando no salário de equilíbrio, mais alto que o
verdadeiro, e gasta, de modo que o capital cai até 0,35 antes de subir
(`resultados/convergencia.csv`).

## O que as famílias escolhem, 1996-2026

Com as heurísticas (`heuristicas.py`), o ABM percorre a história brasileira
desde 1996 reproduzindo o PIB e o gasto observados, e cada família escolhe a
regra de previsão que vinha acertando mais.

![Regras escolhidas pelas famílias](figuras/heuristicas.png)

Nada disso foi imposto. Nos anos de juros estáveis, de 1999 a 2005, a regra
fundamentalista, que aposta no estado estacionário, divide as famílias com o
aprendizado, e a partir de 2006 a regra ingênua passa a dominar, com duas
interrupções em que o aprendizado e a regra fundamentalista voltam, em 2010 e
em 2014-2015. Depois da recessão de 2015-2016, quando o juro líquido cai e
não volta, a regra ingênua fica com quase todas as famílias por quase dez
anos, já que quem aposta na volta ao passado erra sistematicamente, e só em
2025, com os preços estabilizados, o aprendizado volta a ganhar espaço.

## Previsão fora da amostra

Em cada origem, o ABM é calibrado apenas com o que se sabia naquela data, com
dados anuais até dois anos antes, a PNAD até a origem e a tendência dada pelo
PIB trimestral até a origem, e percorre a história desde 1996 reproduzindo o
PIB e o gasto observados, o que fixa na origem a distribuição de riqueza, os
estados de renda e as crenças das famílias. Um VAR(1) para o crescimento da
produtividade inferida e do gasto gera os choques futuros, e 200 simulações
com choques antitéticos dão a previsão e sua incerteza, seguindo o desenho de
Poledna, Miess, Hommes e Rabitsch (2023) para o ABM da Áustria. A tabela
mostra o RMSE relativo ao AR(1) sem as janelas da pandemia, com valores abaixo
de 1 indicando que o modelo errou menos e o negrito marcando as diferenças
significativas a 5% pelo teste de Diebold-Mariano.

| Modelo | PIB h=1 | PIB h=4 | PIB h=8 | Consumo h=1 | Consumo h=4 | FBCF h=1 | FBCF h=2 | FBCF h=4 |
|---|---|---|---|---|---|---|---|---|
| VAR(1) | 0,92 | 0,95 | 0,97 | 0,95 | 0,95 | 0,90 | 0,87 | 0,94 |
| Equilíbrio geral, tendência trimestral | 1,03 | 1,03 | 1,02 | 1,07 | 1,04 | 1,01 | 1,02 | 1,08 |
| ABM 1: crenças fixas | 1,00 | 1,00 | 1,01 | 0,96 | 0,96 | 0,98 | 1,03 | 1,08 |
| ABM 1: aprendizado | 1,00 | 1,02 | 1,03 | 1,00 | 1,00 | 0,98 | 1,00 | 1,06 |
| ABM 1: heurísticas | 0,97 | 0,95 | 0,96 | 1,19 | 1,13 | 0,89 | **0,82** | 0,82 |
| ABM 1: informação rígida | 1,01 | 1,03 | 1,05 | 0,99 | 0,98 | 1,02 | 1,05 | 1,11 |
| ABM 1: atenção limitada | 0,97 | 0,95 | 0,96 | 1,00 | 0,99 | 0,92 | 0,94 | 0,99 |

![ABM e equilíbrio geral contra o AR(1)](../figuras/rmse_abm_sem_pandemia.png)

Fora da pandemia, as regras que olham para os preços correntes preveem
melhor, e com heurísticas e atenção limitada o ABM erra de 3% a 6% menos que o
AR(1) no PIB, enquanto com heurísticas erra de 11% a 20% menos na FBCF, o
melhor resultado de todos os modelos para o investimento, significativo em
h = 2. Contra a média histórica, que usa as mesmas médias, o ganho chega a 28%
na FBCF, o que indica que é a dinâmica das decisões das famílias que acerta.

Cada regra, no entanto, acerta uma coisa diferente, porque as heurísticas
preveem bem o investimento e mal o consumo, com erro 19% maior que o do
AR(1), ao passo que as crenças fixas preveem bem o consumo, com erro 4% menor,
e mal o investimento. Quando as famílias reagem aos preços correntes, o
consumo fica suave demais e o investimento absorve os choques, e quando não
reagem acontece o contrário. Com a pandemia o ABM perde, já que os choques de
produtividade seguem um AR(1) que extrapola a queda de 2020 e a recuperação
seguinte, e as regras que olham para os preços correntes transformam isso em
grandes oscilações do investimento, de modo que na amostra completa o melhor
modelo é o equilíbrio geral com tendência trimestral. Com 40 a 50 origens, só
diferenças grandes aparecem nos testes, e na maior parte dos casos nada é
significativo. A incerteza também depende da regra, porque os intervalos de
90% do ABM com aprendizado, informação rígida e crenças fixas cobrem apenas de
53% a 73% dos investimentos realizados, enquanto os das heurísticas e da
atenção limitada cobrem de 82% a 100% do investimento, mas só de 60% a 77% do
consumo.

O consumo do governo é exógeno no ABM e segue o mesmo AR(1) da referência, de
modo que a comparação nessa variável não diz nada. O ABM sem leiloeiro é
discutido no [README dele](../abm2_sem_leiloeiro/README.md#previsão-fora-da-amostra),
as tabelas completas estão em [`../resultados/`](../resultados/) e as
previsões registradas para 2026-2028 estão em
[`../README.md`](../README.md#previsões-registradas).

## Como rodar

Os comandos rodam a partir da pasta `Econometria/`, com as dependências de
`Python/requirements.txt`.

```bash
python Python/macroeconomia/Forecast/Brasil/2013T4-2026T2/abm1_com_leiloeiro/convergencia.py   # partidas fora do equilíbrio (cerca de meia hora)
python Python/macroeconomia/Forecast/Brasil/2013T4-2026T2/abm1_com_leiloeiro/heuristicas.py    # regras escolhidas, 1996-2026
python Python/macroeconomia/Forecast/Brasil/2013T4-2026T2/comparacao.py --processos 4 --modelos abm_eq abm_apr abm_heu abm_inf abm_aten
python -m unittest discover -s Python/macroeconomia/Forecast/Brasil/2013T4-2026T2/abm1_com_leiloeiro -v
```

## Arquivos

| Arquivo | Conteúdo |
|---|---|
| `familias.py` | problema das famílias, com grade endógena, histograma estacionário, calibração de $\rho$, equilíbrio e tabela de políticas por crença de juro |
| `expectativas.py` | regras de formação de expectativas |
| `economia.py` | a economia com leiloeiro, com população inicial, trimestre com leiloeiro e governo, história guiada pelos dados e previsão por simulação |
| `transicao.py` | transição com previsão perfeita (ponto fixo), com as famílias simuladas ou com o histograma |
| `comum.py` | calibração com a amostra anual inteira e cores das regras nas figuras, usadas aqui e nos experimentos da lei |
| `previsao_abm.py` | o ABM no protocolo de previsão fora da amostra |
| `convergencia.py` | partidas fora do equilíbrio, para ver se o capital e a distribuição da riqueza voltam sozinhos |
| `heuristicas.py` | as regras de previsão que as famílias escolhem de 1996 a 2026 |
| `test_*.py` | 40 testes |
| `resultados/`, `figuras/` | tabelas e figuras |

## Limitações e próximos passos

Na história guiada pelos dados, os dois ABMs explicam a queda do PIB pelo
crescimento da produtividade, e o ABM 2 explica também o desemprego pela
separação, o que transforma as recessões em choques de oferta. Numa
recessão, a produtividade cai, o capital por unidade de eficiência sobe e o
retorno do capital cai, e no ABM 2 com heurísticas as famílias que levam o
retorno corrente às crenças baixam o custo do capital das firmas, fazendo o
investimento do modelo subir na recessão de 2015 e cair depois, justamente
quando nos dados ele se recuperava, o que revela a falta do canal de demanda
e de crédito que derrubou o investimento brasileiro em 2015-2016.

As expectativas racionais estão implementadas apenas para transições sem
risco agregado, e com choques agregados a referência racional exigiria o
método de Krusell e Smith (1998). Os parâmetros comportamentais vêm da
literatura e não foram estimados, e estimá-los pelo método dos momentos
simulados, com os dados de expectativas do Focus e da FGV, é uma extensão
natural. Como no Aiyagari, a riqueza é menos concentrada que nos dados e
converge devagar, e partindo de longe a distribuição leva séculos para se
estabilizar, como mostra a seção sobre convergência. Por fim, algo ainda é
imposto, porque com o leiloeiro os mercados se equilibram a cada trimestre, e
mesmo sem ele as famílias formam suas políticas com o risco de desemprego da
PNAD, e não com o que de fato vivem, além de a tabela de políticas supor, nos
dois casos, o perfil de transferências do estado estacionário e de as regras
de crenças fixas e de atenção limitada conhecerem o equilíbrio por definição.
