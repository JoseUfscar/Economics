/*
 * Diferenca-em-diferencas: y = b0 + b1*tratamento + b2*pos + b3*(tratamento*pos) + erro
 * b3 e o efeito causal estimado do tratamento (ATT).
 *
 * Compile com: make -C C
 * Rode com   : ./C/bin/diff_in_diff
 * (execute a partir da pasta Econometria/, o binario le "dados/...")
 */
#include <stdio.h>
#include <stdlib.h>
#include "../comum/ols.h"

#define MAX_N 10000

int main(void) {
    FILE *f = fopen("dados/did.csv", "r");
    if (!f) { perror("erro ao abrir dados/did.csv"); return 1; }

    char linha[256];
    if (!fgets(linha, sizeof(linha), f)) { fclose(f); return 1; } /* pula cabecalho */

    double tratamento_arr[MAX_N], pos_arr[MAX_N], y_arr[MAX_N];
    int n = 0, unidade, tratamento, pos;
    double y;
    while (n < MAX_N && fscanf(f, "%d,%d,%d,%lf", &unidade, &tratamento, &pos, &y) == 4) {
        tratamento_arr[n] = tratamento;
        pos_arr[n] = pos;
        y_arr[n] = y;
        n++;
    }
    fclose(f);

    double *X = malloc((size_t)n * 4 * sizeof(double));
    double *yv = malloc((size_t)n * sizeof(double));
    for (int i = 0; i < n; i++) {
        X[i * 4 + 0] = 1.0;
        X[i * 4 + 1] = tratamento_arr[i];
        X[i * 4 + 2] = pos_arr[i];
        X[i * 4 + 3] = tratamento_arr[i] * pos_arr[i];
        yv[i] = y_arr[i];
    }

    double beta[4];
    if (ols_estimar(X, yv, n, 4, beta) != 0) {
        fprintf(stderr, "erro: matriz singular\n");
        free(X); free(yv);
        return 1;
    }

    printf("Efeito do tratamento (ATT, DID): %.4f\n", beta[3]);

    free(X); free(yv);
    return 0;
}
