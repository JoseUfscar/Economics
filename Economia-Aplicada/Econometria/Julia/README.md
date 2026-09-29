# Julia

Os exemplos usam apenas a biblioteca padrão do Julia (`LinearAlgebra` e
`DelimitedFiles`), de modo que não é preciso rodar `Pkg.instantiate()` nem ter
internet, e eles funcionam em qualquer instalação padrão (testado na versão
1.10).

## Rodando os exemplos

Os comandos devem ser executados a partir da pasta `Econometria/`, porque os
scripts leem os arquivos em `dados/...`.

```
julia Julia/macroeconometria/ar1.jl
julia Julia/microeconometria/painel_fe.jl
julia Julia/financas/capm.jl
julia Julia/trabalho_desenvolvimento/diff_in_diff.jl
julia Julia/macroeconomia/equilibrio_geral/ramsey.jl
```

### Modelo de equilíbrio geral (`macroeconomia/equilibrio_geral/`)

Esta é a versão em Julia do [modelo de Ramsey com governo](../Python/macroeconomia/Politicas/Lei-15270/equilibrio_geral/README.md),
que refaz a calibração para o Brasil a partir de `dados/brasil/brasil_anual.csv`
e resolve a transição por *reverse shooting*, integrando por Runge-Kutta de
quarta ordem para trás no tempo a partir da direção estável. Como o Python
usa outro algoritmo, baseado num problema de contorno, `test_ramsey.jl`
confere que os dois concordam até a sexta casa decimal.

```
julia Julia/macroeconomia/equilibrio_geral/test_ramsey.jl
```

## Adicionando pacotes

Modelos mais avançados, que usem `GLM.jl`, `DataFrames.jl`, `ARCHModels.jl`
ou `FixedEffectModels.jl`, pedem que o ambiente desta pasta seja ativado e os
pacotes adicionados, o que gera um `Manifest.toml`, ignorado pelo git, com as
versões travadas localmente.

```
julia --project=Julia -e 'using Pkg; Pkg.add(["DataFrames", "GLM"])'
```
