# Diferenca-em-diferencas: y = b0 + b1*tratamento + b2*pos + b3*(tratamento*pos) + erro
# b3 e o efeito causal estimado do tratamento (ATT).
#
# Rode com: Rscript R/trabalho_desenvolvimento/diff_in_diff.R
# (execute a partir da pasta Econometria/)

dados <- read.csv("dados/did.csv")

modelo <- lm(y ~ tratamento * pos, data = dados)
print(summary(modelo))

cat(sprintf("\nEfeito do tratamento (ATT, DID): %.4f\n", coef(modelo)["tratamento:pos"]))
