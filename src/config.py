from pathlib import Path
import os

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data"
POLICY_DIR = DATA_DIR / "airport_policies"
METRICS_FILE = DATA_DIR / "airport_metrics.csv"

CHROMA_DIR = PROJECT_ROOT / ".chroma"

load_dotenv(PROJECT_ROOT / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-3.6-flash"

SUPPORTED_AIRPORTS = ["SFO", "LAX", "JFK"]