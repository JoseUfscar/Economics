"""
Calibração do modelo para o Brasil com dados/brasil/brasil_anual.csv.

Alvos, como médias ou tendências no período escolhido (padrão 2000-2023):
  alpha = 1 - participação do trabalho na renda          (PWT 11.0)
  delta = depreciação / estoque líquido do ano anterior  (Ipea)
  K/Y   = relação capital-produto                        (Ipea)
  n     = tendência de crescimento dos ocupados           (PWT 11.0)
  g     = tendência de crescimento do PIB por ocupado     (PWT 11.0)
  G/Y   = consumo final do governo / PIB                  (IBGE)
  tau_k = alíquota efetiva média sobre a renda do capital (Rabelo, 2025),
          convertida da base bruta para a base líquida de depreciação
  theta = 2, valor usual na literatura (ver sensibilidade em experimentos.py)
  rho   = escolhido para que o estado estacionário reproduza K/Y

Rode a partir da pasta Econometria/:

    python Python/macroeconomia/equilibrio_geral/calibracao.py
"""
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from modelo import Economia, Politica, estado_estacionario

DADOS = Path(__file__).resolve().parents[3] / "dados" / "brasil" / "brasil_anual.csv"

# Rabelo (2025), Cadernos de Finanças Públicas 25(3), Gráfico 4: a alíquota
# média sobre a renda bruta do capital oscila entre cerca de 13% e 23% em
# 2000-2022, com média perto de 16-17% (Mendoza et al.) e 18-19% (ajuste de
# Gollin). Usamos 18% e mostramos a sensibilidade.
TAU_K_BRUTO = 0.18

# Exposição de Motivos nº 19/2025 do Ministério da Fazenda (PL 1.087/2025,
# convertido na Lei 15.270/2025): arrecadação estimada em 2026, em R$ bilhões,
# com o imposto mínimo sobre altas rendas (25,22) e a tributação de dividendos
# remetidos ao exterior (8,90).
RECEITA_LEI_15270 = 25.22 + 8.90


@dataclass(frozen=True)
class Alvos:
    inicio: int
    fim: int
    alpha: float
    delta: float
    capital_produto: float
    n: float
    g: float
    gasto_pib: float
    investimento_pib: float   # não usado na calibração: serve de validação
    consumo_pib: float        # idem (consumo das famílias)


def carregar_dados(caminho: Path = DADOS) -> pd.DataFrame:
    return pd.read_csv(caminho, index_col="ano")


def _tendencia(serie: pd.Series) -> float:
    """Inclinação da regressão de log(serie) no ano: crescimento médio anual."""
    return float(np.polyfit(serie.index, np.log(serie), 1)[0])


def calcular_alvos(dados: pd.DataFrame, inicio: int = 2000, fim: int = 2023) -> Alvos:
    taxa_depreciacao = dados.depreciacao / dados.capital_liquido.shift(1)
    j = dados.loc[inicio:fim]
    return Alvos(
        inicio=inicio, fim=fim,
        alpha=float(1 - j.parcela_trabalho.mean()),
        delta=float(taxa_depreciacao.loc[inicio:fim].mean()),
        capital_produto=float(j.capital_produto.mean()),
        n=_tendencia(j.ocupados),
        g=_tendencia(j.pib_real_pwt / j.ocupados),
        gasto_pib=float((j.consumo_governo / j.pib_nominal).mean()),
        investimento_pib=float((j.fbcf_nominal / j.pib_nominal).mean()),
        consumo_pib=float((j.consumo_familias / j.pib_nominal).mean()),
    )


def aliquota_liquida(tau_bruto: float, alpha: float, delta: float, capital_produto: float) -> float:
    """
    Converte a alíquota sobre a renda bruta do capital (R K) na alíquota do
    modelo, que incide sobre a renda líquida de depreciação ((R - delta) K),
    mantendo a mesma receita: tau_liq (R - delta) = tau_bruto R.
    """
    retorno = alpha / capital_produto        # R = alpha Y / K
    return tau_bruto * retorno / (retorno - delta)


