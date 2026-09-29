# Equilíbrio geral estocástico

Este é o modelo de Ramsey com governo de
[`Politicas/Lei-15270/equilibrio_geral/`](../../../../Politicas/Lei-15270/equilibrio_geral/README.md)
escrito em tempo discreto trimestral e sujeito a três choques, um no
crescimento da produtividade, de natureza permanente, outro na produtividade
transitória e outro no gasto público (`dsge.py`). A economia é linearizada em
logaritmos em torno do crescimento balanceado e resolvida pelo método de
Klein (2000). Os parâmetros estruturais vêm da calibração anual do modelo
contínuo, refeita em cada origem, enquanto os parâmetros dos choques e os
erros de medida são estimados por máxima verossimilhança com o filtro de
Kalman.

Quando o período tende a zero, o estado estacionário e a velocidade de
convergência tendem aos do modelo contínuo, e os testes em `test_dsge.py`
verificam essa propriedade, além da solução exata de Brock-Mirman, da
precisão da linearização e da recuperação dos parâmetros em dados simulados.

A versão com margem e busca está em [`../dsge_busca/`](../dsge_busca/README.md),
e a descrição completa, com os resultados, está no [README da previsão](../README.md).
