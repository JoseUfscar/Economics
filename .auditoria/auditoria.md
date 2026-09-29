# Auditoria: `Economia-Aplicada/Econometria/Python/macroeconomia`

Repositório `JoseUfscar/Economics`, branch `jose/confident-fermat-xs3id6`, commit `ee48d23`.
Nada foi alterado no repositório. Tudo o que rodei, rodei numa cópia.

## Como a auditoria foi feita

- Li todo o código (`.py`), os READMEs, a nota técnica (`.tex`) e o texto extraído do PDF.
- Rodei os 172 testes: 53 do equilíbrio geral, 9 da lei no ABM 1, 16 do protocolo, 12 das referências, 11 do DSGE, 10 do DSGE com busca, 40 do ABM 1 e 21 do ABM 2. Todos passam, em cerca de 9 minutos.
- Reproduzi a calibração, todos os números da parte 1 da nota (efeitos de longo prazo, receita, bem-estar, Laffer, sensibilidade, outros choques), o processo de renda da PNAD e o longo prazo do ABM 2, que saiu idêntico ao CSV até a última casa.
- Conferi, célula por célula, as tabelas dos READMEs contra os CSVs em `resultados/`: RMSE relativo, negritos de Diebold-Mariano, vieses, coberturas, convergência do ABM 1, heurísticas de 1996 a 2026, bem-estar e sensibilidade da lei no ABM 1, previsões registradas.
- Reexecutei `lei_sem_leiloeiro.py`, cuja seção no README da lei está marcada como pendente.
- Conferi na web os fatos da lei e da Exposição de Motivos, e as referências mais citadas.
- Não verifiquei a versão em Julia (não há Julia no ambiente), o Monte Carlo de 100 réplicas e a rodada completa da previsão (2 a 3 horas). Os CSVs dessas partes batem com o texto.

**Veredito.** O código é bom: contas fechadas, testes que conferem soluções exatas e identidades, resultados reproduzíveis. O que falta para publicar está em quatro frentes: (1) uma seção de resultados desatualizada e dois problemas de desenho no experimento da lei sem leiloeiro; (2) um vazamento de informação do futuro na previsão do desemprego, que contradiz o que o README afirma; (3) uma dúzia de afirmações que não batem com os dados ou com o próprio código; (4) a escrita dos READMEs, que tem padrões fáceis de reconhecer como texto de IA. A nota técnica está bem escrita e precisa de poucos ajustes.

---

## 1. Antes de publicar

### 1.1 A lei no ABM sem leiloeiro: números antigos e comparação desigual

`Politicas/Lei-15270/README.md`, seção "No ABM sem leiloeiro", já avisa que os números são de antes das duas correções do ABM 2. Reexecutei o script com o código atual; os números novos estão na seção 7. Mas refazer não basta, porque há dois problemas de desenho:

**(a) A regra de devolução não é a mesma dos outros modelos.** No Aiyagari contínuo (`aiyagari.py`, linha 412) e no ABM 1 (`economia.py`, linha 146), toda a transferência líquida segue os pesos da devolução: a receita nova menos a erosão da base antiga (menos `tau_w w` porque o salário cai, menos `tau_k` antigo porque o capital cai). No ABM 2 (`descentralizada.py`, linhas 594-597 e 661), só o acréscimo do imposto sobre o lucro, `(tau_k - tau_k_base) * lucro`, segue os pesos; a erosão da base entra na parcela uniforme. Na devolução "isenção", isso faz os 50% mais pobres pagarem parte da erosão que, nos outros dois modelos, recai só sobre o grupo intermediário. A diferença que o README destaca (−1,25% no ABM 2 contra −0,42% no Aiyagari, "mais de dois erros-padrão") mistura o efeito de tirar o leiloeiro com essa diferença de regra. O próprio equilíbrio walrasiano de referência do ABM 2 (`F.equilibrio` com `pesos`) usa a regra do Aiyagari, e não a do ABM 2.

