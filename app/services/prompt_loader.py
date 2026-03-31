from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
PROMPTS_DIR = BASE_DIR / "prompts"

PROMPT_FILES = {
    "translator": "translator.txt",
    "clarifier": "clarifier.txt",
    "reformulator": "reformulator.txt",
}


def load_prompt(name: str) -> str:
    filename = PROMPT_FILES.get(name)
    if not filename:
        raise ValueError(f"Prompt inconnu: {name}")
    path = PROMPTS_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Prompt introuvable: {path}")
    return path.read_text(encoding="utf-8").strip()
