"""
O ABM com leiloeiro calibrado com a amostra anual inteira (2000-2023), como
em equilibrio_geral, e os nomes e cores das regras de expectativas nas
figuras. Serve aos experimentos desta pasta (convergência e heurísticas) e
aos da Lei 15.270/2025 (Politicas/Lei-15270/abm1_com_leiloeiro).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))   # macroeconomia/
import caminhos  # noqa: E402,F401

import economia as E  # noqa: E402
import familias as F  # noqa: E402
from calibracao import aumento_tau_k_lei, calcular_alvos, calibrar as calibrar_representativo  # noqa: E402
from calibracao import carregar_dados  # noqa: E402
from calibracao_renda import renda_brasil  # noqa: E402
from experimentos import LARANJA, TINTA  # noqa: E402

PREVISAO_PERFEITA = "previsão perfeita"
CORES = {PREVISAO_PERFEITA: TINTA, "aprendizado": LARANJA, "heurísticas": "#1baf7a",
         "informação rígida": "#8e44ad", "atenção limitada": "#c0392b"}


def economia_base() -> tuple[E.Calibrada, float]:
    """Calibração de equilibrio_geral (anual, 2000-2023) e o aumento de tau_k da lei."""
    dados = carregar_dados()
    alvos = calcular_alvos(dados)
    eco, pol = calibrar_representativo(alvos)
    renda = F.Renda.de_continua(renda_brasil())
    par = F.Parametros(eco.alpha, eco.delta, 0.0, eco.theta, eco.n, eco.g, pol.tau_k)
    est = F.calibrar(par, renda, alvos.capital_produto, alvos.gasto_pib)
    return E.preparar(est), aumento_tau_k_lei(alvos, dados)
