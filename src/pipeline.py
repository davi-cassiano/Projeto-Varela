"""
pipeline.py — Orquestração: liga ingestão, preparação, treino e serving.

É o único lugar que conhece as fontes concretas (Excel, TSV, CSV). Os
demais módulos recebem abstrações (`DataSource`, `EstimadorPreco`). Para
trocar a base de agências por uma API, muda-se uma linha aqui.

Uso, a partir da raiz do repositório:

    python -m src.pipeline                 # pipeline completo
    python -m src.pipeline --sem-download  # não tenta baixar bases auxiliares
"""

from __future__ import annotations

import argparse
import json
import os
import time

import pandas as pd

from . import features, ingest, serve, train

DADOS = "dados"
BRUTOS = os.path.join(DADOS, "brutos")
SAIDA = os.path.join(DADOS, "saida")
FONTE_PRODUTO = os.path.join("produto", "fonte")
PRODUTO = os.path.join("produto", "roteirizacao-visitas.html")


def executar(fonte_agencias: ingest.DataSource, fonte_precos: ingest.DataSource,
             fonte_municipios: ingest.DataSource, fonte_bairros: ingest.DataSource,
             fonte_aeroportos: ingest.DataSource, geojson_estados: dict,
             montar_html: bool = True) -> dict:
    inicio = time.time()
    relatorio: dict = {}

    # 1. Ingestão
    agencias = ingest.carregar_agencias(fonte_agencias)
    municipios = ingest.carregar_municipios(fonte_municipios)
    bairros = ingest.carregar_bairros(fonte_bairros)
    precos = ingest.carregar_precos(fonte_precos)
    aeroportos = ingest.carregar_aeroportos(fonte_aeroportos)
    relatorio["agencias"] = len(agencias)

    # 2. Preparação
    agencias = features.enriquecer_coordenadas(agencias, bairros)
    relatorio["descartadas_por_desvio"] = agencias.attrs["descartadas_por_desvio"]
    relatorio["precisao"] = agencias["precisao"].value_counts().to_dict()
    agencias = features.adicionar_nome_municipio(agencias, municipios)
    atributos = features.atributos_preco(precos)

    # 3. Treino
    agencias = train.treinar_regionais(agencias)
    agencias = features.simular_campos_planejamento(agencias)
    estimador, avaliacoes = train.treinar_modelo_preco(atributos)
    relatorio["regionais"] = int(agencias["regional_id"].nunique())
    relatorio["modelo_preco"] = [a.__dict__ for a in avaliacoes]
    relatorio["modelo_escolhido"] = estimador.nome

    # 4. Serving
    precos_uf = serve.precos_por_uf(estimador, atributos)
    pacote = serve.montar_pacote(
        agencias, aeroportos,
        features.simplificar_estados(geojson_estados),
        features.compactar_cidades(municipios),
        precos_uf, avaliacoes, features.DATA_REFERENCIA.isoformat(),
    )

    os.makedirs(SAIDA, exist_ok=True)
    caminho_pacote = os.path.join(SAIDA, "dados_prototipo.json")
    serve.gravar_pacote(pacote, caminho_pacote)
    agencias.to_csv(os.path.join(SAIDA, "agencias_com_regional.csv"), index=False)

    if montar_html:
        with open(caminho_pacote, encoding="utf-8") as f:
            relatorio["produto_bytes"] = serve.montar_produto(f.read(), FONTE_PRODUTO, PRODUTO)

    relatorio["segundos"] = round(time.time() - inicio, 1)
    with open(os.path.join(SAIDA, "relatorio_execucao.json"), "w", encoding="utf-8") as f:
        json.dump(relatorio, f, ensure_ascii=False, indent=2)
    return relatorio


def main() -> None:
    p = argparse.ArgumentParser(description="Pipeline de roteirização de visitas")
    p.add_argument("--sem-download", action="store_true", help="não baixar bases auxiliares")
    p.add_argument("--sem-html", action="store_true", help="não montar o HTML do produto")
    args = p.parse_args()

    if not args.sem_download:
        ingest.baixar_bases_auxiliares(DADOS)

    consolidada = os.path.join(BRUTOS, "base_consolidada_roteirizacao.xlsx")
    rel = executar(
        fonte_agencias=ingest.ExcelSource(consolidada, "Agencias_Geocodificadas"),
        fonte_precos=ingest.TsvSource(os.path.join(BRUTOS, "2004-2021.tsv")),
        fonte_municipios=ingest.CsvSource(os.path.join(DADOS, "municipios.csv")),
        fonte_bairros=ingest.CsvSource(os.path.join(DADOS, "bairros.csv"), sep=";", quotechar='"'),
        fonte_aeroportos=ingest.ExcelSource(consolidada, "Aeroportos"),
        geojson_estados=ingest.carregar_geojson(os.path.join(DADOS, "uf.geojson")),
        montar_html=not args.sem_html,
    )

    print(f"Agências: {rel['agencias']}  |  regionais: {rel['regionais']}")
    print(f"Precisão: {rel['precisao']}  |  descartadas por desvio: {rel['descartadas_por_desvio']}")
    print(f"Modelo de preço escolhido: {rel['modelo_escolhido']}")
    for a in rel["modelo_preco"]:
        print(f"   {a['nome']:45s} MAE R$ {a['mae']:.3f}/L   RMSE R$ {a['rmse']:.3f}/L")
    print(f"Concluído em {rel['segundos']} s")


if __name__ == "__main__":
    main()
