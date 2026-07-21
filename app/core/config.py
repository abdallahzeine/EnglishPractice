from pathlib import Path

APP_NAME = "EnglishPractice"
DATA_DIR = Path.home() / "Documents" / APP_NAME
DB_PATH = DATA_DIR / "Data.db"


def ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
