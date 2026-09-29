# Equilíbrio geral com margem e busca

O equilíbrio geral estocástico de [`../dsge/`](../dsge/README.md) com os
fundamentos do [ABM sem leiloeiro](../abm2_sem_leiloeiro/README.md), para
aproximar os dois modelos que a previsão compara (`dsge_busca.py`). Em
relação ao modelo sem busca, há quatro mudanças:

- uma margem de 10% sobre o custo marginal, a que aparece no ABM 2;
- busca no mercado de trabalho: o emprego é uma variável de estado, com a
  separação e o desemprego de longo prazo da mesma cadeia trimestral da PNAD
  do ABM, e as firmas abrem vagas até o custo de contratar igualar o valor
  do trabalhador;
- um salário rígido, que acompanha a tendência da produtividade e se ajusta
  aos poucos ao produto marginal, com a rigidez estimada;
- um choque na taxa de separação, além dos três choques do modelo sem busca.

O modelo prevê também a variação do desemprego.

A tecnologia ($\alpha$) é a mesma dos outros modelos, calibrada pela
participação do trabalho da PWT (54,9%). Com a margem, a participação do
trabalho no modelo cai para cerca de 50%, e os lucros ficam com 9% do PIB.
Como a participação medida nos dados já inclui as margens que existem na
economia, a calibração conta a margem duas vezes. A escolha mantém a mesma
tecnologia do ABM 2 e da referência walrasiana, para que a comparação entre
eles não misture tecnologias diferentes; a alternativa seria recalibrar
$\alpha$ para que a participação com a margem fosse 54,9% ($\alpha \approx 0{,}40$).
O custo de contratar (14% do salário de um trimestre, Silva e Toledo, 2009) e
a probabilidade de preencher uma vaga (0,7 por trimestre, den Haan, Ramey e
Watson, 2000) vêm de estudos para os Estados Unidos.

Os testes (`test_dsge_busca.py`) conferem o estado estacionário (fluxos de
emprego, custo de contratar, $K/Y$ e participação do trabalho), a
estabilidade para qualquer rigidez, os sinais das respostas aos choques e o
espaço de estados com o desemprego faltante antes de 2012. A descrição
completa e os resultados estão no [README da previsão](../README.md).

## Referências

- Blanchard, O. e Galí, J. (2010). Labor Markets and Monetary Policy: A New Keynesian Model with Unemployment. *American Economic Journal: Macroeconomics*, 2(2), 1-30.
- den Haan, W. J., Ramey, G. e Watson, J. (2000). Job Destruction and Propagation of Shocks. *American Economic Review*, 90(3), 482-498.
- Hall, R. E. (2005). Employment Fluctuations with Equilibrium Wage Stickiness. *American Economic Review*, 95(1), 50-65.
- Petrongolo, B. e Pissarides, C. A. (2001). Looking into the Black Box: A Survey of the Matching Function. *Journal of Economic Literature*, 39(2), 390-431.
- Pissarides, C. A. (2000). *Equilibrium Unemployment Theory*. 2ª ed. MIT Press.
- Silva, J. I. e Toledo, M. (2009). Labor Turnover Costs and the Cyclical Behavior of Vacancies and Unemployment. *Macroeconomic Dynamics*, 13(S1), 76-96.
