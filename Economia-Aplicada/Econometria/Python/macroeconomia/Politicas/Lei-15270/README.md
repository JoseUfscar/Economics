# Lei 15.270/2025: tributação da renda do capital

Os efeitos de um aumento da tributação da renda do capital do tamanho da Lei
15.270/2025 (+0,85 p.p. na alíquota efetiva sobre a renda líquida do
capital), em três modelos calibrados para o Brasil:

| Pasta | Modelo | Pergunta |
|---|---|---|
| [`equilibrio_geral/`](equilibrio_geral/README.md) | Ramsey-Cass-Koopmans com governo e Aiyagari com famílias heterogêneas, em tempo contínuo, com a [nota técnica](equilibrio_geral/nota_tecnica.pdf) | quanto a economia perde e quem ganha e quem perde |
| `abm1_com_leiloeiro/` | o [ABM com leiloeiro](../../Forecast/Brasil/2013T4-2026T2/abm1_com_leiloeiro/README.md), com cinco regras de expectativas | as conclusões valem quando as famílias não são plenamente racionais? |
| `abm2_sem_leiloeiro/` | o [ABM sem leiloeiro](../../Forecast/Brasil/2013T4-2026T2/abm2_sem_leiloeiro/README.md), com firmas, preços, salários e busca | e quando os preços não vêm de um equilíbrio? |

Os códigos dos dois ABMs ficam na pasta de previsão
([`Forecast/Brasil/2013T4-2026T2/`](../../Forecast/Brasil/2013T4-2026T2/README.md)),
porque servem também à previsão; aqui ficam os experimentos da lei, os
resultados e as figuras. A calibração do equilíbrio geral, por sua vez, é
usada pelos modelos de previsão.

## No equilíbrio geral

No longo prazo, com agente representativo: capital −1,46%, PIB e salários
−0,66%, consumo −0,63% e bem-estar −0,084% do consumo; a receita de longo
prazo fica em 90% da estática. Com famílias heterogêneas, o agregado quase
não muda, mas a forma de devolver a receita decide quem ganha: devolvida
igual para todos, a metade mais pobre ganha 0,58% do consumo; devolvida só
aos empregados do grupo intermediário, como a isenção do imposto de renda
da lei, a metade mais pobre perde 0,42%. Os detalhes estão no
[README do modelo](equilibrio_geral/README.md) e na
[nota técnica](equilibrio_geral/nota_tecnica.pdf).

## No ABM com leiloeiro

O mesmo aumento de $\tau_k$ de [`equilibrio_geral/`](equilibrio_geral/README.md) (+0,85 p.p. sobre a renda
líquida do capital, de surpresa), com a receita nova devolvida igual para
todos ou só aos empregados do grupo intermediário, a faixa beneficiada pela
isenção do imposto de renda. Para cada regra, a economia com e sem reforma
parte do mesmo equilíbrio e recebe os mesmos sorteios de renda de cada
família; o bem-estar é a utilidade descontada que cada família de fato obtém
em 150 anos.

Ganho médio de bem-estar, em % do consumo (entre parênteses, % que ganham):

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

O que muda quando as famílias não são plenamente racionais:

1. **Quem ganha e quem perde não muda.** Em todas as regras, a devolução
   uniforme beneficia a metade mais pobre, e a devolução que imita a lei a
   prejudica. As conclusões distributivas de `equilibrio_geral/` são robustas
   à forma das expectativas.
2. **O tamanho muda.** Com aprendizado e com informação rígida, os ganhos
   encolhem cerca de um terço no agregado e quase ninguém do grupo
   intermediário ganha com a devolução uniforme (5%, contra 29% com
   previsão perfeita).
3. **O caminho do capital oscila com aprendizado.** Logo depois da reforma,
   o juro líquido cai. Quem tem previsão perfeita sabe que ele volta a subir
   à medida que o capital diminui; quem aprende com o passado toma a queda
   como permanente. Como a poupança é muito sensível ao juro esperado (o juro
   de equilíbrio fica só 0,17 p.p. abaixo do ponto em que a poupança
   explode), essas famílias poupam de menos, o capital cai além do novo
   estado estacionário (−2,1% a −2,2% por volta de 30 anos, contra −1,45% no
   longo prazo), o juro sobe de novo e elas corrigem tarde. O resultado são
   ciclos longos e amortecidos, e um custo de bem-estar maior. Com previsão
   perfeita, o ajuste é monótono. O longo prazo é praticamente o mesmo em
   todas as regras (−1,39% a −1,45% nos últimos 20 anos).
