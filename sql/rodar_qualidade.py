"""Carrega as tabelas em SQLite e executa cada bloco de sql/qualidade.sql.
Rodar a partir da raiz do repositório: python sql/rodar_qualidade.py"""

import os
import sqlite3
import sys

import pandas as pd

sys.path.insert(0, os.getcwd())
from src import features, ingest  # noqa: E402

BRUTOS = os.path.join("dados", "brutos")
consolidada = os.path.join(BRUTOS, "base_consolidada_roteirizacao.xlsx")

agencias = ingest.carregar_agencias(ingest.ExcelSource(consolidada, "Agencias_Geocodificadas"))
fonte_bairros = ingest.CsvSource(os.path.join("dados", "bairros.csv"), sep=";", quotechar='"')
bairros = ingest.carregar_bairros(fonte_bairros)
precos = ingest.carregar_precos(ingest.TsvSource(os.path.join(BRUTOS, "2004-2021.tsv")))
prep = features.enriquecer_coordenadas(agencias, bairros)

con = sqlite3.connect(":memory:")
agencias.astype({"cnpj": str}).to_sql("agencias", con, index=False)
prep[["cod_compe_ag", "precisao", "lat", "lon"]].to_sql("agencias_prep", con, index=False)
pd.DataFrame({"descartadas": [prep.attrs["descartadas_por_desvio"]]}).to_sql("resumo_prep", con, index=False)
precos.assign(data=precos["data"].dt.strftime("%Y-%m-%d")).to_sql("precos", con, index=False)
uf_ibge = pd.DataFrame(list(features.UF_POR_CODIGO.items()), columns=["codigo", "uf"])
uf_ibge.to_sql("uf_ibge", con, index=False)

with open(os.path.join("sql", "qualidade.sql"), encoding="utf-8") as f:
    blocos = [b.strip() for b in f.read().split(";") if "SELECT" in b.upper()]

falhas = 0
for bloco in blocos:
    comentarios = [l.strip("- ").strip() for l in bloco.splitlines() if l.strip().startswith("--")]
    titulo = next((c for c in comentarios if c[:1].isdigit()), comentarios[-1])
    linhas = pd.read_sql_query(bloco, con)
    situacao = "passou" if linhas.empty else f"FALHOU ({len(linhas)} linha(s))"
    falhas += not linhas.empty
    print(f"{titulo}\n   {situacao}")
    if not linhas.empty:
        print(linhas.head().to_string(index=False).replace("\n", "\n   "))
print(f"\n{len(blocos) - falhas} de {len(blocos)} consultas sem problema.")
sys.exit(1 if falhas else 0)
