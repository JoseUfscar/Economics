# Referências estatísticas

Os modelos contra os quais os modelos estruturais são comparados, todos
estimados por mínimos quadrados em cada origem e escritos como VAR(1) em
espaço de estados (`referencias.py`):

- a média histórica do crescimento de cada série (passeio aleatório com
  deriva no nível);
- um AR(1) para cada série;
- um VAR(1) das quatro séries das Contas Nacionais.

A média e o AR(1) usam, para cada série, só os trimestres que ela tem, o que
permite prever também o desemprego, que só existe desde 2012. O AR(1) é a
referência das medidas de erro relativo.

A média está aninhada no AR(1), e o AR(1), no VAR(1). Para esses pares, a
comparação usa o teste de Clark e West (2007), porque o de Diebold e Mariano
rejeita de menos a favor do modelo maior. Os testes
(`test_referencias_avaliacao.py`) comparam as estimativas com as do
`statsmodels`, conferem o CRPS, o teste de Diebold-Mariano, a cobertura dos
intervalos, o tamanho do teste de Clark-West e a correção de Holm de
`../avaliacao.py`. O protocolo e os resultados estão no
[README da previsão](../README.md).