**(b) Não há aquecimento.** Em `lei_sem_leiloeiro.py` (linha 51), as economias com e sem reforma partem da referência walrasiana. O ABM 2 leva décadas para sair dela e chegar ao próprio regime (capital 13% a 15% abaixo, margem de 10%). O efeito da lei e o bem-estar são medidos em cima dessa transição. Na previsão, o mesmo modelo usa 100 anos de aquecimento (`AQUECIMENTO = 400`); na lei, deveria usar também, e só então aplicar a reforma.

### 1.2 Previsão: a dessazonalização do desemprego usa dados do futuro

`protocolo.dessazonalizar` (linha 57) calcula os fatores sazonais com a amostra inteira (2012-2026), e `carregar_observaveis` entrega essa série já ajustada a todas as origens. Assim, em 2013T4 a série de desemprego até a origem já carrega informação de 2014 a 2026. O README do protocolo reconhece que os fatores usam a amostra inteira, mas duas linhas depois afirma: "Testes conferem que alterar qualquer dado posterior à origem não muda nenhuma previsão". O teste (`test_protocolo.TestSemOlharOFuturo`) altera a série *depois* de dessazonalizada, então não detecta o problema.

Medi o tamanho: a diferença entre a taxa ajustada com a amostra inteira e a ajustada só com os dados até a origem chega a 0,22 p.p. em 2013T4 e fica entre 0,06 e 0,10 p.p. nas origens de 2014 a 2022. É da ordem do erro de previsão do desemprego em um trimestre. Afeta o DSGE com busca, o ABM 2 (que usa a taxa ajustada como alvo da separação) e as referências do desemprego. O realizado também é a série ajustada com a amostra inteira.

Correção: dessazonalizar dentro de `prever_na_origem`, só com `taxa.loc[:origem]`, e avaliar contra a série ajustada com a amostra inteira (ou contra a variação interanual, que dispensa ajuste). E acrescentar ao teste a alteração da PNAD bruta.

### 1.3 A faixa da isenção não cabe no grupo intermediário

Nota, linhas 646-648: "o novo limite de R$ 5 mil e a redução parcial até R$ 7.350 ficam entre o P80 (R$ 4.470) e o P90 (R$ 6.985), todos dentro desse grupo". R$ 7.350 é maior que R$ 6.985: a ponta de cima da redução parcial está nos 10% com maior renda. O mesmo erro aparece em `equilibrio_geral/README.md` ("a faixa de R$ 3 mil a R$ 7,35 mil") e na docstring de `experimentos_ha.py`. A aproximação continua razoável, porque o benefício perto de R$ 7.350 é quase zero (a redução cai linearmente), mas a frase tem de dizer isso.

### 1.4 O PDF da nota está desatualizado

O PDF foi compilado em 25/09, antes da reorganização das pastas. Na seção "Reprodução", o PDF diz `Python/macroeconomia/equilibrio_geral`; o `.tex` diz `Python/macroeconomia/Politicas/Lei-15270/equilibrio_geral`. Recompilar depois das correções da seção 2.

### 1.5 A tabela dos "pares" está com os rótulos trocados e promete demais

`Forecast/Brasil/2013T4-2026T2/README.md`: a tabela tem as colunas "Com leiloeiro ou equilíbrio" e "Sem leiloeiro", e põe o "ABM 1, com leiloeiro" na coluna "Sem leiloeiro". E o texto diz que a diferença dentro de cada linha "mede o que muda quando os preços deixam de vir de um equilíbrio". No par de cima, o ABM 1 também tem leiloeiro; o que muda é heterogeneidade, não linearidade, expectativas, o jeito de estimar os choques (máxima verossimilhança no DSGE; AR(1) sobre a produtividade inferida no ABM) e o conjunto de dados usados (o DSGE usa as quatro séries; o ABM só PIB e gasto). No par de baixo acontece o mesmo. A frase precisa descrever o que de fato difere.

### 1.6 Previsões registradas que o próprio texto diz não serem críveis

