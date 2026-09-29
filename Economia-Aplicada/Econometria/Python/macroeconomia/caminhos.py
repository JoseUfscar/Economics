"""
Pastas dos modelos de macroeconomia, para que cada script ache os outros.

    Politicas/Lei-15270/                a Lei 15.270/2025
        equilibrio_geral/               Ramsey-Cass-Koopmans e Aiyagari em tempo contínuo
        abm1_com_leiloeiro/             a lei no ABM com leiloeiro
        abm2_sem_leiloeiro/             a lei no ABM sem leiloeiro
    Forecast/Brasil/2013T4-2026T2/      previsão fora da amostra: protocolo e comparação
        referencias/                    média, AR(1) e VAR(1)
        dsge/                           equilíbrio geral estocástico
        dsge_busca/                     equilíbrio geral com margem e busca
        abm1_com_leiloeiro/             ABM com leiloeiro
        abm2_sem_leiloeiro/             ABM sem leiloeiro

Os scripts importam os módulos pelo nome (import dsge, from calibracao
import ...). Cada um começa pondo esta pasta no caminho e importando este
módulo:

    sys.path.insert(0, str(Path(__file__).resolve().parents[k]))   # macroeconomia/
    import caminhos

com k conforme a profundidade da pasta do script.
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
DADOS = RAIZ.parents[1] / "dados" / "brasil"
LEI = RAIZ / "Politicas" / "Lei-15270"
PREVISAO = RAIZ / "Forecast" / "Brasil" / "2013T4-2026T2"
PASTAS = (
    LEI / "equilibrio_geral",
    LEI / "abm1_com_leiloeiro",
    LEI / "abm2_sem_leiloeiro",
    PREVISAO,
    PREVISAO / "referencias",
    PREVISAO / "dsge",
    PREVISAO / "dsge_busca",
    PREVISAO / "abm1_com_leiloeiro",
    PREVISAO / "abm2_sem_leiloeiro",
)

for _pasta in reversed(PASTAS):
    if str(_pasta) not in sys.path:
        sys.path.insert(0, str(_pasta))
