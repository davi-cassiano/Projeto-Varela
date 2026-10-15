"""Testes do serving: regras de modal (US03, US05) e equivalência com o
modelo original decisao_transporte.py."""

import pytest

from src.serve import Aviao, Carro, Modal, Onibus, Opcao, comparar_modais

SAO_PAULO, RIO = (-23.5505, -46.6333), (-22.9068, -43.1729)
SP, CAMPINAS = (-23.5505, -46.6333), (-22.9099, -47.0626)


def test_equivale_ao_modelo_original():
    """Valores de decisao_transporte.py para São Paulo → Rio de Janeiro."""
    r = comparar_modais(SAO_PAULO, RIO)
    assert r["opcoes"]["carro"]["custo"] == pytest.approx(274.32, abs=0.01)
    assert r["opcoes"]["onibus"]["custo"] == pytest.approx(142.76, abs=0.01)
    assert r["opcoes"]["aviao"]["custo"] == pytest.approx(340.55, abs=0.01)


def test_aviao_indisponivel_abaixo_de_150_km():
    """US05: trecho curto não oferece avião."""
    r = comparar_modais(SP, CAMPINAS)
    assert r["opcoes"]["aviao"]["disponivel"] is False
    assert r["recomendado"] != "aviao"


def test_modal_desligado_nunca_e_recomendado():
    """US05: com ônibus desligado nas restrições, nenhum trecho o recomenda."""
    r = comparar_modais(SAO_PAULO, RIO, peso_custo=1.0, modais=[Carro(), Aviao()])
    assert r["recomendado"] != "onibus"


def test_peso_no_custo_escolhe_o_mais_barato_e_no_tempo_o_mais_rapido():
    """US03."""
    assert comparar_modais(SAO_PAULO, RIO, peso_custo=1.0)["recomendado"] == "onibus"
    assert comparar_modais(SAO_PAULO, RIO, peso_custo=0.0)["recomendado"] == "aviao"


def test_carro_usa_o_preco_do_estado():
    """US11: com preço de combustível maior no estado, o carro custa mais."""
    barato = Carro(preco_por_uf={"SP": 6.0}).estimar(100, "SP").custo
    caro = Carro(preco_por_uf={"SP": 7.0}).estimar(100, "SP").custo
    assert caro > barato


def test_modal_novo_entra_sem_alterar_codigo_existente():
    """Open/Closed: um modal novo é só uma classe nova."""

    class Trem(Modal):
        nome = "trem"

        def estimar(self, distancia_reta_km, uf=None):
            return Opcao(self.nome, True, 1.0, 1.0, distancia_reta_km)

    r = comparar_modais(SAO_PAULO, RIO, modais=[Carro(), Onibus(), Trem()])
    assert r["recomendado"] == "trem"


def test_preco_nacional_vem_de_fora_e_nao_do_codigo():
    """Revisão do PR #15: o preço nacional é parâmetro, não constante fixa."""
    import pandas as pd

    from src.serve import precos_por_uf
    from src.train import BaselineNacional

    atributos = pd.DataFrame({"data": pd.to_datetime(["2021-05-01"] * 2), "uf": ["SP", "RJ"]})
    precos = precos_por_uf(BaselineNacional(), atributos, preco_nacional=6.45)
    assert precos == {"SP": 6.45, "RJ": 6.45}
