"""
model.py
--------
Pipeline de modelagem preditiva para o Tech Challenge de NPS Preditivo.

Implementa as fases "Modelagem" e "Avaliação" do CRISP-DM com dois enquadramentos
complementares da mesma pergunta de negócio -- "conseguimos antecipar a insatisfação
a partir de dados operacionais, antes da pesquisa de NPS?":

  * Regressão      -> prevê o nps_score contínuo (RMSE / MAE / R2).
  * Classificação  -> prevê is_detractor = nps_score < 7 (precisão / recall / AUC).

Seguimos deliberadamente o princípio "do simples ao complexo": primeiro um baseline
interpretável linear/logístico e depois um Random Forest. As colunas de vazamento
(repeat_purchase_30d, csat_internal_score) são excluídas do conjunto de features.
"""

from __future__ import annotations

import json
import os
from typing import Dict, Tuple

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    precision_score,
    r2_score,
    recall_score,
    roc_auc_score,
    roc_curve,
    root_mean_squared_error,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from nps.config import (
    FIGURES_DIR,
    MODELS_DIR,
    PROCESSED_DATA_FILE,
)
from nps.data_prep import CATEGORICAL_FEATURES, NUMERIC_FEATURES, TARGET

RANDOM_STATE = 42
TEST_SIZE = 0.2
CV_FOLDS = 5


def build_preprocessor() -> ColumnTransformer:
    """Padroniza as features numéricas e aplica one-hot encoding na região.

    A padronização é necessária para o baseline linear/logístico; é inofensiva para
    os modelos de árvore, então um único preprocessador é reutilizado em todos os
    estimadores.
    """
    return ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), NUMERIC_FEATURES),
            ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
        ]
    )


def get_features_targets(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series, pd.Series]:
    """Separa o dataframe na matriz de features e nos dois alvos.

    Returns:
        X: features operacionais (colunas de vazamento já excluídas por construção).
        y_reg: nps_score contínuo.
        y_clf: is_detractor binário.
    """
    x = df[NUMERIC_FEATURES + CATEGORICAL_FEATURES].copy()
    y_reg = df[TARGET].copy()
    y_clf = df["is_detractor"].copy()
    return x, y_reg, y_clf


# --------------------------------------------------------------------------- #
# Regressão
# --------------------------------------------------------------------------- #
def train_regression(x: pd.DataFrame, y: pd.Series) -> Dict[str, object]:
    """Treina e avalia os modelos de regressão da nota de NPS."""
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=TEST_SIZE, random_state=RANDOM_STATE
    )
    models = {
        "LinearRegression": LinearRegression(),
        "RandomForestRegressor": RandomForestRegressor(
            n_estimators=300, random_state=RANDOM_STATE, n_jobs=-1
        ),
    }
    results: Dict[str, object] = {}
    fitted = {}
    for name, est in models.items():
        pipe = Pipeline([("prep", build_preprocessor()), ("model", est)])
        pipe.fit(x_train, y_train)
        pred = pipe.predict(x_test)
        cv_r2 = cross_val_score(pipe, x_train, y_train, cv=CV_FOLDS, scoring="r2")
        results[name] = {
            "rmse": round(float(root_mean_squared_error(y_test, pred)), 3),
            "mae": round(float(mean_absolute_error(y_test, pred)), 3),
            "r2": round(float(r2_score(y_test, pred)), 3),
            "cv_r2_mean": round(float(cv_r2.mean()), 3),
            "cv_r2_std": round(float(cv_r2.std()), 3),
        }
        fitted[name] = pipe
    # Escolhe o melhor modelo pelo R2 de validação cruzada (em empate, favorece o mais simples).
    best_name = max(results, key=lambda n: results[n]["cv_r2_mean"])
    return {
        "metrics": results,
        "fitted": fitted,
        "split": (x_train, x_test, y_train, y_test),
        "best_name": best_name,
    }


