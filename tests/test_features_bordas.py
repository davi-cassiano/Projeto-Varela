"""Testes unitários das funções de features com casos de borda e
parametrização (Aula 9): zero, vazio, nulo e valores extremos."""

import pandas as pd
import pytest

from src.features import atributos_preco, distancia_km, enriquecer_coordenadas, normalizar, sem_acento

# ---------------------------------------------------------------------
# normalizar / sem_acento
# ---------------------------------------------------------------------

@pytest.mark.parametrize("entrada,esperado", [
    ("V.MARIA", "VILA MARIA"),
    ("JD.CAPRI", "JARDIM CAPRI"),
    ("B. VISTA", "BOA VISTA"),
    ("S.JOSE", "SAO JOSE"),
    ("STA.CECILIA", "SANTA CECILIA"),
    ("SANTA CATARINA", "SANTA CATARINA"),       # palavra inteira não é abreviação
    ("VILA OLIMPIA", "VILA OLIMPIA"),
    ("  centro   ", "CENTRO"),                  # espaços e minúsculas
    ("Jardim São João", "JARDIM SAO JOAO"),     # acentos
    ("BAIRRO-NOVO/II", "BAIRRO NOVO II"),       # pontuação vira espaço
    ("", ""),                                   # vazio
    (None, ""),                                 # nulo
    (123, "123"),                               # número
])
def test_normalizar(entrada, esperado):
    assert normalizar(entrada) == esperado


@pytest.mark.parametrize("entrada,esperado", [
    ("São Paulo", "SAO PAULO"), ("AMAPÁ", "AMAPA"), ("", ""), (None, ""), ("  x ", "X"),
])
def test_sem_acento(entrada, esperado):
    assert sem_acento(entrada) == esperado


# ---------------------------------------------------------------------
# distancia_km
# ---------------------------------------------------------------------

@pytest.mark.parametrize("a,b,esperado,tolerancia", [
    ((-23.55, -46.63), (-23.55, -46.63), 0.0, 1e-9),         # mesmo ponto
    ((-23.55, -46.63), (-22.91, -43.17), 357.0, 5.0),        # São Paulo → Rio
    ((0.0, 0.0), (0.0, 180.0), 20015.0, 5.0),                # meia volta no equador
    ((90.0, 0.0), (-90.0, 0.0), 20015.0, 5.0),               # polo a polo
    ((-23.55, -46.63), (-23.55, -46.62), 1.02, 0.05),        # ~1 km
])
def test_distancia_km(a, b, esperado, tolerancia):
    assert abs(distancia_km(*a, *b) - esperado) <= tolerancia


def test_distancia_e_simetrica():
    assert distancia_km(-23.55, -46.63, -22.91, -43.17) == pytest.approx(
        distancia_km(-22.91, -43.17, -23.55, -46.63))


# ---------------------------------------------------------------------
# enriquecer_coordenadas
# ---------------------------------------------------------------------

def _agencias(*bairros):
    return pd.DataFrame([dict(municipio="SAO PAULO", bairro=b, uf="SP",
                              latitude=-23.55, longitude=-46.63) for b in bairros])


BAIRROS_SP = pd.DataFrame([
    dict(uf="SP", municipio="São Paulo", bairro="Vila Olimpia", latitude=-23.594, longitude=-46.684),
    dict(uf="SP", municipio="São Paulo", bairro="Mirandopolis", latitude=-21.13, longitude=-51.10),
])


def test_tabela_vazia_de_agencias_nao_quebra():
    vazia = pd.DataFrame(columns=["municipio", "bairro", "uf", "latitude", "longitude"])
    r = enriquecer_coordenadas(vazia, BAIRROS_SP)
    assert r.empty and r.attrs["descartadas_por_desvio"] == 0


def test_bairro_nulo_cai_para_o_municipio():
    r = enriquecer_coordenadas(_agencias(None), BAIRROS_SP)
    assert r.loc[0, "precisao"] == "municipio"
    assert r.loc[0, "lat"] == -23.55


def test_grafia_aproximada_recebe_precisao_bairro_aprox():
    r = enriquecer_coordenadas(_agencias("VILA OLIMPA"), BAIRROS_SP)
    assert r.loc[0, "precisao"] == "bairro_aprox"
    assert r.loc[0, "lat"] == -23.594


@pytest.mark.parametrize("desvio_max,precisao_esperada", [
    (0.0, "municipio"),    # limite zero: nenhum bairro sobrevive
    (5.0, "municipio"),    # Vila Olímpia fica a ~7 km do centro: cai
    (10.0, "bairro"),      # com 10 km, fica
    (30.0, "bairro"),      # padrão do projeto
])
def test_limite_de_desvio_e_respeitado(desvio_max, precisao_esperada):
    r = enriquecer_coordenadas(_agencias("VILA OLIMPIA"), BAIRROS_SP, desvio_max_km=desvio_max)
    assert r.loc[0, "precisao"] == precisao_esperada
    assert r.attrs["descartadas_por_desvio"] == (1 if precisao_esperada == "municipio" else 0)


def test_contagem_de_descartes_soma_todas_as_agencias():
    r = enriquecer_coordenadas(_agencias("MIRANDOPOLIS", "MIRANDOPOLIS", "VILA OLIMPIA"), BAIRROS_SP)
    assert r.attrs["descartadas_por_desvio"] == 2
    assert list(r["precisao"]) == ["municipio", "municipio", "bairro"]


# ---------------------------------------------------------------------
# atributos_preco
# ---------------------------------------------------------------------

def _serie(semanas, estados=("SAO PAULO", "RIO DE JANEIRO")):
    datas = pd.date_range("2019-01-05", periods=semanas, freq="7D")
    return pd.DataFrame([dict(data=d, estado=e, preco=4.0 + 0.1 * i)
                         for d in datas for i, e in enumerate(estados)])


def test_estado_desconhecido_levanta_erro():
    with pytest.raises(ValueError, match="estados sem sigla"):
        atributos_preco(_serie(20, estados=("SAO PAULO", "NARNIA")))


@pytest.mark.parametrize("semanas,linhas_esperadas", [
    (5, 0),        # menos que as 12 semanas mínimas: nada sai
    (12, 0),       # a 12ª semana ainda só tem 11 anteriores
    (13, 2),       # a partir da 13ª, uma linha por estado
    (20, 16),      # (20 - 12) semanas × 2 estados
])
def test_minimo_de_historico_para_o_atributo(semanas, linhas_esperadas):
    assert len(atributos_preco(_serie(semanas))) == linhas_esperadas


def test_estado_com_acento_e_mapeado():
    a = atributos_preco(_serie(20, estados=("SÃO PAULO", "AMAPÁ")))
    assert set(a["uf"]) == {"SP", "AP"}


def test_spread_soma_zero_entre_os_estados_na_semana():
    a = atributos_preco(_serie(20))
    assert a.groupby("data")["spread"].sum().abs().max() < 1e-9
