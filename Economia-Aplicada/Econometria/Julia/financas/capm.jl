# CAPM por OLS: retorno_ativo = alpha + beta * retorno_mercado + erro
#
# Usa apenas a biblioteca padrao do Julia (sem Pkg.add necessario).
# Rode com: julia Julia/financas/capm.jl
# (execute a partir da pasta Econometria/)

using DelimitedFiles

dados, _ = readdlm("dados/financas.csv", ',', header=true)
retorno_mercado = Float64.(dados[:, 2])
retorno_ativo = Float64.(dados[:, 3])

X = [ones(length(retorno_mercado)) retorno_mercado]
beta = X \ retorno_ativo

println("alpha estimado : ", round(beta[1], digits=4))
println("beta estimado  : ", round(beta[2], digits=4))