# --------------------------------------------------------------------------- #
# Classificação
# --------------------------------------------------------------------------- #
def train_classification(x: pd.DataFrame, y: pd.Series) -> Dict[str, object]:
    """Treina e avalia os modelos de classificação de risco de detrator."""
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
    )
    models = {
        "LogisticRegression": LogisticRegression(max_iter=1000),
        "RandomForestClassifier": RandomForestClassifier(
            n_estimators=300, random_state=RANDOM_STATE, n_jobs=-1
        ),
    }
    cv = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_STATE)
    results: Dict[str, object] = {}
    fitted = {}
    for name, est in models.items():
        pipe = Pipeline([("prep", build_preprocessor()), ("model", est)])
        pipe.fit(x_train, y_train)
        pred = pipe.predict(x_test)
        proba = pipe.predict_proba(x_test)[:, 1]
        cv_auc = cross_val_score(pipe, x_train, y_train, cv=cv, scoring="roc_auc")
        results[name] = {
            "accuracy": round(float(accuracy_score(y_test, pred)), 3),
            "precision": round(float(precision_score(y_test, pred)), 3),
            "recall": round(float(recall_score(y_test, pred)), 3),
            "f1": round(float(f1_score(y_test, pred)), 3),
            "roc_auc": round(float(roc_auc_score(y_test, proba)), 3),
            "cv_auc_mean": round(float(cv_auc.mean()), 3),
            "cv_auc_std": round(float(cv_auc.std()), 3),
        }
        fitted[name] = pipe
    # Escolhe o melhor modelo pela AUC de validação cruzada (em empate, favorece o mais simples).
    best_name = max(results, key=lambda n: results[n]["cv_auc_mean"])
    return {
        "metrics": results,
        "fitted": fitted,
        "split": (x_train, x_test, y_train, y_test),
        "best_name": best_name,
    }


# --------------------------------------------------------------------------- #
# Funções auxiliares de interpretação
# --------------------------------------------------------------------------- #
def feature_importance(pipe: Pipeline) -> pd.Series:
    """Retorna as importâncias das features da árvore com nomes legíveis."""
    names = pipe.named_steps["prep"].get_feature_names_out()
    names = [n.split("__", 1)[-1] for n in names]  # remove o prefixo do transformador
    importances = pipe.named_steps["model"].feature_importances_
    return pd.Series(importances, index=names).sort_values(ascending=False)


def linear_coefficients(pipe: Pipeline) -> pd.Series:
    """Retorna os coeficientes padronizados da regressão linear (impacto por 1 desvio-padrão)."""
    names = pipe.named_steps["prep"].get_feature_names_out()
    names = [n.split("__", 1)[-1] for n in names]
    coefs = pipe.named_steps["model"].coef_
    return pd.Series(coefs, index=names).sort_values()


# --------------------------------------------------------------------------- #
# Figuras
# --------------------------------------------------------------------------- #
def _save(fig, outdir: str, name: str) -> str:
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, name)
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_model_coefficients(pipe: Pipeline, outdir: str) -> str:
    """Gráfico de barras dos coeficientes padronizados da regressão linear (visão principal).

    Impacto honesto e com sinal de cada driver sobre a nota de NPS; alinhado com o
    ranking de Spearman da EDA.
    """
    coefs = linear_coefficients(pipe)
    coefs = coefs.reindex(coefs.abs().sort_values(ascending=False).index).head(12).iloc[::-1]
    fig, ax = plt.subplots(figsize=(9, 6))
    colors = ["#d64550" if v < 0 else "#2e9e6b" for v in coefs.values]
    ax.barh(coefs.index, coefs.values, color=colors)
    ax.axvline(0, color="#333", linewidth=0.8)
    ax.set_title("Impacto de cada fator no NPS (modelo linear)")
    ax.set_xlabel("Variação no NPS por +1 desvio-padrão")
    return _save(fig, outdir, "model_coefficients.png")


def plot_feature_importance(pipe: Pipeline, outdir: str) -> str:
    """Gráfico de barras das importâncias de features do Random Forest (visão de transparência).

    Exibido ao lado dos coeficientes lineares para evidenciar que a importância das
    árvores infla variáveis de alta cardinalidade, porém pouco informativas (ex.: order_value).
    """
    imp = feature_importance(pipe).head(10).iloc[::-1]
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh(imp.index, imp.values, color="#7a7a7a")
    ax.set_title("Importância no Random Forest (comparação)")
    ax.set_xlabel("Importância (Random Forest)")
    return _save(fig, outdir, "feature_importance.png")


