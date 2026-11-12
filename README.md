# Sistema Dinâmico de Roteirização de Visitas Presenciais

Protótipo navegável de um sistema de apoio à decisão para gerentes regionais de
banco. A partir do cadastro público de agências do Banco Central, o sistema
agrupa as agências em regionais, permite montar uma viagem de visitas e
recomenda a sequência, o meio de transporte e o custo de cada trecho.

**Disciplina:** Projeto e Gestão de Dados (CCD610) — Projeto Integrador
**Situação:** projeto concluído — checkpoints das Aulas 1–3 e 4–6, ciclo de qualidade das Aulas 8 e 9 e sprint final com as 14 stories entregues; apresentação final na Aula 10

[![qualidade](https://github.com/davi-cassiano/Projeto-Varela/actions/workflows/qualidade.yml/badge.svg)](https://github.com/davi-cassiano/Projeto-Varela/actions/workflows/qualidade.yml)

## Integrantes

| Integrante | Frente |
| --- | --- |
| Davi Cassiano | Repositório, revisão de código e prazo |
| Gabriel Felipe | Base de agências e qualidade dos dados |
| Luca Juraski | Modelo de preço e pipeline |
| Victor Meneguin | Negócio, modais e rota |

## Entregas

O projeto é avaliado em checkpoints. Cada um parte do anterior: o Canvas MVP
vira backlog, o backlog vira arquitetura e a arquitetura vira plano.

### Checkpoint 1 · Aulas 1, 2 e 3 — Engenharia de software, CRISP-DM e Lean Inception

| O quê | Onde está |
| --- | --- |
| Repositório versionado, README e dependências | Este repositório |
| Entendimento do negócio e dos dados (CRISP-DM): objetivos, bases, qualidade, riscos e critérios de sucesso | Seções abaixo e apresentação |
| Visão do produto, personas, ondas de funcionalidades e Canvas MVP (Lean Inception) | Seções abaixo e apresentação |
| Protótipo navegável com as jornadas da Onda 1 | [`produto/roteirizacao-visitas.html`](produto/roteirizacao-visitas.html) |
| Apresentação | [`docs/apresentacao-checkpoint-1-3.pptx`](docs/apresentacao-checkpoint-1-3.pptx) |

### Checkpoint 2 · Aulas 4, 5 e 6 — Requisitos, arquitetura e planejamento

| Parte | O quê | Onde está |
| --- | --- | --- |
| 1 · Requisitos | 4 épicos, 14 user stories com critérios Dado/Quando/Então, INVEST, requisitos funcionais, não funcionais e de dados | [`docs/backlog.md`](docs/backlog.md) e [Issues](https://github.com/davi-cassiano/Projeto-Varela/issues) |
| 2 · Arquitetura | Pipeline em ingestão, preparação, treino e serving; princípios SOLID; 23 testes | [`docs/arquitetura.md`](docs/arquitetura.md), [`src/`](src), [`tests/`](tests) |
| 2 · Revisão | Pull request revisado, com comentários resolvidos | [PR #15](https://github.com/davi-cassiano/Projeto-Varela/pull/15) |
| 3 · Planejamento | WBS, Planning Poker, capacidade, matriz de riscos e plano da Sprint 1 | [`docs/planejamento.md`](docs/planejamento.md) |
| Quadro | Backlog com pontos, por onda e situação | [GitHub Projects](https://github.com/users/davi-cassiano/projects/1/views/1) |
| Apresentação | 19 slides | [`docs/apresentacao-checkpoint-4-6.pptx`](docs/apresentacao-checkpoint-4-6.pptx) |
| Notebook | Os dois modelos (k-means e regressão Ridge) executáveis no Google Colab, com os testes do repositório | [Abrir no Colab](https://colab.research.google.com/github/davi-cassiano/Projeto-Varela/blob/main/notebooks/modelos.ipynb) · [`notebooks/modelos.ipynb`](notebooks/modelos.ipynb) |

### Ciclo de qualidade · Aulas 8 e 9 — Maturidade, governança e qualidade

| Parte | O quê | Onde está |
| --- | --- | --- |
| Aula 8 · Autoavaliação | Checklist CMMI/MPS-BR em 6 áreas, com evidência e nota N/P/L/F | [`docs/autoavaliacao-maturidade.md`](docs/autoavaliacao-maturidade.md) |
| Aula 8 · Plano de melhoria | 3 ações com responsável, prazo e indicador | [`docs/plano-melhoria.md`](docs/plano-melhoria.md) |
| Aula 8 · Ata | Decisões e o que muda na próxima sprint | [`docs/atas/2026-11-12.md`](docs/atas/2026-11-12.md) |
| Aula 9 · Qualidade de dados | 6 regras em Python e SQL, relatório, SBAR da pior falha, governança e monitoramento | [`docs/qualidade.md`](docs/qualidade.md), [`src/validate.py`](src/validate.py), [`sql/qualidade.sql`](sql/qualidade.sql) |
| Aula 9 · Testes e CI | 79 testes (bordas, parametrização, fumaça do pipeline), ruff, 88% de cobertura, GitHub Actions | [`tests/`](tests), [`.github/workflows/qualidade.yml`](.github/workflows/qualidade.yml) |
| Aula 9 · Revisão de PR | Pull request revisado por colega com a lista da aula | PRs #28 e #29 |

### Sprint final · 12/11 — produto completo

| Story | O quê | Onde está |
| --- | --- | --- |
| US12 | Sequência otimizada: vizinho mais próximo + 2-opt, 12% menor que a varredura em 20 seleções reais, nunca pior | [`produto/fonte/roteiro.js`](produto/fonte/roteiro.js), [`src/serve.py`](src/serve.py), [`tests/test_sequencia.py`](tests/test_sequencia.py) |
| US14 | Preços atualizados automaticamente: leitura da publicação semanal da ANP, monitor com alerta de drift, execução agendada | [`src/ingest.py`](src/ingest.py) `AnpSource`, [`src/monitor.py`](src/monitor.py), [`.github/workflows/atualizar-precos.yml`](.github/workflows/atualizar-precos.yml) |
| US09 | Exportação do planejamento em A4 | [`produto/fonte/telas_resultado.js`](produto/fonte/telas_resultado.js) |
| US13 | Painel: % dentro da periodicidade contra a meta de 90% e custo acumulado | [`produto/fonte/app.template.html`](produto/fonte/app.template.html) |

---

## O problema

Um gerente regional é responsável por dezenas de agências espalhadas por vários
municípios, às vezes em estados diferentes. Hoje o planejamento das visitas é
manual: a ordem sai da intuição ou de uma planilha, o meio de transporte é
escolhido por hábito, e o custo só aparece na prestação de contas.

O sistema responde a quatro perguntas de uma vez: quais agências visitar, em que
ordem, em quais datas e por qual meio de transporte.

## Visão do produto

> **Para** gerentes regionais **que** precisam planejar visitas presenciais às
> agências sob sua responsabilidade, **o** Sistema de Roteirização de Visitas
> **é** uma ferramenta de apoio à decisão **que** recomenda a sequência de
> visitas e o meio de transporte mais adequado, considerando tempo, distância,
> custo e restrições. **Diferente de** planilhas e planejamento manual,
> **nosso produto** consolida as informações e apresenta cenários comparáveis de
> menor custo e menor tempo.

### Persona

**Rafael Menezes, gerente regional.** Organiza ciclos de visitas considerando
origem, período, agenda, prioridades e regras de viagem. Hoje compara à mão
agências, deslocamentos, custos e alternativas de transporte. Quer um
cronograma viável e uma rota de boa qualidade com menos esforço.

Seis personas foram discutidas no workshop; Rafael foi escolhida por ser quem
planeja o roteiro e sente a dor central. As outras cinco (gerente de agência,
diretor de operações, compliance, motorista, equipe de reembolsos) ficam para
ondas posteriores.

### Canvas MVP

| Bloco | Conteúdo |
| --- | --- |
| Resultado esperado | Validar se uma recomendação automatizada de roteiro ajuda o gerente a planejar com menos esforço, custo e tempo, respeitando restrições e periodicidade |
| Onda 1 (MVP) | Selecionar agências · informar origem, período e restrições · escolher o objetivo · gerar a sequência · recomendar o modal por trecho · exibir distância, tempo e custo · exibir totais e economia · comparar com um cenário de referência |
| Onda 2 | Sequência otimizada · painel gerencial · atualização automática de preços · reotimização dinâmica |
| Fora de escopo | Chatbot, gamificação, integração com Uber e 99, app nativo, aprovação de despesas, hotel, clima |
| Métricas de validação | Redução de custo e tempo por ciclo · ≥ 90% das visitas dentro da periodicidade · ≥ 80% de adoção no piloto · economia sobre a referência |

Das 20 ideias do brainstorming, 8 formaram a Onda 1. As metas de custo e tempo
dependem de uma linha de base real, medida no piloto; o protótipo aproxima essa
linha de base com o cenário de referência.

## O que o protótipo faz

- Agrupa 2.010 agências reais do Itaú Unibanco em 105 regionais, por proximidade geográfica
- Mostra, por regional, o que vence nos próximos 30 dias e o que está em atraso
- Permite selecionar agências com busca, filtros e atalhos por prioridade
- Aceita restrições de agenda: janela de visita, teto diário, limite de dias,
  modais permitidos e regra de pernoite
- Compara carro, ônibus e avião em cada trecho, segundo o peso escolhido entre
  custo e tempo
- Desenha a rota num mapa interativo sobre o território brasileiro
- Compara o resultado com um cenário de referência e estima a economia
- Salva planejamentos e permite reabri-los

## O que o protótipo **não** faz

Por decisão de escopo, ficaram fora desta entrega:

- Algoritmo de roteirização (TSP, VRP, 2-opt). A sequência de visitas usa uma
  regra provisória de varredura geográfica, isolada na função `sequenciar()`
- APIs de mapas, combustível, passagens de ônibus e voos em tempo real
- Banco de dados, autenticação e integração com sistemas do banco

---

## Modelos utilizados

**K-means — aprendizado não supervisionado.** Agrupa as agências pelas
coordenadas para formar as regionais. Nenhuma regra geográfica é escrita à mão:
as cidades-polo emergem dos agrupamentos. Sobre o resultado, duas regras de
produto: teto de 40 e piso de 4 agências por regional. Ver `src/train.py`.

**Regressão Ridge — aprendizado supervisionado (US11).** Estima o preço da
gasolina em cada estado a partir do preço nacional, da diferença recente do
estado e do mês, com a série real da ANP. Treino até dezembro de 2019 e teste em
2020–2021, sem embaralhar as semanas. Erro médio de **R$ 0,095 por litro**,
contra R$ 0,199 do baseline que usava o mesmo preço para todos os estados —
52% menos erro. Com a série atual da ANP (até novembro de 2026) e o mesmo corte,
o teste cobre 2020–2026: R$ 0,116 contra R$ 0,238 do baseline, 51% menos; nas
últimas quatro semanas o erro é de R$ 0,105 (`python -m src.monitor`). Ver
`src/train.py`, `src/monitor.py` e `docs/arquitetura.md`.

**Sequência de visitas — vizinho mais próximo + 2-opt (US12).** A ordem das
visitas minimiza o deslocamento: em 20 seleções reais de 5 a 15 agências, o
circuito fica 12% menor que o da varredura angular anterior e nunca maior.
Ver `produto/fonte/roteiro.js`, `src/serve.py` e `tests/test_sequencia.py`.

**Curvas de custo calibradas.** Custo e tempo de ônibus e avião no formato
`custo = a + b × distância^c`, com coeficientes calibrados sobre faixas
tarifárias da ANTT e a tarifa média da ANAC. Ver `src/serve.py`.

Nenhum modelo generativo é usado pelo sistema. O produto final funciona offline,
sem chamar nenhum serviço externo.

---

## Bases de dados

| Base | Fonte | Papel no projeto |
| --- | --- | --- |
| Agências bancárias em funcionamento | Banco Central, posição de 29/11/2024 | Nós da rede de roteirização: 16.552 agências, 2.010 do Itaú Unibanco no recorte usado |
| Preços de combustíveis | ANP, série semanal 2004–2021 | Treino do modelo de preço por estado (US11) |
| Base consolidada do grupo | Elaborada a partir das duas acima | Coordenadas por município, 73 aeroportos, preços estimados de ônibus e avião |

Bases auxiliares baixadas automaticamente: coordenadas de municípios e bairros,
e contorno dos estados brasileiros.

### Tratamento de qualidade aplicado

A base do Bacen **não traz latitude nem longitude**. As coordenadas foram
obtidas em três níveis, e cada agência registra qual nível foi usado:

| Nível | Como é obtido | Cobertura |
| --- | --- | --- |
| `bairro` | cruzamento de município e bairro | 72,4% |
| `bairro_aprox` | mesmo cruzamento, com correspondência aproximada para absorver abreviações do cadastro | 2,3% |
| `municipio` | centróide pelo código IBGE | 25,3% |

A base pública de bairros contém colisão de nomes — o bairro Mirandópolis, na
capital paulista, recebe as coordenadas da cidade de Mirandópolis, a 530 km. O
pipeline descarta qualquer coordenada de bairro a mais de 30 km do centróide do
próprio município (290 descartadas). O limite único prejudica municípios muito
extensos, como o Rio de Janeiro; a correção está na
[Issue #16](https://github.com/davi-cassiano/Projeto-Varela/issues/16).

### O que é simulado

Prioridade da agência, data limite da visita e data da última visita **não
existem em base pública**: são dados de planejamento interno do banco. No
protótipo eles são gerados de forma determinística a partir do código da
agência, e a interface declara isso ao usuário.

---

## Como executar

### Requisitos

Python 3.10 ou superior e um navegador. O pipeline usa internet apenas na
primeira etapa.

```bash
git clone https://github.com/davi-cassiano/Projeto-Varela.git
cd Projeto-Varela
python -m venv .venv
source .venv/bin/activate        # no Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Bases brutas

Baixe os três arquivos indicados em `dados/brutos/LEIA-ME.md` e coloque-os
naquela pasta.

### Pipeline

Um comando roda tudo, a partir da raiz do projeto:

```bash
python -m src.pipeline                          # série 2004–2021 e preço nacional de R$ 6,70
python -m src.pipeline --atualizar-precos       # US14: baixa a publicação semanal da ANP e usa o preço da última semana
python -m src.pipeline --preco-gasolina 6.45    # preço nacional informado à mão
python -m src.monitor                           # reavalia o modelo nas últimas 4 semanas; alerta acima de R$ 0,25/L
```

O produto versionado foi gerado com `--atualizar-precos` em 12/11/2026: série da
ANP até 07/11/2026 e preço nacional de R$ 6,651/L.

São quatro estágios, cada um num módulo com responsabilidade única:

| Estágio | Módulo | O que faz |
| --- | --- | --- |
| Ingestão | `src/ingest.py` | Carrega e valida as bases brutas, através da abstração `DataSource` |
| Preparação | `src/features.py` | Coordenadas em três níveis de precisão e atributos do modelo |
| Treino | `src/train.py` | K-means das regionais e regressão do preço de combustível |
| Serving | `src/serve.py` | Custo e modal por trecho, preço por estado e pacote do produto |

O resumo da execução fica em `dados/saida/relatorio_execucao.json`.

### Qualidade: lint, testes e validação de dados

```bash
ruff check src/ tests/ sql/                      # análise estática
pytest --cov=src --cov-fail-under=70            # 79 testes com cobertura (88%)
python -m src.validate                          # 6 regras de qualidade de dados → dados/saida/relatorio_qualidade.md
python -m src.validate --amostra                # as mesmas regras sobre o recorte versionado (é o que o CI roda)
python sql/rodar_qualidade.py                   # as mesmas regras em SQL
```

Os três primeiros comandos rodam no GitHub Actions a cada push e pull request
([`.github/workflows/qualidade.yml`](.github/workflows/qualidade.yml)). Os testes
cobrem funções de features com casos de borda e parametrização, as regras de
qualidade, o critério de aceite do modelo e um teste de fumaça do pipeline inteiro
com uma amostra fixa, sem arquivo real.

### No Google Colab, sem instalar nada

[Abrir `notebooks/modelos.ipynb` no Colab](https://colab.research.google.com/github/davi-cassiano/Projeto-Varela/blob/main/notebooks/modelos.ipynb) e usar *Ambiente de execução →
Executar tudo*. O notebook reproduz o k-means das regionais (US01) e a regressão
do preço por estado (US11) a partir dos dois arquivos pequenos em `dados/colab/`,
e no fim clona o repositório e roda os testes.

### Produto

Abra `produto/roteirizacao-visitas.html` no navegador. É um arquivo único e
autocontido, com todos os dados embutidos. Não precisa de servidor nem de
conexão.

---

## Estrutura do projeto

```
.
├── src/
│   ├── ingest.py        ingestão: DataSource e cargas validadas
│   ├── features.py      preparação: coordenadas e atributos
│   ├── train.py         treino: k-means e modelo de preço
│   ├── serve.py         serving: modais, preço por estado, pacote do produto
│   ├── validate.py      regras de qualidade de dados e relatório
│   ├── monitor.py       US14: reavaliação semanal do modelo de preço com alerta
│   └── pipeline.py      orquestração, único ponto que conhece as fontes concretas
├── sql/
│   ├── qualidade.sql    as mesmas regras de qualidade em SQL
│   └── rodar_qualidade.py
├── tests/               pytest: unitários com bordas, regras de qualidade, modelo e fumaça do pipeline
├── .github/workflows/
│   ├── qualidade.yml    CI: ruff, pytest com cobertura e validação de dados
│   └── atualizar-precos.yml   US14: ingestão programada da ANP, toda segunda
├── notebooks/
│   └── modelos.ipynb    k-means e regressão Ridge, executável no Google Colab
├── dados/
│   ├── brutos/          bases originais (não versionadas)
│   ├── colab/           recortes pequenos que o notebook e os testes usam (versionados)
│   └── saida/           pacote do produto e relatório de execução (gerados)
├── produto/
│   ├── fonte/           template, módulos JavaScript e estilos
│   └── roteirizacao-visitas.html   protótipo, gerado pelo pipeline
├── docs/
│   ├── backlog.md       épicos, user stories, INVEST e requisitos (Aula 4)
│   ├── arquitetura.md   arquitetura de referência e SOLID (Aula 5)
│   ├── planejamento.md  WBS, estimativas, riscos e Sprint 1 (Aula 6)
│   ├── apresentacao-checkpoint-1-3.pptx   apresentação das Aulas 1 a 3
│   ├── apresentacao-checkpoint-4-6.pptx   apresentação das Aulas 4 a 6
│   └── img/             gráficos
├── requirements.txt
└── README.md
```

O backlog está nas [Issues](https://github.com/davi-cassiano/Projeto-Varela/issues) do repositório e organizado no [quadro do projeto](https://github.com/users/davi-cassiano/projects/1/views/1).

### Fronteira entre dados e interface

O pipeline produz um único arquivo JSON com agências, regionais, aeroportos,
geometria e os parâmetros do modelo. A interface consome apenas esse formato.
Substituir o pacote por uma resposta de API com a mesma estrutura não exige
mudança nas telas — é a preparação prevista para a integração futura.

O ponto de entrada do algoritmo de roteirização é a função `sequenciar()`, em
`produto/fonte/roteiro.js`, marcada em comentário. Trocar essa função por um
solver de TSP ou VRP é suficiente; o restante do produto não muda.

---

## Metodologia

O projeto segue o CRISP-DM. Situação de cada etapa:

| Etapa | Situação |
| --- | --- |
| 1. Entendimento do negócio | Concluída — objetivos, requisitos, riscos e critérios de sucesso definidos |
| 2. Entendimento dos dados | Concluída — bases levantadas, exploradas e com riscos de qualidade mapeados |
| 3. Preparação dos dados | Concluída — limpeza, geocodificação em três níveis e matriz de distância, tempo e custo |
| 4. Modelagem | Parcial — k-means das regionais e regressão do preço por estado treinados e testados; o algoritmo de roteirização (TSP/VRP) é a US12 |
| 5. Avaliação | Parcial — comparação com cenário de referência implementada; falta a linha de base real |
| 6. Implantação | Não iniciada |

## Próximos passos

O plano completo está em [`docs/planejamento.md`](docs/planejamento.md). As 14
stories do backlog estão entregues: Sprint 1 (US05, US10, US11), protótipo
(stories de interface) e sprint final de 12/11 (US09, US12, US13, US14). As
Sprints 2 a 4 originalmente previstas não aconteceram no prazo (risco R6,
registrado) e foram substituídas pelo ciclo de qualidade e pela sprint final.

O que fica para depois do curso:

| Item | Por quê |
| --- | --- |
| Issue #16 — limite de desvio proporcional ao município | 10 agências do Rio perdem a coordenada de bairro com o limite único de 30 km |
| Validação das stories de interface com um gerente real | Depende de acesso ao banco; é o teste da hipótese do Canvas |
| Reavaliação de maturidade com o mesmo checklist | Para medir se as três ações do plano mudaram as notas |

Fora do escopo do MVP: geocodificação por endereço, tarifas em tempo real,
persistência em banco, autenticação e integração com a agenda corporativa.

## Fontes

- Banco Central do Brasil — agências em funcionamento
- ANP — série histórica de preços de combustíveis
- ANTT — Anuário Estatístico do Transporte Rodoviário
- ANAC — tarifas aéreas domésticas
