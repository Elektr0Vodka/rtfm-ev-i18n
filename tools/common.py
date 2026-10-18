"""Shared helpers for the rtfm-ev-i18n tools.

Repo entry shapes (see CONTRIBUTING.md):

    "key": "text"                                  plain string, human-approved
    "key": {"value": "text", "_ai": true}          string with review flags
    "key": {"plural": {"one": .., "other": ..}}    plural, optional review flags
    "key": null                                    not translated yet

en.json only uses plain strings and flag-free plurals.

RTFM-EV's runtime format (frontend/src/i18n/locales/*.json) is plainer:
a string, or a bare plural object {"one": .., "other": ..}.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOCALES_DIR = ROOT / "locales"
LANGUAGES_FILE = ROOT / "languages.json"
SOURCE_LOCALE = "en"

PLURAL_CATEGORIES = ("zero", "one", "two", "few", "many", "other")
FLAG_FIELDS = ("_ai", "_human", "_seeded")
PLACEHOLDER_RE = re.compile(r"\{(\w+)\}")


def load_languages() -> dict[str, dict]:
    return json.loads(LANGUAGES_FILE.read_text(encoding="utf-8"))


def locale_path(code: str) -> Path:
    return LOCALES_DIR / f"{code}.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def write_json(path: Path, data: dict) -> bool:
    """Write data as JSON; return True when the file content changed."""
    text = dump_json(data)
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return False
    path.write_text(text, encoding="utf-8", newline="\n")
    return True


def entries(catalog: dict) -> dict:
    """The catalog without its _meta block."""
    return {k: v for k, v in catalog.items() if k != "_meta"}


def is_plural(entry) -> bool:
    return isinstance(entry, dict) and "plural" in entry


def forms(entry) -> list[str]:
    """Every text in an entry (one for a string, one per plural form)."""
    if entry is None:
        return []
    if isinstance(entry, str):
        return [entry]
    if "plural" in entry:
        return list(entry["plural"].values())
    return [entry["value"]]


def placeholders(entry) -> set[str]:
    found: set[str] = set()
    for text in forms(entry):
        found.update(PLACEHOLDER_RE.findall(text))
    return found


def status(entry) -> str:
    """One of: missing, ai, human."""
    if entry is None:
        return "missing"
    if isinstance(entry, dict) and entry.get("_ai") and not entry.get("_human"):
        return "ai"
    return "human"


def from_app(entry):
    """Runtime entry -> repo entry (no review flags)."""
    if isinstance(entry, dict):
        return {"plural": dict(entry)}
    return entry


def to_app(entry):
    """Repo entry -> runtime entry; None for untranslated."""
    if entry is None or isinstance(entry, str):
        return entry
    if "plural" in entry:
        return dict(entry["plural"])
    return entry["value"]
