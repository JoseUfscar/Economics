# Tributação do capital no Brasil em equilíbrio geral

Modelos de equilíbrio geral em tempo contínuo, calibrados com dados da PWT
11.0, do Ipea e do IBGE, para medir os efeitos de um aumento da tributação
da renda do capital do tamanho da Lei 15.270/2025. A primeira parte usa um
agente representativo (Ramsey-Cass-Koopmans com governo) e mede quanto a
economia perde em capital, produto, salários e receita, no longo prazo e na
transição, com choques inesperados e anunciados. A segunda usa famílias
heterogêneas (Aiyagari, resolvido pelas equações de Hamilton-Jacobi-Bellman
e Kolmogorov), com risco de desemprego e desigualdade de renda calibrados
com a PNAD Contínua, e mostra quem ganha e quem perde.

A derivação completa, os algoritmos e a discussão estão na
[nota técnica](nota_tecnica.pdf).

## Parte 1: agente representativo

Em unidades de trabalho efetivo ($k=K/AL$, $c=C/AL$), o equilíbrio é

$$
\dot k=k^\alpha-c-\hat g-(\delta+n+g)k,\qquad
\frac{\dot c}{c}=\frac{(1-\tau_k)(\alpha k^{\alpha-1}-\delta)-\rho-\theta g}{\theta},
$$

com imposto $\tau_k$ sobre a renda líquida do capital, imposto $\tau_c$ sobre o
consumo, gasto público $\hat g$ e transferências que fecham o orçamento. A
política pode mudar em datas conhecidas, o que cobre choques inesperados,
anunciados e temporários; os regimes são empilhados num único problema de
contorno.

A calibração usa médias de 2000 a 2023: $\alpha=0{,}451$, $\delta=0{,}0605$,
$n=0{,}0143$, $g=0{,}0067$, $\theta=2$, $\tau_k=0{,}259$ (18% da renda bruta,
segundo Rabelo, 2025) e $\rho=0{,}0889$ para reproduzir $K/Y=2{,}27$ e
$G/Y=0{,}192$. O imposto sobre o consumo começa em zero. O investimento e o
consumo, que não foram usados como alvo, ficam perto dos dados: 18,5% e 62,3%
do PIB no modelo, contra 17,9% e 60,9%.

A nova receita estimada para 2026 (R$ 34,12 bi) equivale a +0,85 p.p. na
alíquota efetiva sobre a renda líquida do capital. No longo prazo:

| Efeito | Valor |
|---|---|
| Estoque de capital | −1,46% |
| PIB e salários | −0,66% |
| Consumo | −0,63% |
| Receita estática | 0,268% do PIB |
| Receita de longo prazo | 0,242% do PIB (90% da estática) |
| Bem-estar (variação equivalente) | −0,084% do consumo |
| Pico da curva de Laffer | $\tau_k$ = 66% (hoje: 26%) |

Esses números provavelmente superestimam a queda do capital. Um quarto da
receita nova vem do imposto sobre dividendos remetidos a não residentes, que
numa economia aberta recai sobre o capital estrangeiro, e boa parte do resto
vem da tributação de dividendos, que afeta pouco o investimento financiado
com lucros retidos. A nota discute os dois pontos e um terceiro, que vai na
direção contrária: a alíquota marginal das famílias do topo sobe bem mais que
a média.

![Transição após o aumento de tau_k](figuras/lei_15270.png)

Com o anúncio antecipado, o consumo sobe já na notícia e o capital começa a
cair antes de a lei valer. Na data da vigência, a economia chega exatamente
ao novo braço estável:

![Diagrama de fase](figuras/diagrama_fase.png)

A nota traz ainda a curva de Laffer de longo prazo, um aumento temporário do
gasto público, um aumento anunciado do imposto sobre o consumo e a
sensibilidade a $\theta$, à alíquota inicial e ao tamanho do choque.

### Estimação estrutural

`estimacao.py` estima $\rho$ e $\theta$ por mínimos quadrados não lineares em
dados sintéticos: o consumo integrado no ano e o capital no fim do ano de duas
transições de 25 anos, com erro de medida de 1%. Em 100 réplicas de Monte
Carlo, o viés é desprezível, o erro-padrão bate com a dispersão das
estimativas e a cobertura dos intervalos de 95% fica entre 96% e 97%. O
estado estacionário só identifica $\rho+\theta g$; são as transições que
separam os dois parâmetros.

![Monte Carlo](figuras/monte_carlo.png)

## Parte 2: famílias heterogêneas

Cada dinastia tem riqueza $a\ge0$ e produtividade $z$, que segue uma cadeia de
Markov. Com $r=(1-\tau_k)(R-\delta)$, a família resolve

