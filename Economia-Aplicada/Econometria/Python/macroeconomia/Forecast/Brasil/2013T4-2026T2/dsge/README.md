# Equilíbrio geral estocástico

O modelo de Ramsey com governo de
[`Politicas/Lei-15270/equilibrio_geral/`](../../../../Politicas/Lei-15270/equilibrio_geral/README.md),
escrito em tempo discreto trimestral e com três choques: crescimento da
produtividade (permanente, como em Aguiar e Gopinath, 2007), produtividade
transitória e gasto público (`dsge.py`). A economia é linearizada em
logaritmos em torno do crescimento balanceado e resolvida pelo método de
Klein (2000). Os parâmetros estruturais vêm da calibração anual do modelo
contínuo, refeita em cada origem; os dos choques e os erros de medida, da
máxima verossimilhança com o filtro de Kalman.

Quando o período tende a zero, o estado estacionário e a velocidade de
convergência tendem aos do modelo contínuo. Os testes (`test_dsge.py`)
conferem isso, a solução exata de Brock-Mirman, a precisão da linearização e
a recuperação dos parâmetros em dados simulados.

A versão com margem e busca está em [`../dsge_busca/`](../dsge_busca/README.md).
A descrição completa e os resultados estão no [README da previsão](../README.md).

## Referências

- Aguiar, M. e Gopinath, G. (2007). Emerging Market Business Cycles: The Cycle Is the Trend. *Journal of Political Economy*, 115(1), 69-102.
- Klein, P. (2000). Using the Generalized Schur Form to Solve a Multivariate Linear Rational Expectations Model. *Journal of Economic Dynamics and Control*, 24(10), 1405-1423.
