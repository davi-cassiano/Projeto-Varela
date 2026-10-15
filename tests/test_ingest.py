"""Testes da ingestão. Usam uma fonte em memória: se a abstração DataSource
funciona, nenhum teste precisa de arquivo em disco."""

import pandas as pd
import pytest

from src.ingest import (DadosInvalidos, MemorySource, carregar_agencias,
                        carregar_precos, limpar_texto)


def agencia(instituicao, cod=1, **extra):
    base = dict(nome_instituicao=instituicao, cod_compe_ag=cod, nome_agencia="CENTRO",
                endereco="RUA A, 1", bairro="CENTRO", cep="01000-000", municipio="SAO PAULO",
                uf="SP", municipio_ibge=3550308, latitude=-23.55, longitude=-46.63)
    base.update(extra)
    return base


def test_fonte_em_memoria_substitui_o_excel():
    """Inversão de Dependência: a carga funciona com qualquer DataSource."""
    fonte = MemorySource(pd.DataFrame([agencia("ITAÚ UNIBANCO S.A.")]))
    assert len(carregar_agencias(fonte)) == 1


def test_filtro_por_nome_exato_exclui_corretoras():
    """O filtro antigo por trecho de texto ("ITA") capturava "TRINUS CAPITAL"."""
    fonte = MemorySource(pd.DataFrame([
        agencia("ITAÚ UNIBANCO S.A.", 1),
        agencia("TRINUS CAPITAL DISTRIBUIDORA DE TÍTULOS E VALORES MOBILIÁRIOS S.A.", 2),
        agencia("BANCO ITAUCARD S.A.", 3),
    ]))
    assert carregar_agencias(fonte)["cod_compe_ag"].tolist() == [1]


def test_coluna_ausente_e_rejeitada():
    df = pd.DataFrame([agencia("ITAÚ UNIBANCO S.A.")]).drop(columns=["latitude"])
    with pytest.raises(DadosInvalidos):
        carregar_agencias(MemorySource(df))


def test_espacos_do_cadastro_sao_removidos():
    df = limpar_texto(pd.DataFrame({"municipio": ["  SAO PAULO   "], "n": [1]}))
    assert df.loc[0, "municipio"] == "SAO PAULO"


def test_preco_fora_de_escala_e_descartado():
    """A exploração encontrou preços com erro de escala na base da ANP."""
    df = pd.DataFrame({
        "DATA FINAL": ["2020-01-04"] * 3, "ESTADO": ["SAO PAULO"] * 3,
        "PRODUTO": ["GASOLINA COMUM"] * 3, "PREÇO MÉDIO REVENDA": [4.5, 15730000000000.0, 0.0],
    })
    assert carregar_precos(MemorySource(df))["preco"].tolist() == [4.5]
