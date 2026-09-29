# Macroeconomia

Modelos macroeconômicos calibrados para o Brasil, em duas frentes:

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

- **[Lei 15.270/2025](Politicas/Lei-15270/README.md):** quanto a economia
  perde com um aumento da tributação da renda do capital do tamanho da lei,
  quem ganha e quem perde, e se as conclusões valem quando as famílias não
  são plenamente racionais e quando os preços não vêm de um equilíbrio.
- **[Previsão fora da amostra](Forecast/Brasil/2013T4-2026T2/README.md):**
  os modelos de equilíbrio geral e os ABMs contra modelos estatísticos,
  prevendo PIB, consumo, FBCF, consumo do governo e desemprego de 1 a 8
  trimestres à frente, com o que se sabia em cada data.

Os modelos se usam uns aos outros: os de previsão partem da calibração do
equilíbrio geral da pasta da lei, e os experimentos da lei nos ABMs usam o
código dos ABMs da pasta de previsão. Cada script põe as pastas no caminho
de importação com `caminhos.py`, então todos rodam de qualquer lugar.

## Como rodar

Da pasta `Econometria/`, com as dependências de `Python/requirements.txt`:

```bash
python Python/macroeconomia/rodar_testes.py                  # todos os testes (cerca de 10 minutos)
python Python/macroeconomia/rodar_testes.py dsge_busca       # só as pastas com esse nome
```

Os comandos de cada modelo estão no README de cada pasta. Os dados ficam em
[`dados/brasil/`](../../dados/brasil/README.md), com os scripts que os
baixam.
