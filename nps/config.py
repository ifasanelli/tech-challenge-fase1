"""
config.py
---------
Configuração central de caminhos do projeto.

Segue a convenção do cookiecutter-data-science: todos os caminhos do projeto
são derivados de uma única raiz (``PROJ_ROOT``) e expostos como constantes, para
que módulos, scripts e notebooks nunca precisem montar caminhos "na mão".

Variáveis de ambiente do arquivo ``.env`` são carregadas automaticamente ao
importar este módulo.
"""

from pathlib import Path

from dotenv import load_dotenv

# Carrega variáveis de ambiente do .env (se existir), tornando-as acessíveis
# via os.environ em qualquer módulo que importe este config.
load_dotenv()

# Raiz do projeto: dois níveis acima deste arquivo
# (nps/config.py -> nps/ -> raiz do projeto).
PROJ_ROOT = Path(__file__).resolve().parents[1]

# --------------------------------------------------------------------------- #
# Diretórios de dados (fluxo em camadas do CRISP-DM / cookiecutter-data-science)
# --------------------------------------------------------------------------- #
DATA_DIR = PROJ_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
INTERIM_DATA_DIR = DATA_DIR / "interim"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
EXTERNAL_DATA_DIR = DATA_DIR / "external"

# --------------------------------------------------------------------------- #
# Demais diretórios do projeto
# --------------------------------------------------------------------------- #
MODELS_DIR = PROJ_ROOT / "models"
REPORTS_DIR = PROJ_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

# --------------------------------------------------------------------------- #
# Arquivos de dados específicos deste desafio
# --------------------------------------------------------------------------- #
RAW_DATA_FILE = RAW_DATA_DIR / "desafio_nps_fase_1.csv"
PROCESSED_DATA_FILE = PROCESSED_DATA_DIR / "nps_clean.csv"
