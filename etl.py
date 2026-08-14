"""Módulo de limpeza e enriquecimento da base de entregas (iFood)."""
import logging
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

NUMERIC_COLS = [
    "Order_Hour", "Is_Weekend", "Is_Festival", "Rider_Experience_Years",
    "Rider_Rating", "Restaurant_Rating", "Order_Items", "Preparation_Time_Min",
    "Road_Distance_km", "Number_of_Signals", "Average_Speed_kmph", "Time_taken_min",
]

CATEGORICAL_COLS = [
    "Day_of_Week", "Weather", "Pickup_Zone", "Dropoff_Zone", "Vehicle_Type",
    "Cuisine_Type", "Restaurant_Load", "Delivery_Distance_Category",
    "Traffic_Level", "Delivery_Priority",
]


def load_data(path: str) -> pd.DataFrame:
    """Carrega o CSV bruto de pedidos de entrega."""
    logger.info("Carregando dados de %s", path)
    df = pd.read_csv(path)
    logger.info("Dataset carregado: %d linhas, %d colunas", *df.shape)
    return df


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Remove duplicatas/linhas incompletas e corrige tipos de dados."""
    df = df.copy()
    n_inicial = len(df)

    df = df.drop_duplicates(subset="Order_ID")
    df = df.drop_duplicates()

    colunas_essenciais = NUMERIC_COLS + CATEGORICAL_COLS + ["Order_Date"]
    df = df.dropna(subset=colunas_essenciais)

    for col in CATEGORICAL_COLS + ["Order_ID"]:
        df[col] = df[col].astype(str).str.strip()

    df["Order_Date"] = pd.to_datetime(df["Order_Date"], errors="coerce")
    df = df.dropna(subset=["Order_Date"])

    for col in NUMERIC_COLS:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=NUMERIC_COLS)

    df = df[
        (df["Road_Distance_km"] > 0)
        & (df["Preparation_Time_Min"] > 0)
        & (df["Time_taken_min"] > 0)
        & (df["Average_Speed_kmph"] > 0)
        & (df["Order_Items"] > 0)
    ]

    df = df[df["Time_taken_min"].between(1, 300)]

    n_final = len(df)
    logger.info("Limpeza concluída: %d -> %d linhas (removidas %d)", n_inicial, n_final, n_inicial - n_final)
    return df.reset_index(drop=True)


def save_data(df: pd.DataFrame, path: str) -> None:
    """Salva o dataset tratado em disco."""
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    logger.info("Dataset processado salvo em %s (%d linhas, %d colunas)", out_path, *df.shape)


def run_etl(input_path: str, output_path: str) -> pd.DataFrame:
    """Executa o pipeline completo de ETL."""
    df = load_data(input_path)
    df = clean_data(df)
    save_data(df, output_path)
    return df


if __name__ == "__main__":
    RAW_PATH = "data/raw/Food_Delivery_Time_Prediction.csv"
    PROCESSED_PATH = "data/processed/food_delivery_processed.csv"
    run_etl(RAW_PATH, PROCESSED_PATH)
