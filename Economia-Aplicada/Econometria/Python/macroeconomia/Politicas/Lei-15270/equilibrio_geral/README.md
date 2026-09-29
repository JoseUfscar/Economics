# Tributação do capital no Brasil em equilíbrio geral

Este projeto usa modelos de equilíbrio geral em tempo contínuo, calibrados com
dados da PWT 11.0, do Ipea e do IBGE, para medir os efeitos de um aumento da
tributação da renda do capital do tamanho previsto na Lei 15.270/2025. A
primeira parte, com agente representativo no modelo de Ramsey–Cass–Koopmans
com governo, pergunta quanto a economia perde em capital, produto, salários e
receita, no longo prazo e ao longo da transição, diante de choques
inesperados e anunciados. A segunda parte, com famílias heterogêneas no
modelo de Aiyagari resolvido pelas equações de Hamilton–Jacobi–Bellman e
Kolmogorov, pergunta quem ganha e quem perde quando o risco de desemprego e a
desigualdade de renda seguem a PNAD Contínua. A derivação completa, os
algoritmos e a discussão estão na [nota técnica](nota_tecnica.pdf).

## Parte 1 — agente representativo

Em unidades de trabalho efetivo, com $k=K/AL$ e $c=C/AL$, o equilíbrio é
descrito por

$$
\dot k=k^\alpha-c-\hat g-(\delta+n+g)k,\qquad
\frac{\dot c}{c}=\frac{(1-\tau_k)(\alpha k^{\alpha-1}-\delta)-\rho-\theta g}{\theta},
$$

em que $\tau_k$ incide sobre a renda líquida do capital, $\tau_c$ sobre o
consumo, $\hat g$ é o gasto público e as transferências fecham o orçamento do
governo. A política pode mudar em datas conhecidas, o que cobre choques
inesperados, anunciados e temporários, e os diferentes regimes são empilhados
num único problema de contorno.

A calibração usa médias de 2000 a 2023, com $\alpha=0{,}451$,
$\delta=0{,}0605$, $n=0{,}0143$, $g=0{,}0067$ e $\theta=2$, uma alíquota
$\tau_k=0{,}259$, que corresponde a 18% da renda bruta segundo Rabelo (2025),
e $\rho=0{,}0889$ escolhido para reproduzir $K/Y=2{,}27$, com $G/Y=0{,}192$. O
investimento e o consumo, que não foram usados como alvo, ficam próximos dos
dados, em 18,5% e 62,3% do PIB no modelo contra 17,9% e 60,9% observados.

A nova receita estimada para 2026, de R$ 34,12 bilhões, equivale a um aumento
de 0,85 p.p. na alíquota efetiva sobre a renda líquida do capital, com os
efeitos de longo prazo resumidos na tabela.

| Efeito | Valor |
|---|---|
| Estoque de capital | −1,46% |
| PIB e salários | −0,66% |
| Consumo | −0,63% |
| Receita estática | 0,268% do PIB |
| Receita de longo prazo | 0,242% do PIB (90% da estática) |
| Bem-estar (variação equivalente) | −0,084% do consumo |
| Pico da curva de Laffer | $\tau_k$ = 66% (hoje, 26%) |

![Transição após o aumento de tau_k](figuras/lei_15270.png)

O anúncio antecipado faz o consumo subir já no momento da notícia e o capital
começar a cair antes de a lei entrar em vigor, e na data da vigência a
economia chega exatamente ao novo braço estável.

![Diagrama de fase](figuras/diagrama_fase.png)

A nota traz ainda a curva de Laffer de longo prazo, um aumento temporário do
gasto público, um aumento anunciado do imposto sobre o consumo e a
sensibilidade dos resultados a $\theta$, à alíquota inicial e ao tamanho do
choque.

### Estimação estrutural

O script `estimacao.py` estima $\rho$ e $\theta$ por mínimos quadrados não
lineares em dados sintéticos que combinam o consumo integrado ao longo do ano
e o capital no fim do ano de duas transições de 25 anos, com erro de medida de
1%. Em 100 réplicas de Monte Carlo o viés é desprezível, o erro-padrão
coincide com a dispersão das estimativas e a cobertura dos intervalos de 95%
fica entre 96% e 97%. Como o estado estacionário identifica apenas a soma
$\rho+\theta g$, são as transições que permitem separar os dois parâmetros.

![Monte Carlo](figuras/monte_carlo.png)

## Parte 2 — famílias heterogêneas

Cada dinastia tem riqueza $a\ge0$ e uma produtividade $z$ que segue uma cadeia
de Markov, e resolve

