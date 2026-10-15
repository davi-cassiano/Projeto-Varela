"""
ingest.py — Ingestão: carregar e validar os dados brutos.

Responsabilidade única (SRP): ler as fontes e garantir que chegaram no
formato esperado. Nada aqui transforma, agrega ou modela.

Inversão de Dependência (DIP): as funções de carga recebem uma
`DataSource`, uma abstração com um único método `load()`. Elas não sabem
se o dado veio de um Excel, de um TSV, de uma API ou de uma tabela em
memória nos testes. Trocar a fonte não mexe em nenhuma linha daqui, nem
no treino, nem no serving.

Stories atendidas: US10 (dados de localização), US11 (série de preços).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd


# ---------------------------------------------------------------------
# Abstração da fonte de dados (DIP)
# ---------------------------------------------------------------------

class DataSource(ABC):
    """Qualquer coisa que entregue uma tabela."""

    @abstractmethod
    def load(self) -> pd.DataFrame:
        ...


class ExcelSource(DataSource):
    def __init__(self, caminho: str, aba: str | int = 0, **opcoes):
        self.caminho, self.aba, self.opcoes = caminho, aba, opcoes

    def load(self) -> pd.DataFrame:
        return pd.read_excel(self.caminho, sheet_name=self.aba, **self.opcoes)


class CsvSource(DataSource):
    def __init__(self, caminho: str, **opcoes):
        self.caminho, self.opcoes = caminho, opcoes

    def load(self) -> pd.DataFrame:
        return pd.read_csv(self.caminho, **self.opcoes)


class TsvSource(CsvSource):
    def __init__(self, caminho: str, **opcoes):
        super().__init__(caminho, sep="\t", **opcoes)


class MemorySource(DataSource):
    """Fonte em memória. Usada nos testes, e prova que a abstração funciona."""

    def __init__(self, tabela: pd.DataFrame):
        self.tabela = tabela

    def load(self) -> pd.DataFrame:
        return self.tabela.copy()


# ---------------------------------------------------------------------
# Validação
# ---------------------------------------------------------------------

class DadosInvalidos(ValueError):
    pass


def exigir_colunas(df: pd.DataFrame, colunas: list[str], nome: str) -> None:
    faltando = [c for c in colunas if c not in df.columns]
    if faltando:
        raise DadosInvalidos(f"{nome}: colunas ausentes {faltando}")


def limpar_texto(df: pd.DataFrame) -> pd.DataFrame:
    """Remove espaços sobrando dos campos de texto.

    A base do Bacen vem com espaços em excesso em todos os campos de
    texto. No pandas 3 essas colunas têm dtype `str`, não `object`, então
    a checagem é feita pelo tipo dos valores, não pelo dtype.
    """
    df = df.copy()
    for c in df.columns:
        if df[c].map(lambda v: isinstance(v, str)).any():
            df[c] = df[c].map(lambda v: v.strip() if isinstance(v, str) else v)
    return df


# ---------------------------------------------------------------------
# Cargas
# ---------------------------------------------------------------------

INSTITUICAO_PADRAO = "ITAÚ UNIBANCO S.A."

COLUNAS_AGENCIAS = [
    "nome_instituicao", "cod_compe_ag", "nome_agencia", "endereco", "bairro",
    "cep", "municipio", "uf", "municipio_ibge", "latitude", "longitude",
]


def carregar_agencias(fonte: DataSource, instituicao: str = INSTITUICAO_PADRAO) -> pd.DataFrame:
    """Agências da instituição, com a coordenada de município da base consolidada.

    O filtro é por nome exato. Um filtro por trecho de texto ("ITA")
    capturava 30 registros que não são agências: corretoras e
    distribuidoras com "CAPITAL" no nome e sedes de outras empresas.
    """
    df = limpar_texto(fonte.load())
    exigir_colunas(df, COLUNAS_AGENCIAS, "agências")
    df = df[df["nome_instituicao"] == instituicao].reset_index(drop=True)
    if df.empty:
        raise DadosInvalidos(f"nenhuma agência para '{instituicao}'")
    if df[["latitude", "longitude"]].isna().any().any():
        raise DadosInvalidos("agências sem coordenada de município")
    return df


def carregar_municipios(fonte: DataSource) -> pd.DataFrame:
    df = fonte.load()
    exigir_colunas(df, ["codigo_ibge", "nome", "latitude", "longitude", "capital", "codigo_uf"], "municípios")
    return df


def carregar_bairros(fonte: DataSource) -> pd.DataFrame:
    df = fonte.load()
    exigir_colunas(df, ["uf", "municipio", "bairro", "latitude", "longitude"], "bairros")
    return df.dropna(subset=["latitude", "longitude"])


def carregar_precos(fonte: DataSource, produto: str = "GASOLINA COMUM") -> pd.DataFrame:
    """Série semanal da ANP, um produto, com colunas padronizadas."""
    df = fonte.load()
    df.columns = [str(c).strip() for c in df.columns]
    exigir_colunas(df, ["DATA FINAL", "ESTADO", "PRODUTO", "PREÇO MÉDIO REVENDA"], "preços ANP")

    df = df[df["PRODUTO"].str.strip() == produto]
    saida = pd.DataFrame({
        "data": pd.to_datetime(df["DATA FINAL"]),
        "estado": df["ESTADO"].str.strip(),
        "preco": pd.to_numeric(df["PREÇO MÉDIO REVENDA"], errors="coerce"),
    }).dropna()

    # A exploração inicial encontrou valores com erro de escala no preço
    # de revenda. Gasolina fora de R$ 0,50 a R$ 15,00 é tratada como erro.
    saida = saida[(saida["preco"] > 0.5) & (saida["preco"] < 15)]
    if saida.empty:
        raise DadosInvalidos(f"série de preços vazia para '{produto}'")
    return saida.sort_values(["data", "estado"]).reset_index(drop=True)


def carregar_aeroportos(fonte: DataSource) -> pd.DataFrame:
    df = fonte.load()
    exigir_colunas(df, ["IATA", "Nome do Aeroporto", "Cidade", "UF", "Latitude", "Longitude"], "aeroportos")
    return df


# ---------------------------------------------------------------------
# Bases auxiliares públicas (baixadas uma vez; depois tudo roda offline)
# ---------------------------------------------------------------------

FONTES_AUXILIARES = {
    "municipios.csv":
        "https://raw.githubusercontent.com/kelvins/municipios-brasileiros/main/csv/municipios.csv",
    "bairros.csv":
        "https://raw.githubusercontent.com/alanwillms/geoinfo/master/latitude-longitude-bairros.csv",
    "uf.geojson":
        "https://raw.githubusercontent.com/codeforgermany/click_that_hood/main/public/data/brazil-states.geojson",
}


def baixar_bases_auxiliares(destino: str = "dados") -> None:
    """Baixa o que falta. Só esta função usa internet no pipeline inteiro."""
    import os
    import requests

    os.makedirs(destino, exist_ok=True)
    for nome, url in FONTES_AUXILIARES.items():
        caminho = os.path.join(destino, nome)
        if os.path.exists(caminho):
            continue
        r = requests.get(url, timeout=120)
        r.raise_for_status()
        with open(caminho, "wb") as f:
            f.write(r.content)


def carregar_geojson(caminho: str) -> dict:
    import json
    with open(caminho, encoding="utf-8") as f:
        dados = json.load(f)
    if dados.get("type") != "FeatureCollection":
        raise DadosInvalidos(f"{caminho}: não é um GeoJSON FeatureCollection")
    return dados
