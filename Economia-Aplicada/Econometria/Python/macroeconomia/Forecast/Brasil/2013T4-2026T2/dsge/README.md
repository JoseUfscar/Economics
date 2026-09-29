# Equilíbrio geral estocástico

O modelo de Ramsey com governo de
[`Politicas/Lei-15270/equilibrio_geral/`](../../../../Politicas/Lei-15270/equilibrio_geral/README.md),
escrito em tempo discreto trimestral e com três choques: crescimento da
produtividade (permanente), produtividade transitória e gasto público
(`dsge.py`). A economia é linearizada em logaritmos em torno do crescimento
balanceado e resolvida pelo método de Klein (2000). Os parâmetros
estruturais vêm da calibração anual do modelo contínuo, refeita em cada
origem; os dos choques e os erros de medida, da máxima verossimilhança com o
filtro de Kalman.

Quando o período tende a zero, o estado estacionário e a velocidade de
convergência tendem aos do modelo contínuo; os testes (`test_dsge.py`)
conferem isso, a solução exata de Brock-Mirman, a precisão da linearização e
a recuperação dos parâmetros em dados simulados.

A versão com margem e busca está em [`../dsge_busca/`](../dsge_busca/README.md).
A descrição completa e os resultados estão no [README da previsão](../README.md).