$$
\beta V_z(a)=\max_c\,u(c)+V_z'(a)\big[(\tilde r-n-g)a+(1-\tau_w)wz+T_z-c\big]
+\sum_{z'}q_{zz'}\big[V_{z'}(a)-V_z(a)\big],
$$

enquanto a distribuição da riqueza sai da equação de Kolmogorov. O processo de
renda vem da PNAD Contínua de 2012 a 2025. O risco de desemprego reproduz a
desocupação média de 9,7%, e a distribuição do tempo de procura é
reproduzida exatamente por dois tipos de desempregado, 42% de curta duração,
com 2,9 meses em média, e o restante de longa duração, com 2 anos. A
desigualdade de renda vem de três tipos permanentes, os 50% com menor renda,
os 40% seguintes e os 10% com maior renda, com rendas relativas de 0,38, 1,00
e 4,10, como na massa de rendimento do trabalho. O Gini da renda no modelo é
de 0,48, contra 0,53 no IBGE, e a riqueza é menos concentrada que nos dados,
com 44% nas mãos dos 10% mais ricos contra cerca de 80% segundo o World
Inequality Database, uma limitação conhecida desse tipo de modelo.

O mesmo aumento de 0,85 p.p. em $\tau_k$ é aplicado de surpresa, e o
bem-estar de cada família é medido levando em conta toda a transição. A
receita nova volta às famílias de duas formas, igual para todas ou apenas
para os empregados do grupo intermediário, que contém a faixa de R$ 3 mil a
R$ 7,35 mil beneficiada pela isenção do imposto de renda na lei.

| Grupo | Devolução uniforme | Devolução isenção |
|---|---|---|
| 50% com menor renda | +0,58% (todos ganham) | −0,42% (todos perdem) |
| 40% seguintes | −0,06% (29% ganham) | +0,49% (todos ganham) |
| 10% com maior renda | −0,35% (todos perdem) | −0,44% (todos perdem) |
| Todos | +0,23% (62% ganham) | −0,06% (40% ganham) |

![Quem ganha e quem perde](figuras/ha_grupos.png)

O agregado quase não muda em relação ao agente representativo, com o capital
caindo 1,45% ou 1,41% contra 1,46%, mas a distribuição muda tudo. Com a
devolução que imita a lei, a metade mais pobre, que já era isenta, sai
perdendo, porque arca com a queda dos salários provocada pela redução do
capital sem receber a isenção.

## Como rodar

Os comandos rodam a partir da pasta `Econometria/`, com as dependências de
`Python/requirements.txt`. Os dados ficam em
[`dados/brasil/`](../../../../../dados/brasil/README.md), junto com os scripts
que os baixam, e a nota compila com `latexmk -pdf nota_tecnica.tex` nesta
pasta.

```bash
python Python/macroeconomia/Politicas/Lei-15270/equilibrio_geral/calibracao.py          # calibração
python Python/macroeconomia/Politicas/Lei-15270/equilibrio_geral/experimentos.py        # parte 1: experimentos e figuras
python Python/macroeconomia/Politicas/Lei-15270/equilibrio_geral/estimacao.py --replicas 100
python Python/macroeconomia/Politicas/Lei-15270/equilibrio_geral/calibracao_renda.py    # processo de renda (PNAD)
python Python/macroeconomia/Politicas/Lei-15270/equilibrio_geral/experimentos_ha.py     # parte 2 (cerca de 3 minutos)
python -m unittest discover -s Python/macroeconomia/Politicas/Lei-15270/equilibrio_geral -v
```

## Arquivos

| Arquivo | Conteúdo |
|---|---|
| `modelo.py` | agente representativo, com estado estacionário, transição com vários regimes (problema de contorno), fluxos anuais e bem-estar |
| `calibracao.py` | alvos a partir dos dados, calibração e momentos |
| `experimentos.py` | parte 1, com experimentos de política, sensibilidade e figuras |
| `estimacao.py` | simulação, estimação de $\rho$ e $\theta$ e Monte Carlo |
| `aiyagari.py` | famílias heterogêneas, com HJB e Kolmogorov por diferenças finitas, equilíbrio, calibração de $\rho$, transição e bem-estar individual |
| `calibracao_renda.py` | risco de desemprego e tipos de renda a partir da PNAD Contínua |
| `experimentos_ha.py` | parte 2, com quem ganha e quem perde, desigualdade e figuras |
| `test_*.py` | 53 testes de equações, soluções exatas, identidades contábeis, calibrações, experimentos e estimação |
| `nota_tecnica.tex`, `.pdf` | derivação, métodos, resultados e referências |

A [versão em Julia](../../../../../Julia/macroeconomia/equilibrio_geral/ramsey.jl)
refaz a calibração e resolve a primeira parte por *reverse shooting*, um
algoritmo diferente, e os resultados coincidem com os do Python até a sexta
casa decimal.
