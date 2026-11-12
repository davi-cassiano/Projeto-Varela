# Relatório de qualidade de dados

Gerado em 12/11/2026 por `python -m src.validate`. Regras em `src/validate.py` e `sql/qualidade.sql`.

| # | Dimensão | Base | Regra | Limite | Medido | Situação |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Unicidade | agências | Um registro por agência | 0 códigos COMPE repetidos | 0 repetidos | ✅ Passou |
| 2 | Completude | agências | Colunas obrigatórias preenchidas | até 1% de nulos por coluna | pior coluna: bairro com 0.05% | ✅ Passou |
| 3 | Validade | agências | UF, CEP e coordenadas em faixas válidas | 0 registros fora da faixa | 0 inválidos | ✅ Passou |
| 4 | Consistência | agências | Município (código IBGE) pertence à UF informada | 0 divergências | 0 divergentes | ✅ Passou |
| 5 | Consistência | agências (após preparação) | Coordenada de bairro coerente com o município (≤ 30 km) | descartes ≤ 10% e cobertura de bairro ≥ 70% | descartes 14.4% (290 de 2010) · cobertura 74.7% | ❌ Falhou |
| 6 | Pontualidade | preços | Série de preços única, válida e atual | 1 linha por semana×estado · preço em R$ 0.5–15.0 · última semana há ≤ 90 dias | 0 duplicadas · 0 fora da faixa · última semana 07/11/2026, há 5 dias | ✅ Passou |

**5 de 6 regras passaram.**

- **Falhou — Coordenada de bairro coerente com o município (≤ 30 km):** descartes 14.4% (290 de 2010) · cobertura 74.7%. colisão de nome de bairro entre municípios; limite único prejudica municípios extensos (Issue #16).
