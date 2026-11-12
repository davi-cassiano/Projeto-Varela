"""Testes das regras de qualidade de dados (Aula 9). Cada regra tem um caso
que passa e um que falha, com tabelas pequenas e fixas."""

from datetime import date

import pandas as pd
import pytest

from src import validate


def _agencias(**troca):
    base = dict(cod_compe_ag=[1, 2, 3, 4], nome_agencia=["A", "B", "C", "D"],
                bairro=["CENTRO"] * 4, cep=["01001-000"] * 4, municipio=["SAO PAULO"] * 4,
                uf=["SP"] * 4, municipio_ibge=[3550308] * 4,
                latitude=[-23.55] * 4, longitude=[-46.63] * 4)
    base.update(troca)
    return pd.DataFrame(base)


def test_unicidade_passa_e_falha():
    assert validate.unicidade_agencias(_agencias()).passou
    r = validate.unicidade_agencias(_agencias(cod_compe_ag=[1, 1, 3, 4]))
    assert not r.passou and "2 repetidos" in r.medido


def test_completude_tolera_ate_um_por_cento():
    assert validate.completude_agencias(_agencias()).passou
    r = validate.completude_agencias(_agencias(bairro=["CENTRO", None, "CENTRO", "CENTRO"]))
    assert not r.passou and "bairro" in r.medido


@pytest.mark.parametrize("troca", [
    dict(uf=["SP", "XX", "SP", "SP"]),
    dict(cep=["01001-000", "1001", "01001-000", "01001-000"]),
    dict(latitude=[-23.55, 12.0, -23.55, -23.55]),      # fora do Brasil
    dict(longitude=[-46.63, -46.63, -20.0, -46.63]),
])
def test_validade_reprova_cada_campo_invalido(troca):
    assert validate.validade_agencias(_agencias()).passou
    r = validate.validade_agencias(_agencias(**troca))
    assert not r.passou and r.medido == "1 inválidos"


def test_consistencia_municipio_uf():
    assert validate.consistencia_municipio_uf(_agencias()).passou
    r = validate.consistencia_municipio_uf(_agencias(uf=["SP", "SP", "RJ", "SP"]))
    assert not r.passou and "RJ≠SP" in r.detalhe


def _prep(precisoes, descartadas):
    df = pd.DataFrame({"precisao": precisoes})
    df.attrs["descartadas_por_desvio"] = descartadas
    return df


def test_consistencia_de_coordenadas_usa_os_dois_limites():
    assert validate.consistencia_coordenadas(_prep(["bairro"] * 9 + ["municipio"], 0)).passou
    # descartes acima de 10%
    assert not validate.consistencia_coordenadas(_prep(["bairro"] * 8 + ["municipio"] * 2, 2)).passou
    # cobertura abaixo de 70%
    assert not validate.consistencia_coordenadas(_prep(["bairro"] * 6 + ["municipio"] * 4, 0)).passou


def _precos(ultima="2026-11-01", preco_extra=None, duplicar=False):
    datas = pd.date_range(end=ultima, periods=4, freq="7D")
    linhas = [dict(data=d, estado=e, preco=5.0) for d in datas for e in ("SAO PAULO", "ACRE")]
    if preco_extra is not None:
        linhas[0]["preco"] = preco_extra
    if duplicar:
        linhas.append(linhas[0])
    return pd.DataFrame(linhas)


def test_precos_atuais_passam():
    assert validate.integridade_precos(_precos(), hoje=date(2026, 11, 12)).passou


def test_precos_antigos_falham_na_pontualidade():
    r = validate.integridade_precos(_precos(ultima="2021-05-01"), hoje=date(2026, 11, 12))
    assert not r.passou and "01/05/2021" in r.medido


def test_precos_duplicados_ou_fora_da_faixa_falham():
    hoje = date(2026, 11, 12)
    assert not validate.integridade_precos(_precos(duplicar=True), hoje).passou
    assert not validate.integridade_precos(_precos(preco_extra=42.0), hoje).passou


def test_relatorio_lista_as_falhas():
    resultados = validate.validar(_agencias(), _prep(["bairro"] * 10, 0),
                                  _precos(ultima="2021-05-01"), hoje=date(2026, 11, 12))
    md = validate.relatorio_markdown(resultados, date(2026, 11, 12))
    assert "5 de 6 regras passaram" in md
    assert "Falhou — Série de preços" in md


def test_relatorio_e_gravado_em_json_e_markdown(tmp_path):
    resultados = validate.validar(_agencias(), _prep(["bairro"] * 10, 0), _precos(), hoje=date(2026, 11, 12))
    validate.gravar(resultados, str(tmp_path), date(2026, 11, 12))
    assert (tmp_path / "relatorio_qualidade.json").exists()
    assert "6 de 6 regras passaram" in (tmp_path / "relatorio_qualidade.md").read_text(encoding="utf-8")
