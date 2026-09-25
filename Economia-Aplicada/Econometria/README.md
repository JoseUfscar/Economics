# Econometria

Modelagem e econometria aplicada, organizada por **linguagem** (cada uma
como um projeto independente) e, dentro de cada linguagem, por **área da
economia**. O objetivo é ter uma base comum para
lançar modelos em R, Python, Julia e C, comparando implementações da mesma
técnica em linguagens diferentes quando fizer sentido.

## Estrutura

```
Econometria/
├── R/            # projeto R (apenas base R, sem dependências externas)
├── Python/       # projeto Python (numpy, pandas, statsmodels, scipy)
├── Julia/        # projeto Julia (apenas biblioteca padrão)
├── C/            # implementações em C puro (OLS via equações normais)
└── dados/        # datasets sintéticos compartilhados + dados reais do Brasil (dados/brasil/)
```

Cada pasta de linguagem tem as mesmas quatro áreas como subpastas:

| Área | Conteúdo inicial |
|---|---|
| `macroeconometria/` | Séries temporais — modelo AR(1) por OLS |
| `microeconometria/` | Dados em painel — efeitos fixos por LSDV |
| `financas/` | Econometria financeira — CAPM (regressão de retornos) |
| `trabalho_desenvolvimento/` | Avaliação de política — diferença-em-diferenças (DID) |

Essas quatro áreas foram o ponto de partida; para adicionar uma nova área
(ex: comércio internacional, organização industrial), basta criar a mesma
subpasta em cada linguagem que for usá-la. A primeira área nova é
`macroeconomia/` (Python e Julia), com modelos de equilíbrio geral.

## Datasets compartilhados (`dados/`)

Os quatro exemplos usam datasets **sintéticos** (gerados com seed fixa),
para que o mesmo modelo rodado em R, Python, Julia e C produza os mesmos
coeficientes — útil para conferir se uma implementação nova está correta
comparando com as outras linguagens. Veja `dados/README.md` para os detalhes
de cada dataset e como regerá-los.

Os scripts sempre leem os CSVs com caminho relativo `dados/...`, então
**rode todo exemplo a partir da pasta `Econometria/`**.

## Como rodar cada linguagem

Ver o `README.md` dentro de cada pasta (`R/`, `Python/`, `Julia/`, `C/`) para
instruções específicas de setup e execução.

## Convenção para novos modelos

- Um script/programa por modelo, na pasta da área correspondente.
- Nome do arquivo descreve o modelo (ex: `var.py`, `garch.jl`, `logit.R`).
- Um cabeçalho de comentário curto explicando a equação estimada e como rodar.
- Sempre que possível, ler dados de `dados/` (ou de uma subpasta de dados
  própria da área, se o dataset não fizer sentido nas outras linguagens).

## Equilíbrio geral em tempo contínuo

[Tributação do capital no Brasil em equilíbrio geral](Python/macroeconomia/equilibrio_geral/README.md):
modelos em tempo contínuo calibrados com dados da PWT 11.0, do Ipea e do IBGE
para medir os efeitos de um aumento da tributação da renda do capital do
tamanho da Lei 15.270/2025. A primeira parte usa o modelo de
Ramsey–Cass–Koopmans com governo (choques inesperados e anunciados, estimação
estrutural com Monte Carlo e uma versão em Julia que confere os resultados com
outro algoritmo). A segunda usa famílias heterogêneas (modelo de Aiyagari,
resolvido pelas equações de Hamilton–Jacobi–Bellman e Kolmogorov, com risco de
desemprego e desigualdade calibrados com a PNAD Contínua) para mostrar quem
ganha e quem perde. A [nota técnica](Python/macroeconomia/equilibrio_geral/nota_tecnica.pdf)
traz a derivação completa.
