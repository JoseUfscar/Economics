# R

Projeto em R puro, em que os exemplos usam apenas `base` e `stats`, que já
vêm com qualquer instalação do R, sem pacotes externos. Isso garante que o
ponto de partida rode em qualquer máquina sem exigir nada além do próprio R.

## Rodando os exemplos

Os comandos devem ser executados a partir da pasta `Econometria/`, porque os
scripts leem os arquivos em `dados/...`.

```
Rscript R/macroeconometria/ar1.R
Rscript R/microeconometria/painel_fe.R
Rscript R/financas/capm.R
Rscript R/trabalho_desenvolvimento/diff_in_diff.R
```

## Adicionando pacotes

Para modelos que dependam de pacotes de fora do base R, como `plm`, `vars`,
`rugarch` ou `fixest`, a recomendação é usar o
[`renv`](https://rstudio.github.io/renv/) para travar as versões, o que cria
nesta pasta um `renv.lock` com as dependências do projeto.

```r
install.packages("renv")
renv::init()
renv::snapshot()
```
