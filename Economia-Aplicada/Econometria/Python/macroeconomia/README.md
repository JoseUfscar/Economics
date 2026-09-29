# Macroeconomia

Modelos macroeconômicos calibrados para o Brasil, organizados em duas frentes
que compartilham boa parte do código.

```
macroeconomia/
├── Politicas/
│   └── Lei-15270/                  tributação da renda do capital
│       ├── equilibrio_geral/       Ramsey-Cass-Koopmans e Aiyagari em tempo contínuo, nota técnica
│       ├── abm1_com_leiloeiro/     a lei no ABM com leiloeiro
│       └── abm2_sem_leiloeiro/     a lei no ABM sem leiloeiro
├── Forecast/
│   └── Brasil/
│       └── 2013T4-2026T2/          previsão fora da amostra: protocolo, comparação e resultados
│           ├── referencias/        média, AR(1) e VAR(1)
│           ├── dsge/               equilíbrio geral estocástico
│           ├── dsge_busca/         equilíbrio geral com margem e busca
│           ├── abm1_com_leiloeiro/ ABM com 20 mil famílias e leiloeiro walrasiano
│           └── abm2_sem_leiloeiro/ ABM com firmas, preços, salários e busca
├── caminhos.py                     põe as pastas dos modelos no caminho de importação
└── rodar_testes.py                 roda os testes de todas as pastas
```

A pasta da [Lei 15.270/2025](Politicas/Lei-15270/README.md) investiga quanto a
economia perde com um aumento da tributação da renda do capital do tamanho
previsto na lei, quem ganha e quem perde com ele e se essas conclusões
continuam valendo quando as famílias não são plenamente racionais ou quando
os preços deixam de vir de um equilíbrio. A pasta de
[previsão fora da amostra](Forecast/Brasil/2013T4-2026T2/README.md) coloca os
modelos de equilíbrio geral e os ABMs contra modelos estatísticos na previsão
do PIB, do consumo, da FBCF, do consumo do governo e do desemprego, de 1 a 8
trimestres à frente, sempre com o que se sabia em cada data.

As duas frentes dependem uma da outra, já que os modelos de previsão partem
da calibração do equilíbrio geral guardado na pasta da lei e os experimentos
da lei nos ABMs usam o código dos ABMs guardado na pasta de previsão. Para
que tudo rode de qualquer lugar, cada script registra as pastas no caminho de
importação por meio de `caminhos.py`.

## Como rodar

Os comandos rodam a partir da pasta `Econometria/`, com as dependências de
`Python/requirements.txt`, e os de cada modelo estão no README da pasta
correspondente. Os dados ficam em [`dados/brasil/`](../../dados/brasil/README.md),
junto com os scripts que os baixam.

```bash
python Python/macroeconomia/rodar_testes.py                  # todos os testes (cerca de 10 minutos)
python Python/macroeconomia/rodar_testes.py dsge_busca       # só as pastas com esse nome
```
