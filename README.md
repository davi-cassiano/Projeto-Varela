# Sistema Dinâmico de Roteirização de Visitas Presenciais

## Sobre o Projeto

O projeto consiste no desenvolvimento de uma ferramenta web para auxiliar os Regionais do Itaú no planejamento de visitas presenciais às agências sob sua responsabilidade.

Atualmente, a ordem das visitas pode ser definida manualmente, levando em consideração principalmente a experiência do Regional. A proposta do projeto é automatizar esse processo, considerando fatores como tempo de deslocamento, custo da viagem e os diferentes meios de transporte disponíveis.

A ferramenta receberá as agências que devem ser visitadas, a origem da viagem, as datas disponíveis e outras possíveis restrições. Com essas informações, o sistema irá calcular uma sequência recomendada para as visitas, buscando reduzir o tempo e/ou o custo total da viagem.

Os meios de transporte considerados inicialmente são carro, ônibus e avião.

## Objetivos

### Objetivo Geral

Desenvolver uma ferramenta capaz de recomendar uma sequência de visitas às agências, buscando reduzir o tempo e o custo das viagens realizadas pelos Regionais.

### Objetivos Específicos

* Sugerir automaticamente a ordem das agências a serem visitadas.
* Comparar diferentes meios de transporte para cada trecho.
* Apresentar o tempo e o custo estimado de cada trecho.
* Permitir escolher entre priorizar tempo, custo ou uma combinação dos dois.
* Permitir simular diferentes cenários, alterando datas e agências.
* Considerar restrições de agenda e prioridades de determinadas agências.
* Gerar informações sobre as rotas realizadas, custos e tempos de deslocamento.

## Metodologia

O projeto será desenvolvido seguindo a metodologia CRISP-DM (Cross-Industry Standard Process for Data Mining).

As etapas previstas são:

### 1. Entendimento do Negócio

Nesta etapa foi identificado o problema e definidos os objetivos da ferramenta, além dos requisitos, riscos e critérios de sucesso.

### 2. Entendimento dos Dados

Será realizado o levantamento das bases disponíveis, incluindo informações das agências, endereços, coordenadas, regras de visita e dados relacionados aos meios de transporte.

### 3. Preparação dos Dados

Os dados serão tratados e organizados para que possam ser utilizados pelo modelo. Entre as atividades estão a limpeza das bases e a criação de uma matriz contendo informações de distância, tempo e custo entre os pontos.

### 4. Modelagem

Será desenvolvido o algoritmo responsável por encontrar uma rota adequada para as visitas.

O problema possui características semelhantes ao Problema do Caixeiro-Viajante (TSP) e ao Vehicle Routing Problem (VRP). Algumas possibilidades inicialmente consideradas são algoritmos como Nearest Neighbor, 2-opt e outras técnicas de otimização.

### 5. Avaliação

As rotas geradas serão avaliadas considerando o tempo, o custo e a qualidade da sequência encontrada. Também será analisado o tempo necessário para o sistema gerar uma recomendação.

### 6. Implantação

Após os testes e validações, a aplicação poderá ser disponibilizada para utilização pelos usuários.

## Funcionamento

O funcionamento esperado da ferramenta é:

1. O usuário informa sua origem.
2. Seleciona as agências que precisam ser visitadas.
3. Informa o período disponível para as visitas.
4. O sistema consulta os dados necessários para os deslocamentos.
5. O algoritmo calcula as possíveis rotas.
6. A ferramenta apresenta a rota recomendada.

A resposta deverá mostrar a ordem das agências, o meio de transporte recomendado, o tempo e o custo de cada trecho e os valores totais da viagem.

## Dados

Entre os dados necessários para o funcionamento do projeto estão:

* Cadastro das agências;
* Endereço das agências;
* Coordenadas geográficas;
* Regional responsável;
* Periodicidade das visitas;
* Regras de priorização;
* Distância entre os locais;
* Tempo estimado de deslocamento;
* Preços de transporte.

Para o carro, o custo poderá ser estimado a partir da distância percorrida, combustível, pedágios e regras de reembolso. Para ônibus e avião, poderão ser utilizadas fontes de preços de passagens.

## ## Datasets e Fontes de Dados

Até o momento, os datasets e fontes de dados utilizados no projeto são:

[Banco Central do Brasil – Cadastro de Agências](https://www.bcb.gov.br/acessoinformacao/legado?url=https:%2F%2Fwww.bcb.gov.br%2Ffis%2Finfo%2Fagencias.asp) – utilizado como fonte de localização das agências bancárias.

[Kaggle – Gas Prices in Brazil](https://www.kaggle.com/datasets/matheusfreitag/gas-prices-in-brazil?resource=download) – utilizado como fonte de dados históricos de preços de combustíveis no Brasil, auxiliando na estimativa dos custos dos deslocamentos realizados de carro.

Essas são as fontes utilizadas até o momento. Conforme o desenvolvimento do projeto avançar, novos datasets e fontes de dados poderão ser incorporados para complementar as informações necessárias para a roteirização, como dados de transporte, preços de passagens, tempos de deslocamento e outras informações relevantes para o modelo.

## Otimização

A principal parte do projeto será encontrar uma sequência de visitas que apresente um resultado melhor em relação ao tempo e ao custo da viagem.

O sistema deverá considerar diferentes possibilidades de rota e, de acordo com a preferência do usuário, escolher a alternativa mais adequada.

Além do custo e do tempo, poderão ser consideradas outras restrições, como:

* Datas disponíveis;
* Horários;
* Prioridade de determinadas agências;
* Limite de dias de viagem;
* Quantidade de agências no ciclo.

## Aplicação Web

A solução será desenvolvida como uma aplicação web interativa.

A interface deverá permitir que o usuário informe os dados necessários e visualize o resultado da roteirização de forma simples.

A rota poderá ser apresentada por meio de uma lista com a ordem das agências e, posteriormente, também poderá ser utilizada uma visualização em mapa.

## Critérios de Sucesso

O projeto pretende alcançar os seguintes resultados:

* Redução do tempo médio de deslocamento;
* Redução do custo médio das viagens;
* Aumento do número de visitas realizadas dentro da periodicidade prevista;
* Maior utilização da ferramenta pelos Regionais.

Como metas iniciais apresentadas no documento de entendimento do negócio, estão o aumento para pelo menos 90% das agências visitadas dentro da periodicidade prevista e pelo menos 80% de utilização mensal da ferramenta pelos Regionais participantes do piloto.

## Riscos

Alguns dos principais riscos identificados são:

* Dados de preços de passagens indisponíveis ou instáveis;
* Base de agências desatualizada;
* Dependência de APIs externas;
* Aumento da complexidade computacional conforme o número de agências;
* Restrições de segurança e compliance;
* Baixa adesão dos usuários.

Para reduzir esses riscos, poderão ser utilizadas alternativas como dados históricos, cache de informações, validação das bases e algoritmos de otimização mais eficientes.

## Integrantes

* Davi Cassiano
* Gabriel Felipe
* Victor Meneguin
* Luca Juraski

## Status

O projeto está atualmente na etapa de Entendimento do Negócio da metodologia CRISP-DM.

As próximas etapas envolvem o levantamento e preparação dos dados, desenvolvimento do algoritmo de roteirização, construção da aplicação web e avaliação dos resultados.
