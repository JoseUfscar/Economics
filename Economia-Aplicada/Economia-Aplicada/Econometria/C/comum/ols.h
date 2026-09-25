#ifndef OLS_H
#define OLS_H

/*
 * Estima beta = (X'X)^-1 X'y por eliminacao de Gauss-Jordan com pivoteamento
 * parcial (resolve as equacoes normais). Usada por todos os exemplos em C,
 * ja que a linguagem nao tem algebra linear embutida.
 *
 * X: matriz n x k (n observacoes, k regressores, incluindo a coluna de 1s
 *    para o intercepto se necessario), em row-major: X[i*k + j].
 * y: vetor de tamanho n.
 * beta: vetor de saida de tamanho k, alocado pelo chamador.
 *
 * Retorna 0 em caso de sucesso, -1 se X'X for singular (colunas
 * colineares ou observacoes insuficientes).
 */
int ols_estimar(const double *X, const double *y, int n, int k, double *beta);

#endif
