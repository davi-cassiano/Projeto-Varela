"""US12 · Sequência otimizada de visitas. Critério de aceite: em 20 seleções
de 5 a 15 agências, a distância total nunca é maior que a da varredura
geográfica e é menor em pelo menos 10% na média. As seleções saem do
recorte real de agências versionado em dados/colab/, com semente fixa."""

import os

import numpy as np
import pandas as pd
import pytest

from src.serve import distancia_circuito, sequenciar_visitas, varredura_angular

CSV = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "dados", "colab", "agencias_itau_geocodificadas.csv")


def _selecoes(n=20, semente=42):
    ag = pd.read_csv(CSV).drop_duplicates(["lat", "lon"])   # agências com a mesma coordenada não formam trecho
    rng = np.random.default_rng(semente)
    ufs = [u for u, g in ag.groupby("uf") if len(g) >= 15]
    for _ in range(n):
        g = ag[ag["uf"] == rng.choice(ufs)]
        amostra = g.sample(int(rng.integers(5, 16)), random_state=int(rng.integers(0, 10**6)))
        pontos = list(zip(amostra["lat"], amostra["lon"], strict=True))
        yield pontos[0], pontos[1:]


def test_criterio_de_aceite_us12():
    razoes = []
    for origem, pontos in _selecoes():
        base = distancia_circuito(origem, varredura_angular(origem, pontos))
        otima = distancia_circuito(origem, sequenciar_visitas(origem, pontos))
        assert otima <= base + 1e-6, "sequência otimizada pior que a varredura"
        razoes.append(otima / base)
    reducao_media = 1 - float(np.mean(razoes))
    assert reducao_media >= 0.10, f"redução média de {reducao_media:.1%}, abaixo de 10%"


def test_sequencia_visita_todas_as_agencias_uma_vez():
    origem, pontos = next(_selecoes())
    ordem = sequenciar_visitas(origem, pontos)
    assert sorted(ordem) == sorted(pontos)


@pytest.mark.parametrize("pontos", [[], [(-23.5, -46.6)]])
def test_casos_triviais(pontos):
    assert sequenciar_visitas((-23.55, -46.63), pontos) == pontos


def test_dois_opt_desfaz_cruzamento():
    """Quadrado visitado em ordem cruzada (X) vira o contorno."""
    origem = (0.0, 0.0)
    cruzado = [(0.0, 1.0), (1.0, 0.0), (1.0, 1.0)]       # 0,0 → 0,1 → 1,0 → 1,1 → 0,0 cruza
    assert distancia_circuito(origem, sequenciar_visitas(origem, cruzado)) < distancia_circuito(origem, cruzado)
