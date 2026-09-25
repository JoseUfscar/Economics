# Modelo AR(1) por OLS: pib_t = c + phi * pib_{t-1} + erro_t
#
# Rode com: Rscript R/macroeconometria/ar1.R
# (execute a partir da pasta Econometria/)

dados <- read.csv("dados/macro_series.csv")

y <- dados$pib_crescimento[-1]
y_lag <- dados$pib_crescimento[-nrow(dados)]

modelo <- lm(y ~ y_lag)
print(summary(modelo))

cat(sprintf("\nc estimado   : %.4f\n", coef(modelo)[1]))
cat(sprintf("phi estimado : %.4f\n", coef(modelo)[2]))
