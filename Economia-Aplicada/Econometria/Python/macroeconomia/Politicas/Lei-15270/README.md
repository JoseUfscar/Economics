# Lei 15.270/2025 e a tributação da renda do capital

Esta pasta estuda os efeitos de um aumento da tributação da renda do capital
do tamanho previsto na Lei 15.270/2025, equivalente a 0,85 p.p. na alíquota
efetiva sobre a renda líquida do capital, em três modelos calibrados para o
Brasil que respondem a perguntas complementares.

| Pasta | Modelo | Pergunta |
|---|---|---|
| [`equilibrio_geral/`](equilibrio_geral/README.md) | Ramsey-Cass-Koopmans com governo e Aiyagari com famílias heterogêneas, em tempo contínuo, com a [nota técnica](equilibrio_geral/nota_tecnica.pdf) | quanto a economia perde e quem ganha e quem perde |
| `abm1_com_leiloeiro/` | o [ABM com leiloeiro](../../Forecast/Brasil/2013T4-2026T2/abm1_com_leiloeiro/README.md), com cinco regras de expectativas | as conclusões valem quando as famílias não são plenamente racionais? |
| `abm2_sem_leiloeiro/` | o [ABM sem leiloeiro](../../Forecast/Brasil/2013T4-2026T2/abm2_sem_leiloeiro/README.md), com firmas, preços, salários e busca | e quando os preços não vêm de um equilíbrio? |

O código dos dois ABMs fica na pasta de previsão,
[`Forecast/Brasil/2013T4-2026T2/`](../../Forecast/Brasil/2013T4-2026T2/README.md),
porque serve também à previsão, e aqui ficam apenas os experimentos da lei,
com seus resultados e figuras. No sentido inverso, a calibração do equilíbrio
geral guardada aqui é usada pelos modelos de previsão.

## No equilíbrio geral

Com agente representativo, o aumento reduz no longo prazo o capital em 1,46%,
o PIB e os salários em 0,66% e o consumo em 0,63%, com uma perda de bem-estar
de 0,084% do consumo, e a receita de longo prazo fica em 90% da estática. Com
famílias heterogêneas o agregado quase não muda, mas a forma de devolver a
receita decide quem ganha, já que a metade mais pobre ganha 0,58% do consumo
quando a receita é devolvida igualmente a todos e perde 0,42% quando ela vai
apenas para os empregados do grupo intermediário, como na isenção do imposto
de renda prevista na lei. Os detalhes estão no [README do modelo](equilibrio_geral/README.md)
e na [nota técnica](equilibrio_geral/nota_tecnica.pdf).

## No ABM com leiloeiro

O experimento aplica de surpresa o mesmo aumento de $\tau_k$ usado em
[`equilibrio_geral/`](equilibrio_geral/README.md) e devolve a receita nova
igualmente a todos ou apenas aos empregados do grupo intermediário, a faixa
beneficiada pela isenção do imposto de renda. Para cada regra de
expectativas, a economia com reforma e a economia sem reforma partem do mesmo
equilíbrio e recebem os mesmos sorteios de renda para cada família, e o
bem-estar é medido pela utilidade descontada que cada família de fato obtém
ao longo de 150 anos. A tabela mostra o ganho médio de bem-estar em % do
consumo e, entre parênteses, a porcentagem de famílias que ganham.

| Devolução | Grupo | Previsão perfeita | Aprendizado | Heurísticas | Informação rígida | Atenção limitada | Aiyagari contínuo |
|---|---|---|---|---|---|---|---|
| Uniforme | 50% com menor renda | +0,53 (100) | +0,43 (100) | +0,53 (100) | +0,42 (100) | +0,50 (100) | +0,58 (100) |
| Uniforme | 40% seguintes | −0,06 (29) | −0,11 (5) | −0,06 (28) | −0,11 (4) | −0,08 (21) | −0,06 (29) |
| Uniforme | 10% com maior renda | −0,34 (0) | −0,37 (0) | −0,34 (0) | −0,37 (0) | −0,35 (0) | −0,35 (0) |
| Uniforme | Todos | +0,21 (61) | +0,13 (52) | +0,21 (61) | +0,13 (52) | +0,19 (59) | +0,23 (62) |
| Isenção | 50% com menor renda | −0,48 (0) | −0,51 (0) | −0,44 (0) | −0,50 (0) | −0,50 (0) | −0,42 (0) |
| Isenção | 40% seguintes | +0,51 (99) | +0,43 (99) | +0,49 (99) | +0,42 (99) | +0,49 (99) | +0,49 (100) |
| Isenção | 10% com maior renda | −0,44 (0) | −0,45 (0) | −0,43 (0) | −0,45 (0) | −0,44 (0) | −0,44 (0) |
| Isenção | Todos | −0,08 (40) | −0,13 (40) | −0,07 (40) | −0,13 (40) | −0,10 (40) | −0,06 (40) |