def plot_confusion(pipe: Pipeline, x_test, y_test, outdir: str) -> str:
    """Matriz de confusão do classificador de detrator."""
    pred = pipe.predict(x_test)
    cm = confusion_matrix(y_test, pred)
    fig, ax = plt.subplots(figsize=(6, 5))
    ConfusionMatrixDisplay(cm, display_labels=["Não detrator", "Detrator"]).plot(
        ax=ax, cmap="Blues", colorbar=False
    )
    ax.set_title("Matriz de confusão (detrator)")
    return _save(fig, outdir, "confusion_matrix.png")


def plot_roc(pipe: Pipeline, x_test, y_test, outdir: str) -> str:
    """Curva ROC do classificador de detrator."""
    proba = pipe.predict_proba(x_test)[:, 1]
    fpr, tpr, _ = roc_curve(y_test, proba)
    auc = roc_auc_score(y_test, proba)
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.plot(fpr, tpr, color="#3b6ea5", linewidth=2.5, label=f"AUC = {auc:.2f}")
    ax.plot([0, 1], [0, 1], color="#999", linestyle="--")
    ax.set_title("Curva ROC")
    ax.set_xlabel("Falso positivo")
    ax.set_ylabel("Verdadeiro positivo")
    ax.legend(loc="lower right")
    return _save(fig, outdir, "roc_curve.png")


# --------------------------------------------------------------------------- #
# Orquestração
# --------------------------------------------------------------------------- #
def run_pipeline(
    processed_path: str = str(PROCESSED_DATA_FILE),
    models_dir: str = str(MODELS_DIR),
    figures_dir: str = str(FIGURES_DIR),
) -> Dict[str, object]:
    """Treina os dois modelos, persiste artefatos e figuras e retorna um resumo.

    Por padrão usa os caminhos centralizados no config.py; podem ser sobrescritos.
    """
    df = pd.read_csv(processed_path)
    x, y_reg, y_clf = get_features_targets(df)

    reg = train_regression(x, y_reg)
    clf = train_classification(x, y_clf)

    # Melhores estimadores, escolhidos pela métrica de validação cruzada.
    best_reg = reg["fitted"][reg["best_name"]]
    best_clf = clf["fitted"][clf["best_name"]]

    os.makedirs(models_dir, exist_ok=True)
    joblib.dump(best_reg, os.path.join(models_dir, "nps_regressor.pkl"))
    joblib.dump(best_clf, os.path.join(models_dir, "detractor_classifier.pkl"))

    # Interpretação: coeficientes lineares (principal, honesto) + importância do RF (comparação).
    linear_coefs = linear_coefficients(reg["fitted"]["LinearRegression"])
    rf_importance = feature_importance(clf["fitted"]["RandomForestClassifier"])

    summary = {
        "best_regression": reg["best_name"],
        "best_classification": clf["best_name"],
        "regression": reg["metrics"],
        "classification": clf["metrics"],
        "linear_coefficients": linear_coefs.round(4).to_dict(),
        "rf_importance": rf_importance.round(4).to_dict(),
        "n_features": int(x.shape[1]),
        "excluded_leakage": ["repeat_purchase_30d", "csat_internal_score"],
    }
    with open(os.path.join(models_dir, "metrics.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=2)

    # Figuras de avaliação / interpretação.
    _, x_test, _, y_test = clf["split"]
    plot_model_coefficients(reg["fitted"]["LinearRegression"], figures_dir)
    plot_feature_importance(clf["fitted"]["RandomForestClassifier"], figures_dir)
    plot_confusion(best_clf, x_test, y_test, figures_dir)
    plot_roc(best_clf, x_test, y_test, figures_dir)

    # Relatório de classificação (texto) para a classe positiva de detrator.
    pred = best_clf.predict(x_test)
    summary["classification_report"] = classification_report(
        y_test, pred, target_names=["Não detrator", "Detrator"]
    )
    return summary


if __name__ == "__main__":
    # Permite executar o pipeline de modelagem pela linha de comando.
    # Os caminhos vêm do config.py (data/processed, models, reports/figures).
    out = run_pipeline()
    print(json.dumps({k: v for k, v in out.items() if k != "classification_report"},
                     ensure_ascii=False, indent=2))
    print("\n", out["classification_report"])
