"""
Economia sem leiloeiro: firmas que fixam preços e salários, mercado de
trabalho com busca e mercado de bens com fornecedores.

As famílias são as de economia.py: cada uma escolhe o consumo com a política
ótima para as suas crenças (expectativas.py), com os tipos permanentes e o
risco de desemprego calibrados com a PNAD. O que muda é tudo o que o
leiloeiro fazia:

  trabalho   quem está empregado trabalha numa firma, e o desemprego é o que
             sobra: separações à taxa da cadeia trimestral da PNAD, demissões
             quando a firma encolhe e contratações por busca. A cada rodada, o
             desempregado se candidata com uma probabilidade (maior para quem
             é de curta duração, como na PNAD) a uma firma com vagas, sorteada
             com peso nas vagas e no salário oferecido. O desempregado recebe
             do governo a mesma fração da renda do seu tipo que no Aiyagari,
             mas não produz.
  bens       cada família compra de poucos fornecedores, do mais barato ao
             mais caro, e a firma raciona quando o estoque acaba. Quem é
             racionado poupa o que não gastou. Depois das famílias, o governo
             e o investimento das firmas compram o que sobrou. O que não se
             vende vira estoque, que se deprecia.
  produção   cada firma produz com todo o quadro e ajusta o quadro aos
             poucos pelo estoque: quer mais gente quando o estoque fica
             abaixo de uma faixa e menos quando fica acima (Lengnick, 2013;
             Delli Gatti et al., 2011).
  preços     cada firma revê o preço com uma probabilidade por trimestre
             (Calvo) e cobra uma margem sobre o custo unitário, com o capital e
             o trabalho na combinação de custo mínimo. A margem sobe quando o
             estoque fica baixo e desce quando sobra, dentro de uma faixa.
  salários   a firma que não preenche a maior parte das vagas oferece mais; a
             que passa dois anos sem essa dificuldade oferece menos (Lengnick,
             2013). O preço repassa só a parte do trabalho no custo, então
             essa regra sozinha levaria o salário real para cima sem limite;
             é a margem, que sobe quando falta produto, que o segura. O
             salário real e a margem saem desse conflito, não do produto
             marginal.
  capital    as firmas pertencem a um fundo, onde as famílias guardam a
             riqueza. Cada firma investe para chegar ao capital de custo
             mínimo para o quadro que quer, com o custo do capital dado pelo
             retorno que as famílias esperam. O retorno do fundo é o lucro
             realizado, não o produto marginal: não existe mercado de capital.

A contabilidade fecha por construção: a riqueza das famílias mais o saldo do
governo é igual ao capital mais o valor dos estoques, a cada trimestre.

Unidades: tudo por família (k_f é o capital da firma f dividido pelo número
de famílias), em unidades de eficiência como em economia.py. Rendas, produto
e gasto em taxa anual; estoques, vendas e compras em quantidades do
trimestre. Os preços e salários são relativos ao índice de preços do
trimestre anterior; não há moeda.

A referência é o equilíbrio walrasiano com os mesmos fundamentos
(`referencia`): famílias iguais, desempregados que não produzem e recebem
benefício do governo, e o desemprego da PNAD.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))   # macroeconomia/
import caminhos  # noqa: E402,F401

import economia as E  # noqa: E402
import familias as F  # noqa: E402

EMPREGADO, CURTA, LONGA = 0, 1, 2


# --- equilíbrio walrasiano de referência --------------------------------------

def desempregados(renda: F.Renda) -> np.ndarray:
    """Estados de desemprego (curta e longa duração), na ordem de calibracao_renda."""
    return np.arange(renda.estados) % 3 != EMPREGADO


# Sem leiloeiro, o retorno do fundo pode ficar muito abaixo do de equilíbrio,
# e as famílias precisam de políticas para crenças de juro baixo e negativo.
LACUNAS = np.geomspace(0.25, 0.0003, 22)


def referencia(par: F.Parametros, renda: F.Renda, capital_produto: float, gasto_pib: float,
               grades: F.Grades = F.Grades()) -> E.Calibrada:
    """Calibração com os desempregados fora da produção, recebendo benefício do governo."""
    est = F.calibrar(par, renda, capital_produto, gasto_pib, grades, beneficio=desempregados(renda))
    return E.preparar(est, grades, LACUNAS)


def reformada(cal0: E.Calibrada, aumento: float, pesos) -> E.Calibrada:
    par1 = replace(cal0.par, tau_k=cal0.par.tau_k + aumento)
    est1 = F.equilibrio(par1, cal0.renda, pesos, K_inicial=cal0.est.K,
                        beneficio=desempregados(cal0.renda))
    return E.preparar(est1, lacunas=LACUNAS)


# --- comportamento das firmas e dos mercados -------------------------------------

@dataclass(frozen=True)
class Comportamento:
    """
    Regras das firmas e dos mercados, por trimestre. Os valores vêm da
    literatura de ABM macro, convertidos para trimestres:

      preços      revisão com probabilidade 0,75 por trimestre, que equivale à
                  frequência mensal de 37% de mudança de preços no Brasil
                  (Gouvea, 2007); a margem sobre o custo unitário muda até 2
                  p.p. por trimestre, entre −5% e +15% (Lengnick, 2013, usa
                  +2,5% a +15% sobre o custo marginal)
      salários    passo até 3% (1,9% ao mês em Lengnick, 2013) quando mais da
                  metade das vagas fica aberta; corte depois de 8 trimestres
                  sem essa dificuldade (24 meses em Lengnick)
      estoques    faixa de 15% a 45% das vendas trimestrais esperadas; abaixo
                  dela, a firma quer até 5% mais trabalho e sobe a margem;
                  acima, quer até 5% menos e baixa a margem; o estoque se
                  deprecia 5% por trimestre
      busca       3 rodadas por trimestre; peso do salário na escolha da firma
                  com elasticidade 5
      demissões   só quando o quadro passa 5% do desejado, no máximo 10% do
                  quadro por trimestre (retenção de mão de obra)
      capital     reposição da depreciação e do crescimento de tendência mais
                  3% por trimestre da distância até o capital de custo mínimo
                  para o quadro desejado. É o único valor calibrado com dados:
                  com ele, o desvio-padrão do crescimento trimestral da FBCF
                  na história do ABM de 1996 a 2013 (previsao_descentralizada,
                  com o PIB, o gasto e o desemprego observados) fica em 3,6
                  p.p. na média de quatro sementes, contra 3,5 p.p. nas Contas
                  Nacionais (com 10% por trimestre seria 12 p.p.). O período
                  termina antes da primeira origem da avaliação de previsões
      fornecedores 3 por família; a cada trimestre, com probabilidade 0,25, a
                  família conhece uma firma qualquer e troca o fornecedor mais
                  caro se ela for mais barata; quem foi racionado troca o
                  fornecedor que faltou, com probabilidade 0,5, por uma firma
                  sorteada com peso no tamanho (Lengnick, 2013)
      produtividade das firmas: AR(1) do log com persistência 0,95 por
                  trimestre e desvio-padrão estacionário 0,1
    """

    firmas: int = 200
    persistencia_produtividade: float = 0.95
    dispersao_produtividade: float = 0.1
    revisao_preco: float = 0.75
    passo_margem: float = 0.02
    margem_minima: float = -0.05
    margem_maxima: float = 0.15
    depreciacao_estoque: float = 0.05
    estoque_baixo: float = 0.15
    estoque_alto: float = 0.45
    ajuste_vendas: float = 0.5
    passo_salario: float = 0.03
    vagas_dificeis: float = 0.5
    paciencia_salario: int = 8
    rodadas_busca: int = 3
    peso_salario: float = 5.0
    passo_quadro: float = 0.05
    quadro_minimo: float = 0.05
    folga_demissao: float = 0.05
    demissao_maxima: float = 0.10
    ajuste_capital: float = 0.03
    fornecedores: int = 3
    procura_fornecedor: float = 0.25
    troca_racionado: float = 0.5
    elasticidade_institucional: float = 2.0


@dataclass(frozen=True)
class Fluxos:
    """Fluxos do mercado de trabalho, em probabilidades por trimestre."""

    separacao: float
    q_curto: float          # fração de quem perde o emprego que é de curta duração
    busca_curta: float      # probabilidade de se candidatar em cada rodada
    busca_longa: float

    @staticmethod
    def da_renda(renda: F.Renda, rodadas: int) -> "Fluxos":
        """
        Os fluxos da cadeia de Markov trimestral da PNAD, a mesma do modelo com
        leiloeiro: a separação é a probabilidade de passar de empregado a
        desempregado no trimestre, e a busca por rodada reproduz a
        probabilidade de voltar ao emprego. Com vagas sobrando, quem se
        candidata é contratado, e o emprego segue exatamente essa cadeia; com
        poucas vagas, a saída do desemprego é menor, e o desemprego passa a
        depender das firmas.
        """
        P = renda.P
        para_curta, para_longa = P[EMPREGADO, CURTA], P[EMPREGADO, LONGA]

        def por_rodada(achar):
            return float(1 - (1 - achar) ** (1 / rodadas))

        return Fluxos(float(para_curta + para_longa), float(para_curta / (para_curta + para_longa)),
                      por_rodada(P[CURTA, EMPREGADO]), por_rodada(P[LONGA, EMPREGADO]))


@dataclass
class Economia:
    cal: E.Calibrada
    comp: Comportamento
    fluxos: Fluxos
    tau_k_base: float | None = None   # numa reforma, a alíquota de antes: a receita a mais segue os pesos

    @property
    def media_log_phi(self) -> float:
        # log phi ~ N(mu, s^2) com E[1/phi] = 1: a mesma produção agregada que a
        # firma representativa quando todas as firmas produzem o mesmo.
        return self.comp.dispersao_produtividade ** 2 / 2

    @property
    def eficiencia(self) -> np.ndarray:
        """Unidades de eficiência de quem está empregado, por tipo."""
        return self.cal.renda.z[np.arange(0, self.cal.renda.estados, 3)]

    @property
    def trabalho_referencia(self) -> float:
        return F.trabalho_e_beneficio(self.cal.renda, desempregados(self.cal.renda))[0]


@dataclass
class Estado:
    # famílias
    s: np.ndarray            # riqueza no fim do trimestre anterior, já com o retorno do fundo
    tipo: np.ndarray
    curta: np.ndarray        # tipo de desempregado de quem perde o emprego (sorteado na separação)
    empregador: np.ndarray   # firma de cada família, -1 se desempregada
    duracao: np.ndarray      # trimestres desde a perda do emprego (0 para quem está empregado)
    fornecedores: np.ndarray # (N, m)
    crencas: object
    # firmas
    log_phi: np.ndarray
    k: np.ndarray            # capital, por família
    x: np.ndarray            # estoque, quantidade
    p: np.ndarray            # preço relativo
    w: np.ndarray            # salário por unidade de eficiência
    margem: np.ndarray       # margem sobre o custo unitário
    quadro_alvo: np.ndarray  # trabalho que a firma quer empregar (unidades de eficiência por família)
    vendas_esperadas: np.ndarray
    sem_vaga: np.ndarray     # trimestres seguidos sem dificuldade para contratar
    # agregados
    r: float                 # último retorno líquido do fundo, taxa anual
    governo: float           # saldo do governo: gasto não realizado e imposto sobre o lucro
    governo_reforma: float = 0.0   # a parte do imposto que vem do aumento da alíquota
    log_X: float = 0.0
    c: np.ndarray | None = None   # consumo (quantidade) de cada família no trimestre anterior
    pib: float = np.nan      # produto do trimestre anterior (taxa anual, unidades de eficiência dele)
    G: float = np.nan        # gasto que o governo quis comprar no trimestre anterior

    @property
    def N(self) -> int:
        return self.s.size


# --- auxiliares vetorizados -----------------------------------------------------

def _soma_por_grupo(valores: np.ndarray, grupos: np.ndarray) -> np.ndarray:
    """Soma acumulada dentro de cada grupo (grupos contíguos)."""
    acumulada = np.cumsum(valores)
    inicio = np.r_[True, grupos[1:] != grupos[:-1]]
    base = (acumulada - valores)[inicio]
    return acumulada - base[np.cumsum(inicio) - 1]


def _sortear_com_peso(pesos: np.ndarray, n: int, rng) -> np.ndarray:
    acumulada = np.cumsum(pesos)
    return np.minimum(np.searchsorted(acumulada, rng.random(n) * acumulada[-1], side="right"),
                      pesos.size - 1)


def _fornecedores_iniciais(N: int, m: int, pesos: np.ndarray, rng) -> np.ndarray:
    lista = _sortear_com_peso(pesos, N * m, rng).reshape(N, m)
    while True:
        ordenada = np.sort(lista, axis=1)
        repetida = np.any(ordenada[:, 1:] == ordenada[:, :-1], axis=1)
        if not repetida.any():
            return lista
        lista[repetida] = _sortear_com_peso(pesos, repetida.sum() * m, rng).reshape(-1, m)


def trabalho_das_firmas(estado: Estado, eficiencia_familia: np.ndarray, firmas: int) -> np.ndarray:
    empregado = estado.empregador >= 0
    return np.bincount(estado.empregador[empregado], eficiencia_familia[empregado], firmas)


def custo_unitario(phi, w, R, alpha):
    """Custo por unidade produzida com capital e trabalho na combinação de custo mínimo."""
    return (R / alpha) ** alpha * (w / (1 - alpha)) ** (1 - alpha) / phi


# --- população inicial --------------------------------------------------------

def estado_inicial(eco: Economia, crencas, N: int, rng) -> Estado:
    """
    Parte da referência walrasiana: famílias estratificadas como em
    economia.estado_inicial (com os estados de emprego da PNAD), firmas que
    produzem o mesmo e usam capital e trabalho na proporção do equilíbrio, com
    insumos inversamente proporcionais à produtividade, preços iguais ao
    custo unitário e salários iguais ao do equilíbrio. O capital desconta o
    valor dos estoques, para que a riqueza das famílias seja a do equilíbrio.
    """
    cal, comp = eco.cal, eco.comp
    par, est, renda = cal.par, cal.est, cal.renda
    D, alpha, n_firmas = par.periodo, par.alpha, comp.firmas
    base = E.estado_inicial(cal, crencas, N, rng)
    tipo, situacao = renda.tipo[base.j], base.j % 3
    empregado = situacao == EMPREGADO

    log_phi = eco.media_log_phi + comp.dispersao_produtividade * rng.standard_normal(n_firmas)
    log_phi += np.log(np.mean(np.exp(-log_phi)))        # E[1/phi] = 1 exato na amostra
    phi = np.exp(log_phi)
    L = eco.trabalho_referencia
    k_por_l = est.K / L
    fatia = (1 / phi) / np.sum(1 / phi)

    eficiencia = eco.eficiencia[tipo] / N
    ordem = rng.permutation(np.flatnonzero(empregado))
    meio = np.cumsum(eficiencia[ordem]) - eficiencia[ordem] / 2
    empregador = np.full(N, -1)
    empregador[ordem] = np.minimum(np.searchsorted(np.cumsum(fatia), meio / eficiencia[ordem].sum()),
                                   n_firmas - 1)
    l = np.bincount(empregador[ordem], eficiencia[ordem], n_firmas)
    k = k_por_l * l
    y = phi * k**alpha * l ** (1 - alpha)
    vendas = D * y
    x = (comp.estoque_baixo + comp.estoque_alto) / 2 * vendas
    p = custo_unitario(phi, est.w, alpha * est.y / est.K, alpha)   # = custo marginal
    riqueza = base.s.mean() * par.fator_crescimento
    k *= (riqueza - p @ x) / k.sum()

    fornecedores = _fornecedores_iniciais(N, comp.fornecedores, vendas, rng)
    fator = par.fator_crescimento   # os estoques estão em unidades de antes do crescimento
    # Quem começa desempregado já procura há um tempo: 1 a 4 trimestres.
    duracao = np.where(empregado, 0, rng.integers(1, 5, N))
    return Estado(s=base.s, tipo=tipo, curta=situacao == CURTA, empregador=empregador, duracao=duracao,
                  fornecedores=fornecedores, crencas=crencas, log_phi=log_phi,
                  k=k / fator, x=x / fator, p=p, w=np.full(n_firmas, est.w),
                  margem=np.zeros(n_firmas), quadro_alvo=l.copy(), vendas_esperadas=vendas / fator,
                  sem_vaga=np.zeros(n_firmas, dtype=int), r=est.r, governo=0.0,
                  pib=float(p @ (phi * k**alpha * l ** (1 - alpha))), G=par.gasto)


# --- mercados -------------------------------------------------------------------

def _demitir(empregador, eficiencia, reducao, rng) -> np.ndarray:
    """Demite, em ordem aleatória, até a redução de trabalho pedida por firma (sem passar dela)."""
    cand = np.flatnonzero((empregador >= 0))
    cand = cand[reducao[empregador[cand]] > 0]
    if cand.size == 0:
        return cand
    firma = empregador[cand]
    ordem = np.lexsort((rng.random(cand.size), firma))
    cand, firma = cand[ordem], firma[ordem]
    acumulado = _soma_por_grupo(eficiencia[cand], firma)
    return cand[acumulado <= reducao[firma] + 1e-15]


def _buscar(empregador, curta, eficiencia, vagas, w, eco: Economia, rng, procura):
    """
    Rodadas de busca. Cada desempregado que começou o trimestre desempregado
    (quem acabou de perder o emprego espera o trimestre seguinte, como na
    cadeia de Markov trimestral) se candidata com probabilidade por rodada a
    uma firma com vagas, sorteada com peso vagas x (w / w médio)^e.
    A firma aceita, em ordem aleatória, enquanto houver vaga. Devolve o
    número de contratações e as vagas que sobraram.
    """
    comp, fluxos = eco.comp, eco.fluxos
    vagas = vagas.copy()
    contratados = 0
    w_medio = np.mean(w)
    for _ in range(comp.rodadas_busca):
        abertas = vagas > 1e-12
        if not abertas.any():
            break
        desempregado = np.flatnonzero((empregador < 0) & procura)
        chance = np.where(curta[desempregado], fluxos.busca_curta, fluxos.busca_longa)
        cand = desempregado[rng.random(desempregado.size) < chance]
        if cand.size == 0:
            continue
        atracao = np.where(abertas, vagas * (w / w_medio) ** comp.peso_salario, 0.0)
        firma = _sortear_com_peso(atracao, cand.size, rng)
        ordem = np.lexsort((rng.random(cand.size), firma))
        cand, firma = cand[ordem], firma[ordem]
        acumulado = _soma_por_grupo(eficiencia[cand], firma)
        aceita = acumulado - eficiencia[cand] < vagas[firma]
        empregador[cand[aceita]] = firma[aceita]
        vagas = np.maximum(vagas - np.bincount(firma[aceita], eficiencia[cand[aceita]], vagas.size), 0.0)
        contratados += int(aceita.sum())
    return contratados, vagas


def _mercado_de_bens(orcamento, fornecedores, p, estoque, pedido_institucional, peso_institucional,
                     rng=None, rodadas_institucionais: int = 3):
    """
    Primeiro as famílias, em rodadas: em cada uma, a família pede ao próximo
    fornecedor da sua lista (do mais barato ao mais caro) o que o orçamento
    restante compra, e a firma que não tem estoque para todos atende cada
    família na mesma proporção. Quem ainda tem orçamento depois dos seus
    fornecedores tenta, numa última rodada, uma firma que ainda tem estoque,
    sorteada com peso no estoque. Depois, as compras institucionais (governo e
    investimento das firmas) se dividem entre as firmas que ainda têm
    estoque, com peso no tamanho e no preço. As famílias vêm primeiro para que
    a falta de bens não vire poupança forçada que financia o investimento.

    Cada firma percebe a demanda pelas vendas mais a demanda que ficou sem
    atender no fim das rodadas, atribuída à primeira firma que racionou cada
    família: somadas, dão o excesso de demanda da economia, sem contar duas
    vezes quem foi racionado numa firma e comprou em outra.
    """
    N, m = fornecedores.shape   # pedidos das famílias em quantidade própria; firmas, por família
    n_firmas = p.size
    ordenados = np.take_along_axis(fornecedores, np.argsort(p[fornecedores], axis=1), axis=1)
    estoque = estoque.copy()
    resto = orcamento.copy()
    quantidade = np.zeros(N)
    vendas = np.zeros(n_firmas)
    racionou = np.full(N, -1)
    for rodada in range(m + (rng is not None)):
        if rodada < m:
            firma = ordenados[:, rodada]
        elif estoque.sum() > 0:
            firma = _sortear_com_peso(np.maximum(estoque, 0.0), N, rng)
        else:
            break
        pedido = resto / p[firma]
        demanda = np.bincount(firma, pedido, n_firmas) / N
        fracao = np.minimum(np.divide(estoque, demanda, out=np.ones(n_firmas), where=demanda > 0), 1.0)
        levado = pedido * fracao[firma]
        vendido = demanda * fracao
        vendas += vendido
        estoque -= vendido
        quantidade += levado
        resto -= levado * p[firma]
        faltou = (fracao[firma] < 1 - 1e-12) & (pedido > 0) & (racionou < 0)
        racionou[faltou] = firma[faltou]
    resto_inst, gasto_inst, quantidade_inst = pedido_institucional, 0.0, 0.0
    for _ in range(rodadas_institucionais):
        peso = np.where(estoque > 1e-15, peso_institucional, 0.0)
        if resto_inst <= 1e-15 or peso.sum() <= 0:
            break
        pedido_inst = resto_inst * peso / peso.sum() / p
        fracao = np.minimum(np.divide(estoque, pedido_inst, out=np.ones(n_firmas),
                                      where=pedido_inst > 0), 1.0)
        vendido = pedido_inst * fracao
        vendas += vendido
        estoque -= vendido
        gasto_rodada = float(vendido @ p)
        gasto_inst += gasto_rodada
        quantidade_inst += float(vendido.sum())
        resto_inst -= gasto_rodada
    # A demanda que ninguém atendeu fica com a firma que primeiro racionou cada
    # família (e, a das compras institucionais, com as firmas pelo peso).
    faltou = racionou >= 0
    nao_atendida = np.bincount(racionou[faltou], resto[faltou] / p[racionou[faltou]], n_firmas) / N
    if resto_inst > 1e-15:
        nao_atendida += resto_inst * peso_institucional / peso_institucional.sum() / p
    return orcamento - resto, quantidade, vendas, gasto_inst, quantidade_inst, racionou, vendas + nao_atendida


def _atualizar_fornecedores(fornecedores, racionou, p, tamanho, comp: Comportamento, rng):
    fornecedores = fornecedores.copy()
    N, m = fornecedores.shape
    # Quem foi racionado troca, com probabilidade, o fornecedor que faltou.
    troca = np.flatnonzero((racionou >= 0) & (rng.random(N) < comp.troca_racionado))
    nova = _sortear_com_peso(tamanho, troca.size, rng)
    coluna = np.argmax(fornecedores[troca] == racionou[troca, None], axis=1)
    livre = ~np.any(fornecedores[troca] == nova[:, None], axis=1)
    fornecedores[troca[livre], coluna[livre]] = nova[livre]
    # Quem procura conhece uma firma qualquer e troca o fornecedor mais caro, se
    # ela for mais barata.
    procura = np.flatnonzero(rng.random(N) < comp.procura_fornecedor)
    nova = rng.integers(p.size, size=procura.size)
    coluna = np.argmax(p[fornecedores[procura]], axis=1)
    mais_cara = fornecedores[procura, coluna]
    melhor = (p[nova] < p[mais_cara]) & ~np.any(fornecedores[procura] == nova[:, None], axis=1)
    fornecedores[procura[melhor], coluna[melhor]] = nova[melhor]
    return fornecedores


# --- o trimestre ------------------------------------------------------------------

def _mercado_de_trabalho(eco: Economia, e: Estado, eficiencia: np.ndarray, separacao: float, rng):
    """Separações, demissões e busca de um trimestre, com a probabilidade de separação dada."""
    comp, fluxos = eco.comp, eco.fluxos
    N, n_firmas = e.N, e.k.size
    # Separações.
    empregador, curta = e.empregador.copy(), e.curta.copy()
    procura = empregador < 0
    sai = (empregador >= 0) & (rng.random(N) < separacao)
    empregador[sai] = -1
    curta[sai] = rng.random(int(sai.sum())) < fluxos.q_curto
    # Demissões e vagas, pelo quadro que cada firma quer.
    l = np.bincount(empregador[empregador >= 0], eficiencia[empregador >= 0], n_firmas)
    excesso = l > e.quadro_alvo * (1 + comp.folga_demissao)
    reducao = np.where(excesso, np.minimum(l - e.quadro_alvo, comp.demissao_maxima * l), 0.0)
    demitidos = _demitir(empregador, eficiencia, reducao, rng)
    empregador[demitidos] = -1
    curta[demitidos] = rng.random(demitidos.size) < fluxos.q_curto
    l = np.bincount(empregador[empregador >= 0], eficiencia[empregador >= 0], n_firmas)
    vagas = np.maximum(e.quadro_alvo - l, 0.0)
    # Busca.
    contratados, sobra = _buscar(empregador, curta, eficiencia, vagas, e.w, eco, rng, procura)
    return empregador, curta, sai, demitidos, vagas, sobra, contratados


def _separacao_para(eco: Economia, e: Estado, eficiencia: np.ndarray, alvo: float, rng,
                    iteracoes: int = 30) -> float:
    """
    Probabilidade de separação que leva o desemprego do fim do trimestre ao
    alvo, por bissecção, com os mesmos números aleatórios em cada tentativa.
    Se o alvo estiver fora do alcance, fica no extremo mais próximo.
    """
    inicio = rng.bit_generator.state

    def desemprego(p):
        rng.bit_generator.state = inicio
        return float(np.mean(_mercado_de_trabalho(eco, e, eficiencia, p, rng)[0] < 0))

    baixo, alto = 0.0, 0.5
    try:
        if desemprego(baixo) >= alvo:
            return baixo
        if desemprego(alto) <= alvo:
            return alto
        for _ in range(iteracoes):
            meio = (baixo + alto) / 2
            baixo, alto = (meio, alto) if desemprego(meio) < alvo else (baixo, meio)
        return (baixo + alto) / 2
    finally:
        rng.bit_generator.state = inicio


def trimestre(eco: Economia, e: Estado, rng, log_gamma: float | None = None, gasto: float | None = None,
              crescimento_pib: float | None = None, crescimento_gasto: float | None = None,
              separacao: float | None = None, desemprego_alvo: float | None = None) -> tuple[Estado, dict]:
    """
    Um trimestre. O crescimento da produtividade é log_gamma ou, com
    `crescimento_pib` (Delta log do PIB a reproduzir), o que faz o produto do
    ABM crescer isso. O gasto do governo é `gasto` (taxa anual por unidade
    de eficiência) ou cresce `crescimento_gasto` (Delta log). A probabilidade
    de separação é a da PNAD, `separacao` ou a que leva o desemprego ao fim
    do trimestre a `desemprego_alvo`.
    """
    cal, comp, fluxos = eco.cal, eco.comp, eco.fluxos
    par, renda = cal.par, cal.renda
    D, alpha, N, n_firmas = par.periodo, par.alpha, e.N, e.k.size

    # 1. Produtividade das firmas.
    rho = comp.persistencia_produtividade
    log_phi = (eco.media_log_phi + rho * (e.log_phi - eco.media_log_phi)
               + comp.dispersao_produtividade * np.sqrt(1 - rho**2) * rng.standard_normal(n_firmas))
    phi = np.exp(log_phi)

    # 2. Separações, demissões e busca.
    eficiencia = eco.eficiencia[e.tipo] / N
    if desemprego_alvo is not None:
        separacao = _separacao_para(eco, e, eficiencia, desemprego_alvo, rng)
    separacao = fluxos.separacao if separacao is None else separacao
    empregador, curta, sai, demitidos, vagas_abertas, vagas, contratados = _mercado_de_trabalho(
        eco, e, eficiencia, separacao, rng)
    empregado = empregador >= 0
    l = np.bincount(empregador[empregado], eficiencia[empregado], n_firmas)

    # 3. Crescimento: capital, riqueza e estoques em unidades de eficiência do
    # novo trimestre. O produto é fator^alpha vezes o produto com o capital
    # antigo, o que dá o log_gamma que reproduz o crescimento do PIB.
    if crescimento_pib is not None:
        antigo = float(e.p @ (phi * e.k**alpha * l ** (1 - alpha)))
        log_gamma = (crescimento_pib - np.log(antigo) + np.log(e.pib)) / (1 - alpha) - par.n * D
    fator = np.exp(-log_gamma - par.n * D)
    a, k, x = e.s * fator, e.k * fator, e.x * fator * (1 - comp.depreciacao_estoque)
    esperadas, governo = e.vendas_esperadas * fator, e.governo * fator
    governo_reforma = e.governo_reforma * fator
    if gasto is None:
        gasto = e.G * np.exp(crescimento_gasto) * fator

    # 4. Produção, com todo o quadro (o estoque já perdeu a depreciação).
    y = phi * k**alpha * l ** (1 - alpha)
    estoque = x + D * y

    # 5. Rendas e governo.
    W = float(e.w @ l)
    L = float(l.sum())
    w_medio = W / L if L > 0 else float(np.mean(e.w))
    situacao = np.where(empregado, EMPREGADO, np.where(curta, CURTA, LONGA))
    j = e.tipo * 3 + situacao
    z = renda.z[j]
    bruta = np.where(empregado, e.w[np.maximum(empregador, 0)] * z, w_medio * z)
    B = float(np.mean(np.where(empregado, 0.0, w_medio * z)))
    # A receita que vem do aumento da alíquota (numa reforma) volta com os pesos
    # da reforma; o resto do orçamento, igual para todos.
    T_reforma = governo_reforma / D
    T = par.tau_w * (W + B) - B - gasto + governo / D
    pesos = cal.pesos[j]
    renda_disponivel = (1 - par.tau_w) * bruta + (T - T_reforma) + T_reforma * pesos / pesos.mean()
    m = a + D * renda_disponivel

    # 6. Crenças, consumo e investimento desejados.
    r_e, w_e = e.crencas.atualizar(e.r, w_medio, rng)
    consumo = np.clip(cal.tabela.consumo(m, j, r_e, w_e), 1e-9, m / D)
    # Custo do capital: o retorno que os donos do fundo esperam, antes do imposto.
    R_exigido = max(float(np.mean(r_e)) / (1 - par.tau_k), 0.005) + par.delta
    k_alvo = e.quadro_alvo * alpha * e.w / ((1 - alpha) * R_exigido)   # proporção de custo mínimo
    # Reposição da depreciação e do crescimento de tendência, mais uma fração
    # da distância até o alvo: no crescimento balanceado, k = k_alvo qualquer
    # que seja a velocidade do ajuste.
    reposicao = par.delta * D + np.exp((par.g + par.n) * D) - 1
    investimento = np.maximum(reposicao * k + comp.ajuste_capital * (k_alvo - k), 0.0)

    # 7. Mercado de bens.
    pedido_governo = D * gasto
    pedido_inst = pedido_governo + investimento.sum()
    peso_inst = esperadas * e.p ** -comp.elasticidade_institucional
    gasto_familias, quantidade, vendas, gasto_inst, quantidade_inst, racionou, pedidos = _mercado_de_bens(
        D * consumo, e.fornecedores, e.p, estoque, pedido_inst, peso_inst, rng)
    atendido = gasto_inst / pedido_inst if pedido_inst > 0 else 0.0
    preco_inst = gasto_inst / quantidade_inst if quantidade_inst > 0 else 1.0
    gasto_governo = atendido * pedido_governo
    novo_capital = atendido * investimento / preco_inst

    # 8. Firmas: estoques, expectativas, capital, preços e salários.
    x_novo = estoque - vendas
    esperadas_novas = esperadas + comp.ajuste_vendas * (pedidos - esperadas)
    k_novo = (1 - par.delta * D) * k + novo_capital
    custo = custo_unitario(phi, e.w, R_exigido, alpha)
    # Estoque baixo: a firma quer mais trabalho e sobe a margem; estoque alto:
    # quer menos e baixa a margem.
    sinal = np.where(x_novo < comp.estoque_baixo * esperadas_novas, 1.0,
                     np.where(x_novo > comp.estoque_alto * esperadas_novas, -1.0, 0.0))
    margem = np.clip(e.margem + sinal * comp.passo_margem * rng.random(n_firmas),
                     comp.margem_minima, comp.margem_maxima)
    minimo = comp.quadro_minimo * eficiencia.sum() / n_firmas
    quadro_alvo = e.quadro_alvo * (1 + sinal * comp.passo_quadro * rng.random(n_firmas))
    quadro_alvo = np.clip(quadro_alvo, minimo, np.maximum(l, minimo) * (1 + comp.passo_quadro))
    revisa = rng.random(n_firmas) < comp.revisao_preco
    p = np.where(revisa, custo * (1 + margem), e.p)
    # O salário revisto parte do salário médio do mercado: quem sobe passa a
    # pagar pelo menos a média, e quem corta, no máximo a média. Sem essa
    # âncora, o salário de cada firma seria um passeio aleatório, e a
    # dispersão entre firmas cresceria por séculos.
    dificil = vagas > comp.vagas_dificeis * vagas_abertas + 1e-15
    sem_vaga = np.where(dificil, 0, e.sem_vaga + 1)
    w = np.where(dificil, np.maximum(e.w, w_medio) * (1 + comp.passo_salario * rng.random(n_firmas)),
                 e.w)
    corta = sem_vaga >= comp.paciencia_salario
    w = np.where(corta, np.minimum(w, w_medio) * (1 - comp.passo_salario * rng.random(n_firmas)), w)
    sem_vaga = np.where(corta, 0, sem_vaga)
    indice = float(p @ vendas / vendas.sum()) if vendas.sum() > 0 else float(np.mean(p))
    p, w = p / indice, w / indice

    # 9. Fundo: o lucro é o que sobra do valor dos ativos depois das dívidas
    # com as famílias e com o governo; a parte líquida vai para as famílias.
    ativos = float(k_novo.sum() + p @ x_novo)
    poupanca = m - gasto_familias
    governo_antes = pedido_governo - gasto_governo
    lucro = ativos - float(poupanca.mean()) - governo_antes
    imposto = par.tau_k * lucro
    base = par.tau_k if eco.tau_k_base is None else eco.tau_k_base
    imposto_reforma = (par.tau_k - base) * lucro
    liquido = (1 - par.tau_k) * lucro
    s_novo = poupanca * (1 + liquido / poupanca.mean())
    r = liquido / (poupanca.mean() * D)

    fornecedores = _atualizar_fornecedores(e.fornecedores, racionou, p, esperadas_novas, comp, rng)
    duracao = np.where(empregado, 0, e.duracao + 1)
    procurando = duracao[~empregado]
    c = quantidade / D
    log_X = e.log_X + log_gamma + par.n * D
    Y = float(e.p @ y)
    C, I_ = float(gasto_familias.mean()) / D, float(gasto_inst - gasto_governo) / D
    registro = {
        "y": Y, "C": C, "I": I_, "G": gasto_governo / D, "dX": Y - C - I_ - gasto_governo / D,
        "K": float(k.sum()), "L": L, "desemprego": float(np.mean(~empregado)),
        "w": w_medio, "salarios": W, "r": r, "R_exigido": R_exigido, "r_e": float(np.mean(r_e)),
        "w_e": float(np.mean(w_e)), "transferencia": T, "beneficio": B,
        "participacao_trabalho": W / Y if Y > 0 else np.nan,
        "vagas": float(vagas_abertas.sum()), "vagas_nao_preenchidas": float(vagas.sum()),
        "contratacoes": contratados / N, "separacoes": int(sai.sum()) / N, "demissoes": demitidos.size / N,
        "racionadas": float(np.mean(racionou >= 0)),   # faltou produto em algum fornecedor
        "sem_comprar_tudo": float(np.mean(gasto_familias < D * consumo * (1 - 1e-9))),
        "margem": float(np.average(e.p / custo - 1, weights=vendas)) if vendas.sum() > 0 else np.nan,
        "margem_alvo": float(np.average(margem, weights=vendas)) if vendas.sum() > 0 else np.nan,
        "dispersao_precos": float(np.std(np.log(e.p))), "dispersao_salarios": float(np.std(np.log(e.w))),
        "estoques": float(p @ x_novo), "investimento_atendido": atendido,
        "procura_ate_1_ano": float(np.mean(procurando <= 4)) if procurando.size else np.nan,
        "procura_1_a_2_anos": float(np.mean((procurando > 4) & (procurando <= 8))) if procurando.size else np.nan,
        "procura_2_anos_ou_mais": float(np.mean(procurando > 8)) if procurando.size else np.nan,
        "quadro_alvo": float(quadro_alvo.sum()),
        "probabilidade_separacao": separacao, "log_gamma": log_gamma, "G_pedido": gasto,
        "log_X": log_X,
    }
    novo = Estado(s=s_novo, tipo=e.tipo, curta=curta, empregador=empregador, duracao=duracao,
                  fornecedores=fornecedores,
                  crencas=e.crencas, log_phi=log_phi, k=k_novo, x=x_novo, p=p, w=w, margem=margem,
                  quadro_alvo=quadro_alvo,
                  vendas_esperadas=esperadas_novas, sem_vaga=sem_vaga, r=r,
                  governo=governo_antes + imposto, governo_reforma=imposto_reforma, log_X=log_X, c=c,
                  pib=Y, G=gasto)
    return novo, registro


def simular(eco: Economia, estado: Estado, rng, trimestres: int, gasto: float | None = None):
    """Trimestres sem choques agregados, com crescimento de tendência."""
    par = eco.cal.par
    gasto = par.gasto if gasto is None else gasto
    linhas = []
    for _ in range(trimestres):
        estado, registro = trimestre(eco, estado, rng, par.g * par.periodo, gasto)
        linhas.append(registro)
    return estado, pd.DataFrame(linhas)
