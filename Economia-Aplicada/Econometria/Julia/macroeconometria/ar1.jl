# Modelo AR(1) por OLS: pib_t = c + phi * pib_{t-1} + erro_t
#
# Usa apenas a biblioteca padrao do Julia (sem Pkg.add necessario).
# Rode com: julia Julia/macroeconometria/ar1.jl
# (execute a partir da pasta Econometria/)

using DelimitedFiles

dados, _ = readdlm("dados/macro_series.csv", ',', header=true)
pib = Float64.(dados[:, 2])

y = pib[2:end]
y_lag = pib[1:end-1]

X = [ones(length(y_lag)) y_lag]
beta = X \ y

println("c estimado   : ", round(beta[1], digits=4))
println("phi estimado : ", round(beta[2], digits=4))
