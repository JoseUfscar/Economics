# CAPM por OLS: retorno_ativo = alpha + beta * retorno_mercado + erro
#
# Rode com: Rscript R/financas/capm.R
# (execute a partir da pasta Econometria/)

dados <- read.csv("dados/financas.csv")

modelo <- lm(retorno_ativo ~ retorno_mercado, data = dados)
print(summary(modelo))

cat(sprintf("\nalpha estimado : %.4f\n", coef(modelo)[1]))
cat(sprintf("beta estimado  : %.4f\n", coef(modelo)[2]))
