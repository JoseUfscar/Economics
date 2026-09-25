/*
 * Painel com efeitos fixos por firma (LSDV): investimento_it = a_i + b*vendas_it + erro_it
 * (assume firmas numeradas sequencialmente de 1 a max_firma; firma 1 vira a categoria base)
 *
 * Compile com: make -C C
 * Rode com   : ./C/bin/painel_fe
 * (execute a partir da pasta Econometria/, o binario le "dados/...")
 */
#include <stdio.h>
#include <stdlib.h>
#include "../comum/ols.h"

#define MAX_N 10000

int main(void) {
    FILE *f = fopen("dados/painel.csv", "r");
    if (!f) { perror("erro ao abrir dados/painel.csv"); return 1; }

    char linha[256];
    if (!fgets(linha, sizeof(linha), f)) { fclose(f); return 1; } /* pula cabecalho */

    int firma_arr[MAX_N];
    double investimento_arr[MAX_N], vendas_arr[MAX_N];
    int n = 0, firma, ano, max_firma = 0;
    double investimento, vendas;
    while (n < MAX_N && fscanf(f, "%d,%d,%lf,%lf", &firma, &ano, &investimento, &vendas) == 4) {
        firma_arr[n] = firma;
        investimento_arr[n] = investimento;
        vendas_arr[n] = vendas;
        if (firma > max_firma) max_firma = firma;
        n++;
    }
    fclose(f);

    int k = 2 + (max_firma - 1); /* intercepto + vendas + (max_firma - 1) dummies */
    double *X = calloc((size_t)n * k, sizeof(double));
    double *y = malloc((size_t)n * sizeof(double));

    for (int i = 0; i < n; i++) {
        X[i * k + 0] = 1.0;
        X[i * k + 1] = vendas_arr[i];
        if (firma_arr[i] > 1) {
            X[i * k + 1 + (firma_arr[i] - 1)] = 1.0;
        }
        y[i] = investimento_arr[i];
    }

    double *beta = malloc((size_t)k * sizeof(double));
    if (ols_estimar(X, y, n, k, beta) != 0) {
        fprintf(stderr, "erro: matriz singular\n");
        free(X); free(y); free(beta);
        return 1;
    }

    printf("Efeito estimado de vendas sobre investimento: %.4f\n", beta[1]);

    free(X); free(y); free(beta);
    return 0;
}
