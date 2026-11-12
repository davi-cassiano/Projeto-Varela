"""Teste de fumaça do pipeline (Aula 9): o fluxo completo — ingestão,
preparação, treino e serving — roda numa amostra pequena e fixa, sem
nenhum arquivo real, e produz um pacote coerente. Também cobre a
reprodutibilidade: duas execuções dão o mesmo resultado."""

import json
import os

import pandas as pd
import pytest

from src import pipeline
from src.ingest import MemorySource

# ---------------------------------------------------------------------
# Amostra fixa: 10 agências em duas cidades, 2 estados de preço, 1 aeroporto
# ---------------------------------------------------------------------

AGENCIAS = pd.DataFrame([
    dict(nome_instituicao="ITAÚ UNIBANCO S.A.", cod_compe_ag=i, nome_agencia=f"AG {i}",
         endereco="RUA X", bairro=b, cep="01001-000", municipio=m, uf=uf,
         municipio_ibge=ibge, latitude=lat, longitude=lon)
    for i, (b, m, uf, ibge, lat, lon) in enumerate([
        ("CENTRO", "SAO PAULO", "SP", 3550308, -23.55, -46.63),
        ("VILA OLIMPIA", "SAO PAULO", "SP", 3550308, -23.55, -46.63),
        ("MIRANDOPOLIS", "SAO PAULO", "SP", 3550308, -23.55, -46.63),   # bairro a 530 km: cai
        ("PINHEIROS", "SAO PAULO", "SP", 3550308, -23.55, -46.63),
        ("MOEMA", "SAO PAULO", "SP", 3550308, -23.55, -46.63),
        ("CENTRO", "RIO DE JANEIRO", "RJ", 3304557, -22.91, -43.17),
        ("COPACABANA", "RIO DE JANEIRO", "RJ", 3304557, -22.91, -43.17),
        ("TIJUCA", "RIO DE JANEIRO", "RJ", 3304557, -22.91, -43.17),
        ("BOTAFOGO", "RIO DE JANEIRO", "RJ", 3304557, -22.91, -43.17),
        ("BARRA", "RIO DE JANEIRO", "RJ", 3304557, -22.91, -43.17),
    ], start=1)
] + [dict(nome_instituicao="OUTRO BANCO S.A.", cod_compe_ag=99, nome_agencia="FORA", endereco="",
          bairro="CENTRO", cep="00000-000", municipio="SAO PAULO", uf="SP", municipio_ibge=3550308,
          latitude=-23.55, longitude=-46.63)])

BAIRROS = pd.DataFrame([
    dict(uf="SP", municipio="São Paulo", bairro="Vila Olimpia", latitude=-23.594, longitude=-46.684),
    dict(uf="SP", municipio="São Paulo", bairro="Mirandopolis", latitude=-21.13, longitude=-51.10),
    dict(uf="SP", municipio="São Paulo", bairro="Pinheiros", latitude=-23.561, longitude=-46.702),
    dict(uf="RJ", municipio="Rio de Janeiro", bairro="Copacabana", latitude=-22.971, longitude=-43.182),
])

MUNICIPIOS = pd.DataFrame([
    dict(codigo_ibge=3550308, nome="São Paulo", latitude=-23.55, longitude=-46.63, capital=1, codigo_uf=35),
    dict(codigo_ibge=3304557, nome="Rio de Janeiro", latitude=-22.91, longitude=-43.17, capital=1, codigo_uf=33),
])

AEROPORTOS = pd.DataFrame([dict(IATA="GRU", **{"Nome do Aeroporto": "Guarulhos"}, Cidade="GUARULHOS",
                                UF="SP", Latitude=-23.43, Longitude=-46.47)])

GEOJSON = {"features": [
    {"properties": {"sigla": "SP", "name": "São Paulo"},
     "geometry": {"type": "Polygon", "coordinates": [[[-53, -25], [-44, -25], [-44, -20], [-53, -20], [-53, -25]]]}},
]}