`previsao_registrada_202602.csv` inclui FBCF de −35% (ABM 2, atenção limitada) e +16% (ABM 2, heurísticas) até 2027T4. O README diz que não são críveis. Para um registro público de previsões, é melhor tirá-las do arquivo ou marcá-las numa coluna, e dizer por quê.

---

## 2. Erros e imprecisões pontuais

Todos conferidos contra o código ou os CSVs.

| Onde | Está | Deveria ser | Por quê |
|---|---|---|---|
| Nota, l. 306 | 0,18 × 0,199/(0,199 − 0,060) = 0,259 | 0,18 × 0,1986/(0,1986 − 0,0605) = 0,259 | com 0,060 a conta dá 0,258 |
| Nota, l. 390 | "... × 0,0085/0,741 = −1,46%" | usar 0,00854 | com 0,0085 a conta dá −1,45%; e a fórmula é a variação do log, vale dizer |
| Nota, l. 617-620 | 19,2%, 40,0%, 40,8% | 19,0%, 40,0%, 40,9% (brutos) ou 19,1%, 40,0%, 41,0% (normalizados) | 40,8% dá renda relativa 4,08, não 4,10; `calibracao_renda` usa os normalizados |
| Nota, l. 726-727 | "a perda dos mais ricos e a receita seriam maiores" | tirar "e a receita" | a receita depende de K agregado, que é calibrado; a concentração não a muda |
| Nota, l. 465-466 | capital cai 2,5% | 2,6% | o modelo dá −2,56% |
| Nota, seção 5 | fator "(1,05)^(−1/2)" | dizer que τ_c = 0 na calibração | o fator só é esse porque a alíquota inicial é zero; a tabela de calibração não menciona τ_c |
| Nota, l. 554 | r = αK^(α−1) − δ e r̃ | manter R, r e k da parte 1 | na parte 1, r é o retorno líquido após impostos; na parte 2, é antes do imposto; K maiúsculo em unidades de eficiência |
| Nota, l. 614 e READMEs | "a família recebe 40% da sua renda do trabalho" | dizer de onde vem o 40% e que, no Aiyagari e no ABM 1, o desempregado **produz** esses 40% | `familias.py`, linha 261: "sem benefício, todos os estados produzem, L = E[z] = 1"; no ABM 2 o desempregado não produz e o governo paga. É uma hipótese escondida, e muda o L entre os modelos (o README do ABM 2 diz que isso reduz o capital em 4%) |
| Nota, l. 626 | Gini do modelo 0,48 contra 0,53 do IBGE | dizer que os conceitos diferem | o modelo mede renda total por dinastia; o IBGE, renda domiciliar per capita |
| Nota, l. 712-715 | Domeij e Heathcote como "o mesmo mecanismo visto do outro lado" | reescrever | lá o ponto é a troca de imposto sobre capital por imposto sobre trabalho e a transição; a frase simplifica demais |
| Nota, bibliografia | 22 obras | citar ou tirar | Acemoglu, Barro e Sala-i-Martin, Cass, Chamley, Gollin, Huggett, Judd (1985), Koopmans, Ramsey e Romer não são citados no texto; Acemoglu está depois de Achdou e Aiyagari |
| Nota, l. 369-371 | anúncio em 15/03/2025, "data da Exposição de Motivos" | justificar ou usar 18/03 | a EM é datada de 15/03 (um sábado); o PL foi apresentado e anunciado em 18/03. Três dias não mudam nada, mas o parecerista pergunta |
| README da previsão, item 3 | equilíbrio geral com tendência trimestral é "o melhor na amostra completa para o PIB" | "o melhor de h = 1 a h = 5" | em h = 6 e h = 7 o ABM 2 com informação rígida erra menos (0,89 e 0,92 contra 0,92 e 0,93); o README raiz repete a afirmação |
| README da previsão, item 5 | cobertura de 74% a 81% para o PIB em h = 8 | 72% a 81% | o DSGE com busca cobre 72%; o texto é de antes de ele entrar |
| README do ABM 1, tabela | informação rígida, PIB h = 8 sem pandemia: 1,05 | 1,04 | CSV: 1,0445; o README principal já diz 1,04 |
| README do ABM 1 | "um VAR(1) para o crescimento da produtividade e do gasto" | "dois AR(1) com choques correlacionados" | `Exogenos` é um VAR diagonal; o README do ABM 2 descreve certo |
| README do ABM 1, item 5 | coberturas de 53% a 73%, 82% a 100%, 60% a 77% | dizer amostra e horizontes | as faixas misturam a amostra toda e a sem pandemia; crenças fixas chega a 76% em h = 6 |
| README do ABM 1 e raiz | "os ganhos de bem-estar por grupo também batem" | "ficam a até 0,06 p.p." | previsão perfeita contra Aiyagari: +0,53 contra +0,58; −0,48 contra −0,42; +0,21 contra +0,23. É perto, mas não "bate" |
| README da lei, item 3 | longo prazo de −1,39% a −1,45% | dizer que é na devolução uniforme | na isenção, −1,36% a −1,41% |
| README da lei, sensibilidade | +0,40; +0,42; −1,5% | +0,39; +0,41; −1,4% | CSV: 0,3949; 0,4149; −1,4499. Parece tabela de uma rodada anterior |
| README do ABM 2, sensibilidade | "Aprendizado, média de duas sementes ... `csv`):" | abrir o parêntese | e explicar por que a linha "Base" (0,95; 0,84; 10,6%) difere da tabela principal (0,97; 0,87; 10,2%): 150 anos e 2 sementes contra 300 anos e 1 semente |
| README do ABM 1, heurísticas | "cada família escolhe a regra que vinha acertando mais" | "cada família sorteia uma regra com probabilidades logit do desempenho de cada uma" | o desempenho é comum a todos; é isso que faz as famílias trocarem em bloco |
| `descentralizada.Comportamento` | docstring | incluir `elasticidade_institucional = 2` | o parâmetro entra na divisão das compras do governo e das firmas e não está documentado |

