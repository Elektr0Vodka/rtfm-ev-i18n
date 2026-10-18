"""Give every locale in languages.json exactly the keys of en.json.

- Creates missing locale files.
- Adds new keys as null, in en.json's order.
- Drops keys that no longer exist in en.json.
- Resets a value to null when en.json switched that key between a plain
  string and a plural (the old translation no longer fits).
- Refreshes _meta.language/name/managed_by from languages.json; keeps notes.

Never touches a translated value otherwise.
"""

from __future__ import annotations

import sys

from common import SOURCE_LOCALE, entries, is_plural, load_json, load_languages, locale_path, write_json


def main() -> int:
    languages = load_languages()
    en = entries(load_json(locale_path(SOURCE_LOCALE)))

    for code, info in languages.items():
        if code == SOURCE_LOCALE:
            continue
        path = locale_path(code)
        catalog = load_json(path) if path.exists() else {}
        old_meta = catalog.get("_meta", {})
        current = entries(catalog)

        meta = {"language": code, "name": info["name"], "managed_by": info["managed_by"]}
        if "notes" in old_meta:
            meta["notes"] = old_meta["notes"]

        out: dict = {}
        added = reset = 0
        for key, en_value in en.items():
            if key not in current:
                out[key] = None
                added += 1
                continue
            value = current[key]
            if value is not None and is_plural(value) != is_plural(en_value):
                value = None
                reset += 1
            out[key] = value
        dropped = sum(1 for k in current if k not in en)

        if write_json(path, {"_meta": meta, **out}):
            print(f"{code}: +{added} added, -{dropped} dropped, {reset} reset (shape change)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
