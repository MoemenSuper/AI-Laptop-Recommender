import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_FOLDER = PROJECT_ROOT / "data"
FRONTEND_FOLDER = PROJECT_ROOT / "frontend"
INTRO_FOLDER = FRONTEND_FOLDER / "intro"
DASHBOARD_FOLDER = FRONTEND_FOLDER / "dashboard"
ASSETS_FOLDER = FRONTEND_FOLDER / "assets"


@dataclass(frozen=True)
class TechSpecsConfig:
    api_key: str
    api_id: str
    base_url: str = "https://api.techspecs.io/v5"

    @property
    def configured(self):
        return bool(self.api_key and self.api_id)

    @property
    def headers(self):
        return {
            "accept": "application/json",
            "X-API-KEY": self.api_key,
            "X-API-ID": self.api_id,
        }


TECHSPECS_CONFIG = TechSpecsConfig(
    api_key=os.getenv("TECHSPECS_API_KEY", ""),
    api_id=os.getenv("TECHSPECS_API_ID", ""),
    base_url=os.getenv("TECHSPECS_BASE_URL", "https://api.techspecs.io/v5"),
)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_BASE_URL = os.getenv(
    "GROQ_BASE_URL",
    "https://api.groq.com/openai/v1/chat/completions",
)

CSV_FILE_PATH = os.getenv("LAPTOP_CSV_PATH") or str(DATA_FOLDER / "laptop_specs_enhanced.csv")
