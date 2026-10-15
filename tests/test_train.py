"""Testes do treino: regras de capacidade das regionais (k-means) e o
critério de aceite do modelo de preço (US11)."""

import os

import numpy as np
import pandas as pd
import pytest

from src.train import (BaselineNacional, RegressaoEstado, avaliar,
                       separar_no_tempo, treinar_regionais)



RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TSV_ANP = os.path.join(RAIZ, "dados", "brutos", "2004-2021.tsv")
CSV_ANP = os.path.join(RAIZ, "dados", "colab", "precos_gasolina_comum_anp.csv")


def _precos():
    """Série bruta da ANP se estiver baixada; senão, o recorte de gasolina
    comum versionado em dados/colab/ (o mesmo que o notebook usa)."""
    from src.ingest import TsvSource, carregar_precos

    if os.path.exists(TSV_ANP):
        return carregar_precos(TsvSource(TSV_ANP))
    return pd.read_csv(CSV_ANP, parse_dates=["data"])


def _agencias(pontos):
    return pd.DataFrame([dict(lat=la, lon=lo, cod_compe_ag=i, municipio_nome=f"Cidade {i % 7}",
                              bairro="CENTRO") for i, (la, lo) in enumerate(pontos)])


def test_nenhuma_regional_fura_teto_nem_piso():
    rng = np.random.default_rng(0)
    centros = [(-23.5, -46.6), (-22.9, -47.0), (-16.7, -49.3), (-3.1, -60.0)]
    pontos = [(c[0] + rng.normal(0, .3), c[1] + rng.normal(0, .3)) for c in centros for _ in range(55)]
    r = treinar_regionais(_agencias(pontos), teto=40, piso=4)
    tamanhos = r.groupby("regional_id").size()
    assert tamanhos.max() <= 40
    assert tamanhos.min() >= 4


def test_praca_densa_na_mesma_coordenada_e_fatiada():
    """Sem eixo geográfico para cortar, o grupo é dividido por código."""
    r = treinar_regionais(_agencias([(-23.55, -46.63)] * 95), teto=40, piso=4)
    assert r.groupby("regional_id").size().max() <= 40


def test_nomes_de_regionais_sao_unicos():
    rng = np.random.default_rng(1)
    pontos = [(-23.5 + rng.normal(0, .05), -46.6 + rng.normal(0, .05)) for _ in range(160)]
    r = treinar_regionais(_agencias(pontos))
    assert r.groupby("regional_id")["regional"].first().is_unique


@pytest.mark.skipif(not os.path.exists(TSV_ANP) and not os.path.exists(CSV_ANP),
                    reason="série de preços não disponível")
def test_criterio_de_aceite_us11():
    """US11: MAE de no máximo R$ 0,15/L no teste (2020-2021) e pelo menos
    25% abaixo do baseline, que usa o mesmo preço para todos os estados."""
    from src.features import atributos_preco

    atributos = atributos_preco(_precos())
    treino, teste = separar_no_tempo(atributos)
    modelo = avaliar(RegressaoEstado().ajustar(treino), teste)
    baseline = avaliar(BaselineNacional().ajustar(treino), teste)

    assert modelo.mae <= 0.15
    assert modelo.mae <= 0.75 * baseline.mae


def test_separacao_temporal_nao_mistura_periodos():
    a = pd.DataFrame({"data": pd.to_datetime(["2019-12-28", "2020-01-04", "2021-01-02"])})
    treino, teste = separar_no_tempo(a)
    assert treino["data"].max() < teste["data"].min()
