"""Testes da preparação. Ligados ao critério de aceite da US10."""

import pandas as pd

from src.features import atributos_preco, enriquecer_coordenadas, normalizar


def test_abreviacao_do_bacen_e_expandida():
    assert normalizar("V.MARIA") == "VILA MARIA"
    assert normalizar("JD.CAPRI") == "JARDIM CAPRI"
    assert normalizar("B. VISTA") == "BOA VISTA"


def test_palavra_comum_nao_e_tratada_como_abreviacao():
    """Defeito corrigido: "SANTA CATARINA" virava "SAO ANTA CATARINA"."""
    assert normalizar("SANTA CATARINA") == "SANTA CATARINA"
    assert normalizar("VILA OLIMPIA") == "VILA OLIMPIA"


def _agencia(bairro):
    return pd.DataFrame([dict(municipio="SAO PAULO", bairro=bairro, uf="SP",
                              latitude=-23.55, longitude=-46.63)])


def test_bairro_valido_recebe_coordenada_de_bairro():
    bairros = pd.DataFrame([dict(uf="SP", municipio="São Paulo", bairro="Vila Olimpia",
                                 latitude=-23.594, longitude=-46.684)])
    r = enriquecer_coordenadas(_agencia("VILA OLIMPIA"), bairros)
    assert r.loc[0, "precisao"] == "bairro"
    assert r.loc[0, "lat"] == -23.594


def test_bairro_a_530_km_e_descartado():
    """US10: o bairro Mirandópolis recebia as coordenadas da cidade de
    Mirandópolis, a 530 km. Coordenada a mais de 30 km do município cai."""
    bairros = pd.DataFrame([dict(uf="SP", municipio="São Paulo", bairro="Mirandopolis",
                                 latitude=-21.13, longitude=-51.10)])
    r = enriquecer_coordenadas(_agencia("MIRANDOPOLIS"), bairros)
    assert r.loc[0, "precisao"] == "municipio"
    assert (r.loc[0, "lat"], r.loc[0, "lon"]) == (-23.55, -46.63)
    assert r.attrs["descartadas_por_desvio"] == 1


def test_toda_agencia_termina_com_coordenada():
    """US10: 100% das agências recebem ao menos a coordenada do município."""
    r = enriquecer_coordenadas(_agencia("BAIRRO INEXISTENTE"), pd.DataFrame(
        columns=["uf", "municipio", "bairro", "latitude", "longitude"]))
    assert r[["lat", "lon"]].notna().all().all()


def test_atributo_do_modelo_usa_so_o_passado():
    """spread_52 de uma semana não pode conter a própria semana."""
    datas = pd.date_range("2019-01-05", periods=30, freq="7D")
    linhas = []
    for i, d in enumerate(datas):
        linhas.append(dict(data=d, estado="SAO PAULO", preco=4.0))
        linhas.append(dict(data=d, estado="ACRE", preco=4.0 + (1.0 if i == 29 else 0.0)))
    a = atributos_preco(pd.DataFrame(linhas))
    ultima_acre = a[(a["uf"] == "AC")].iloc[-1]
    assert ultima_acre["spread"] > 0          # a última semana tem salto
    assert abs(ultima_acre["spread_52"]) < 1e-9   # mas o atributo ainda não o vê
