"""
eda.py
------
Funções reutilizáveis de análise exploratória de dados (estatísticas + gráficos).

As funções calculam as estatísticas voltadas ao negócio e salvam as figuras
usadas no notebook de EDA e nos relatórios.
"""

from __future__ import annotations

import os
from typing import Dict, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from tech_challenge_fase1.config import FIGURES_DIR, PROCESSED_DATA_FILE
from tech_challenge_fase1.data_prep import NUMERIC_FEATURES, TARGET

# Diretório padrão das figuras (definido no config central do projeto).
DEFAULT_FIGURES_DIR = str(FIGURES_DIR)

# Código de cores padrão do NPS: vermelho = detrator, âmbar = neutro, verde = promotor.
SEGMENT_ORDER = ["Detrator", "Neutro", "Promotor"]
SEGMENT_COLORS = {"Detrator": "#d64550", "Neutro": "#e8a33d", "Promotor": "#2e9e6b"}
DETRACTOR_LINE = 7.0  # notas abaixo deste valor são de detratores


def set_style() -> None:
    sns.set_theme(style="whitegrid", context="talk")
    plt.rcParams["figure.autolayout"] = True
    plt.rcParams["axes.titleweight"] = "bold"


def compute_nps_metric(df: pd.DataFrame) -> float:
    """Retorna a métrica principal de NPS (% promotores - % detratores), na escala 0-100."""
    seg = df["nps_category"]
    pct_promoter = (seg == "Promotor").mean()
    pct_detractor = (seg == "Detrator").mean()
    return round((pct_promoter - pct_detractor) * 100, 1)


def segment_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """Contagem e percentual de clientes por segmento de NPS."""
    counts = df["nps_category"].value_counts().reindex(SEGMENT_ORDER).fillna(0).astype(int)
    pct = (counts / counts.sum() * 100).round(1)
    return pd.DataFrame({"count": counts, "pct": pct})


def spearman_with_target(df: pd.DataFrame, features: List[str] | None = None) -> pd.Series:
    """Correlação de Spearman de cada feature com a nota de NPS, ordenada.

    Spearman é preferida por ser monotônica e robusta a outliers.
    """
    features = features or NUMERIC_FEATURES
    corr = df[features + [TARGET]].corr(method="spearman")[TARGET].drop(TARGET)
    return corr.sort_values()


def mean_nps_by(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """NPS médio e contagem de clientes para cada valor de uma coluna discreta."""
    return df.groupby(col)[TARGET].agg(["mean", "count"]).round(2)


# --------------------------------------------------------------------------- #
# Figuras
# --------------------------------------------------------------------------- #
def _save(fig, outdir: str, name: str) -> str:
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, name)
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_nps_distribution(df: pd.DataFrame, outdir: str = DEFAULT_FIGURES_DIR) -> str:
    """Histograma da nota de NPS com o limite de detrator destacado."""
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.histplot(df[TARGET], bins=22, kde=True, color="#3b6ea5", ax=ax)
    ax.axvline(DETRACTOR_LINE, color="#d64550", linestyle="--", linewidth=2)
    ax.text(DETRACTOR_LINE - 0.1, ax.get_ylim()[1] * 0.9, "Detratores (< 7)",
            ha="right", color="#d64550", fontsize=12)
    ax.set_title("Distribuição do NPS (a maioria dos clientes é detratora)")
    ax.set_xlabel("Nota de NPS (0-10)")
    ax.set_ylabel("Número de clientes")
    return _save(fig, outdir, "nps_distribution.png")


def plot_segment_bar(df: pd.DataFrame, outdir: str = DEFAULT_FIGURES_DIR) -> str:
    """Gráfico de barras da proporção de detratores / neutros / promotores."""
    dist = segment_distribution(df)
    fig, ax = plt.subplots(figsize=(8, 5))
    colors = [SEGMENT_COLORS[s] for s in dist.index]
    ax.bar(dist.index, dist["pct"], color=colors)
    for i, (pct, cnt) in enumerate(zip(dist["pct"], dist["count"])):
        ax.text(i, pct + 1, f"{pct}%\n({cnt})", ha="center", fontsize=12)
    ax.set_title(f"Composição do NPS  |  NPS = {compute_nps_metric(df):.0f}")
    ax.set_ylabel("% de clientes")
    ax.set_ylim(0, 100)
    return _save(fig, outdir, "nps_segments.png")


