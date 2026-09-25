/*
 * CAPM por OLS: retorno_ativo = alpha + beta * retorno_mercado + erro
 *
 * Compile com: make -C C
 * Rode com   : ./C/bin/capm
 * (execute a partir da pasta Econometria/, o binario le "dados/...")
 */
#include <stdio.h>
#include <stdlib.h>
#include "../comum/ols.h"

#define MAX_N 10000

int main(void) {
    FILE *f = fopen("dados/financas.csv", "r");
    if (!f) { perror("erro ao abrir dados/financas.csv"); return 1; }

    char linha[256];
    if (!fgets(linha, sizeof(linha), f)) { fclose(f); return 1; } /* pula cabecalho */

    double retorno_mercado[MAX_N], retorno_ativo[MAX_N];
    int n = 0, periodo;
    double rm, ra;
    while (n < MAX_N && fscanf(f, "%d,%lf,%lf", &periodo, &rm, &ra) == 3) {
        retorno_mercado[n] = rm;
        retorno_ativo[n] = ra;
        n++;
    }
    fclose(f);

    double *X = malloc((size_t)n * 2 * sizeof(double));
    double *y = malloc((size_t)n * sizeof(double));
    for (int i = 0; i < n; i++) {
        X[i * 2 + 0] = 1.0;
        X[i * 2 + 1] = retorno_mercado[i];
        y[i] = retorno_ativo[i];
    }

    double beta[2];
    if (ols_estimar(X, y, n, 2, beta) != 0) {
        fprintf(stderr, "erro: matriz singular\n");
        free(X); free(y);
        return 1;
    }

    printf("alpha estimado : %.4f\n", beta[0]);
    printf("beta estimado  : %.4f\n", beta[1]);

    free(X); free(y);
    return 0;
}
