#include <stdlib.h>
#include <math.h>
#include "ols.h"

int ols_estimar(const double *X, const double *y, int n, int k, double *beta) {
    double *XtX = calloc((size_t)k * k, sizeof(double));
    double *Xty = calloc((size_t)k, sizeof(double));
    double *aug = malloc((size_t)k * (k + 1) * sizeof(double));
    if (!XtX || !Xty || !aug) {
        free(XtX); free(Xty); free(aug);
        return -1;
    }

    for (int i = 0; i < n; i++) {
        for (int a = 0; a < k; a++) {
            Xty[a] += X[i * k + a] * y[i];
            for (int b = 0; b < k; b++) {
                XtX[a * k + b] += X[i * k + a] * X[i * k + b];
            }
        }
    }

    /* monta a matriz aumentada [XtX | Xty] e resolve por Gauss-Jordan */
    for (int a = 0; a < k; a++) {
        for (int b = 0; b < k; b++) {
            aug[a * (k + 1) + b] = XtX[a * k + b];
        }
        aug[a * (k + 1) + k] = Xty[a];
    }

    for (int col = 0; col < k; col++) {
        int pivo = col;
        double maior = fabs(aug[col * (k + 1) + col]);
        for (int r = col + 1; r < k; r++) {
            double v = fabs(aug[r * (k + 1) + col]);
            if (v > maior) { maior = v; pivo = r; }
        }
        if (maior < 1e-10) {
            free(XtX); free(Xty); free(aug);
            return -1;
        }
        if (pivo != col) {
            for (int c = 0; c <= k; c++) {
                double tmp = aug[col * (k + 1) + c];
                aug[col * (k + 1) + c] = aug[pivo * (k + 1) + c];
                aug[pivo * (k + 1) + c] = tmp;
            }
        }
        double pivo_val = aug[col * (k + 1) + col];
        for (int c = 0; c <= k; c++) {
            aug[col * (k + 1) + c] /= pivo_val;
        }
        for (int r = 0; r < k; r++) {
            if (r == col) continue;
            double fator = aug[r * (k + 1) + col];
            for (int c = 0; c <= k; c++) {
                aug[r * (k + 1) + c] -= fator * aug[col * (k + 1) + c];
            }
        }
    }

    for (int a = 0; a < k; a++) {
        beta[a] = aug[a * (k + 1) + k];
    }

    free(XtX); free(Xty); free(aug);
    return 0;
}