def plot_nps_by_delay(df: pd.DataFrame, outdir: str = DEFAULT_FIGURES_DIR) -> str:
    """NPS médio por dias de atraso na entrega -- o ponto de ruptura da experiência."""
    g = mean_nps_by(df, "delivery_delay_days")
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(g.index, g["mean"], marker="o", color="#3b6ea5", linewidth=2.5)
    ax.axhline(DETRACTOR_LINE, color="#d64550", linestyle="--", linewidth=1.5)
    ax.text(g.index.max(), DETRACTOR_LINE + 0.1, "limite de detrator (7)",
            ha="right", color="#d64550", fontsize=11)
    ax.set_title("Ponto de ruptura: cada dia de atraso derruba o NPS")
    ax.set_xlabel("Dias de atraso na entrega")
    ax.set_ylabel("NPS médio")
    ax.set_ylim(0, 10)
    return _save(fig, outdir, "nps_by_delay.png")


def plot_mean_nps_bar(df: pd.DataFrame, col: str, title: str, xlabel: str,
                      name: str, outdir: str = DEFAULT_FIGURES_DIR) -> str:
    """Gráfico de barras genérico do NPS médio por uma coluna operacional discreta."""
    g = mean_nps_by(df, col)
    fig, ax = plt.subplots(figsize=(9, 5))
    bar_colors = ["#2e9e6b" if v >= DETRACTOR_LINE else "#d64550" for v in g["mean"]]
    ax.bar(g.index.astype(str), g["mean"], color=bar_colors)
    ax.axhline(DETRACTOR_LINE, color="#555", linestyle="--", linewidth=1)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("NPS médio")
    ax.set_ylim(0, 10)
    return _save(fig, outdir, name)


def plot_driver_ranking(df: pd.DataFrame, outdir: str = DEFAULT_FIGURES_DIR) -> str:
    """Barras horizontais da correlação de Spearman de cada driver operacional com o NPS."""
    corr = spearman_with_target(df)
    fig, ax = plt.subplots(figsize=(9, 6))
    colors = ["#d64550" if v < 0 else "#2e9e6b" for v in corr.values]
    ax.barh(corr.index, corr.values, color=colors)
    ax.axvline(0, color="#333", linewidth=0.8)
    ax.set_title("O que move o NPS (correlação de Spearman)")
    ax.set_xlabel("Correlação com o NPS (-1 a +1)")
    return _save(fig, outdir, "driver_ranking.png")


def plot_correlation_heatmap(df: pd.DataFrame, outdir: str = DEFAULT_FIGURES_DIR) -> str:
    """Mapa de calor da correlação de Spearman entre os drivers operacionais e o NPS."""
    cols = NUMERIC_FEATURES + [TARGET]
    corr = df[cols].corr(method="spearman")
    fig, ax = plt.subplots(figsize=(12, 10))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="RdBu_r", center=0,
                vmin=-1, vmax=1, ax=ax, annot_kws={"size": 8})
    ax.set_title("Matriz de correlação (Spearman)")
    return _save(fig, outdir, "correlation_heatmap.png")


def plot_nps_by_region(df: pd.DataFrame, outdir: str = DEFAULT_FIGURES_DIR) -> str:
    """Boxplot do NPS por região."""
    order = df.groupby("customer_region")[TARGET].median().sort_values().index
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.boxplot(data=df, x="customer_region", y=TARGET, order=order,
                color="#3b6ea5", ax=ax)
    ax.set_title("NPS por região (diferença pequena)")
    ax.set_xlabel("Região")
    ax.set_ylabel("Nota de NPS")
    return _save(fig, outdir, "nps_by_region.png")


def generate_all_figures(df: pd.DataFrame, outdir: str = DEFAULT_FIGURES_DIR) -> Dict[str, str]:
    """Gera todas as figuras da EDA e retorna um mapa nome -> caminho."""
    set_style()
    paths = {
        "nps_distribution": plot_nps_distribution(df, outdir),
        "nps_segments": plot_segment_bar(df, outdir),
        "nps_by_delay": plot_nps_by_delay(df, outdir),
        "nps_by_complaints": plot_mean_nps_bar(
            df, "complaints_count", "Mais reclamações, menos satisfação",
            "Número de reclamações", "nps_by_complaints.png", outdir),
        "nps_by_contacts": plot_mean_nps_bar(
            df, "customer_service_contacts", "Cada contato com o SAC custa NPS",
            "Contatos com o atendimento", "nps_by_contacts.png", outdir),
        "driver_ranking": plot_driver_ranking(df, outdir),
        "correlation_heatmap": plot_correlation_heatmap(df, outdir),
        "nps_by_region": plot_nps_by_region(df, outdir),
    }
    return paths


if __name__ == "__main__":
    # Permite executar a geração das figuras pela linha de comando.
    # Lê o dataset processado e salva todas as figuras em FIGURES_DIR (config.py).
    df = pd.read_csv(PROCESSED_DATA_FILE)
    figuras = generate_all_figures(df)
    print(f"{len(figuras)} figuras geradas em {DEFAULT_FIGURES_DIR}")
    for nome, caminho in figuras.items():
        print(f" - {nome} -> {caminho}")
