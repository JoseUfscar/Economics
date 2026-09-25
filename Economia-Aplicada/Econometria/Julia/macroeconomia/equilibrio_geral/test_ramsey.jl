# Testes da versão Julia e comparação com a versão Python.
#
# Os valores de referência vêm de Python/macroeconomia/equilibrio_geral
# (problema de contorno com solve_bvp); aqui a transição é obtida por reverse
# shooting. Rode a partir da pasta Econometria/:
#     julia Julia/macroeconomia/equilibrio_geral/test_ramsey.jl

using Test

include("ramsey.jl")

e, p, choque = calibrar(ler_csv("dados/brasil/brasil_anual.csv"))
ee = estado_estacionario(e, p)
p1 = Politica(p.tau_k + choque, p.gasto)

@testset "Calibração igual à do Python" begin
    @test e.alpha ≈ 0.45113848396666667 rtol = 1e-10
    @test e.delta ≈ 0.06045495430903774 rtol = 1e-10
    @test e.rho ≈ 0.08892489338985976 rtol = 1e-10
    @test e.n ≈ 0.014336068141053612 rtol = 1e-8
    @test e.g ≈ 0.006723782758045677 rtol = 1e-8
    @test p.tau_k ≈ 0.2587885957785586 rtol = 1e-10
    @test p.gasto ≈ 0.3774164565266651 rtol = 1e-10
    @test choque ≈ 0.008535937910345289 rtol = 1e-10
end

@testset "Estado estacionário" begin
    @test ee.k ≈ 4.460024132270059 rtol = 1e-12
    @test ee.c ≈ 1.2221191301084433 rtol = 1e-12
    @test ee.lambda_estavel ≈ -0.06186081523112795 rtol = 1e-10
    # Euler e restrição de recursos
    @test (1 - p.tau_k) * (e.alpha * ee.k^(e.alpha - 1) - e.delta) ≈ e.rho + e.theta * e.g
    @test ee.y ≈ ee.c + p.gasto + (e.delta + e.n + e.g) * ee.k
end

@testset "Transição de surpresa igual à do Python" begin
    caminho = transicao_surpresa(e, p1, ee.k)
    referencia = Dict(0.0 => (4.460024132270059, 1.2261513438176599),
                      5.0 => (4.442694753831317, 1.2230425420586186),
                      10.0 => (4.429988680444958, 1.2207599698217715),
                      25.0 => (4.408805911011999, 1.2169486160002079))
    for (t, (k, c)) in referencia
        kj, cj = caminho(t)
        @test kj ≈ k rtol = 1e-6
        @test cj ≈ c rtol = 1e-6
    end
end

@testset "Choque anunciado igual ao do Python" begin
    inicio, vigencia = transicao_anunciada(e, p, p1, ee.k, 0.8)
    @test inicio[1] ≈ ee.k rtol = 1e-9
    @test inicio[2] ≈ 1.2256126475839924 rtol = 1e-6
    @test vigencia[1] ≈ 4.457090778676872 rtol = 1e-6
    # choque ilustrativo maior, anunciado 3 anos antes
    grande = Politica(p.tau_k + 0.10, p.gasto)
    inicio, vigencia = transicao_anunciada(e, p, grande, ee.k, 3.0)
    @test inicio[2] ≈ 1.2498133456831075 rtol = 1e-6
    @test vigencia[1] ≈ 4.358650324617339 rtol = 1e-6
end
