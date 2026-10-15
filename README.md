# Sistema Dinâmico de Roteirização de Visitas Presenciais

Protótipo navegável de um sistema de apoio à decisão para gerentes regionais de
banco. A partir do cadastro público de agências do Banco Central, o sistema
agrupa as agências em regionais, permite montar uma viagem de visitas e
recomenda a sequência, o meio de transporte e o custo de cada trecho.

**Disciplina:** Projeto e Gestão de Dados (CCD610) — Projeto Integrador
**Entrega:** Checkpoint das aulas 1, 2 e 3

## Integrantes

- Davi Cassiano
- Gabriel Felipe
- Victor Meneguin
- Luca Juraski

---

## O problema

Um gerente regional é responsável por dezenas de agências espalhadas por vários
municípios, às vezes em estados diferentes. Hoje o planejamento das visitas é
manual: a ordem sai da intuição ou de uma planilha, o meio de transporte é
escolhido por hábito, e o custo só aparece na prestação de contas.

O sistema responde a quatro perguntas de uma vez: quais agências visitar, em que
ordem, em quais datas e por qual meio de transporte.

## O que o protótipo faz

- Agrupa 2.040 agências reais em 106 regionais, por proximidade geográfica
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
52% menos erro. Ver `src/train.py` e `docs/arquitetura.md`.

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
próprio município.

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
git clone <URL DO REPOSITÓRIO>
cd roteirizacao-agencias
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
python -m src.pipeline
```

São quatro estágios, cada um num módulo com responsabilidade única:

| Estágio | Módulo | O que faz |
| --- | --- | --- |
| Ingestão | `src/ingest.py` | Carrega e valida as bases brutas, através da abstração `DataSource` |
| Preparação | `src/features.py` | Coordenadas em três níveis de precisão e atributos do modelo |
| Treino | `src/train.py` | K-means das regionais e regressão do preço de combustível |
| Serving | `src/serve.py` | Custo e modal por trecho, preço por estado e pacote do produto |

O resumo da execução fica em `dados/saida/relatorio_execucao.json`.

### Testes

```bash
python -m pytest tests/ -v
```

22 testes, um arquivo por módulo, ligados aos critérios de aceite do backlog.

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
│   └── pipeline.py      orquestração, único ponto que conhece as fontes concretas
├── tests/               pytest, um arquivo por módulo
├── dados/
│   ├── brutos/          bases originais (não versionadas)
│   └── saida/           pacote do produto e relatório de execução (gerados)
├── produto/
│   ├── fonte/           template, módulos JavaScript e estilos
│   └── roteirizacao-visitas.html   protótipo, gerado pelo pipeline
├── docs/
│   ├── backlog.md       épicos, user stories, INVEST e requisitos (Aula 4)
│   ├── arquitetura.md   arquitetura de referência e SOLID (Aula 5)
│   ├── planejamento.md  WBS, estimativas, riscos e Sprint 1 (Aula 6)
│   └── img/             gráficos
├── requirements.txt
└── README.md
```

O backlog está nas [Issues](https://github.com/davi-cassiano/Projeto-Varela/issues) do repositório.

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

1. Substituir a varredura geográfica por um algoritmo de roteirização
2. Geocodificação por endereço, levando a precisão do bairro ao nível de rua
3. Consulta de preços e tarifas em tempo real
4. Persistência em banco, autenticação e integração com a agenda corporativa

## Fontes

- Banco Central do Brasil — agências em funcionamento
- ANP — série histórica de preços de combustíveis
- ANTT — Anuário Estatístico do Transporte Rodoviário
- ANAC — tarifas aéreas domésticas