def calibrar(alvos: Alvos, theta: float = 2.0, tau_bruto: float = TAU_K_BRUTO):
    """Devolve (Economia, Politica) coerentes com os alvos."""
    retorno = alvos.alpha / alvos.capital_produto
    tau_k = aliquota_liquida(tau_bruto, alvos.alpha, alvos.delta, alvos.capital_produto)
    # Euler no estado estacionário: (1 - tau_k)(R - delta) = rho + theta g.
    rho = (1 - tau_k) * (retorno - alvos.delta) - theta * alvos.g
    eco = Economia(alpha=alvos.alpha, delta=alvos.delta, rho=rho, theta=theta,
                   n=alvos.n, g=alvos.g)
    y = estado_estacionario(eco, Politica(tau_k=tau_k)).y
    return eco, Politica(tau_k=tau_k, gasto=alvos.gasto_pib * y)


def aumento_tau_k_lei(alvos: Alvos, dados: pd.DataFrame,
                      receita_bi: float = RECEITA_LEI_15270) -> float:
    """
    Tamanho do choque em tau_k equivalente à nova receita sobre altas rendas:
    receita / renda do capital líquida de depreciação, (alpha - delta K/Y) PIB,
    usando o PIB nominal do último ano disponível. É uma ordem de grandeza:
    supõe que toda a nova receita incide sobre a renda do capital.
    """
    pib_bi = dados.pib_nominal.dropna().iloc[-1] / 1e3   # R$ milhões -> bilhões
    renda_capital = (alvos.alpha - alvos.delta * alvos.capital_produto) * pib_bi
    return receita_bi / renda_capital


def tabela_calibracao(alvos: Alvos, eco: Economia, pol: Politica) -> pd.DataFrame:
    ee = estado_estacionario(eco, pol)
    periodo = f"{alvos.inicio}-{alvos.fim}"
    linhas = [
        ("alpha", eco.alpha, f"1 - participação do trabalho, PWT 11.0, média {periodo}"),
        ("delta", eco.delta, f"depreciação / capital líquido, Ipea, média {periodo}"),
        ("n", eco.n, f"tendência dos ocupados, PWT 11.0, {periodo}"),
        ("g", eco.g, f"tendência do PIB por ocupado, PWT 11.0, {periodo}"),
        ("theta", eco.theta, "valor usual na literatura"),
        ("tau_k", pol.tau_k, f"Rabelo (2025): {TAU_K_BRUTO:.0%} da renda bruta, em base líquida"),
        ("rho", eco.rho, f"reproduz K/Y = {alvos.capital_produto:.3f} (Ipea, média {periodo})"),
        ("G/Y", pol.gasto / ee.y, f"consumo do governo / PIB, IBGE, média {periodo}"),
    ]
    return pd.DataFrame(linhas, columns=["parametro", "valor", "fonte ou alvo"])


def momentos(alvos: Alvos, eco: Economia, pol: Politica) -> pd.DataFrame:
    """Compara momentos do estado estacionário com os dados."""
    ee = estado_estacionario(eco, pol)
    investimento = (eco.delta + eco.n + eco.g) * ee.k / ee.y
    return pd.DataFrame([
        ("K/Y (alvo)", ee.k / ee.y, alvos.capital_produto),
        ("G/Y (alvo)", pol.gasto / ee.y, alvos.gasto_pib),
        ("I/Y (não usado)", investimento, alvos.investimento_pib),
        ("C/Y (não usado)", ee.c / ee.y, alvos.consumo_pib),
    ], columns=["momento", "modelo", "dados"])


def main() -> None:
    dados = carregar_dados()
    alvos = calcular_alvos(dados)
    eco, pol = calibrar(alvos)
    ee = estado_estacionario(eco, pol)
    with pd.option_context("display.max_colwidth", 80, "display.width", 140):
        print(tabela_calibracao(alvos, eco, pol).to_string(index=False, float_format="%.4f"))
        print()
        print(momentos(alvos, eco, pol).to_string(index=False, float_format="%.3f"))
    print(f"\nRetorno líquido após impostos: r* = {ee.r:.2%}")
    print(f"Velocidade de convergência: {-ee.lambda_estavel:.2%} ao ano "
          f"(meia-vida de {np.log(2) / -ee.lambda_estavel:.1f} anos)")
    print(f"Choque da Lei 15.270/2025 em tau_k: +{100 * aumento_tau_k_lei(alvos, dados):.2f} p.p. "
          f"(ordem de grandeza)")


if __name__ == "__main__":
    main()
