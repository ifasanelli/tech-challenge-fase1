# NPS Preditivo — Tech Challenge Fase 1

<a target="_blank" href="https://cookiecutter-data-science.drivendata.org/">
    <img src="https://img.shields.io/badge/CCDS-Project%20template-328F97?logo=cookiecutter" />
</a>

Transformar **dados operacionais** de um e-commerce (pedidos, logística e atendimento) em
**insights acionáveis** sobre satisfação do cliente — e em um modelo que **antecipa o NPS antes
da pesquisa**, permitindo ação preventiva.

> **Resultado em uma frase:** a satisfação é definida pela **operação**, não pelo perfil do
> cliente. O **atraso na entrega** é o fator nº 1 (cada dia de atraso ≈ −1 ponto de NPS), seguido
> por **reclamações** e **atrito no atendimento**. O NPS atual é **−80** (84% detratores).

---

## 1. Objetivo do projeto

Responder, com pensamento analítico e *storytelling* com dados:
1. **Entendimento do negócio** — qual o problema, por que o NPS importa, quem se beneficia.
2. **Definição da target** — qual variável representa a satisfação e como usá-la sem vazamento.
3. **EDA com foco em negócio** — quais fatores são críticos, o que gera detratores, onde está o
   ponto de ruptura, e qual o perfil de NPS alto/baixo.
4. **Modelo preditivo (opcional)** — antecipar o detrator a partir de dados operacionais.

## 2. Descrição da base de dados

`data/raw/desafio_nps_fase_1.csv` — **2.500 pedidos**, 19 colunas, **sem valores ausentes e sem
duplicatas**. Um pedido por linha.

| Grupo | Variáveis |
|---|---|
| Identificadores | `customer_id`, `order_id` |
| Cliente | `customer_age`, `customer_region`, `customer_tenure_months` |
| Pedido | `order_value`, `items_quantity`, `discount_value`, `payment_installments` |
| Logística | `delivery_time_days`, `delivery_delay_days`, `freight_value`, `delivery_attempts` |
| Atendimento | `customer_service_contacts`, `resolution_time_days`, `complaints_count` |
| Satisfação / resultado | **`nps_score`** (alvo, 0–10), `csat_internal_score`, `repeat_purchase_30d` |

> `repeat_purchase_30d` e `csat_internal_score` **não** são usados como entrada do modelo
> (vazamento — ver `reports/02_definicao_target.md`).

## 3. Metodologia (CRISP-DM)

| Fase CRISP-DM | Onde está |
|---|---|
| Business Understanding | `reports/01_entendimento_negocio.md` |
| Target / Data Understanding | `reports/02_definicao_target.md` |
| Data Prep + EDA | `nps/data_prep.py`, `nps/eda.py`, `notebooks/01_eda.ipynb`, `reports/03_eda_insights.md` |
| Modeling + Evaluation | `nps/model.py`, `notebooks/02_modelagem.ipynb`, `reports/04_estrategia_modelo.md` |

- **EDA**: classificação de variáveis → qualidade de dados → univariada → bivariada →
  multivariada (correlação de **Spearman**) → registro de hipóteses.
- **Modelagem**: *“simples antes de complexo”* — baseline interpretável (Regressão Linear /
  Logística) comparado a Random Forest; *split* 80/20 + validação cruzada de 5 folds.

## 4. Principais resultados

**EDA — o que move o NPS (Spearman):** `delivery_delay_days` −0,59 · `complaints_count` −0,49 ·
`customer_service_contacts` −0,34 · `resolution_time_days` −0,19 · (demais ≈ 0).

**Modelo (vencedor = modelo simples, mais interpretável):**

| Tarefa | Modelo | Métrica principal |
|---|---|---|
| Regressão (`nps_score`) | Regressão Linear | R² 0,55 · RMSE 1,69 · MAE 1,33 |
| Classificação (`is_detractor`) | Regressão Logística | AUC 0,87 (CV 0,90) · Recall 0,96 |

## 5. Estrutura do repositório

```
tech-challenge-fase1/
├── README.md                 # este arquivo
├── Makefile                  # comandos de conveniência (make data, make figures, make train)
├── requirements.txt          # dependências (ambiente reproduzível)
├── pyproject.toml            # metadados do pacote nps e config de ferramentas
├── data/
│   ├── raw/                  # base original (desafio_nps_fase_1.csv)
│   └── processed/            # base tratada (gerada: nps_clean.csv)
├── notebooks/
│   ├── 01_eda.ipynb          # análise exploratória (executado, com saídas)
│   └── 02_modelagem.ipynb    # pipeline do modelo (executado, com saídas)
├── nps/
│   ├── config.py             # caminhos centralizados do projeto (lê o .env)
│   ├── data_prep.py          # carga, validação, limpeza, features de alvo
│   ├── eda.py                # estatísticas e gráficos reutilizáveis
│   └── model.py              # features, split, treino, avaliação, persistência
├── models/                   # modelos .pkl + metrics.json (gerados)
└── reports/
    ├── 01_entendimento_negocio.md
    ├── 02_definicao_target.md
    ├── 03_eda_insights.md    # linguagem para gestão (não técnica)
    ├── 04_estrategia_modelo.md
    └── figures/              # gráficos .png (gerados)
```

## 6. Como reproduzir

Requisitos: Python 3.13 (ver `requires-python` no `pyproject.toml`).

```bash
# 1) Ambiente
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt                       # instala as libs + o pacote nps (-e .)

# 2) Opção A — Makefile (caminho recomendado)
make data        # -> data/processed/nps_clean.csv (+ relatório de qualidade)
make figures     # -> reports/figures/* (8 figuras de EDA)
make train       # -> models/*.pkl, models/metrics.json, reports/figures/* (avaliação)

# 2) Opção B — scripts diretos
python nps/data_prep.py      # -> data/processed/nps_clean.csv
python nps/eda.py            # -> figuras de EDA
python nps/model.py          # -> models/*.pkl, models/metrics.json, figuras de avaliação

# 2) Opção C — notebooks (de cima a baixo)
jupyter lab                  # abrir e executar notebooks/01_eda.ipynb e 02_modelagem.ipynb
```

Os notebooks recriam todas as figuras de `reports/figures/` e os artefatos de `models/`. Tudo
é determinístico (`random_state=42`).

## 7. Convenções

- **Idioma:** relatórios, README e **comentários do código em português**; **nomes de colunas
  em inglês**, seguindo o dicionário de dados original.
- **Caminhos centralizados:** todos os caminhos do projeto são derivados de `nps/config.py`
  (que lê o `.env`), evitando caminhos fixos espalhados pelo código.
- **Reprodutibilidade:** dependências fixadas em `requirements.txt`; pré-processamento e modelo
  encapsulados em `Pipeline` do scikit-learn (sem vazamento entre treino e teste).
