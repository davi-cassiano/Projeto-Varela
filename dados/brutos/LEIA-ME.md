# Bases brutas

Estes arquivos não são versionados por causa do tamanho. Baixe-os aqui
antes de rodar o pipeline.

| Arquivo | Fonte | Onde obter |
| --- | --- | --- |
| `202411AGENCIAS.xlsx` | Banco Central do Brasil — agências em funcionamento, posição de 29/11/2024 | https://www.bcb.gov.br/fis/info/agencias.asp |
| `2004-2021.tsv` | ANP — série histórica semanal de preços de combustíveis | https://www.kaggle.com/datasets/matheusfreitag/gas-prices-in-brazil |
| `base_consolidada_roteirizacao.xlsx` | Consolidação do grupo: agências com coordenada de município, aeroportos, preços estimados de ônibus e avião e matriz de decisão de transporte | Produzida pelo grupo a partir das duas bases acima |

As bases auxiliares (coordenadas de municípios, bairros e contorno dos
estados) são baixadas automaticamente pela etapa `01_baixar_bases.py`.