$$
\beta V_z(a)=\max_c\,u(c)+V_z'(a)\big[(r-n-g)a+(1-\tau_w)wz+T_z-c\big]
+\sum_{z'}q_{zz'}\big[V_{z'}(a)-V_z(a)\big],
$$

e a distribuição de riqueza sai da equação de Kolmogorov. O processo de renda
vem da PNAD Contínua de 2012 a 2025. A desocupação média é de 9,7%, e dois
tipos de desempregado reproduzem exatamente a distribuição do tempo de
procura: 42% são de curta duração (2,9 meses em média) e o resto, de longa
duração (2 anos). Há três tipos permanentes de renda (os 50% com menor renda,
os 40% seguintes e os 10% com maior renda), com renda relativa de 0,38, 1,00
e 4,10, como na massa de rendimento do trabalho. Desempregada, a família
recebe 40% da renda do trabalho do seu tipo. Esse número é uma escolha de
calibração, e nesse modelo o desempregado continua produzindo essa fração;
no ABM sem leiloeiro, ao contrário, ele não produz e recebe do governo.

O Gini da renda no modelo é 0,48, e o do rendimento domiciliar per capita do
IBGE, 0,53 (os conceitos não são idênticos). A riqueza é menos concentrada
que nos dados: 44% com os 10% mais ricos, contra cerca de 80% segundo o World
Inequality Database. É uma limitação conhecida desse tipo de modelo.

O mesmo aumento de 0,85 p.p. em $\tau_k$ é aplicado de surpresa, e o bem-estar
de cada família é medido incluindo toda a transição. A receita nova volta de
duas formas: igual para todas as famílias ou só para os empregados do grupo
intermediário. Esse grupo termina no P90 da PNAD de 2025 (R$ 6.985 por mês) e
contém quase toda a faixa beneficiada pela lei, de R$ 3 mil a R$ 7.350; só a
ponta de cima, onde o desconto já é pequeno, fica nos 10% com maior renda.

| Grupo | Devolução uniforme | Devolução isenção |
|---|---|---|
| 50% com menor renda | +0,58% (todos ganham) | −0,42% (todos perdem) |
| 40% seguintes | −0,06% (29% ganham) | +0,49% (todos ganham) |
| 10% com maior renda | −0,35% (todos perdem) | −0,44% (todos perdem) |
| Todos | +0,23% (62% ganham) | −0,06% (40% ganham) |

![Quem ganha e quem perde](figuras/ha_grupos.png)

O capital de longo prazo cai 1,45% com a devolução uniforme e 1,41% com a
isenção, perto dos 1,46% do agente representativo. A distribuição dos ganhos,
por outro lado, depende da devolução. Com a devolução que imita a lei, a
metade mais pobre, que já era isenta, perde: arca com a queda dos salários
que a redução do capital provoca e não recebe a isenção.

A isenção custa menos que a receita nova (R$ 25,84 bi contra R$ 34,12 bi em
2026). Se o grupo intermediário recebe só a fração 25,84/34,12 da
transferência e o resto volta igualmente a todos, a metade mais pobre perde
0,18%, o grupo intermediário ganha 0,35%, os 10% com maior renda perdem 0,42%
e o ganho médio fica em zero (`resultados/ha_bem_estar.csv`).

## Como rodar

Da pasta `Econometria/`, com as dependências de `Python/requirements.txt`:

```bash
python Python/macroeconomia/Politicas/Lei-15270/equilibrio_geral/calibracao.py          # calibração
python Python/macroeconomia/Politicas/Lei-15270/equilibrio_geral/experimentos.py        # parte 1: experimentos e figuras
python Python/macroeconomia/Politicas/Lei-15270/equilibrio_geral/estimacao.py --replicas 100
python Python/macroeconomia/Politicas/Lei-15270/equilibrio_geral/calibracao_renda.py    # processo de renda (PNAD)
python Python/macroeconomia/Politicas/Lei-15270/equilibrio_geral/experimentos_ha.py     # parte 2 (cerca de 3 minutos)
python -m unittest discover -s Python/macroeconomia/Politicas/Lei-15270/equilibrio_geral -v
```

Os dados ficam em [`dados/brasil/`](../../../../../dados/brasil/README.md), com os
scripts que os baixam. A nota compila com `latexmk -pdf nota_tecnica.tex`
nesta pasta.

## Arquivos

| Arquivo | Conteúdo |
|---|---|
| `modelo.py` | agente representativo: estado estacionário, transição com vários regimes (problema de contorno), fluxos anuais, bem-estar |
| `calibracao.py` | alvos a partir dos dados, calibração e momentos |
| `experimentos.py` | parte 1: experimentos de política, sensibilidade e figuras |
| `estimacao.py` | simulação, estimação de $\rho$ e $\theta$ e Monte Carlo |
| `aiyagari.py` | famílias heterogêneas: HJB e Kolmogorov por diferenças finitas, equilíbrio, calibração de $\rho$, transição e bem-estar individual |
| `calibracao_renda.py` | risco de desemprego e tipos de renda a partir da PNAD Contínua |
| `experimentos_ha.py` | parte 2: quem ganha e quem perde, desigualdade e figuras |
| `resultados/ha_bem_estar.csv` | ganho de bem-estar por grupo e capital de longo prazo em cada devolução, usados pelos experimentos da lei nos ABMs |
| `test_*.py` | 54 testes: equações, soluções exatas, identidades contábeis, calibrações, experimentos e estimação |
| `nota_tecnica.tex`, `.pdf` | derivação, métodos, resultados e referências |

A [versão em Julia](../../../../../Julia/macroeconomia/equilibrio_geral/ramsey.jl)
refaz a calibração e resolve a parte 1 por *reverse shooting*, outro
algoritmo; os resultados coincidem com os do Python até a 6ª casa decimal.