---

## 3. Questões de método para resolver ou declarar

### Equilíbrio geral

1. **O mapeamento da lei em τ_k superestima provavelmente o efeito sobre o capital.** Três razões, nenhuma discutida na nota:
   - R$ 8,90 bi dos R$ 34,12 bi (26%) são IRRF sobre dividendos remetidos a **não residentes**. Numa economia fechada, isso vira imposto sobre o poupador doméstico. Numa economia aberta, afeta o investimento estrangeiro, com outra elasticidade.
   - Grande parte da receita nova vem da tributação de dividendos. Pela "visão nova" (Auerbach, 1979; Bradford, 1981), um imposto sobre dividendos pouco afeta o investimento financiado com lucros retidos; Yagan (2015, *AER*) não achou efeito do corte de 2003 nos EUA sobre o investimento. O −1,46% é mais um teto que uma estimativa central, e a nota deveria dizer isso.
   - O IRPFM incide só sobre rendas acima de R$ 600 mil por ano, e o modelo sobe a alíquota média de todo o capital. A alíquota marginal do topo sobe bem mais que 0,85 p.p.
2. **Chamley-Judd não aparece.** Chamley (1986) e Judd (1985) estão na bibliografia e não no texto. Um estudo sobre tributação do capital em Ramsey precisa situar o resultado nessa literatura, e de preferência em Straub e Werning (2020, *AER*).
3. **Devolução "isenção".** Toda a receita nova (R$ 34,12 bi) vai para o grupo intermediário, mas a isenção custa R$ 25,84 bi. A nota avisa. Uma variante mais fiel: R$ 25,84 bi para o grupo intermediário e o resto de forma uniforme (ou abatendo dívida).
4. **O mesmo risco de desemprego para todos os tipos** e a taxa de reposição de 40% sem fonte. A PNAD permite calibrar desocupação e duração por faixa de renda.
5. **A curva de Laffer é de estado estacionário.** Para política fiscal, o que importa é o valor presente da receita na transição. Com o capital caindo devagar, o valor presente fica mais perto da receita estática que os 90% do longo prazo.

### ABM 1

