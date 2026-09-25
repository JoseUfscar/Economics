# Modelo de Ramsey-Cass-Koopmans com governo, em tempo contínuo (versão Julia)
#
#   dk/dt = k^alpha - c - gasto - (delta + n + g) k
#   dc/dt = c [(1 - tau_k)(alpha k^(alpha-1) - delta) - rho - theta g] / theta
#
# Refaz a calibração para o Brasil a partir de dados/brasil/brasil_anual.csv e
# resolve a transição após um aumento de tau_k por "reverse shooting": parte de
# um ponto muito próximo do estado estacionário, sobre a direção estável, e
# integra o sistema para trás no tempo com Runge-Kutta de 4ª ordem. Integrar
# para trás torna a direção instável contrativa, então o método é estável.
# O Python resolve o mesmo problema como problema de contorno (solve_bvp);
# como os algoritmos são diferentes, a comparação entre as versões é um teste.
#
# Usa só a biblioteca padrão. Rode a partir da pasta Econometria/:
#     julia Julia/macroeconomia/equilibrio_geral/ramsey.jl

struct Economia
    alpha::Float64
    delta::Float64
    rho::Float64
    theta::Float64
    n::Float64
    g::Float64
end

struct Politica
    tau_k::Float64
    gasto::Float64
end

media(x) = sum(x) / length(x)

function estado_estacionario(e::Economia, p::Politica)
    retorno_bruto = e.delta + (e.rho + e.theta * e.g) / (1 - p.tau_k)
    k = (e.alpha / retorno_bruto)^(1 / (1 - e.alpha))
    y = k^e.alpha
    c = y - p.gasto - (e.delta + e.n + e.g) * k
    # Jacobiano [[a, -1], [b, 0]] com b < 0: ponto de sela
    a = e.alpha * k^(e.alpha - 1) - (e.delta + e.n + e.g)
    b = c * (1 - p.tau_k) * e.alpha * (e.alpha - 1) * k^(e.alpha - 2) / e.theta
    raiz = sqrt(a^2 - 4b)
    estavel = (a - raiz) / 2
    return (k = k, c = c, y = y, lambda_estavel = estavel, inclinacao = a - estavel)
end

function campo(e::Economia, p::Politica, x)
    k, c = x
    dk = k^e.alpha - c - p.gasto - (e.delta + e.n + e.g) * k
    dc = c * ((1 - p.tau_k) * (e.alpha * k^(e.alpha - 1) - e.delta) - e.rho - e.theta * e.g) / e.theta
    return (dk, dc)
end

function passo_rk4(e, p, x, h)
    f(z) = campo(e, p, z)
    soma(z, d, s) = (z[1] + s * d[1], z[2] + s * d[2])
    d1 = f(x)
    d2 = f(soma(x, d1, h / 2))
    d3 = f(soma(x, d2, h / 2))
    d4 = f(soma(x, d3, h))
    return (x[1] + h / 6 * (d1[1] + 2d2[1] + 2d3[1] + d4[1]),
            x[2] + h / 6 * (d1[2] + 2d2[2] + 2d3[2] + d4[2]))
end

"""
Braço estável até passar de `k_alvo`, por integração para trás a partir de
(k*, c*) + eps k* (1, s). Devolve vetores (k, c) na ordem da integração; o
i-ésimo ponto fica (i - 1) h anos antes do ponto de partida.
"""
function braco_estavel(e::Economia, p::Politica, k_alvo; h = 0.005, eps = 1e-8)
    ee = estado_estacionario(e, p)
    sinal = k_alvo > ee.k ? 1.0 : -1.0
    x = (ee.k * (1 + sinal * eps), ee.c + sinal * eps * ee.k * ee.inclinacao)
    ks, cs = [x[1]], [x[2]]
    while sinal * (x[1] - k_alvo) < 0
        x = passo_rk4(e, p, x, -h)
        push!(ks, x[1])
        push!(cs, x[2])
    end
    return ks, cs, h
end

"Interpola c no braço estável (vetores monotônicos em k)."
function c_no_braco(ks, cs, k)
    ordem = sortperm(ks)
    kk, cc = ks[ordem], cs[ordem]
    i = clamp(searchsortedlast(kk, k), 1, length(kk) - 1)
    w = (k - kk[i]) / (kk[i + 1] - kk[i])
    return (1 - w) * cc[i] + w * cc[i + 1]
end

"""
Transição inesperada a partir de k0: devolve funções k(t) e c(t) para t >= 0,
obtidas invertendo o tempo da integração para trás.
"""
function transicao_surpresa(e::Economia, p::Politica, k0)
    ks, cs, h = braco_estavel(e, p, k0)
    m = length(ks)
    w = (k0 - ks[m - 1]) / (ks[m] - ks[m - 1])   # onde o braço cruza k0
    t_cruzamento = (m - 2 + w) * h                  # tempo entre k0 e o início
    function avaliar(t)
        s = t_cruzamento - t                        # posição na integração para trás
        s <= 0 && return (ks[1], cs[1])
        i = floor(Int, s / h) + 1
        f = s / h - (i - 1)
        return ((1 - f) * ks[i] + f * ks[i + 1], (1 - f) * cs[i] + f * cs[i + 1])
    end
    return avaliar