def _precos():
    """Série semanal fixa, 2018 a meados de 2020, com o RJ sempre R$ 0,30 acima de SP."""
    datas = pd.date_range("2018-01-06", "2020-06-27", freq="7D")
    linhas = []
    for d in datas:
        base = 4.0 + 0.5 * ((d.year - 2018) + d.dayofyear / 366)
        linhas.append({"DATA FINAL": d, "ESTADO": "SAO PAULO", "PRODUTO": "GASOLINA COMUM", "PREÇO MÉDIO REVENDA": base})
        linhas.append({"DATA FINAL": d, "ESTADO": "RIO DE JANEIRO", "PRODUTO": "GASOLINA COMUM", "PREÇO MÉDIO REVENDA": base + 0.30})
        linhas.append({"DATA FINAL": d, "ESTADO": "SAO PAULO", "PRODUTO": "ETANOL", "PREÇO MÉDIO REVENDA": 3.0})
    return pd.DataFrame(linhas)


def _executar(tmp_path, monkeypatch, **kw):
    tmp_path.mkdir(exist_ok=True)
    monkeypatch.chdir(tmp_path)           # o pipeline grava em dados/saida relativo ao cwd
    return pipeline.executar(
        fonte_agencias=MemorySource(AGENCIAS), fonte_precos=MemorySource(_precos()),
        fonte_municipios=MemorySource(MUNICIPIOS), fonte_bairros=MemorySource(BAIRROS),
        fonte_aeroportos=MemorySource(AEROPORTOS), geojson_estados=GEOJSON,
        montar_html=False, **kw,
    )


@pytest.fixture
def execucao(tmp_path, monkeypatch):
    relatorio = _executar(tmp_path, monkeypatch, preco_nacional=6.0)
    with open(os.path.join("dados", "saida", "dados_prototipo.json"), encoding="utf-8") as f:
        pacote = json.load(f)
    return relatorio, pacote


def test_fumaca_roda_de_ponta_a_ponta(execucao):
    relatorio, pacote = execucao
    assert relatorio["agencias"] == 10                      # o outro banco ficou de fora
    assert relatorio["descartadas_por_desvio"] == 1         # Mirandópolis
    assert relatorio["regionais"] >= 1
    assert relatorio["modelo_escolhido"]
    assert len(pacote["agencias"]) == 10
    assert {a["uf"] for a in pacote["agencias"]} == {"SP", "RJ"}
    assert pacote["aeroportos"][0]["iata"] == "GRU"
    assert pacote["estados"][0]["uf"] == "SP"


def test_preco_por_estado_preserva_a_diferenca_aprendida(execucao):
    _, pacote = execucao
    por_uf = pacote["parametros"]["precoGasolinaPorUf"]
    assert por_uf["RJ"] - por_uf["SP"] == pytest.approx(0.30, abs=0.05)
    assert pacote["parametros"]["carro"]["precoGasolinaLitro"] == 6.0


def test_toda_agencia_tem_regional_e_coordenada(execucao):
    _, pacote = execucao
    for a in pacote["agencias"]:
        assert a["regional"] >= 0 and a["lat"] and a["lon"]
        assert a["precisao"] in ("bairro", "bairro_aprox", "municipio")


def test_execucao_e_reprodutivel(tmp_path, monkeypatch):
    """Mesma entrada e mesma semente: mesmo pacote. O carimbo de geração é
    removido antes de comparar, para o teste só quebrar por motivo certo
    (revisão do PR #28)."""
    def pacote_sem_carimbo(pasta):
        with open(pasta / "dados" / "saida" / "dados_prototipo.json", encoding="utf-8") as f:
            p = json.load(f)
        p.pop("geradoEm", None)
        return p

    _executar(tmp_path / "a", monkeypatch)
    _executar(tmp_path / "b", monkeypatch)
    assert pacote_sem_carimbo(tmp_path / "a") == pacote_sem_carimbo(tmp_path / "b")
