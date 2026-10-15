"""
features.py — Preparação: transformar dados em atributos.

Responsabilidade única (SRP): recebe tabelas já carregadas e validadas
pelo ingest.py e devolve tabelas transformadas. Não lê arquivo, não
treina e não serve.

Funções puras, sem estado: cada uma pode ser testada isoladamente com
uma tabela pequena montada no próprio teste.

Stories atendidas: US10 (escada de precisão das coordenadas),
US11 (atributos do modelo de preço).
"""

from __future__ import annotations

import difflib
import hashlib
import math
import re
import unicodedata
from datetime import date, timedelta

import pandas as pd

# ---------------------------------------------------------------------
# Texto
# ---------------------------------------------------------------------

# Cada abreviação só é expandida quando é uma palavra inteira (\b): "S. CECILIA"
# vira "SAO CECILIA", mas "SANTA CATARINA" fica intacto. Sem o \b, a regra do
# "S" transformava "SANTA CATARINA" em "SAO ANTA CATARINA".
ABREVIACOES = [
    (r"^S\b\.?\s*", "SAO "), (r"^STA\b\.?\s*", "SANTA "), (r"^STO\b\.?\s*", "SANTO "),
    (r"^V\b\.?\s*", "VILA "), (r"^JD\b\.?\s*", "JARDIM "), (r"^PQ\b\.?\s*", "PARQUE "),
    (r"^PQE\b\.?\s*", "PARQUE "), (r"^CH\b\.?\s*", "CHACARA "), (r"^CID\b\.?\s*", "CIDADE "),
    (r"^CJ\b\.?\s*", "CONJUNTO "), (r"^PR\b\.?\s*", "PRAIA "), (r"^B\b\.?\s*VISTA", "BOA VISTA"),
    (r"^N\b\.?\s*SRA\b\.?\s*", "NOSSA SENHORA "), (r"^PRES\b\.?\s*", "PRESIDENTE "),
    (r"^ENG\b\.?\s*", "ENGENHEIRO "), (r"^PROF\b\.?\s*", "PROFESSOR "),
    (r"^DR\b\.?\s*", "DOUTOR "), (r"^AL\b\.?\s*", "ALAMEDA "),
]


def sem_acento(texto) -> str:
    t = str(texto or "").strip().upper()
    return unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()


