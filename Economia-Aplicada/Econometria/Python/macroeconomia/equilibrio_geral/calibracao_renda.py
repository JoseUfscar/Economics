"""
Processo de renda do modelo de Aiyagari calibrado com a PNAD Contínua (IBGE).

Tipos permanentes: os 50% com menor rendimento do trabalho, os 40% seguintes
e os 10% com maior rendimento (tabela 7543), com produtividade proporcional à
renda média de cada grupo.

Risco de desemprego, igual para todos os tipos, com dois tipos de
desempregado (curta e longa duração). Com saída a taxa constante, o tempo de
procura já decorrido de quem está desempregado segue uma exponencial; com dois
tipos, uma mistura de exponenciais, ajustada às quatro faixas da tabela 1616.
A taxa de separação reproduz a desocupação média (tabela 4099). Enquanto
desempregada, a família recebe uma fração `razao` da renda do seu tipo.

Rode a partir da pasta Econometria/:

    python Python/macroeconomia/equilibrio_geral/calibracao_renda.py
"""
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import least_squares

from aiyagari import Renda

PASTA_DADOS = Path(__file__).resolve().parents[3] / "dados" / "brasil"
CORTES = np.array([0.0, 1 / 12, 1.0, 2.0, np.inf])   # faixas de tempo de procura, em anos
COLUNAS_PROCURA = ["procura_menos_de_1_mes", "procura_1_mes_a_1_ano",
                   "procura_1_a_2_anos", "procura_2_anos_ou_mais"]
GRUPOS = {  # tipo: (fração da população, faixas da tabela 7543)
    "50% com menor renda": (0.5, ["massa_ate_p10", "massa_p10_p20", "massa_p20_p30",
                                  "massa_p30_p40", "massa_p40_p50"]),
    "40% seguintes": (0.4, ["massa_p50_p60", "massa_p60_p70", "massa_p70_p80",
                            "massa_p80_p90"]),
    "10% com maior renda": (0.1, ["massa_p90_p95", "massa_p95_p99", "massa_acima_p99"]),
}
RAZAO_DESEMPREGO = 0.4


def carregar_pnad(pasta: Path = PASTA_DADOS):
    trimestral = pd.read_csv(pasta / "pnad_trimestral.csv", index_col="trimestre")
    anual = pd.read_csv(pasta / "pnad_anual.csv", index_col="ano")
    return trimestral, anual


def parcelas_mistura(p_curto: float, f_curto: float, f_longo: float) -> np.ndarray:
    """Probabilidade de cada faixa de tempo de procura decorrido na mistura."""
    def faixas(f):
        return np.exp(-f * CORTES[:-1]) - np.exp(-f * CORTES[1:])
    return p_curto * faixas(f_curto) + (1 - p_curto) * faixas(f_longo)


def ajustar_duracao(parcelas: np.ndarray) -> tuple[float, float, float]:
    """(p_curto, f_curto, f_longo) que reproduzem as parcelas das quatro faixas."""
    def residuos(x):
        p, f_curto, f_longo = 1 / (1 + np.exp(-x[0])), np.exp(x[1]), np.exp(x[2])
        return parcelas_mistura(p, f_curto, f_longo)[:3] - parcelas[:3]

    ajuste = least_squares(residuos, x0=[0.0, np.log(3.0), np.log(0.3)], xtol=1e-14, ftol=1e-14)
    p, f_curto, f_longo = 1 / (1 + np.exp(-ajuste.x[0])), np.exp(ajuste.x[1]), np.exp(ajuste.x[2])
    if f_curto < f_longo:
        p, f_curto, f_longo = 1 - p, f_longo, f_curto
    return float(p), float(f_curto), float(f_longo)


@dataclass(frozen=True)
class Desemprego:
    taxa: float          # u, fração da força de trabalho
    p_curto: float       # fração dos desempregados que é de curta duração
    f_curto: float       # taxas anuais de saída do desemprego
    f_longo: float
    q_curto: float       # fração de quem perde o emprego que vira de curta duração
    separacao: float     # taxa anual de perda do emprego

    @property
    def duracao_media(self) -> float:
        """Duração média completa de um episódio de desemprego, em anos."""
        return self.q_curto / self.f_curto + (1 - self.q_curto) / self.f_longo


