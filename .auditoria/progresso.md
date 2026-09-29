# Progresso das correções da auditoria

Pasta temporária: sai do repositório quando tudo estiver pronto.
O relatório da auditoria está em `auditoria.md`, nesta pasta.
Para retomar: ler este arquivo e continuar do primeiro item sem `[x]`.
Ambiente: `pip install -r Economia-Aplicada/Econometria/Python/requirements.txt`;
rodar os scripts pesados numa cópia da pasta `Econometria/` e copiar de volta
só `resultados/` e `figuras/`.

## Blocos

- [ ] 1. Previsão: dessazonalização do desemprego em tempo real (só com dados até a origem), teste que altera a PNAD bruta
- [ ] 2. Avaliação: Clark-West para os pares aninhados (média e VAR(1) contra o AR(1)); p-valor de Holm entre modelos
- [ ] 3. Previsões registradas: tirar ABM 2 com heurísticas e com atenção limitada, com a explicação
- [ ] 4. Reestimar os modelos que usam o desemprego (media ar1 eg_busca eg_busca_trim abm2_*) e refazer tabelas e figuras
- [ ] 5. Lei no ABM 2: mesma regra de devolução do Aiyagari e do ABM 1 (a variação da transferência em relação à economia sem reforma segue os pesos); 100 anos de aquecimento antes da reforma; rodar de novo
- [ ] 6. ABM 2 longo prazo e sensibilidade com mais sementes e erros-padrão
- [ ] 7. Equilíbrio geral: `experimentos_ha.py` grava CSV com o resumo; variante com R$ 25,84 bi para o grupo intermediário e o resto uniforme; `lei_com_leiloeiro.py` lê o CSV em vez de números digitados
- [ ] 8. Nota técnica: todas as correções da seção 2 e 3 da auditoria, Chamley-Judd, mapeamento da lei, hipótese do desempregado que produz, bibliografia; recompilar o PDF
- [ ] 9. READMEs: corrigir números e afirmações (seção 2), pares da previsão, informação rígida, heurísticas; referências completas
- [ ] 10. Escrita: reescrever os READMEs sem os padrões da seção 5
- [ ] 11. Repositório: .gitignore, versões usadas, CI, CITATION.cff
- [ ] 12. Revisão final: testes, conferência dos números nos textos, tirar a pasta `.auditoria/`

## Fora do escopo desta rodada (seção 6 da auditoria, extensões)

Anúncio no Aiyagari, alíquota por tipo, trabalho elástico, economia aberta,
lucros retidos, concentração de riqueza, desemprego por tipo, Laffer em valor
presente, Mankiw-Reis com expectativa racional, SMM, Krusell-Smith, α com
margem, crédito e política monetária no ABM 2, Focus, safras, PIT.
Licença: decisão do autor (falta escolher).

## Notas de andamento
