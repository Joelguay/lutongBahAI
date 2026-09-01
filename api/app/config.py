import os
from pathlib import Path

from dotenv import load_dotenv

API_DIR = Path(__file__).resolve().parents[1]
load_dotenv(API_DIR / ".env")

DEFAULT_CLASSES = [
    "Banana",
    "Carrot",
    "Chicken",
    "Eggplant",
    "Egg",
    "Garlic",
    "Onion",
    "Potato",
    "Tomato",
]


def weights_path() -> Path:
    raw = os.getenv("WEIGHTS_PATH", "weights/best.pt")
    path = Path(raw)
    if not path.is_absolute():
        path = API_DIR / path
    return path


def frontend_origins() -> list[str]:
    raw = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


def gemini_model() -> str:
    return os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
