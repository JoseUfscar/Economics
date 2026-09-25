# Diferenca-em-diferencas: y = b0 + b1*tratamento + b2*pos + b3*(tratamento*pos) + erro
# b3 e o efeito causal estimado do tratamento (ATT).
#
# Usa apenas a biblioteca padrao do Julia (sem Pkg.add necessario).
# Rode com: julia Julia/trabalho_desenvolvimento/diff_in_diff.jl
# (execute a partir da pasta Econometria/)

using DelimitedFiles

dados, _ = readdlm("dados/did.csv", ',', header=true)
tratamento = Float64.(dados[:, 2])
pos = Float64.(dados[:, 3])
y = Float64.(dados[:, 4])
tratamento_pos = tratamento .* pos

X = [ones(length(y)) tratamento pos tratamento_pos]
beta = X \ y

println("Efeito do tratamento (ATT, DID): ", round(beta[4], digits=4))
