"""
Estimação estrutural de rho e theta em dados sintéticos gerados pelo modelo.

A economia calibrada para o Brasil parte de dois capitais iniciais conhecidos
(60% e 140% de k*). Observam-se, por 25 anos, o consumo agregado de cada ano e
o capital no fim de cada ano, com erro de medida log-normal independente de
desvio-padrão sigma = 1%. Os demais parâmetros ficam nos valores calibrados.
rho e theta saem de mínimos quadrados não lineares nos logaritmos, resolvendo
o equilíbrio de novo a cada avaliação.

No estado estacionário só a soma rho + theta g é identificada; são as
transições que separam os dois parâmetros. O Monte Carlo mede viés, erro
quadrático médio e cobertura dos intervalos de 95%.

Rode a partir da pasta Econometria/:

    python Python/macroeconomia/equilibrio_geral/estimacao.py
    python Python/macroeconomia/equilibrio_geral/estimacao.py --replicas 200
"""
import argparse
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import least_squares

from calibracao import calcular_alvos, calibrar, carregar_dados
from modelo import Economia, Politica, estado_estacionario, fluxos_anuais, resolver_transicao

RAZOES_K0 = (0.6, 1.4)
ANOS = 25
SIGMA = 0.01
LIMITES = ([0.005, 0.25], [0.25, 8.0])   # rho, theta
PARTIDAS = ((0.05, 1.0), (0.12, 4.0))


def simular(eco: Economia, pol: Politica, anos: int = ANOS,
            razoes=RAZOES_K0) -> pd.DataFrame:
    """Consumo anual e capital de fim de ano, sem erro de medida."""
    k_estrela = estado_estacionario(eco, pol).k
    partes = []
    for i, razao in enumerate(razoes, start=1):
        traj = resolver_transicao(eco, razao * k_estrela, pol)
        fluxos = fluxos_anuais(traj, anos)
        partes.append(pd.DataFrame({"trajetoria": i, "k0": razao * k_estrela,
                                    "ano": fluxos.ano, "C": fluxos.C, "K": fluxos.K_fim}))
    return pd.concat(partes, ignore_index=True)


def adicionar_ruido(dados: pd.DataFrame, sigma: float, rng) -> pd.DataFrame:
    """Erros independentes N(0, sigma²) nos logaritmos de C e K."""
    ruido = rng.normal(0.0, sigma, size=(len(dados), 2))
    return dados.assign(C_obs=dados.C * np.exp(ruido[:, 0]), K_obs=dados.K * np.exp(ruido[:, 1]))


def estimar(dados: pd.DataFrame, eco: Economia, pol: Politica, sigma: float = SIGMA,
            partidas=PARTIDAS) -> dict:
    """
    Mínimos quadrados não lineares em (rho, theta), com os demais parâmetros e
    os k0 fixos. Os resíduos são padronizados por sigma, então (J'J)^-1 é a
    matriz de covariância assintótica quando o modelo está correto.
    """
    grupos = [(g.k0.iloc[0], g.sort_values("ano")) for _, g in dados.groupby("trajetoria")]
    observado = np.concatenate([np.log(g[["C_obs", "K_obs"]].to_numpy()).ravel()
                                for _, g in grupos])

    def residuos(x):
        try:
            candidato = replace(eco, rho=x[0], theta=x[1])
            previsto = []
            for k0, g in grupos:
                fluxos = fluxos_anuais(resolver_transicao(candidato, k0, pol), len(g))
                previsto.append(np.log(fluxos[["C", "K_fim"]].to_numpy()).ravel())
        except (ValueError, RuntimeError):
            return np.full(observado.size, 1e3)   # parâmetros sem equilíbrio válido
        return (observado - np.concatenate(previsto)) / sigma

    ajustes = [least_squares(residuos, partida, bounds=LIMITES, x_scale=(0.01, 1.0))
               for partida in partidas]
    melhor = min(ajustes, key=lambda a: a.cost)
    jac = melhor.jac
    covariancia = np.linalg.inv(jac.T @ jac)
    erros = np.sqrt(np.diag(covariancia))
    return {
        "rho": melhor.x[0], "theta": melhor.x[1],
        "ep_rho": erros[0], "ep_theta": erros[1],
        "correlacao": covariancia[0, 1] / (erros[0] * erros[1]),
        "objetivo": 2 * melhor.cost,             # soma dos resíduos ao quadrado
        "n_obs": observado.size,
        "condicao": np.linalg.cond(jac * melhor.x),  # sensibilidade a variações relativas
    }