def normalizar(texto) -> str:
    """Maiúsculas, sem acento, com as abreviações do cadastro do Bacen expandidas."""
    t = str(texto or "").strip().upper()
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()
    t = re.sub(r"[^A-Z0-9\s\.]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    for padrao, troca in ABREVIACOES:
        t = re.sub(padrao, troca, t)
    return re.sub(r"\s+", " ", t.replace(".", " ")).strip()


# ---------------------------------------------------------------------
# Geografia
# ---------------------------------------------------------------------

RAIO_TERRA_KM = 6371.0


def distancia_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distância em linha reta (haversine)."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * RAIO_TERRA_KM * math.asin(math.sqrt(a))


DESVIO_MAX_KM = 30.0


def enriquecer_coordenadas(agencias: pd.DataFrame, bairros: pd.DataFrame,
                           desvio_max_km: float = DESVIO_MAX_KM) -> pd.DataFrame:
    """Escada de precisão da coordenada de cada agência (US10).

    bairro        cruzamento exato de município e bairro
    bairro_aprox  correspondência aproximada, para absorver abreviações
    municipio     centróide do município, cobertura garantida

    Validação de sanidade: a base pública de bairros tem colisão de nomes
    (o bairro Mirandópolis, em São Paulo, recebe as coordenadas da cidade
    de Mirandópolis, a 530 km). Coordenada de bairro a mais de
    `desvio_max_km` do centro do próprio município é descartada.
    """
    b = bairros.copy()
    b["mun_n"] = b["municipio"].map(normalizar)
    b["bai_n"] = b["bairro"].map(normalizar)
    b = b.drop_duplicates(subset=["uf", "mun_n", "bai_n"])

    indice = {(r.uf, r.mun_n, r.bai_n): (r.latitude, r.longitude) for r in b.itertuples()}
    por_municipio: dict = {}
    for r in b.itertuples():
        por_municipio.setdefault((r.uf, r.mun_n), []).append(r.bai_n)

    lats, lons, precisoes, descartadas = [], [], [], 0
    for a in agencias.itertuples():
        mun, bai = normalizar(a.municipio), normalizar(a.bairro)
        coord, precisao = indice.get((a.uf, mun, bai)), "bairro"

        if coord is None and bai and (a.uf, mun) in por_municipio:
            perto = difflib.get_close_matches(bai, por_municipio[(a.uf, mun)], n=1, cutoff=0.82)
            if perto:
                coord, precisao = indice.get((a.uf, mun, perto[0])), "bairro_aprox"

        if coord is not None and distancia_km(a.latitude, a.longitude, *coord) > desvio_max_km:
            coord, descartadas = None, descartadas + 1

        if coord is None:
            coord, precisao = (a.latitude, a.longitude), "municipio"

        lats.append(coord[0]); lons.append(coord[1]); precisoes.append(precisao)

    saida = agencias.copy()
    saida["lat"], saida["lon"], saida["precisao"] = lats, lons, precisoes
    saida.attrs["descartadas_por_desvio"] = descartadas
    return saida


def adicionar_nome_municipio(agencias: pd.DataFrame, municipios: pd.DataFrame) -> pd.DataFrame:
    """Grafia correta do município pelo código IBGE (o Bacen grava "SAO PAULO")."""
    nomes = municipios[["codigo_ibge", "nome"]].rename(columns={"nome": "municipio_nome"})
    saida = agencias.merge(nomes, left_on="municipio_ibge", right_on="codigo_ibge", how="left")
    saida["municipio_nome"] = saida["municipio_nome"].fillna(saida["municipio"].str.title())
    return saida.drop(columns=["codigo_ibge"])


# ---------------------------------------------------------------------
# Campos de planejamento simulados
# ---------------------------------------------------------------------

DATA_REFERENCIA = date(2026, 9, 10)


def _semente(chave: str) -> float:
    return int(hashlib.md5(chave.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF


def simular_campos_planejamento(agencias: pd.DataFrame, hoje: date = DATA_REFERENCIA) -> pd.DataFrame:
    """Prioridade, data limite e última visita.

    SIMULADOS: não existem em base pública. São derivados de um hash do
    código da agência, para serem estáveis entre execuções.
    """
    prioridades, limites, ultimas = [], [], []
    for i, a in enumerate(agencias.itertuples()):
        s = _semente(f"{a.regional_id}-{a.cod_compe_ag}-{i}")
        p = "alta" if s < 0.22 else ("media" if s < 0.68 else "baixa")
        janela = {"alta": 45, "media": 110, "baixa": 200}[p]
        prioridades.append(p)
        limites.append((hoje + timedelta(days=int(7 + s * janela))).isoformat())
        ultimas.append((hoje - timedelta(days=int(30 + s * 300))).isoformat())
    saida = agencias.copy()
    saida["prioridade"], saida["data_limite"], saida["ultima_visita"] = prioridades, limites, ultimas
    return saida


# ---------------------------------------------------------------------
# Atributos do modelo de preço de combustível (US11)
# ---------------------------------------------------------------------

UF_POR_ESTADO = {
    "ACRE": "AC", "ALAGOAS": "AL", "AMAPA": "AP", "AMAZONAS": "AM", "BAHIA": "BA",
    "CEARA": "CE", "DISTRITO FEDERAL": "DF", "ESPIRITO SANTO": "ES", "GOIAS": "GO",
    "MARANHAO": "MA", "MATO GROSSO": "MT", "MATO GROSSO DO SUL": "MS",
    "MINAS GERAIS": "MG", "PARA": "PA", "PARAIBA": "PB", "PARANA": "PR",
    "PERNAMBUCO": "PE", "PIAUI": "PI", "RIO DE JANEIRO": "RJ",
    "RIO GRANDE DO NORTE": "RN", "RIO GRANDE DO SUL": "RS", "RONDONIA": "RO",
    "RORAIMA": "RR", "SANTA CATARINA": "SC", "SAO PAULO": "SP", "SERGIPE": "SE",
    "TOCANTINS": "TO",
}


def atributos_preco(precos: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por semana e estado, com os atributos do modelo.

    alvo        preço médio de revenda no estado
    nacional    média dos estados na mesma semana
    spread      diferença do estado para a média nacional
    spread_52   spread médio do estado nas 52 semanas anteriores
                (só usa o passado, para não vazar informação do futuro)
    """
    df = precos.copy()
    df["uf"] = df["estado"].map(sem_acento).map(UF_POR_ESTADO)
    if df["uf"].isna().any():
        desconhecidos = sorted(df.loc[df["uf"].isna(), "estado"].unique())
        raise ValueError(f"estados sem sigla: {desconhecidos}")

    df["nacional"] = df.groupby("data")["preco"].transform("mean")
    df["spread"] = df["preco"] - df["nacional"]
    df = df.sort_values(["uf", "data"])
    df["spread_52"] = (
        df.groupby("uf")["spread"]
        .transform(lambda s: s.shift(1).rolling(52, min_periods=12).mean())
    )
    df["mes"] = df["data"].dt.month
    return df.dropna(subset=["spread_52"]).reset_index(drop=True)


# ---------------------------------------------------------------------
# Geometria para o mapa do produto
# ---------------------------------------------------------------------

UF_POR_CODIGO = {
    11: "RO", 12: "AC", 13: "AM", 14: "RR", 15: "PA", 16: "AP", 17: "TO",
    21: "MA", 22: "PI", 23: "CE", 24: "RN", 25: "PB", 26: "PE", 27: "AL",
    28: "SE", 29: "BA", 31: "MG", 32: "ES", 33: "RJ", 35: "SP", 41: "PR",
    42: "SC", 43: "RS", 50: "MS", 51: "MT", 52: "GO", 53: "DF",
}


def simplificar_estados(geojson: dict, tolerancia: float = 0.035) -> list[dict]:
    """Contorno dos estados reduzido de 3,4 MB para cerca de 60 KB, sem
    ilhas minúsculas, para caber embutido no HTML."""
    from shapely.geometry import shape
    from shapely.ops import unary_union

    saida = []
    for f in geojson["features"]:
        g = shape(f["geometry"])
        if g.geom_type == "MultiPolygon":
            partes = [p for p in g.geoms if p.area > 0.02] or [max(g.geoms, key=lambda p: p.area)]
            g = unary_union(partes)
        s = g.simplify(tolerancia, preserve_topology=True)
        geoms = s.geoms if s.geom_type == "MultiPolygon" else [s]
        c = g.representative_point()
        saida.append({
            "uf": f["properties"]["sigla"], "nome": f["properties"]["name"],
            "aneis": [[[round(x, 3), round(y, 3)] for x, y in p.exterior.coords] for p in geoms],
            "centro": [round(c.x, 3), round(c.y, 3)],
        })
    return saida


def compactar_cidades(municipios: pd.DataFrame) -> list[list]:
    """[nome, UF, latitude, longitude, capital], para rotular o mapa."""
    return [[r.nome, UF_POR_CODIGO.get(r.codigo_uf, ""), round(r.latitude, 3),
             round(r.longitude, 3), int(r.capital)] for r in municipios.itertuples()]
