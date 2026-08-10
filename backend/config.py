from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parents[1]

@dataclass(frozen=True)
class Settings:
    app_name: str = "Ethical Horizon Intelligence v3"
    db_path: Path = Path(os.getenv("EH_DB_PATH", BASE_DIR / "data" / "ethical_horizon.db"))
    root_path: str = os.getenv("EH_ROOT_PATH", "").rstrip("/")
    request_timeout: float = float(os.getenv("EH_REQUEST_TIMEOUT", "25"))
    ncbi_email: str = os.getenv("NCBI_EMAIL", "")
    ncbi_api_key: str = os.getenv("NCBI_API_KEY", "")
    openalex_api_key: str = os.getenv("OPENALEX_API_KEY", "")
    crossref_mailto: str = os.getenv("CROSSREF_MAILTO", "")
    default_max_results: int = int(os.getenv("EH_DEFAULT_MAX_RESULTS", "25"))
    max_results_cap: int = int(os.getenv("EH_MAX_RESULTS_CAP", "100"))

settings = Settings()
