"""Load config.toml into a simple nested dict."""
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config.toml"


def load(path: Path = CONFIG_PATH) -> dict:
    if not path.exists():
        raise SystemExit(
            f"Config not found: {path}\n"
            f"Copy config.example.toml to config.toml and fill it in."
        )
    with open(path, "rb") as f:
        return tomllib.load(f)
