# R

Projeto em R puro — os exemplos usam apenas `base`/`stats` (que já vêm com
qualquer instalação do R), sem pacotes externos. Isso mantém o ponto de
partida rodando em qualquer máquina sem precisar instalar nada além do R.

## Rodando os exemplos

A partir da **pasta `Econometria/`** (os scripts leem `dados/...`):

```
Rscript R/macroeconometria/ar1.R
Rscript R/microeconometria/painel_fe.R
Rscript R/financas/capm.R
Rscript R/trabalho_desenvolvimento/diff_in_diff.R
```

## Adicionando pacotes

Para modelos que precisem de pacotes de fora do base R (`plm`, `vars`,
`rugarch`, `fixest`, etc.), recomenda-se usar o
[`renv`](https://rstudio.github.io/renv/) para travar as versões:

```r
install.packages("renv")
renv::init()
renv::snapshot()
```

Isso vai criar um `renv.lock` nesta pasta com as dependências do projeto R.
