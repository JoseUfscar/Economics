"""
O que as famílias escolhem, 1996-2026: com as heurísticas, o ABM percorre a
história brasileira reproduzindo o PIB e o gasto observados, e cada família
escolhe a regra de previsão que vinha acertando mais. Grava a fração de cada
regra e o juro realizado e esperado em cada trimestre.

Rode a partir da pasta Econometria/ (cerca de um minuto):

    python Python/macroeconomia/Forecast/Brasil/2013T4-2026T2/abm1_com_leiloeiro/heuristicas.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))   # macroeconomia/
import caminhos  # noqa: E402,F401

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

import economia as E  # noqa: E402
import expectativas as X  # noqa: E402
import protocolo  # noqa: E402
from comum import economia_base  # noqa: E402
from experimentos import AZUL, LARANJA, TINTA, TINTA_2, _estilo, _virgula  # noqa: E402

PASTA = Path(__file__).resolve().parent
N = 20_000


def historia_heuristicas(cal: E.Calibrada) -> pd.DataFrame:
    crescimento = protocolo.carregar_crescimento()
    _, hist = E.historia(cal, crescimento, X.Heuristicas(), N)
    return hist


def figura_heuristicas(hist: pd.DataFrame, destino: Path) -> None:
    _estilo()
    h = hist.iloc[1:]
    x = [t // 100 + (t % 100 - 0.5) / 4 for t in h.index]
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 5.6), sharex=True,
                                   gridspec_kw={"height_ratios": [2, 1.2]})
    colunas = [c for c in h.columns if c.startswith("fracao_")]
    cores = {"fracao_fundamentalista": TINTA, "fracao_aprendizado": LARANJA, "fracao_ingênua": AZUL}
    ax1.stackplot(x, *[100 * h[c] for c in colunas], labels=[c.removeprefix("fracao_") for c in colunas],
                  colors=[cores.get(c, TINTA_2) for c in colunas], alpha=0.85)
    ax1.set(ylabel="% das famílias", ylim=(0, 100))
    ax1.set_title("Regras de previsão escolhidas pelas famílias, 1996-2026", pad=30)
    ax1.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncol=3, borderaxespad=0.3)
    ax2.plot(x, 100 * h.r, color=TINTA, label="juro líquido realizado")
    ax2.plot(x, 100 * h.r_e, color=AZUL, label="juro esperado (média)")
    ax2.set(ylabel="% ao ano")
    ax2.legend(loc="lower left")
    for ax in (ax1, ax2):
        _virgula(ax)
    fig.tight_layout()
    fig.savefig(destino)
    plt.close(fig)


def main() -> None:
    cal, _ = economia_base()
    hist = historia_heuristicas(cal)
    pasta_res, pasta_fig = PASTA / "resultados", PASTA / "figuras"
    pasta_res.mkdir(exist_ok=True)
    pasta_fig.mkdir(exist_ok=True)
    hist.to_csv(pasta_res / "historia_heuristicas.csv", float_format="%.6g")
    figura_heuristicas(hist, pasta_fig / "heuristicas.png")
    print(f"Resultados em {pasta_res} e figuras em {pasta_fig}")


if __name__ == "__main__":
    main()
