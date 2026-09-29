# Equilíbrio geral com margem e busca

Esta versão do equilíbrio geral estocástico de [`../dsge/`](../dsge/README.md)
recebe os fundamentos do [ABM sem leiloeiro](../abm2_sem_leiloeiro/README.md),
de modo que a diferença entre os dois na previsão meça a falta de coordenação
e não hipóteses diferentes (`dsge_busca.py`). As firmas cobram uma margem de
10% sobre o custo marginal, próxima da que emerge no ABM, e o emprego passa a
ser uma variável de estado, com a separação e o desemprego de longo prazo
tirados da mesma cadeia trimestral da PNAD usada no ABM e com vagas abertas
até que o custo de contratar se iguale ao valor do trabalhador para a firma.
O salário acompanha a tendência da produtividade, mas só se ajusta aos poucos
ao produto marginal, com um grau de rigidez estimado, e um choque na taxa de
separação se soma aos três choques do modelo sem busca.

O modelo prevê também a variação do desemprego. Os testes em
`test_dsge_busca.py` conferem o estado estacionário, com os fluxos de emprego,
o custo de contratar, a relação $K/Y$ e a participação do trabalho, a
estabilidade da solução para qualquer grau de rigidez, os sinais das
respostas aos choques e o espaço de estados com o desemprego faltante antes
de 2012. A descrição completa, com os resultados, está no
[README da previsão](../README.md).
