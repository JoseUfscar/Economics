# Referências estatísticas

Os modelos contra os quais os modelos estruturais são comparados, todos
estimados por mínimos quadrados em cada origem e escritos como VAR(1) em
espaço de estados (`referencias.py`):

- **média histórica** do crescimento de cada série (passeio aleatório com
  deriva no nível);
- **AR(1)** de cada série;
- **VAR(1)** das quatro séries das Contas Nacionais.

A média e o AR(1) usam, para cada série, só os trimestres que ela tem, o que
permite prever também o desemprego, que só existe desde 2012. O AR(1) é a
referência das medidas de erro relativo.

Os testes (`test_referencias_avaliacao.py`) comparam as estimativas com as
do `statsmodels` e conferem o CRPS, o teste de Diebold-Mariano e a cobertura
dos intervalos de `../avaliacao.py`. O protocolo e os resultados estão no
[README da previsão](../README.md).
