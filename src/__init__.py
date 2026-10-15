"""Pipeline do Sistema de Roteirização de Visitas às Agências.

Arquitetura de referência em três estágios (Aula 5):

    ingest.py    ingestão: carrega e valida os dados brutos
    features.py  preparação: transforma dados em atributos
    train.py     treino: ajusta os modelos (k-means e preço de combustível)
    serve.py     serving: aplica os modelos e entrega o resultado ao produto

pipeline.py orquestra os quatro em sequência.
"""
