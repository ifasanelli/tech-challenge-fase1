"""
data_prep.py
------------
Carregamento, validação e limpeza de dados para o Tech Challenge de NPS Preditivo.

Seguindo as fases "Entendimento dos Dados" e "Preparação dos Dados" do CRISP-DM,
este módulo transforma os dados brutos em um dataset limpo e pronto
para análise, documentando cada verificação de qualidade executada.
"""

from __future__ import annotations

import os
from typing import Dict

import numpy as np
import pandas as pd

from tech_challenge_fase1.config import PROCESSED_DATA_FILE, RAW_DATA_FILE

# --------------------------------------------------------------------------- #
# Grupos de colunas (fonte única da verdade, reutilizada pelo módulo de modelagem)
# --------------------------------------------------------------------------- #
ID_COLS = ["customer_id", "order_id"]
TARGET = "nps_score"

# Variáveis que codificam a própria satisfação ou que são co-resultados da pesquisa.
# Elas NÃO estão disponíveis "antes da pesquisa de NPS", então usá-las como
# preditoras causaria vazamento do alvo (target leakage). São mantidas no arquivo
# processado, mas excluídas das features.
LEAKAGE_COLS = ["repeat_purchase_30d", "csat_internal_score"]

CATEGORICAL_FEATURES = ["customer_region"]

# Features operacionais conhecidas antes da pesquisa de NPS (pedidos / logística / atendimento).
NUMERIC_FEATURES = [
    "customer_age",
    "customer_tenure_months",
    "order_value",
    "items_quantity",
    "discount_value",
    "payment_installments",
    "delivery_time_days",
    "delivery_delay_days",
    "freight_value",
    "delivery_attempts",
    "customer_service_contacts",
    "resolution_time_days",
    "complaints_count",
]

# Faixas de valores plausíveis usadas na verificação de validade (semântica do dicionário de dados).
VALID_RANGES = {
    "customer_age": (0, 120),
    "nps_score": (0, 10),
    "csat_internal_score": (0, 10),
    "repeat_purchase_30d": (0, 1),
    "delivery_delay_days": (0, np.inf),
    "delivery_time_days": (0, np.inf),
    "order_value": (0, np.inf),
}


def load_raw_data(path: str) -> pd.DataFrame:
    """Carrega a exportação bruta em CSV.

    Args:
        path: Caminho para desafio_nps_fase_1.csv.

    Returns:
        DataFrame bruto, uma linha por pedido.
    """
    return pd.read_csv(path)


def validate_data(df: pd.DataFrame) -> Dict[str, object]:
    """Executa verificações de qualidade dos dados (completude, consistência, validade, unicidade).

    Reflete as cinco dimensões de qualidade de dados.

    Args:
        df: DataFrame bruto.

    Returns:
        Dicionário resumindo o relatório de qualidade.
    """
    report: Dict[str, object] = {}
    report["shape"] = df.shape
    report["missing_total"] = int(df.isna().sum().sum())
    report["missing_by_column"] = df.isna().sum()[df.isna().sum() > 0].to_dict()
    report["duplicate_rows"] = int(df.duplicated().sum())
    report["id_uniqueness"] = {c: int(df[c].nunique()) for c in ID_COLS if c in df}

    # Validação: conta valores fora da faixa de negócio esperada.
    out_of_range = {}
    for col, (low, high) in VALID_RANGES.items():
        if col in df.columns:
            mask = (df[col] < low) | (df[col] > high)
            n = int(mask.sum())
            if n:
                out_of_range[col] = n
    report["out_of_range"] = out_of_range
    return report


def nps_segment(score: pd.Series) -> pd.Series:
    """Mapeia uma nota de NPS (0-10) para o segmento padrão.

    Faixas: Detrator (< 7), Neutro (7-8.99), Promotor (>= 9).

    Args:
        score: Série com as notas de NPS.

    Returns:
        Série com os rótulos de categoria.
    """
    conditions = [score < 7, score < 9]
    choices = ["Detrator", "Neutro"]
    return pd.Series(np.select(conditions, choices, default="Promotor"), index=score.index)


def add_target_features(df: pd.DataFrame) -> pd.DataFrame:
    """Adiciona colunas-alvo derivadas usadas pela EDA e pela modelagem.

    Adiciona:
        nps_category: Detrator / Neutro / Promotor.
        is_detractor: 1 quando nps_score < 7 (alvo de classificação).

    Args:
        df: DataFrame contendo nps_score.

    Returns:
        DataFrame com as colunas extras (cópia).
    """
    df = df.copy()
    df["nps_category"] = nps_segment(df[TARGET])
    df["is_detractor"] = (df[TARGET] < 7).astype(int)
    return df


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica as etapas de limpeza.

    A exportação bruta não possui valores ausentes nem duplicatas, então a limpeza
    é leve: remove linhas exatamente duplicadas (idempotente) e reinicia o índice.
    A função foi escrita de forma defensiva para que o pipeline continue correto em
    futuras atualizações dos dados.

    Args:
        df: DataFrame bruto (ou validado).

    Returns:
        DataFrame limpo.
    """
    df = df.drop_duplicates().reset_index(drop=True)
    return df


def build_processed_dataset(raw_path: str, out_path: str) -> pd.DataFrame:
    """Preparação ponta a ponta: carregar -> limpar -> adicionar alvos -> persistir.

    Args:
        raw_path: Caminho para o CSV bruto.
        out_path: Onde gravar o CSV processado.

    Returns:
        O DataFrame processado.
    """
    df = load_raw_data(raw_path)
    df = clean_data(df)
    df = add_target_features(df)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    df.to_csv(out_path, index=False)
    return df


if __name__ == "__main__":
    # Permite executar a etapa de preparação pela linha de comando.
    # Os caminhos vêm do módulo de configuração central (config.py).
    raw = str(RAW_DATA_FILE)
    out = str(PROCESSED_DATA_FILE)
    data = load_raw_data(raw)
    print("Relatório de qualidade:", validate_data(data))
    processed = build_processed_dataset(raw, out)
    print(f"Dataset processado salvo em {out} com shape {processed.shape}")
