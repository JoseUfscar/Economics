# Julia

Os exemplos usam só a biblioteca padrão do Julia (`LinearAlgebra`,
`DelimitedFiles`), então não é preciso `Pkg.instantiate()` nem internet para
rodá-los — funcionam com qualquer instalação padrão do Julia (testado na
1.10).

## Rodando os exemplos

A partir da **pasta `Econometria/`** (os scripts leem `dados/...`):

```
julia Julia/macroeconometria/ar1.jl
julia Julia/microeconometria/painel_fe.jl
julia Julia/financas/capm.jl
julia Julia/trabalho_desenvolvimento/diff_in_diff.jl
julia Julia/macroeconomia/equilibrio_geral/ramsey.jl
```

### Modelo de equilíbrio geral (`macroeconomia/equilibrio_geral/`)

Versão em Julia do [modelo de Ramsey com governo](../Python/macroeconomia/equilibrio_geral/README.md).
Refaz a calibração para o Brasil a partir de `dados/brasil/brasil_anual.csv` e
resolve a transição por *reverse shooting* (Runge-Kutta de 4ª ordem para trás
no tempo, a partir da direção estável). O Python usa outro algoritmo (problema
de contorno), e `test_ramsey.jl` confere que os dois concordam até a 6ª casa:

```
julia Julia/macroeconomia/equilibrio_geral/test_ramsey.jl
```

## Adicionando pacotes

Para modelos mais avançados (`GLM.jl`, `DataFrames.jl`, `ARCHModels.jl`,
`FixedEffectModels.jl` etc.), ative o ambiente desta pasta e adicione:

```
julia --project=Julia -e 'using Pkg; Pkg.add(["DataFrames", "GLM"])'
```

Isso vai gerar um `Manifest.toml` (ignorado pelo git) travando as versões
localmente.