def calibrar_desemprego(trimestral: pd.DataFrame, inicio: int = 201201,
                        fim: int = 202504) -> Desemprego:
    janela = trimestral.loc[inicio:fim]
    parcelas = janela[COLUNAS_PROCURA].mean().to_numpy() / 100
    parcelas = parcelas / parcelas.sum()
    u = janela.taxa_desocupacao.mean() / 100
    p, f_curto, f_longo = ajustar_duracao(parcelas)
    # Estoque na proporção p : 1-p  <=>  entradas na proporção q/f_curto : (1-q)/f_longo.
    q = p * f_curto / (p * f_curto + (1 - p) * f_longo)
    duracao = q / f_curto + (1 - q) / f_longo
    separacao = u / ((1 - u) * duracao)          # u / (1 - u) = s * duração média
    return Desemprego(u, p, f_curto, f_longo, q, separacao)


def produtividade_dos_tipos(anual: pd.DataFrame, inicio: int = 2012, fim: int = 2025):
    """Massas populacionais e renda relativa de cada tipo (média de 1 entre ocupados)."""
    janela = anual.loc[inicio:fim]
    massas = np.array([fracao for fracao, _ in GRUPOS.values()])
    parcelas = np.array([janela[faixas].sum(axis=1).mean() for _, faixas in GRUPOS.values()])
    parcelas = parcelas / parcelas.sum()
    return massas, parcelas / massas


def renda_brasil(razao: float = RAZAO_DESEMPREGO, pnad=None) -> Renda:
    """
    Processo com 3 tipos x 3 situações (empregado, desempregado de curta e de
    longa duração), na ordem tipo a tipo, normalizado para E[z] = 1.
    """
    trimestral, anual = carregar_pnad() if pnad is None else pnad
    d = calibrar_desemprego(trimestral)
    massas, produtividade = produtividade_dos_tipos(anual)
    bloco = np.array([[0.0, d.separacao * d.q_curto, d.separacao * (1 - d.q_curto)],
                      [d.f_curto, 0.0, 0.0],
                      [d.f_longo, 0.0, 0.0]])
    situacoes = np.array([1 - d.taxa, d.taxa * d.p_curto, d.taxa * (1 - d.p_curto)])
    fator = np.array([1.0, razao, razao])
    z = np.concatenate([e * fator for e in produtividade])
    pi = np.concatenate([m * situacoes for m in massas])
    z = z / (pi @ z)
    intensidades = np.kron(np.eye(len(massas)), bloco)
    return Renda(z=tuple(z), intensidades=tuple(map(tuple, intensidades)), pi=tuple(pi))


def main() -> None:
    trimestral, anual = carregar_pnad()
    d = calibrar_desemprego(trimestral)
    massas, produtividade = produtividade_dos_tipos(anual)
    print(f"Desocupação média 2012-2025: {d.taxa:.1%}")
    print(f"Desempregados de curta duração: {d.p_curto:.1%} do estoque, saída {d.f_curto:.2f}/ano "
          f"({12 / d.f_curto:.1f} meses); longa duração: saída {d.f_longo:.2f}/ano "
          f"({12 / d.f_longo:.1f} meses)")
    print(f"Separação: {d.separacao:.3f}/ano; duração média de um episódio: "
          f"{12 * d.duracao_media:.1f} meses")
    observado = trimestral.loc[201201:202504, COLUNAS_PROCURA].mean().to_numpy() / 100
    ajustado = parcelas_mistura(d.p_curto, d.f_curto, d.f_longo)
    print("Tempo de procura (dados x modelo):",
          ", ".join(f"{o:.1%} x {m:.1%}" for o, m in zip(observado / observado.sum(), ajustado)))
    for nome, massa, e in zip(GRUPOS, massas, produtividade):
        print(f"  {nome}: {massa:.0%} dos ocupados, renda relativa {e:.2f}")


if __name__ == "__main__":
    main()
