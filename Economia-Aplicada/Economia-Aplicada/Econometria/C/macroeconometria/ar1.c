/*
 * Modelo AR(1) por OLS: pib_t = c + phi * pib_{t-1} + erro_t
 *
 * Compile com: make -C C
 * Rode com   : ./C/bin/ar1
 * (execute a partir da pasta Econometria/, o binario le "dados/...")
 */
#include <stdio.h>
#include <stdlib.h>
#include "../comum/ols.h"

#define MAX_N 10000

int main(void) {
    FILE *f = fopen("dados/macro_series.csv", "r");
    if (!f) { perror("erro ao abrir dados/macro_series.csv"); return 1; }

    char linha[256];
    if (!fgets(linha, sizeof(linha), f)) { fclose(f); return 1; } /* pula cabecalho */

    double pib[MAX_N];
    int n = 0, trimestre;
    double valor;
    while (n < MAX_N && fscanf(f, "%d,%lf", &trimestre, &valor) == 2) {
        pib[n++] = valor;
    }
    fclose(f);

    int m = n - 1; /* observacoes apos criar a defasagem */
    double *X = malloc((size_t)m * 2 * sizeof(double));
    double *y = malloc((size_t)m * sizeof(double));
    for (int i = 0; i < m; i++) {
        X[i * 2 + 0] = 1.0;
        X[i * 2 + 1] = pib[i];
        y[i] = pib[i + 1];
    }

    double beta[2];
    if (ols_estimar(X, y, m, 2, beta) != 0) {
        fprintf(stderr, "erro: matriz singular\n");
        free(X); free(y);
        return 1;
    }

    printf("c estimado   : %.4f\n", beta[0]);
    printf("phi estimado : %.4f\n", beta[1]);

    free(X); free(y);
    return 0;
}
