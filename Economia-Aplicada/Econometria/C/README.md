# C

Implementações em C puro, sem dependências externas como GSL ou BLAS, que
usam apenas `libc` e `libm`. A ideia é oferecer uma base para quem precise de
controle total sobre desempenho e memória ou queira portar os modelos para um
ambiente sem linguagem interpretada.

## Álgebra linear compartilhada (`comum/`)

Os arquivos `comum/ols.c` e `comum/ols.h` implementam o OLS pelas equações
normais, `beta = (X'X)^-1 X'y`, resolvidas por eliminação de Gauss-Jordan com
pivoteamento parcial. Todos os exemplos usam essa mesma função, que serve de
bloco de construção para qualquer modelo linear novo em C.

## Compilando e rodando

O comando abaixo gera os binários em `C/bin/`, que devem ser executados a
partir da pasta `Econometria/`, porque leem os arquivos em `dados/...` pelo
caminho relativo.

```
make -C C
./C/bin/ar1
./C/bin/painel_fe
./C/bin/capm
./C/bin/diff_in_diff
```

Os binários podem ser apagados com `make -C C limpar`.

## Adicionando um modelo novo

O arquivo `.c` fica na pasta da área, ou numa área nova, e usa `ols_estimar`,
de `comum/ols.h`, para qualquer regressão linear. Modelos não lineares, como
probit ou GARCH por máxima verossimilhança, vão precisar de um otimizador
próprio, que ainda não existe aqui. Por fim, basta acrescentar um alvo no
`Makefile` seguindo o padrão dos que já estão lá.
