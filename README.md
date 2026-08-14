# Previsão de Tempo de Entrega (iFood)

## Descrição

Projeto de Machine Learning para prever o tempo de entrega de pedidos (`Time_taken_min`), com base em características do pedido, condições de trânsito/clima, distância, perfil do entregador e do restaurante. O objetivo final é ter um pipeline robusto e reprodutível — do tratamento dos dados ao modelo treinado — com uma simulação funcional de previsão para novos pedidos.

## Integrantes
- Davi Cassiano Rosa
- Gabriel Felipe Cantorani
- Victor Meneguin

## Dataset

- **Arquivo bruto:** `data/raw/Food_Delivery_Time_Prediction.csv`
- **Arquivo tratado:** `data/processed/food_delivery_processed.csv`
- **Tamanho:** ~50.000 pedidos
- **Variável alvo:** `Time_taken_min` (tempo de entrega em minutos)

### Principais colunas

| Categoria | Colunas |
|---|---|
| Pedido | `Order_ID`, `Order_Date`, `Order_Hour`, `Day_of_Week`, `Is_Weekend`, `Is_Festival`, `Order_Items`, `Cuisine_Type`, `Delivery_Priority` |
| Contexto externo | `Weather`, `Traffic_Level`, `Number_of_Signals`, `Average_Speed_kmph` |
| Localização | `Pickup_Zone`, `Dropoff_Zone`, `Road_Distance_km`, `Delivery_Distance_Category` |
| Entregador | `Vehicle_Type`, `Rider_Experience_Years`, `Rider_Rating` |
| Restaurante | `Restaurant_Rating`, `Restaurant_Load`, `Preparation_Time_Min` |
| Alvo | `Time_taken_min` |

## ETL

O tratamento dos dados está em `src/etl.py` e é dividido em três etapas:

1. **`load_data`** — carrega o CSV bruto.
2. **`clean_data`** — remove duplicatas (por `Order_ID` e linha inteira), descarta linhas com valores faltantes nas colunas essenciais, corrige tipos (datas e numéricos), remove valores fisicamente inválidos (distância, tempo, velocidade e itens ≤ 0) e filtra outliers de tempo de entrega fora do intervalo 1–300 min.
3. **`save_data`** — salva o dataset tratado em `data/processed/`.

Para rodar o ETL:
```bash
python src/etl.py
```

## Objetivos do projeto

1. **ETL concluído** — dados carregados, limpos e validados.
2. **Análise exploratória (EDA):** entender distribuições, correlações e outliers (ex.: impacto de clima, trânsito e distância no tempo de entrega).
3. **Engenharia de features:** criar variáveis derivadas (ex.: período do dia, mesma zona de coleta/entrega, velocidade efetiva) e codificar variáveis categóricas.
4. **Modelagem:** treinar e comparar modelos de regressão (ex.: Regressão Linear, Random Forest, XGBoost/LightGBM).
5. **Avaliação:** métricas como MAE, RMSE e R², com validação cruzada.
6. **Simulação/Deploy:** interface simples (script ou app) para simular a previsão de tempo de entrega a partir de novos dados de pedido.

## Estrutura do projeto