6. **"Informação rígida" não é Mankiw e Reis.** Em `expectativas.py` (linha 115), quem atualiza adota a previsão do **aprendizado adaptativo**, e não a expectativa racional. Em Mankiw e Reis (2002), quem atualiza passa a saber tudo. A regra do código é aprendizado com atualização esporádica, e por isso se comporta como o aprendizado, só que mais devagar. Ou se muda a regra (quem atualiza recebe o caminho de previsão perfeita) ou se muda o nome e a tabela de referências.
7. **Parte da robustez é por construção.** A regra fundamentalista (dentro das heurísticas) e a atenção limitada ancoram as crenças no **novo** estado estacionário, que as famílias conhecem no instante da reforma. Por isso ficam perto da previsão perfeita. O README reconhece isso na seção de limitações, mas o item 4 da lei ("Heurísticas e atenção limitada ficam perto da previsão perfeita") apresenta como resultado.
8. **A história das heurísticas usa o estado estacionário calibrado com 2000-2023** (`comum.economia_base`). Em 1996, a regra fundamentalista já "sabe" a média de 2000-2023. Para a narrativa de 1996-2026, é um pequeno vazamento de informação; vale uma frase.
9. **O ABM prevê o PIB quase como um AR(1).** A produtividade é escolhida para reproduzir o PIB observado, e os choques futuros saem de um AR(1) dessa produtividade inferida. Não surpreende que a razão contra o AR(1) fique perto de 1. Vale dizer.

### ABM 2 e DSGE com busca

10. **Participação do trabalho.** α vem de 1 menos a participação do trabalho da PWT (54,9%). Com a margem de 10%, o modelo passa a ter 49,6% (DSGE com busca) ou 50,8% (ABM 2), com lucros de 9% do PIB. A participação dos dados já inclui as margens que existem na economia; a calibração conta a margem duas vezes. Ou se recalibra α para que a participação com margem seja 54,9% (α ≈ 0,40), ou se discute a escolha.
11. **Margem e parâmetros de fora.** O próprio README mostra que a margem é cerca de dois terços do teto escolhido. O custo de contratar (Silva e Toledo, 2009) e a probabilidade de preencher a vaga (den Haan, Ramey e Watson, 2000) são calibrados para os EUA. Os parâmetros de firma vêm de Lengnick (2013), um modelo artificial.
12. **Poucas sementes.** O longo prazo usa uma semente por regra; a sensibilidade, duas. Faltam erros-padrão.

### Avaliação das previsões

13. **Diebold-Mariano com modelos aninhados.** A média e o AR(1) estão aninhados no VAR(1), e a média no AR(1). Para esses casos, o teste de Clark e West (2007) é o adequado; o DM tem tamanho errado.
14. **Muitos testes.** São 17 modelos, 5 variáveis, 8 horizontes e 2 amostras: mais de mil p-valores. A 5%, esperam-se dezenas de "significativos" por acaso. Os negritos isolados (por exemplo, heurísticas do ABM 1 na FBCF em h = 2) precisam de uma correção (Holm) ou de um *Model Confidence Set* (Hansen, Lunde e Nason, 2011).
15. **A referência natural no Brasil é o Focus.** A mediana das expectativas do Focus para o PIB tem data de coleta e cobre toda a janela de avaliação. Comparar contra ela diz muito mais que contra o AR(1).
16. **Safra dos dados.** O README reconhece que os dados são os revisados e diz que isso "favorece um pouco todos os modelos, por igual". O "por igual" não tem base: modelos que usam o PIB anual com dois anos de defasagem e modelos que usam o trimestral são afetados de formas diferentes. Tirar o "por igual" ou usar as safras (o IBGE publica as séries de cada divulgação das Contas Trimestrais).

---

## 4. Reprodutibilidade e repositório