![Bem-estar por grupo e regra](abm1_com_leiloeiro/figuras/lei_bem_estar.png)

Quando as famílias não são plenamente racionais, quem ganha e quem perde
continua o mesmo, porque em todas as regras a devolução uniforme beneficia a
metade mais pobre e a devolução que imita a lei a prejudica, o que mostra que
as conclusões distributivas de `equilibrio_geral/` resistem à forma das
expectativas. O tamanho dos efeitos, no entanto, muda, e com aprendizado ou
informação rígida os ganhos agregados encolhem cerca de um terço, enquanto
quase ninguém do grupo intermediário ganha com a devolução uniforme (5%,
contra 29% com previsão perfeita).

O caminho do capital também muda com o aprendizado. Logo depois da reforma o
juro líquido cai, e quem tem previsão perfeita sabe que ele voltará a subir à
medida que o capital diminui, mas quem aprende com o passado toma a queda como
permanente. Como a poupança é muito sensível ao juro esperado, já que o juro
de equilíbrio fica apenas 0,17 p.p. abaixo do ponto em que a poupança
explode, essas famílias poupam de menos e o capital cai além do novo estado
estacionário, chegando a −2,1% ou −2,2% por volta de 30 anos, contra −1,45% no
longo prazo, até que o juro volte a subir e elas corrijam tarde. O resultado
são ciclos longos e amortecidos e um custo de bem-estar maior, ao passo que,
com previsão perfeita, o ajuste é monótono, embora o longo prazo seja
praticamente o mesmo em todas as regras (−1,39% a −1,45% nos últimos 20
anos). As heurísticas e a atenção limitada ficam perto da previsão perfeita
porque ancoram parte das crenças no novo estado estacionário definido pela
reforma, e só o aprendizado e a informação rígida dependem inteiramente do
passado.

![Capital depois da reforma](abm1_com_leiloeiro/figuras/lei_capital.png)

Como os parâmetros comportamentais vêm da literatura, a devolução uniforme foi
refeita com valores abaixo e acima de cada um
(`abm1_com_leiloeiro/resultados/sensibilidade.csv`).

| Regra | Parâmetro | 50% com menor renda | 40% seguintes | 10% com maior renda | Todos | Menor capital no caminho |
|---|---|---|---|---|---|---|
| Aprendizado | ganho 0,01 | +0,40 | −0,13 | −0,37 | +0,11 | −2,9% |
| Aprendizado | ganho 0,05 | +0,46 | −0,10 | −0,36 | +0,15 | −1,6% |
| Heurísticas | intensidade 0,2 | +0,54 | −0,06 | −0,34 | +0,21 | −1,5% |
| Heurísticas | intensidade 5 | +0,51 | −0,07 | −0,35 | +0,19 | −1,5% |
| Informação rígida | $\lambda$ = 0,10 | +0,42 | −0,12 | −0,37 | +0,12 | −2,4% |
| Informação rígida | $\lambda$ = 0,50 | +0,43 | −0,11 | −0,37 | +0,13 | −2,1% |
| Atenção limitada | $\bar m$ = 0,70 | +0,54 | −0,06 | −0,34 | +0,21 | −1,5% |
| Atenção limitada | $\bar m$ = 0,95 | +0,48 | −0,08 | −0,35 | +0,17 | −1,4% |

Os sinais nunca mudam, e o que mais pesa é a velocidade do aprendizado, pois
quanto mais devagar as famílias atualizam as crenças, maior a queda do capital
antes da recuperação e menor o ganho de bem-estar, enquanto as heurísticas e a
atenção limitada quase não dependem dos parâmetros.

