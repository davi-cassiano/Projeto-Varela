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
produto: teto de 40 e piso de 4 agências por regional, aplicados por subdivisão
recursiva e absorção de grupos pequenos. Ver `pipeline/03_definir_regionais.py`.

**Ajuste de curva de potência — regressão não linear.** Estima custo e tempo de
cada modal a partir da distância, no formato `custo = a + b × distância^c`, com
coeficientes calibrados sobre faixas tarifárias reais da ANTT e a tarifa média
doméstica da ANAC. O custo de carro sai de preço de combustível, consumo e
pedágio. Ver `pipeline/decisao_transporte.py` e a versão em JavaScript em
`produto/fonte/motor.js`, validada dígito a dígito contra o original.

Nenhum modelo generativo é usado pelo sistema. O produto final funciona offline,
sem chamar nenhum serviço externo.

---

## Bases de dados

| Base | Fonte | Papel no projeto |
| --- | --- | --- |
| Agências bancárias em funcionamento | Banco Central, posição de 29/11/2024 | Nós da rede de roteirização: 16.552 agências, 2.040 delas do recorte usado |
| Preços de combustíveis | ANP, série semanal 2004–2021 | Calibração do custo de deslocamento rodoviário |
| Base consolidada do grupo | Elaborada a partir das duas acima | Coordenadas por município, 73 aeroportos, preços estimados de ônibus e avião |

Bases auxiliares baixadas automaticamente: coordenadas de municípios e bairros,
e contorno dos estados brasileiros.

### Tratamento de qualidade aplicado

A base do Bacen **não traz latitude nem longitude**. As coordenadas foram
obtidas em três níveis, e cada agência registra qual nível foi usado:

| Nível | Como é obtido | Cobertura |
| --- | --- | --- |
| `bairro` | cruzamento de município e bairro | 72% |
| `bairro_aprox` | mesmo cruzamento, com correspondência aproximada para absorver abreviações do cadastro | 3% |
| `municipio` | centróide pelo código IBGE | 25% |

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

Execute as cinco etapas na ordem, a partir da raiz do projeto:

```bash
python pipeline/01_baixar_bases.py          # bases auxiliares e geometria
python pipeline/02_enriquecer_coordenadas.py # coordenadas em três níveis
python pipeline/03_definir_regionais.py      # k-means com teto e piso
python pipeline/04_gerar_dados.py            # pacote de dados do produto
python pipeline/05_montar_produto.py         # gera o HTML final
```

### Produto

Abra `produto/roteirizacao-visitas.html` no navegador. É um arquivo único e
autocontido, com todos os dados embutidos. Não precisa de servidor nem de
conexão.

---

## Estrutura do projeto

```
.
├── dados/
│   ├── brutos/          bases originais (não versionadas)
│   └── ...              arquivos intermediários gerados pelo pipeline
├── pipeline/
│   ├── 01_baixar_bases.py
│   ├── 02_enriquecer_coordenadas.py
│   ├── 03_definir_regionais.py
│   ├── 04_gerar_dados.py
│   ├── 05_montar_produto.py
│   └── decisao_transporte.py    modelo de custo e tempo por modal
├── produto/
│   ├── fonte/           template, módulos JavaScript e estilos
│   └── roteirizacao-visitas.html   gerado pela etapa 05
├── docs/
│   └── apresentacao-roteirizacao.pptx
├── requirements.txt
└── README.md
```

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
| 4. Modelagem | Parcial — k-means formando as regionais e modelo de custo por modal implementados; o algoritmo de roteirização (TSP/VRP) é o próximo passo |
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
