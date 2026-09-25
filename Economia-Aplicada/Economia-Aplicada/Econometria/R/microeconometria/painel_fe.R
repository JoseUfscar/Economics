# Painel com efeitos fixos por firma (LSDV): investimento_it = a_i + b*vendas_it + erro_it
#
# Rode com: Rscript R/microeconometria/painel_fe.R
# (execute a partir da pasta Econometria/)

dados <- read.csv("dados/painel.csv")
dados$firma <- factor(dados$firma)

modelo <- lm(investimento ~ vendas + firma, data = dados)
print(summary(modelo))

cat(sprintf("\nEfeito estimado de vendas sobre investimento: %.4f\n", coef(modelo)["vendas"]))