- **Não há `.gitignore`.** Um `import` meu criou pastas `__pycache__` dentro do repositório (apaguei). Qualquer pessoa que rodar os scripts vai sujar o `git status`. Acrescentar `__pycache__/`, `*.pyc`, `.venv/`.
- **Não há `LICENSE` nem `CITATION.cff`.** Para publicar, os dois são necessários: sem licença, ninguém pode reusar o código legalmente.
- **`requirements.txt` só tem limites inferiores.** Os resultados saíram idênticos com numpy 2.4.6, pandas 3.0.6, scipy 1.17.1, statsmodels 0.15.0 e matplotlib 3.11.2 (Python 3.11). Vale gravar as versões que geraram os CSVs.
- **Sem integração contínua.** Uma GitHub Action que rode `rodar_testes.py` a cada push custa pouco.
- **Números copiados no código.** `lei_com_leiloeiro.py` tem `HA_CAPITAL` e `HA_GANHO` digitados a partir do README do equilíbrio geral. Se o modelo contínuo mudar, a figura fica errada sem aviso. Melhor ler de um CSV gravado por `experimentos_ha.py`.
- **Os ABMs e a previsão não têm nota técnica.** Só o equilíbrio geral tem. Para publicar, os READMEs precisam virar um texto com bibliografia completa: hoje citam cerca de 30 trabalhos (Kreps, Carroll, Evans e Honkapohja, Milani, Brock e Hommes, Anufriev e Hommes, Mankiw e Reis, Gabaix, Young, Poledna et al., Lengnick, Delli Gatti et al., Gouvea, Klein, Hall, Blanchard e Galí, Pissarides, Silva e Toledo, den Haan et al., Petrongolo e Pissarides, Diebold e Mariano, Harvey et al., Gneiting e Raftery, Krusell e Smith...) sem nenhuma referência completa.
- As contagens de testes e os tempos dos READMEs estão certos (53, 40, 21, 49; cerca de 10 minutos).

---

## 5. Escrita: o que soa como IA

A nota técnica está bem escrita: frases com sujeito e verbo, números no lugar certo, pouca ênfase. Os READMEs têm os padrões que qualquer leitor treinado reconhece. Não é uma palavra aqui e ali; é a estrutura.

**Padrões e exemplos:**

1. **Lista numerada com conclusão em negrito depois de cada tabela.** São perto de cem ocorrências, sempre com a mesma forma: "1. **Quem ganha e quem perde não muda.** Em todas as regras...". Todo README segue o molde tabela → lista de 3 a 6 conclusões em negrito. Isso é a marca mais forte.
2. **Contraste "X, não Y".** "O equilíbrio é emergente, não imposto." "Quem define essa velocidade é o processo de renda, não as expectativas." "Esses ciclos vêm do capital, das margens e da produtividade das firmas, não do mercado de trabalho." "É a dinâmica das decisões das famílias que acerta."
3. **Frases de efeito curtas.** "A distribuição muda tudo." (nota e README) "A dinâmica estrutural acrescenta pouco, mas acrescenta." "Emergir não garante chegar ao equilíbrio certo." "Nada disso foi imposto." "Chegar a uma economia estável deu trabalho, e o caminho diz algo." "aqui sem ninguém tê-la posto no modelo."
4. **Rótulos que anunciam o que vem.** "O que os números dizem:", "Três resultados se destacam.", "**O que emerge:**", "O que muda quando as famílias não são plenamente racionais:".
5. **"Emerge" e "emergente" cerca de 20 vezes.**
6. **Títulos em pergunta.** "O equilíbrio é imposto ou emergente?", "e quando os preços não vêm de um equilíbrio?".
7. **Abertura grandiosa.** "a tarefa mais direta que existe para um modelo macroeconômico: prever dados que ele não viu." "escritos para serem lidos e não só executados."
8. **Travessões.** Os READMEs de previsão e dos ABMs já não têm; ainda há no README raiz (7), no do equilíbrio geral (5) e na nota (9).
9. **Na nota:** "Três resultados se destacam. **Primeiro**... **Segundo**, a distribuição muda tudo" (l. 696-701) e a alternância entre "adotamos/convertemos/supomos" e voz impessoal.

