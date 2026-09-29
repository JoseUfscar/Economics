# Equilíbrio geral com margem e busca

O equilíbrio geral estocástico de [`../dsge/`](../dsge/README.md) com os
fundamentos do [ABM sem leiloeiro](../abm2_sem_leiloeiro/README.md), para que
a diferença entre os dois na previsão meça a falta de coordenação, e não
hipóteses diferentes (`dsge_busca.py`):

- **margem** de 10% sobre o custo marginal, a que emerge no ABM 2;
- **busca**: o emprego é uma variável de estado, com a separação e o
  desemprego de longo prazo da mesma cadeia trimestral da PNAD do ABM, e
  vagas abertas até o custo de contratar igualar o valor do trabalhador;
- **salário rígido**, que acompanha a tendência da produtividade e se ajusta
  aos poucos ao produto marginal, com a rigidez estimada;
- **choque de separação**, além dos três choques do modelo sem busca.

Prevê também a variação do desemprego. Os testes (`test_dsge_busca.py`)
conferem o estado estacionário (fluxos de emprego, custo de contratar,
$K/Y$ e participação do trabalho), a estabilidade para qualquer rigidez, os
sinais das respostas aos choques e o espaço de estados com o desemprego
faltante antes de 2012. A descrição completa e os resultados estão no
[README da previsão](../README.md).