def monte_carlo(eco: Economia, pol: Politica, replicas: int, sigma: float = SIGMA,
                semente: int = 2026) -> pd.DataFrame:
    verdade = simular(eco, pol)
    rng = np.random.default_rng(semente)
    linhas = []
    for r in range(replicas):
        estimativa = estimar(adicionar_ruido(verdade, sigma, rng), eco, pol, sigma)
        linhas.append({"replica": r, **estimativa})
    return pd.DataFrame(linhas)


def resumo_monte_carlo(mc: pd.DataFrame, eco: Economia) -> pd.DataFrame:
    linhas = []
    for nome, verdadeiro in (("rho", eco.rho), ("theta", eco.theta)):
        erro = mc[nome] - verdadeiro
        linhas.append({
            "parametro": nome, "verdadeiro": verdadeiro, "media": mc[nome].mean(),
            "vies": erro.mean(), "rmse": np.sqrt((erro**2).mean()),
            "dp_estimativas": mc[nome].std(), "ep_medio": mc[f"ep_{nome}"].mean(),
            "cobertura_95": (np.abs(erro / mc[f"ep_{nome}"]) < 1.96).mean(),
        })
    return pd.DataFrame(linhas)


def figura_monte_carlo(mc: pd.DataFrame, eco: Economia, destino: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from experimentos import AZUL, FUNDO, TINTA, TINTA_2, _estilo, _virgula

    _estilo()
    fig, ax = plt.subplots(figsize=(7.5, 4.8))
    theta = np.linspace(mc.theta.min() - 0.05, mc.theta.max() + 0.05, 50)
    r_estrela = eco.rho + eco.theta * eco.g
    ax.plot(theta, r_estrela - eco.g * theta, color=TINTA_2, linewidth=1.2)
    ax.annotate(r"$\rho + \theta g = r^*$ (só o estado estacionário)", (theta[0], r_estrela - eco.g * theta[0]),
                xytext=(10, 0), textcoords="offset points", ha="left", va="center",
                color=TINTA_2, fontsize=8.5)
    ax.plot(mc.theta, mc.rho, "o", color=AZUL, markersize=4.5, alpha=0.75,
            markeredgecolor=FUNDO, markeredgewidth=0.8)
    ax.plot(eco.theta, eco.rho, "o", color=TINTA, markersize=7, markeredgecolor=FUNDO,
            markeredgewidth=1.5)
    ax.annotate("valor verdadeiro", (eco.theta, eco.rho), xytext=(-110, -60),
                textcoords="offset points", color=TINTA, fontsize=8.5,
                arrowprops={"arrowstyle": "-", "color": TINTA_2, "linewidth": 0.8})
    ax.set(xlabel=r"$\hat\theta$", ylabel=r"$\hat\rho$")
    ax.set_title(f"Estimativas em {len(mc)} amostras simuladas (25 anos, 2 transições)")
    _virgula(ax)
    fig.tight_layout()
    fig.savefig(destino)
    plt.close(fig)


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description="Estimação sintética de rho e theta.")
    parser.add_argument("--replicas", type=int, default=0,
                        help="número de réplicas do Monte Carlo (0 = só uma estimação)")
    parser.add_argument("--semente", type=int, default=2026)
    args = parser.parse_args(argv)

    eco, pol = calibrar(calcular_alvos(carregar_dados()))
    amostra = adicionar_ruido(simular(eco, pol), SIGMA, np.random.default_rng(args.semente))
    est = estimar(amostra, eco, pol)
    print(f"Valores verdadeiros: rho = {eco.rho:.4f}, theta = {eco.theta:.2f}")
    print(f"Estimativas: rho = {est['rho']:.4f} ({est['ep_rho']:.4f}), "
          f"theta = {est['theta']:.3f} ({est['ep_theta']:.3f}); "
          f"correlação = {est['correlacao']:.2f}")
    print(f"Soma dos resíduos² = {est['objetivo']:.1f} com {est['n_obs']} observações; "
          f"número de condição = {est['condicao']:.1f}")
    if args.replicas:
        mc = monte_carlo(eco, pol, args.replicas, semente=args.semente)
        print(f"\nMonte Carlo com {args.replicas} réplicas:")
        print(resumo_monte_carlo(mc, eco).to_string(index=False, float_format="%.4f"))
        destino = Path(__file__).resolve().parent / "figuras" / "monte_carlo.png"
        figura_monte_carlo(mc, eco, destino)
        print(f"Figura gravada em {destino}")


if __name__ == "__main__":
    main()
