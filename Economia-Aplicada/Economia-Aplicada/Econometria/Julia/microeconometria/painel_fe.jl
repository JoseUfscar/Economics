# Painel com efeitos fixos por firma (LSDV): investimento_it = a_i + b*vendas_it + erro_it
#
# Usa apenas a biblioteca padrao do Julia (sem Pkg.add necessario).
# Rode com: julia Julia/microeconometria/painel_fe.jl
# (execute a partir da pasta Econometria/)

using DelimitedFiles

dados, _ = readdlm("dados/painel.csv", ',', header=true)
firma = Int.(dados[:, 1])
investimento = Float64.(dados[:, 3])
vendas = Float64.(dados[:, 4])

firmas_unicas = sort(unique(firma))
n = length(firma)
k = length(firmas_unicas)

# dummies de efeito fixo por firma (a primeira firma vira a categoria base)
D = zeros(n, k - 1)
for j in 2:k
    D[:, j - 1] .= (firma .== firmas_unicas[j])
end

X = [ones(n) vendas D]
beta = X \ investimento

println("Efeito estimado de vendas sobre investimento: ", round(beta[2], digits=4))
