"""Validate every locale file. Exit 1 on any error.

Checks:
- each locales/*.json is listed in languages.json, and en.json exists
- JSON schema (schema/locale.schema.json)
- _meta.language matches the file name
- en.json has no nulls and no review flags
- no key that en.json does not have
- a key is a plural in a locale only when it is a plural in en.json
- placeholders ({name}) match en.json; a plural may leave out {count}
- every glossary/do-not-translate.txt term in the English text is kept

Missing keys are fine here (tools/sync_keys.py adds them as null).
"""

from __future__ import annotations

import re
import sys

from jsonschema import Draft7Validator

from common import (
    LOCALES_DIR,
    ROOT,
    SOURCE_LOCALE,
    entries,
    forms,
    is_plural,
    load_json,
    load_languages,
    placeholders,
)

KEEP_TERMS_FILE = ROOT / "glossary" / "do-not-translate.txt"


def load_keep_terms() -> list[tuple[str, re.Pattern]]:
    terms = []
    for line in KEEP_TERMS_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            terms.append((line, re.compile(rf"(?<!\w){re.escape(line)}(?!\w)")))
    return terms


def main() -> int:
    languages = load_languages()
    validator = Draft7Validator(load_json(ROOT / "schema" / "locale.schema.json"))
    keep_terms = load_keep_terms()
    errors: list[str] = []

    files = {p.stem: p for p in sorted(LOCALES_DIR.glob("*.json"))}
    if SOURCE_LOCALE not in files:
        print("error: locales/en.json is missing", file=sys.stderr)
        return 1
    for code in files:
        if code not in languages:
            errors.append(f"locales/{code}.json: not listed in languages.json")

    catalogs = {}
    for code, path in files.items():
        try:
            catalogs[code] = load_json(path)
        except ValueError as exc:
            errors.append(f"locales/{code}.json: invalid JSON: {exc}")
    en = entries(catalogs.get(SOURCE_LOCALE, {}))

    for code, catalog in catalogs.items():
        where = f"locales/{code}.json"
        for err in validator.iter_errors(catalog):
            path = "/".join(str(p) for p in err.absolute_path) or "<root>"
            errors.append(f"{where}: {path}: {err.message[:200]}")
        if catalog.get("_meta", {}).get("language") != code:
            errors.append(f"{where}: _meta.language must be {code!r}")

        for key, value in entries(catalog).items():
            loc = f"{where}: {key}"
            if code == SOURCE_LOCALE:
                if value is None or (isinstance(value, dict) and set(value) != {"plural"}):
                    errors.append(f"{loc}: en.json values must be plain strings or flag-free plurals")
                continue
            if key not in en:
                errors.append(f"{loc}: key does not exist in en.json")
                continue
            if value is None:
                continue
            source = en[key]
            if is_plural(value) != is_plural(source):
                kind = "a plural" if is_plural(source) else "a plain string"
                errors.append(f"{loc}: must be {kind}, like in en.json")
                continue

            want, got = placeholders(source), placeholders(value)
            if is_plural(source):
                want = want - {"count"}
            if got - placeholders(source):
                errors.append(f"{loc}: unknown placeholder(s) {sorted(got - placeholders(source))}")
            if want - got:
                errors.append(f"{loc}: missing placeholder(s) {sorted(want - got)}")

            source_text = " ".join(forms(source))
            text = " ".join(forms(value))
            for term, pattern in keep_terms:
                if pattern.search(source_text) and not pattern.search(text):
                    errors.append(f"{loc}: keep {term!r} untranslated")

    for line in errors:
        print(f"error: {line}")
    counted = {c: sum(1 for v in entries(cat).values() if v is not None) for c, cat in catalogs.items()}
    print(f"checked {len(catalogs)} locales, {len(en)} keys; {len(errors)} error(s)")
    if not errors:
        print("translated: " + ", ".join(f"{c} {n}" for c, n in counted.items()))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