Vale notar ainda que crer para sempre no estado estacionário não é
expectativa racional fora dele. Com essas crenças e sem nenhuma reforma, a
economia se afasta sozinha do equilíbrio, porque um capital um pouco maior
eleva salários e transferências, as famílias poupam o excedente e o capital
sobe ainda mais, em 0,2% em 25 anos, 1,6% em 75 e 8,4% em 150. Com
aprendizado, a mesma economia permanece no equilíbrio, dentro de ±0,4%, o
que confirma que o equilíbrio de expectativas racionais é estável sob
aprendizado, como em Evans e Honkapohja (2001), e justifica usar a previsão
perfeita, e não as crenças fixas, como referência neoclássica do experimento
(`abm1_com_leiloeiro/resultados/estabilidade.csv`).

## No ABM sem leiloeiro

> Os números desta seção foram calculados antes de duas correções no ABM 2,
> que passou a ancorar os salários na média do mercado e a repor o
> crescimento de tendência no investimento, como descrito no
> [README dele](../../Forecast/Brasil/2013T4-2026T2/abm2_sem_leiloeiro/README.md),
> e ainda serão refeitos com `abm2_sem_leiloeiro/lei_sem_leiloeiro.py`.

O mesmo aumento de $\tau_k$ é aplicado à economia descentralizada, com
aprendizado, em 48 sementes. Como essa economia flutua sozinha, os caminhos
com e sem reforma se separam depois de alguns anos mesmo com os mesmos números
aleatórios, e uma única semente misturaria o efeito da lei com o ciclo, algo
que a média de 48 sementes resolve
(`abm2_sem_leiloeiro/resultados/mercados_lei_15270_resumo.csv`). A tabela
traz o ganho médio de bem-estar em % do consumo, com o erro-padrão entre
parênteses.

| Devolução | Grupo | Sem leiloeiro | Aiyagari contínuo |
|---|---|---|---|
| Uniforme | 50% com menor renda | +0,62 (0,31) | +0,58 |
| Uniforme | 40% seguintes | −0,03 (0,14) | −0,06 |
| Uniforme | 10% com maior renda | −0,28 (0,09) | −0,35 |
| Uniforme | Todos | +0,27 (0,22) | +0,23 |
| Isenção | 50% com menor renda | −1,25 (0,33) | −0,42 |
| Isenção | 40% seguintes | +0,78 (0,14) | +0,49 |
| Isenção | 10% com maior renda | −0,38 (0,09) | −0,44 |
| Isenção | Todos | −0,35 (0,23) | −0,06 |

| Devolução | Capital no longo prazo, sem leiloeiro | Novo equilíbrio walrasiano | Desemprego |
|---|---|---|---|
| Uniforme | −2,2% (0,6) | −1,45% | 0,00 p.p. (0,02) |
| Isenção | −1,4% (0,6) | −1,41% | 0,00 p.p. (0,02) |

![A lei sem leiloeiro](abm2_sem_leiloeiro/figuras/mercados_lei_capital.png)

As linhas tracejadas da figura marcam o novo equilíbrio walrasiano. As
conclusões distributivas sobrevivem à saída do leiloeiro, porque, com firmas
que fixam preços, busca e racionamento, a devolução uniforme continua
beneficiando a metade mais pobre e a que imita a lei continua prejudicando-a
e beneficiando o grupo intermediário. Com a isenção, porém, a perda dos mais
pobres é maior, de 1,25% do consumo contra 0,42% no Aiyagari, uma diferença
de mais de dois erros-padrão. A lei não altera o desemprego, que depende dos
fluxos do mercado de trabalho, sobre os quais o imposto sobre o capital não
atua. Por fim, o efeito não pode ser observado família por família, já que em
qualquer grupo cerca de metade ganha e metade perde, porque a trajetória de
cada uma, com quem é demitido, quando e de qual firma, muda com a reforma, e
o efeito da lei só aparece na média de muitas famílias e de muitas sementes.

## Como rodar

Os comandos rodam a partir da pasta `Econometria/`, com as dependências de
`Python/requirements.txt`.

```bash
python Python/macroeconomia/Politicas/Lei-15270/equilibrio_geral/experimentos.py        # agente representativo
python Python/macroeconomia/Politicas/Lei-15270/equilibrio_geral/experimentos_ha.py     # famílias heterogêneas
python Python/macroeconomia/Politicas/Lei-15270/abm1_com_leiloeiro/lei_com_leiloeiro.py # ABM com leiloeiro (cerca de 10 minutos)
python Python/macroeconomia/Politicas/Lei-15270/abm2_sem_leiloeiro/lei_sem_leiloeiro.py # ABM sem leiloeiro (cerca de 15 minutos com 4 núcleos)
python Python/macroeconomia/rodar_testes.py Lei-15270
```
