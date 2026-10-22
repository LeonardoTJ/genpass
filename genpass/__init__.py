"""Advanced Password Generator package."""

from __future__ import annotations

import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

try:
    __version__ = version("genpass")
except PackageNotFoundError:
    __version__ = "0+uninstalled"

__all__ = ["__version__", "DATA_DIR", "default_wordlists"]


def _resource_dir() -> Path:
    """Directory containing bundled package data (wordlists).

    Works for normal installs, editable installs, and PyInstaller
    ``_MEIPASS`` frozen builds.
    """
    if hasattr(sys, "_MEIPASS"):  # PyInstaller
        return Path(sys._MEIPASS) / "genpass" / "data"
    return Path(__file__).resolve().parent / "data"


DATA_DIR = _resource_dir()


def default_wordlists(language="all") -> list[str]:
    """Resolve all bundled languages by default, or one explicitly selected language."""
    names = {"en": "eff_large_wordlist.txt", "ja": "diceware_jp.txt", "es": "DW-Espanol-1.txt"}
    if language == "all":
        return [str(DATA_DIR / name) for name in names.values()]
    if language not in names:
        raise ValueError(f"Unknown language: {language}")
    return [str(DATA_DIR / names[language])]
