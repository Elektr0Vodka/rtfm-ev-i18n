"""Regenerate the status table in README.md between the status markers."""

from __future__ import annotations

import sys

from common import ROOT, SOURCE_LOCALE, entries, load_json, load_languages, locale_path, status

BEGIN, END = "<!-- status:begin -->", "<!-- status:end -->"


def build_table() -> str:
    languages = load_languages()
    total = len(entries(load_json(locale_path(SOURCE_LOCALE))))
    rows = [
        "| Language | Code | Completion | Human | AI drafted | Outdated | Missing | In app | Managed by |",
        "|----------|------|-----------:|------:|-----------:|---------:|--------:|:------:|------------|",
    ]
    for code, info in languages.items():
        counts = {"human": 0, "ai": 0, "stale": 0, "missing": 0}
        for value in entries(load_json(locale_path(code))).values():
            counts[status(value)] += 1
        done = counts["human"] + counts["ai"] + counts["stale"]
        pct = done * 100 // total if total else 0
        rows.append(
            f"| {info['name']} | `{code}` | {pct}% | {counts['human']} | {counts['ai']} | {counts['stale']} "
            f"| {counts['missing']} | {'yes' if info['in_app'] else 'no'} | {info['managed_by']} |"
        )
    return "\n".join(rows)


def main() -> int:
    readme = ROOT / "README.md"
    text = readme.read_text(encoding="utf-8")
    start, end = text.index(BEGIN) + len(BEGIN), text.index(END)
    new = text[:start] + "\n\n" + build_table() + "\n\n" + text[end:]
    if new != text:
        readme.write_text(new, encoding="utf-8", newline="\n")
        print("README.md status table updated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
