"""
Formação de expectativas das famílias do ABM.

Toda família otimiza (a política de familias.TabelaPoliticas), mas com as
crenças que tem sobre o juro líquido r e o salário w (por unidade de
eficiência) que vão vigorar daqui em diante. As regras vão do neoclássico
tradicional às hipóteses de racionalidade limitada da literatura recente:

  Equilibrio          crê que o juro e o salário do equilíbrio estacionário
                      valem para sempre (a regra "fundamentalista" de Brock e
                      Hommes). Só é expectativa racional no estado
                      estacionário: fora dele, o benchmark racional é a
                      previsão perfeita de transicao.py
  Aprendizado         aprendizado adaptativo com ganho constante
                      (Evans e Honkapohja, 2001; Milani, 2007)
  Ingenua             toma os preços correntes como permanentes
  AtencaoLimitada     desconto cognitivo: percebe só uma fração m dos desvios
                      em relação ao equilíbrio (Gabaix, 2020)
  InformacaoRigida    a cada trimestre só uma fração lambda das famílias
                      atualiza a previsão, e quem atualiza adota a do
                      aprendizado (Carroll, 2003, com a rigidez de Mankiw e
                      Reis, 2002; em Mankiw e Reis, quem atualiza passa a ter
                      expectativas racionais)
  Heuristicas         escolha entre regras pelo desempenho passado das
                      previsões, com logit (Brock e Hommes, 1997; Anufriev e
                      Hommes, 2012)

Interface: iniciar(N, r_eq, w_eq, rng) no começo e atualizar(r, w, rng) a
cada trimestre, depois de observar os preços; atualizar devolve (r_e, w_e),
escalares ou vetores de tamanho N. Depois de uma mudança de política,
iniciar recebe o novo equilíbrio e herdar(r, w) devolve às regras com
memória (aprendizado, informação rígida) as crenças que tinham antes.
"""
from __future__ import annotations

from collections import deque

import numpy as np


class Equilibrio:
    nome = "fundamentalista"

    def herdar(self, r, w):
        pass

    def iniciar(self, N, r_eq, w_eq, rng):
        self.r_eq, self.w_eq = r_eq, w_eq

    def atualizar(self, r, w, rng):
        return self.r_eq, self.w_eq


class Aprendizado:
    nome = "aprendizado"

    def __init__(self, ganho: float = 0.02):
        if not 0 < ganho <= 1:
            raise ValueError("o ganho precisa estar em (0, 1]")
        self.ganho = ganho

    def iniciar(self, N, r_eq, w_eq, rng):
        self.r_hat, self.w_hat = r_eq, w_eq

    def herdar(self, r, w):
        self.r_hat, self.w_hat = r, w

    def atualizar(self, r, w, rng):
        self.r_hat += self.ganho * (r - self.r_hat)
        self.w_hat += self.ganho * (w - self.w_hat)
        return self.r_hat, self.w_hat


class Ingenua:
    nome = "ingênua"

    def herdar(self, r, w):
        pass

    def iniciar(self, N, r_eq, w_eq, rng):
        pass

    def atualizar(self, r, w, rng):
        return r, w


class AtencaoLimitada:
    nome = "atenção limitada"

    def __init__(self, atencao: float = 0.85):
        if not 0 <= atencao <= 1:
            raise ValueError("a atenção precisa estar em [0, 1]")
        self.m = atencao

    def herdar(self, r, w):
        pass

    def iniciar(self, N, r_eq, w_eq, rng):
        self.r_eq, self.w_eq = r_eq, w_eq

    def atualizar(self, r, w, rng):
        return (self.r_eq + self.m * (r - self.r_eq),
                self.w_eq + self.m * (w - self.w_eq))


