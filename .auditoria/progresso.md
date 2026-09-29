# Progresso das correções da auditoria

Pasta temporária: sai do repositório quando tudo estiver pronto.
O relatório da auditoria está em `auditoria.md`, nesta pasta.
Para retomar: ler este arquivo e continuar do primeiro item sem `[x]`.
Ambiente: `pip install -r Economia-Aplicada/Econometria/Python/requirements.txt`;
rodar os scripts pesados numa cópia da pasta `Econometria/` e copiar de volta
só `resultados/` e `figuras/`.

## Blocos

- [x] 1. Previsão: dessazonalização do desemprego em tempo real (só com dados até a origem), teste que altera a PNAD bruta
- [x] 2. Avaliação: Clark-West para os pares aninhados (média e VAR(1) contra o AR(1)); p-valor de Holm entre modelos
- [x] 3. Previsões registradas: tirar ABM 2 com heurísticas e com atenção limitada, com a explicação
- [ ] 4. Reestimar os modelos que usam o desemprego (media ar1 eg_busca eg_busca_trim abm2_*) e refazer tabelas e figuras
- [~] 5. Lei no ABM 2: mesma regra de devolução do Aiyagari e do ABM 1 (a variação da transferência em relação à economia sem reforma segue os pesos); 100 anos de aquecimento antes da reforma; rodar de novo
- [~] 6. ABM 2 longo prazo e sensibilidade com mais sementes e erros-padrão
- [x] 7. Equilíbrio geral: `experimentos_ha.py` grava CSV com o resumo; variante com R$ 25,84 bi para o grupo intermediário e o resto uniforme; `lei_com_leiloeiro.py` lê o CSV em vez de números digitados
- [x] 8. Nota técnica: todas as correções da seção 2 e 3 da auditoria, Chamley-Judd, mapeamento da lei, hipótese do desempregado que produz, bibliografia; recompilar o PDF
- [~] 9. READMEs: corrigir números e afirmações (seção 2), pares da previsão, informação rígida, heurísticas; referências completas
- [~] 10. Escrita: reescrever os READMEs sem os padrões da seção 5
- [x] 11. Repositório: .gitignore, versões usadas, CI, CITATION.cff
- [ ] 12. Revisão final: testes, conferência dos números nos textos, tirar a pasta `.auditoria/`

## Fora do escopo desta rodada (seção 6 da auditoria, extensões)

Anúncio no Aiyagari, alíquota por tipo, trabalho elástico, economia aberta,
lucros retidos, concentração de riqueza, desemprego por tipo, Laffer em valor
presente, Mankiw-Reis com expectativa racional, SMM, Krusell-Smith, α com
margem, crédito e política monetária no ABM 2, Focus, safras, PIT.
Licença: decisão do autor (falta escolher).

## Notas de andamento
- Blocos 1 a 3 no commit 4cab09e. O bloco 4 roda numa cópia (comparacao.py
  --modelos media ar1 eg_busca eg_busca_trim abm2_eq abm2_apr abm2_heu abm2_inf
  abm2_aten --processos 4); se a sessão cair, rodar de novo e copiar
  resultados/ e figuras/ da previsão.
- Holm: família = todos os modelos comparados à mesma referência, por variável
  e horizonte. `p_teste` = Clark-West (unilateral) para média e VAR(1), DM nos
  outros.
- Bloco 5: código no commit 060c408; falta rodar lei_sem_leiloeiro.py
  (cerca de 10 min) e atualizar a seção da lei no ABM 2 do README da lei.
- Bloco 6: código no commit 495871f; falta rodar experimentos_mercados.py
  e atualizar as tabelas do README do ABM 2.
- Blocos 7 e 8 nos commits c4188e1 e 2c8d99f. Variante "isenção, resto
  uniforme": 50% mais pobres −0,18%, grupo intermediário +0,35%, topo
  −0,42%, média 0,01%, capital −1,42%.
- LaTeX: apt-get install texlive-latex-base texlive-latex-recommended
  texlive-latex-extra texlive-lang-portuguese texlive-fonts-recommended
  lmodern latexmk; compilar numa cópia e copiar só o PDF.
- Bloco 11 no commit 75cbc6c (workflow do GitHub Actions aceito no push).
- Blocos 9 e 10: prontos e no commit ff6b88d os READMEs do equilíbrio
  geral, ABM 1, dsge, dsge_busca e referências. O README da lei está
  reescrito localmente com o marcador %%ABM2%% esperando os números novos.
  Faltam: README da lei (seção ABM 2), ABM 2, previsão, macroeconomia e raiz.
- Achado novo com 4 sementes no longo prazo do ABM 2: com aprendizado, o
  desvio do desemprego sobe para 0,84 p.p. (erro-padrão 0,62); uma semente
  teve um episódio grande de desemprego. A frase "o desemprego quase não se
  mexe" precisa de qualificação.