end

"""
Aumento anunciado: a política nova vale a partir de `antecedencia`. Até lá a
economia segue a dinâmica antiga e chega exatamente ao braço estável novo.
Procura por bisseção o ponto k_a do braço novo tal que, integrando a dinâmica
antiga para trás por `antecedencia` anos, se volte a k0. Devolve (k, c) no
anúncio e (k_a, c_a) na vigência.
"""
function transicao_anunciada(e::Economia, p0::Politica, p1::Politica, k0, antecedencia; h = 0.001)
    ks, cs, _ = braco_estavel(e, p1, k0)
    passos = round(Int, antecedencia / h)
    function volta(k_a)
        x = (k_a, c_no_braco(ks, cs, k_a))
        for _ in 1:passos
            x = passo_rk4(e, p0, x, -antecedencia / passos)
        end
        return x
    end
    k1 = estado_estacionario(e, p1).k
    a, b = min(k1, k0), max(k1, k0)
    fa = volta(a)[1] - k0
    for _ in 1:80
        meio = (a + b) / 2
        fm = volta(meio)[1] - k0
        if sign(fm) == sign(fa)
            a, fa = meio, fm
        else
            b = meio
        end
    end
    k_a = (a + b) / 2
    return volta(k_a), (k_a, c_no_braco(ks, cs, k_a))
end

# ---------------------------------------------------------------- calibração

function ler_csv(caminho)
    linhas = readlines(caminho)
    colunas = split(linhas[1], ',')
    dados = Dict(String(c) => Float64[] for c in colunas)
    for linha in linhas[2:end]
        for (c, v) in zip(colunas, split(linha, ','))
            push!(dados[String(c)], isempty(v) ? NaN : parse(Float64, v))
        end
    end
    return dados
end

"Inclinação da regressão de log(x) no ano (crescimento médio anual)."
function tendencia(anos, x)
    X = [ones(length(anos)) anos]
    return (X \ log.(x))[2]
end

function calibrar(dados; inicio = 2000, fim = 2023, theta = 2.0, tau_bruto = 0.18)
    ano = dados["ano"]
    j = findall(a -> inicio <= a <= fim, ano)
    alpha = 1 - media(dados["parcela_trabalho"][j])
    delta = media(dados["depreciacao"][j] ./ dados["capital_liquido"][j .- 1])
    capital_produto = media(dados["capital_produto"][j])
    n = tendencia(ano[j], dados["ocupados"][j])
    g = tendencia(ano[j], dados["pib_real_pwt"][j] ./ dados["ocupados"][j])
    gasto_pib = media(dados["consumo_governo"][j] ./ dados["pib_nominal"][j])

    retorno = alpha / capital_produto
    tau_k = tau_bruto * retorno / (retorno - delta)   # mesma receita em base líquida
    rho = (1 - tau_k) * (retorno - delta) - theta * g
    e = Economia(alpha, delta, rho, theta, n, g)
    y = estado_estacionario(e, Politica(tau_k, 0.0)).y
    p = Politica(tau_k, gasto_pib * y)

    # Choque da Lei 15.270/2025: R$ 34,12 bi (EM nº 19/2025) sobre a renda
    # líquida do capital no último ano com PIB nominal.
    pib_bi = dados["pib_nominal"][findlast(!isnan, dados["pib_nominal"])] / 1e3
    choque = 34.12 / ((alpha - delta * capital_produto) * pib_bi)
    return e, p, choque
end

function main()
    e, p, choque = calibrar(ler_csv("dados/brasil/brasil_anual.csv"))
    ee = estado_estacionario(e, p)
    println("Calibração: alpha = ", round(e.alpha, digits = 4), ", delta = ", round(e.delta, digits = 4),
            ", rho = ", round(e.rho, digits = 4), ", n = ", round(e.n, digits = 4),
            ", g = ", round(e.g, digits = 4), ", tau_k = ", round(p.tau_k, digits = 4))
    println("Estado estacionário: k* = ", round(ee.k, digits = 6), ", c* = ", round(ee.c, digits = 6),
            ", lambda = ", round(ee.lambda_estavel, digits = 6))

    p1 = Politica(p.tau_k + choque, p.gasto)
    caminho = transicao_surpresa(e, p1, ee.k)
    println("\nAumento de ", round(100 * choque, digits = 2), " p.p. em tau_k, de surpresa:")
    for t in (0.0, 5.0, 10.0, 25.0)
        k, c = caminho(t)
        println("  t = ", lpad(t, 4), ":  k = ", round(k, digits = 6), ",  c = ", round(c, digits = 6))
    end
    inicio, vigencia = transicao_anunciada(e, p, p1, ee.k, 0.8)
    println("Anunciado 0,8 ano antes: c no anúncio = ", round(inicio[2], digits = 6),
            ", k na vigência = ", round(vigencia[1], digits = 6))
end

if abspath(PROGRAM_FILE) == @__FILE__
    main()
end
