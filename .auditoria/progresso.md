# Progresso das correções da auditoria

Pasta temporária: sai do repositório quando tudo estiver pronto.
O relatório da auditoria está em `auditoria.md`, nesta pasta.
Para retomar: ler este arquivo e continuar do primeiro item sem `[x]`.
Ambiente: `pip install -r Economia-Aplicada/Econometria/Python/requirements-versoes.txt`;
rodar os scripts pesados numa cópia da pasta `Econometria/` e copiar de volta
só `resultados/` e `figuras/`.

## Blocos

- [x] 1. Previsão: dessazonalização do desemprego em tempo real (só com dados até a origem), teste que altera a PNAD bruta
- [x] 2. Avaliação: Clark-West para os pares aninhados (média e VAR(1) contra o AR(1)); p-valor de Holm entre modelos
- [x] 3. Previsões registradas: tirar ABM 2 com heurísticas e com atenção limitada, com a explicação
- [x] 4. Reestimar os modelos que usam o desemprego e refazer tabelas e figuras (resultados copiados para o repositório; desemprego avaliado a partir de 2014T4, `PRIMEIRA_ORIGEM_DESEMPREGO` em comparacao.py)
- [~] 5. Lei no ABM 2: regra de devolução e aquecimento (ver notas); falta rodar `experimentos_ha.py` e `lei_sem_leiloeiro.py` (96 sementes) e escrever a seção do ABM 2 no README da lei
- [x] 6. ABM 2 longo prazo e sensibilidade com quatro sementes e erros-padrão (resultados copiados; README do ABM 2 reescrito)
- [x] 7. Equilíbrio geral: CSV com o resumo; variante com R$ 25,84 bi; `lei_com_leiloeiro.py` lê o CSV
- [x] 8. Nota técnica corrigida e PDF recompilado (falta acrescentar a variante "isenção, só a receita nova" quando ela rodar)
- [~] 9. READMEs: previsão, ABM 2, macroeconomia, raiz e Econometria reescritos (não commitados ainda); falta a seção do ABM 2 no README da lei (%%ABM2%%)
- [~] 10. Escrita: idem
- [ ] Commit e push de tudo o que está pendente (o Bash ficou fora do ar; `git status` primeiro)
- [x] 11. Repositório: .gitignore, versões usadas, CI, CITATION.cff
- [ ] 12. Revisão final: testes, conferência dos números nos textos, tirar a pasta `.auditoria/`

## Fora do escopo desta rodada (seção 6 da auditoria, extensões)

Anúncio no Aiyagari, alíquota por tipo, trabalho elástico, economia aberta,
lucros retidos, concentração de riqueza, desemprego por tipo, Laffer em valor
presente, Mankiw-Reis com expectativa racional, SMM, Krusell-Smith, α com
margem, crédito e política monetária no ABM 2, Focus, safras, PIT.
Licença: decisão do autor (falta escolher).

## Notas de andamento

- Holm: família = todos os modelos comparados à mesma referência, por variável
  e horizonte. `p_teste` = Clark-West (unilateral, a favor do modelo maior)
  para média e VAR(1), DM nos outros. Nas tabelas dos READMEs, negrito = DM a
  5% para os modelos não aninhados; † = significativo depois de Holm; para a
  média e o VAR(1), marcar à parte o Clark-West.
- Desemprego: com a dessazonalização em tempo real, em 2013T4 havia só 7
  variações da taxa e o AR(1) saiu explosivo (coeficiente -2,4, previsão de
  -487 p.p. em h=8). Por isso a avaliação do desemprego começa em 2014T4
  (três anos de PNAD). Os modelos continuam usando a série desde 2012.
- Regra de devolução na lei:
  * Aiyagari e ABM 1 (regra principal da nota): a transferência inteira segue
    os pesos.
  * No ABM 2 isso não funciona: depois do aquecimento, o modelo tem crises
    ocasionais de desemprego, e as cópias com e sem reforma passam por elas em
    datas diferentes; a regra "a diferença de orçamento segue os pesos" fazia o
    grupo da devolução absorver essas diferenças de ciclo (rodada de 48
    sementes: 50% mais pobres de -7,7% a +14,4% por semente).
  * Decisão: ABM 2 volta à regra "só a receita do aumento de tau_k segue os
    pesos" (descentralizada.py como antes do commit 060c408), mantendo o
    aquecimento de 100 anos. Para comparar, o Aiyagari ganhou a mesma regra
    (`Governo.tau_k_base`, variante "isenção, só a receita nova" em
    experimentos_ha.py), e o equilíbrio walrasiano de referência do ABM 2 usa
    a mesma regra (`familias.equilibrio(..., tau_k_base=)`). Testes passam.
  * Falta: rodar experimentos_ha.py (grava resultados/ha_bem_estar.csv com a
    variante nova) e lei_sem_leiloeiro.py (96 sementes, uns 20 min), copiar os
    resultados e escrever a seção no README da lei (marcador %%ABM2%%), além
    de uma frase na nota técnica sobre a variante.
- Longo prazo do ABM 2 com 4 sementes: em 10 de 12 simulações o desemprego
  quase não se mexe; a semente 2 tem crises (aprendizado: até 26% perto do
  ano 280; atenção limitada: até 17%). Já está no README do ABM 2.
- Resultados da previsão (para o README da previsão e o da raiz), razões ao
  AR(1): na amostra toda, o equilíbrio geral com tendência trimestral é o
  melhor para o PIB de h=1 a 5 e o ABM 2 com informação rígida de h=6 a 8;
  para o consumo, o ABM 2 com informação rígida de h=3 a 8. Desemprego em
  h=8: equilíbrio geral com busca 0,72 (0,75 sem pandemia), ABM 2 com
  aprendizado 0,75 (0,83). Viés do desemprego em h=8 sem pandemia: busca
  -0,64, ABM 2 aprendizado -1,34, AR(1) -2,34. Cobertura do PIB em h=8: 70% a
  81%; do desemprego em h=4: 65% a 77%.