**Como reescrever.** Trocar as listas de conclusões por um ou dois parágrafos corridos que comecem pelo número, sem negrito; tirar as frases de efeito; deixar o leitor tirar a conclusão. Três exemplos:

> Antes: "1. **Quem ganha e quem perde não muda.** Em todas as regras, a devolução uniforme beneficia a metade mais pobre, e a devolução que imita a lei a prejudica. As conclusões distributivas de `equilibrio_geral/` são robustas à forma das expectativas."
>
> Depois: "Em todas as regras de expectativas, a devolução uniforme beneficia a metade mais pobre (de +0,42% a +0,53% do consumo) e a devolução que imita a lei a prejudica (de −0,44% a −0,51%), como no modelo contínuo."

> Antes: "O agregado quase não muda em relação ao agente representativo (...), mas a distribuição muda tudo."
>
> Depois: "O capital de longo prazo cai 1,45% ou 1,41%, perto dos 1,46% do agente representativo. Os ganhos e perdas por grupo, no entanto, dependem inteiramente de como a receita volta."

> Antes: "**Chegar a uma economia estável deu trabalho, e o caminho diz algo.** As primeiras versões explodiram ou colapsaram, e cada falha apontou um mecanismo:"
>
> Depois: "As primeiras versões do modelo eram instáveis. Quatro problemas apareceram, cada um ligado a uma regra das firmas:"

Uma regra prática para a revisão: se uma frase pode ser apagada sem perder nenhum número nem nenhuma informação, apague.

---

## 6. Roteiro para afrouxar hipóteses

Em ordem de retorno por esforço.

**Equilíbrio geral (lei)**
1. *Anúncio no Aiyagari.* `aiyagari.transicao` já aceita `vigencia > 0`; falta só rodar o anúncio de 15/03/2025 com famílias heterogêneas. É o ganho mais barato.
2. *Alíquota por tipo.* τ_k diferente para os 10% do topo (o IRPFM) e a isenção como redução de τ_w do grupo intermediário, em vez de transferência. Em `aiyagari.py`, basta que `Governo` aceite `tau_k` e `tau_w` por estado e que `_fluxo` use o retorno líquido de cada estado.
3. *Oferta de trabalho elástica com imposto progressivo* (Heathcote, Storesletten e Violante, 2017). Sem isso, a isenção nunca distorce nada.
4. *Economia aberta pequena* com prêmio de risco e o IRRF sobre remessas incidindo sobre o capital estrangeiro.
5. *Firma com decisão de distribuir ou reter lucros*, para separar a visão nova da antiga na tributação de dividendos.
6. *Concentração de riqueza.* Um estado de renda muito alta e raro (Castañeda et al., 2003) ou retornos heterogêneos (Benhabib, Bisin e Zhu, 2011) para chegar aos 80% do WID.
7. *Desemprego por tipo e informalidade*, com a PNAD por faixa de renda, e o desempregado fora da produção, como no ABM 2.
8. *Laffer em valor presente*, com a transição.

**ABM 1**
9. Informação rígida de verdade: quem atualiza recebe o caminho de previsão perfeita.
10. Estimar os parâmetros comportamentais (ganho, intensidade, λ, m̄) por momentos simulados, com as expectativas do Focus e da FGV.
11. Benchmark racional com risco agregado (Krusell e Smith, 1998).

**ABM 2**
12. Harmonizar a regra de devolução e pôr aquecimento no experimento da lei (seção 1.1).
13. Recalibrar α com a margem e calibrar o teto da margem com margens medidas no Brasil (PIA-Empresa do IBGE).
14. Suavizar o retorno do fundo nas crenças, como o próprio README propõe.
15. Crédito, entrada e saída de firmas e política monetária: sem isso o desemprego não oscila.
16. Mais sementes e erros-padrão em todas as tabelas.

**Previsão**
17. Dessazonalização em tempo real (seção 1.2).
18. Focus como referência; Clark-West para os aninhados; Model Confidence Set.
19. Safras das Contas Trimestrais.
20. Avaliar as densidades também pelo PIT e pelo log score, além do CRPS e da cobertura.

