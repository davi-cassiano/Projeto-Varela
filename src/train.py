"""
train.py — Treino: ajustar os modelos.

Responsabilidade única (SRP): recebe atributos prontos do features.py e
devolve modelos ajustados e suas métricas. Não lê arquivo e não monta a
saída do produto.

Dois modelos:

1. K-means (não supervisionado) — forma as regionais agrupando as
   agências por latitude e longitude, com regras de capacidade por cima.
2. Regressão do preço da gasolina por estado (supervisionado, US11).

Open/Closed e Liskov: todo estimador de preço implementa a mesma
interface `EstimadorPreco`. Um modelo novo entra como uma classe nova,
sem mudar `avaliar()` nem o serve.py, e qualquer estimador substitui
outro sem quebrar quem o usa.

Stories atendidas: US10 e US11, e indiretamente US01 (recorte por regional).
"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.linear_model import Ridge

SEMENTE = 42


# =====================================================================
# 1. Regionais por k-means
# =====================================================================

TETO_AGENCIAS = 40   # acima disso a regional é subdividida
PISO_AGENCIAS = 4    # abaixo disso é absorvida pela vizinha


def _matriz_distancias(pontos: np.ndarray) -> np.ndarray:
    p = np.radians(pontos)
    la, lo = p[:, 0:1], p[:, 1:2]
    a = np.sin((la - la.T) / 2) ** 2 + np.cos(la) * np.cos(la.T) * np.sin((lo - lo.T) / 2) ** 2
    return 2 * 6371.0 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def _fatiar(ag: pd.DataFrame, idx, teto: int):
    """Último recurso: grupo acima do teto com todas as agências na mesma
    coordenada. Sem eixo geográfico para cortar, divide por código da
    agência — como um banco faz numa praça densa, repartindo por carteira."""
    ordenado = list(ag.loc[idx].sort_values("cod_compe_ag").index)
    n = int(math.ceil(len(ordenado) / teto))
    return [pd.Index(f) for f in np.array_split(ordenado, n)]


def _dividir(ag: pd.DataFrame, idx, teto: int):
    g = ag.loc[idx]
    if len(g) <= teto:
        return [idx]
    distintos = g[["lat", "lon"]].drop_duplicates().shape[0]
    if distintos < 2:
        return _fatiar(ag, idx, teto)

    k = min(int(math.ceil(len(g) / teto)), distintos)
    rotulos = KMeans(n_clusters=k, n_init=10, random_state=SEMENTE).fit_predict(g[["lat", "lon"]].values)

    saida = []
    for c in range(k):
        sub = g.index[rotulos == c]
        if len(sub) == len(g):
            return _fatiar(ag, idx, teto)
        saida += _dividir(ag, sub, teto)
    return saida


def _absorver_pequenas(ag: pd.DataFrame, grupos, piso: int, teto: int):
    grupos = [list(g) for g in grupos]
    while True:
        tam = [len(g) for g in grupos]
        pequenas = [i for i, n in enumerate(tam) if n < piso]
        if not pequenas:
            break
        centros = np.array([ag.loc[g, ["lat", "lon"]].mean().values for g in grupos])
        dist = _matriz_distancias(centros)
        np.fill_diagonal(dist, np.inf)

        i = min(pequenas, key=lambda x: tam[x])
        candidatas = [j for j in np.argsort(dist[i]) if j != i and tam[j] + tam[i] <= teto]
        if not candidatas:
            break  # manter separada é melhor que furar o teto
        j = int(candidatas[0])
        grupos[j] = grupos[j] + grupos[i]
        grupos.pop(i)
    return grupos


def _nomear(ag: pd.DataFrame, grupos) -> dict[int, str]:
    """Nome da regional = cidade com mais agências; desempata por segunda
    cidade ou bairro predominante quando o polo se repete."""
    nomes = {i: ag.loc[g, "municipio_nome"].value_counts().index[0] for i, g in enumerate(grupos)}

    por_polo: dict = {}
    for i, n in nomes.items():
        por_polo.setdefault(n, []).append(i)

    finais = dict(nomes)
    for polo, ids in por_polo.items():
        if len(ids) == 1:
            continue
        usados = set()
        for i in ids:
            g = ag.loc[grupos[i]]
            alternativas = list(g["municipio_nome"].value_counts().index[1:])
            alternativas += [str(b).title() for b in g["bairro"].value_counts().index[:5]]
            escolhido = next((a for a in alternativas if a and a != polo and a not in usados), None)
            if escolhido:
                usados.add(escolhido)
                finais[i] = f"{polo} / {escolhido}"

    contagem: dict = {}
    for i in sorted(finais):
        contagem[finais[i]] = contagem.get(finais[i], 0) + 1
        if contagem[finais[i]] > 1:
            finais[i] = f"{finais[i]} {contagem[finais[i]]}"
    return finais


def treinar_regionais(agencias: pd.DataFrame, teto: int = TETO_AGENCIAS,
                      piso: int = PISO_AGENCIAS) -> pd.DataFrame:
    """Atribui `regional_id` e `regional` a cada agência."""
    ag = agencias.reset_index(drop=True)
    grupos = _dividir(ag, ag.index, teto)
    grupos = _absorver_pequenas(ag, grupos, piso, teto)
    nomes = _nomear(ag, grupos)

    saida = ag.copy()
    saida["regional_id"] = -1
    for i, g in enumerate(grupos):
        saida.loc[g, "regional_id"] = i
    saida["regional"] = saida["regional_id"].map(nomes)
    return saida


def extensao_km(grupo: pd.DataFrame) -> float:
    pts = grupo[["lat", "lon"]].drop_duplicates().values
    return 0.0 if len(pts) < 2 else float(_matriz_distancias(pts).max())


# =====================================================================
# 2. Preço da gasolina por estado (US11)
# =====================================================================

class EstimadorPreco(ABC):
    """Interface comum: aprende com a série e prevê o preço de um estado
    dado o preço nacional. Interface pequena de propósito (ISP)."""

    nome = "estimador"

    @abstractmethod
    def ajustar(self, treino: pd.DataFrame) -> "EstimadorPreco":
        ...

    @abstractmethod
    def prever(self, tabela: pd.DataFrame) -> np.ndarray:
        """`tabela` tem ao menos as colunas uf, nacional, spread_52 e mes."""


class BaselineNacional(EstimadorPreco):
    """O que o produto fazia: o mesmo preço para todos os estados."""

    nome = "Baseline: preço nacional para todos"

    def ajustar(self, treino):
        return self

    def prever(self, tabela):
        return tabela["nacional"].to_numpy()


class EfeitoMedioEstado(EstimadorPreco):
    """Preço nacional + diferença média de cada estado no fim do treino."""

    nome = "Nacional + efeito médio do estado"

    def __init__(self, anos: int = 2):
        self.anos = anos

    def ajustar(self, treino):
        corte = treino["data"].max() - pd.DateOffset(years=self.anos)
        self.efeito_ = treino[treino["data"] > corte].groupby("uf")["spread"].mean()
        return self

    def prever(self, tabela):
        return (tabela["nacional"] + tabela["uf"].map(self.efeito_).fillna(0)).to_numpy()


class RegressaoEstado(EstimadorPreco):
    """Regressão linear regularizada (Ridge) da diferença do estado para a
    média nacional, a partir da diferença recente do próprio estado, do
    estado e do mês."""

    nome = "Regressão Ridge da diferença do estado"

    def __init__(self, alpha: float = 1.0):
        self.alpha = alpha

    def _matriz(self, tabela):
        x = pd.get_dummies(tabela[["uf"]].astype(str), prefix="uf")
        x = x.reindex(columns=getattr(self, "colunas_", x.columns), fill_value=0)
        x["spread_52"] = tabela["spread_52"].to_numpy()
        for m in range(2, 13):
            x[f"mes_{m}"] = (tabela["mes"].to_numpy() == m).astype(float)
        return x.astype(float)

    def ajustar(self, treino):
        self.colunas_ = pd.get_dummies(treino[["uf"]].astype(str), prefix="uf").columns
        self.modelo_ = Ridge(alpha=self.alpha).fit(self._matriz(treino), treino["spread"])
        return self

    def prever(self, tabela):
        return tabela["nacional"].to_numpy() + self.modelo_.predict(self._matriz(tabela))


# ---------------------------------------------------------------------

CORTE_TEMPORAL = "2020-01-01"


@dataclass
class Avaliacao:
    nome: str
    mae: float
    rmse: float


def separar_no_tempo(atributos: pd.DataFrame, corte: str = CORTE_TEMPORAL):
    """Treino antes do corte, teste depois. Nunca embaralhar: o modelo não
    pode ver semanas futuras no treino."""
    treino = atributos[atributos["data"] < corte]
    teste = atributos[atributos["data"] >= corte]
    return treino, teste


def avaliar(estimador: EstimadorPreco, teste: pd.DataFrame) -> Avaliacao:
    erro = teste["preco"].to_numpy() - estimador.prever(teste)
    return Avaliacao(estimador.nome, float(np.mean(np.abs(erro))), float(np.sqrt(np.mean(erro ** 2))))


def treinar_modelo_preco(atributos: pd.DataFrame, corte: str = CORTE_TEMPORAL):
    """Ajusta os candidatos, avalia no período de teste e escolhe o de menor MAE.

    Devolve o vencedor reajustado com toda a série, para servir, e a
    tabela de avaliações para o relatório.
    """
    treino, teste = separar_no_tempo(atributos, corte)
    candidatos = [BaselineNacional(), EfeitoMedioEstado(), RegressaoEstado()]
    avaliacoes = [avaliar(c.ajustar(treino), teste) for c in candidatos]

    melhor = min(range(len(candidatos)), key=lambda i: avaliacoes[i].mae)
    vencedor = type(candidatos[melhor])().ajustar(atributos)
    return vencedor, avaliacoes


def erro_por_mes(estimador: EstimadorPreco, teste: pd.DataFrame) -> pd.Series:
    """MAE mês a mês no teste, para enxergar drift: o erro cresce à medida
    que o teste se afasta do fim do treino?"""
    t = teste.copy()
    t["erro_abs"] = np.abs(t["preco"].to_numpy() - estimador.prever(t))
    return t.groupby(t["data"].dt.to_period("M"))["erro_abs"].mean()
