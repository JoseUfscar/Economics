# C

Implementações em C puro, sem dependências externas (nem GSL, nem BLAS) —
só `libc` e `libm`. A ideia é servir de base para quem quiser modelos com
controle total de desempenho/memória, ou para portar para um ambiente sem
runtime de linguagem interpretada.

## Álgebra linear compartilhada (`comum/`)

`comum/ols.c` / `comum/ols.h` implementam OLS por equações normais
(`beta = (X'X)^-1 X'y`), resolvidas por eliminação de Gauss-Jordan com
pivoteamento parcial. Todos os exemplos de todas as áreas usam essa mesma
função — ela é o bloco de construção para qualquer modelo linear novo em C.

## Compilando e rodando

```
make -C C
```

Isso gera os binários em `C/bin/`. Rode a partir da **pasta `Econometria/`**
(os binários leem `dados/...` com caminho relativo):

```
./C/bin/ar1
./C/bin/painel_fe
./C/bin/capm
./C/bin/diff_in_diff
```

Para limpar os binários: `make -C C limpar`.

## Adicionando um modelo novo

1. Crie o `.c` na pasta da área (ou uma nova área).
2. Use `ols_estimar` de `comum/ols.h` para qualquer regressão linear; para
   modelos não-lineares (probit, MLE de GARCH, etc.) você vai precisar de um
   otimizador próprio — não há nenhum incluído aqui ainda.
3. Adicione um alvo no `Makefile` seguindo o padrão dos existentes.