---

## 7. A lei no ABM 2 reexecutada

`lei_sem_leiloeiro.py` com o código atual, 48 sementes, 5 minutos em 4 núcleos. Ganho médio de bem-estar em % do consumo (erro-padrão entre parênteses):

| Devolução | Grupo | README (antigo) | Código atual | Aiyagari contínuo |
|---|---|---|---|---|
| Uniforme | 50% com menor renda | +0,62 (0,31) | +0,94 (0,26) | +0,58 |
| Uniforme | 40% seguintes | −0,03 (0,14) | +0,05 (0,14) | −0,06 |
| Uniforme | 10% com maior renda | −0,28 (0,09) | −0,27 (0,10) | −0,35 |
| Uniforme | Todos | +0,27 (0,22) | +0,47 (0,20) | +0,23 |
| Isenção | 50% com menor renda | −1,25 (0,33) | −0,78 (0,25) | −0,42 |
| Isenção | 40% seguintes | +0,78 (0,14) | +0,88 (0,13) | +0,49 |
| Isenção | 10% com maior renda | −0,38 (0,09) | −0,42 (0,09) | −0,44 |
| Isenção | Todos | −0,35 (0,23) | −0,08 (0,19) | −0,06 |

| Devolução | Capital no longo prazo (antigo) | Código atual | Novo equilíbrio walrasiano | Desemprego (atual) |
|---|---|---|---|---|
| Uniforme | −2,2% (0,6) | −1,8% (0,5) | −1,45% | −0,01 p.p. (0,02) |
| Isenção | −1,4% (0,6) | −1,1% (0,5) | −1,41% | −0,01 p.p. (0,02) |

O que muda no texto:

- O item 2 do README ("com a isenção, a perda dos mais pobres é maior: −1,25% contra −0,42%, uma diferença de mais de dois erros-padrão") deixa de valer. Agora é −0,78% contra −0,42%, a 1,4 erro-padrão. O mesmo vale para a devolução uniforme (+0,94% contra +0,58%).
- O sinal do grupo intermediário na devolução uniforme muda (−0,03 para +0,05), sem significância.
- Os itens 1, 3 e 4 continuam valendo: os sinais dos grupos extremos são os do Aiyagari, o desemprego não se mexe e cerca de metade das famílias de cada grupo ganha (42% a 55%).
- Esses números ainda carregam os dois problemas da seção 1.1 (regra de devolução diferente e falta de aquecimento). Convém corrigir os dois e só então reescrever a seção.

---

## Fontes consultadas

- [Lei nº 15.270/2025 (Planalto)](https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2025/lei/l15270.htm) e [Câmara dos Deputados](https://www2.camara.leg.br/legin/fed/lei/2025/lei-15270-26-novembro-2025-798354-publicacaooriginal-177117-pl.html)
- [EM nº 00019/2025 MF](https://www.planalto.gov.br/ccivil_03/projetos/ato_2023_2026/2025/pl/exm/exm-0019-25-mf.doc)
- [Nota técnica de impacto 13/2025 da Conorf/Senado](https://www12.senado.leg.br/orcamento/documentos/estudos/tipos-de-estudos/notas-tecnicas-e-informativos/sto-2025-00465-nota-tecnica-de-impacto-orcamentario-e-financeiro-13-2025-317401-principal-346516-validado.pdf) (confirma 25,84; 25,22; 8,90 e a data do PL, 18/03/2025)
- [Rabelo (2025), Cadernos de Finanças Públicas 25(3)](https://publicacoes.tesouro.gov.br/index.php/cadernos/article/view/269)
- [Gouvea (2007), BCB Working Paper 143](https://www.bcb.gov.br/pec/wps/ingl/wps143.pdf)
- [Mayer Brown sobre a Lei 15.270](https://www.mayerbrown.com/pt/insights/publications/2025/12/enactment-of-law-no-15270-2025-which-establishes-dividend-taxation-expands-the-exemption-threshold-and-introduces-a-minimum-tax-on-high-incomes)
