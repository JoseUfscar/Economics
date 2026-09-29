# Referências estatísticas

Os modelos estruturais são comparados com três referências estatísticas,
todas estimadas por mínimos quadrados em cada origem e escritas como um
VAR(1) em espaço de estados em `referencias.py`. A mais simples é a média
histórica do crescimento de cada série, que equivale a um passeio aleatório
com deriva no nível, seguida por um AR(1) para cada série e por um VAR(1) com
as quatro séries das Contas Nacionais. A média e o AR(1) usam, para cada
série, apenas os trimestres em que ela existe, o que permite prever também o
desemprego, disponível só a partir de 2012, e o AR(1) serve de referência
para todas as medidas de erro relativo.

Os testes em `test_referencias_avaliacao.py` comparam as estimativas com as
do `statsmodels` e conferem o CRPS, o teste de Diebold-Mariano e a cobertura
dos intervalos calculados em `../avaliacao.py`. O protocolo e os resultados
estão no [README da previsão](../README.md).
