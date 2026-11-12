"""US14 · Preços atualizados automaticamente: leitura da publicação da ANP e
reavaliação do modelo com alerta (RNF06)."""

import pandas as pd
import pytest

from src.features import atributos_preco
from src.ingest import AnpSource, DadosInvalidos, carregar_precos
from src.monitor import LIMITE_ALERTA, avaliar_recente, preco_nacional_atual


def _planilha_anp(tmp_path, linhas_de_cabecalho=6):
    """Reproduz o layout da ANP: texto institucional, depois a tabela."""
    cab = [["AGÊNCIA NACIONAL DO PETRÓLEO"] + [None] * 7] * linhas_de_cabecalho
    titulos = ["DATA INICIAL", "DATA FINAL", "REGIÃO", "ESTADO", "PRODUTO",
               "NÚMERO DE POSTOS PESQUISADOS", "UNIDADE DE MEDIDA", "PREÇO MÉDIO REVENDA"]
    dados = [["2026-10-25", "2026-10-31", "SUDESTE", "SAO PAULO", "GASOLINA COMUM", 100, "R$/l", 6.1],
             ["2026-10-25", "2026-10-31", "NORTE", "ACRE", "GASOLINA COMUM", 10, "R$/l", 7.2],
             ["2026-10-25", "2026-10-31", "SUDESTE", "SAO PAULO", "ETANOL HIDRATADO", 100, "R$/l", 4.0]]
    caminho = tmp_path / "anp.xlsx"
    pd.DataFrame(cab + [titulos] + dados).to_excel(caminho, header=False, index=False)
    return str(caminho)


@pytest.mark.parametrize("linhas_de_cabecalho", [0, 6, 17])
def test_leitura_acha_a_tabela_sob_cabecalho_de_tamanho_variavel(tmp_path, linhas_de_cabecalho):
    df = AnpSource.ler_planilha(_planilha_anp(tmp_path, linhas_de_cabecalho))
    assert list(df.columns)[:2] == ["DATA INICIAL", "DATA FINAL"] and len(df) == 3


def test_planilha_sem_titulos_e_rejeitada(tmp_path):
    caminho = tmp_path / "x.xlsx"
    pd.DataFrame([["nada", "aqui"]]).to_excel(caminho, header=False, index=False)
    with pytest.raises(DadosInvalidos):
        AnpSource.ler_planilha(str(caminho))


def test_fonte_anp_entra_na_mesma_carga_que_o_arquivo_antigo(tmp_path):
    """DIP: carregar_precos não sabe se veio do TSV de 2004-2021 ou da ANP."""
    fonte = AnpSource(cache=_planilha_anp(tmp_path), atualizar=False)
    precos = carregar_precos(fonte)
    assert list(precos.columns) == ["data", "estado", "preco"]
    assert len(precos) == 2                      # etanol ficou de fora
    assert preco_nacional_atual(precos) == pytest.approx(6.65)


def _serie(semanas=80, choque_final=0.0):
    datas = pd.date_range("2025-01-04", periods=semanas, freq="7D")
    linhas = []
    for i, d in enumerate(datas):
        extra = choque_final if i >= semanas - 4 else 0.0
        linhas.append(dict(data=d, estado="SAO PAULO", preco=6.0))
        linhas.append(dict(data=d, estado="ACRE", preco=7.0 + extra))
        linhas.append(dict(data=d, estado="AMAPA", preco=5.5 - extra))
    return pd.DataFrame(linhas)


def test_sem_mudanca_nao_ha_alerta():
    m = avaliar_recente(atributos_preco(_serie()))
    assert not m.alerta and m.mae_recente < 0.05 and m.semanas_avaliadas == 4


def test_choque_nas_ultimas_semanas_dispara_alerta():
    m = avaliar_recente(atributos_preco(_serie(choque_final=1.0)))
    assert m.alerta and m.mae_recente > LIMITE_ALERTA
    assert m.mae_recente < m.mae_baseline_recente     # mesmo no choque, melhor que o baseline