class InformacaoRigida:
    """
    Cada família revê a informação com probabilidade `lam` por trimestre;
    quem revê adota a previsão da regra `base` naquele momento, quem não revê
    mantém a da última revisão. A regra base é o aprendizado, como os
    domicílios de Carroll (2003), que copiam a previsão corrente dos
    profissionais; não é a expectativa racional de Mankiw e Reis (2002).
    """

    nome = "informação rígida"

    def __init__(self, base=None, lam: float = 0.25):
        if not 0 < lam <= 1:
            raise ValueError("lam precisa estar em (0, 1]")
        self.base = Aprendizado() if base is None else base
        self.lam = lam

    def iniciar(self, N, r_eq, w_eq, rng):
        self.base.iniciar(N, r_eq, w_eq, rng)
        self.r_i = np.full(N, float(r_eq))
        self.w_i = np.full(N, float(w_eq))

    def herdar(self, r, w):
        self.base.herdar(r, w)
        self.r_i[:], self.w_i[:] = r, w

    def atualizar(self, r, w, rng):
        r_base, w_base = self.base.atualizar(r, w, rng)
        revisa = rng.random(self.r_i.size) < self.lam
        self.r_i[revisa] = r_base if np.isscalar(r_base) else np.asarray(r_base)[revisa]
        self.w_i[revisa] = w_base if np.isscalar(w_base) else np.asarray(w_base)[revisa]
        return self.r_i, self.w_i


class Heuristicas:
    """
    Regras de previsão em competição. O desempenho de cada regra é o erro da
    previsão feita `horizonte` trimestres antes contra a média dos preços
    realizados desde então (em p.p. para o juro e em % para o salário),
    acumulado com memória `memoria`:

        U_h <- memoria U_h - (1 - memoria) erro_h^2
        fração_h = exp(intensidade U_h) / soma_k exp(intensidade U_k)

    A cada trimestre cada família sorteia a sua regra com essas frações.
    """

    nome = "heurísticas"

    def __init__(self, regras=None, intensidade: float = 1.0, memoria: float = 0.7,
                 horizonte: int = 4):
        self.regras = [Equilibrio(), Aprendizado(), Ingenua()] if regras is None else regras
        self.intensidade, self.memoria, self.horizonte = intensidade, memoria, horizonte

    def iniciar(self, N, r_eq, w_eq, rng):
        for regra in self.regras:
            regra.iniciar(N, r_eq, w_eq, rng)
        H = len(self.regras)
        self.N = N
        self.desempenho = np.zeros(H)
        self.previsoes = deque(maxlen=self.horizonte + 1)   # (H, 2) por trimestre
        self.realizados = deque(maxlen=self.horizonte)
        self.fracoes = np.full(H, 1 / H)
        self.escolha = rng.integers(H, size=N)

    def herdar(self, r, w):
        for regra in self.regras:
            regra.herdar(r, w)

    def probabilidades(self) -> np.ndarray:
        v = self.intensidade * self.desempenho
        v = np.exp(v - v.max())
        return v / v.sum()

    def atualizar(self, r, w, rng):
        self.realizados.append((r, w))
        if len(self.previsoes) == self.horizonte + 1:
            antiga = self.previsoes[0]
            r_medio, w_medio = np.mean(self.realizados, axis=0)
            erro = (100 * (r_medio - antiga[:, 0])) ** 2 + (100 * (w_medio / antiga[:, 1] - 1)) ** 2
            self.desempenho = self.memoria * self.desempenho - (1 - self.memoria) * erro
        previsoes = np.array([[float(np.mean(v)) for v in regra.atualizar(r, w, rng)]
                              for regra in self.regras])
        self.previsoes.append(previsoes)
        self.fracoes = self.probabilidades()
        self.escolha = rng.choice(len(self.regras), size=self.N, p=self.fracoes)
        return previsoes[self.escolha, 0], previsoes[self.escolha, 1]


REGRAS = {
    "equilibrio": Equilibrio,
    "aprendizado": Aprendizado,
    "heuristicas": Heuristicas,
    "informacao": InformacaoRigida,
    "atencao": AtencaoLimitada,
}