4. **Heurísticas e atenção limitada ficam perto da previsão perfeita.** As
   duas regras ancoram parte das crenças no novo estado estacionário, que a
   reforma define; só o aprendizado e a informação rígida dependem
   inteiramente do passado.

![Capital depois da reforma](abm1_com_leiloeiro/figuras/lei_capital.png)

**Sensibilidade.** Os parâmetros comportamentais vêm da literatura, então a
devolução uniforme foi refeita com valores abaixo e acima de cada um
(`abm1_com_leiloeiro/resultados/sensibilidade.csv`):

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

Os sinais nunca mudam. O que pesa é a velocidade do aprendizado: quanto mais
devagar as famílias atualizam as crenças, maior a queda do capital antes da
recuperação e menor o ganho de bem-estar. As heurísticas e a atenção
limitada quase não dependem dos parâmetros.

**Estabilidade.** Crer para sempre no estado estacionário não é expectativa
racional fora dele. Com essas crenças e sem reforma nenhuma, a economia se
afasta sozinha do equilíbrio: se o capital sobe um pouco, os salários e as
transferências sobem, as famílias poupam o excedente e o capital sobe mais
(+0,2% em 25 anos, +1,6% em 75 e +8,4% em 150). Com aprendizado, a mesma
economia fica no equilíbrio (±0,4%): o equilíbrio de expectativas racionais é
estável sob aprendizado, como em Evans e Honkapohja (2001). Por isso o
benchmark neoclássico do experimento é a previsão perfeita, e não as crenças
fixas (`abm1_com_leiloeiro/resultados/estabilidade.csv`).

## No ABM sem leiloeiro

> **Pendente.** Os números desta seção foram calculados antes de duas
> correções no ABM 2 (salários ancorados na média e reposição da tendência no
> investimento, descritas no [README dele](../../Forecast/Brasil/2013T4-2026T2/abm2_sem_leiloeiro/README.md))
> e serão refeitos com `abm2_sem_leiloeiro/lei_sem_leiloeiro.py`.

O mesmo aumento de $\tau_k$ na economia descentralizada, com aprendizado,
em 48 sementes. Como a economia flutua sozinha, mesmo com os mesmos números
aleatórios os caminhos com e sem reforma se separam depois de alguns anos,
e uma semente só mistura o efeito da lei com o ciclo; a média de 48 separa
os dois (`abm2_sem_leiloeiro/resultados/mercados_lei_15270_resumo.csv`). Ganho médio de
bem-estar em % do consumo, com o erro-padrão entre parênteses:

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

As linhas tracejadas são o novo equilíbrio walrasiano.

1. **As conclusões distributivas sobrevivem à saída do leiloeiro.** Com
   firmas que fixam preços, busca e racionamento, a devolução uniforme
   continua beneficiando a metade mais pobre, e a que imita a lei continua
   prejudicando-a e beneficiando o grupo intermediário.
2. **Com a isenção, a perda dos mais pobres é maior**: −1,25% do consumo,
   contra −0,42% no Aiyagari, uma diferença de mais de dois erros-padrão.
3. **A lei não mexe no desemprego.** O desemprego depende dos fluxos do
   mercado de trabalho, e o imposto sobre o capital não os altera.
4. **Não dá para ver o efeito família por família.** Em qualquer grupo,
   cerca de metade das famílias ganha e metade perde, porque o caminho de
   cada uma (quem é demitido, quando, de qual firma) muda com a reforma. O
   efeito da lei só aparece na média de muitas famílias e de muitas
   sementes.

## Como rodar

Da pasta `Econometria/`, com as dependências de `Python/requirements.txt`:

```bash
python Python/macroeconomia/Politicas/Lei-15270/equilibrio_geral/experimentos.py        # agente representativo
python Python/macroeconomia/Politicas/Lei-15270/equilibrio_geral/experimentos_ha.py     # famílias heterogêneas
python Python/macroeconomia/Politicas/Lei-15270/abm1_com_leiloeiro/lei_com_leiloeiro.py # ABM com leiloeiro (cerca de 10 minutos)
python Python/macroeconomia/Politicas/Lei-15270/abm2_sem_leiloeiro/lei_sem_leiloeiro.py # ABM sem leiloeiro (cerca de 15 minutos com 4 núcleos)
python Python/macroeconomia/rodar_testes.py Lei-15270
```
