"""Import catalogs from RTFM-EV's runtime format into locales/.

    python tools/import_app.py --app-dir <dir with en.json>
        Mirror en.json (the source of truth lives in the RTFM-EV repo).

    python tools/import_app.py --app-dir <dir> --fill nl,de
        Also take values from the app's nl.json / de.json for keys that are
        still null here, flagged "_ai": true. Developers write a first
        draft in the app when they add a key; this brings it here for
        review. A value that is not null here is never touched. A value
        identical to English is skipped, since the app copies English for
        keys nobody has translated.

Run tools/sync_keys.py before --fill when en.json gained keys, so every
locale has them.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from common import (
    SOURCE_LOCALE,
    entries,
    from_app,
    load_json,
    load_languages,
    locale_path,
    write_json,
)


def import_source(app_dir: Path, languages: dict) -> None:
    app_en = entries(load_json(app_dir / f"{SOURCE_LOCALE}.json"))
    target = locale_path(SOURCE_LOCALE)
    old = entries(load_json(target)) if target.exists() else {}

    new = {k: from_app(v) for k, v in app_en.items()}
    added = [k for k in new if k not in old]
    removed = [k for k in old if k not in new]
    changed = [k for k in new if k in old and old[k] != new[k]]

    meta = {
        "language": SOURCE_LOCALE,
        "name": languages[SOURCE_LOCALE]["name"],
        "managed_by": languages[SOURCE_LOCALE]["managed_by"],
    }
    write_json(target, {"_meta": meta, **new})
    print(f"en: {len(new)} keys, +{len(added)} added, -{len(removed)} removed, {len(changed)} text changed")
    for key in changed:
        print(f"  changed: {key}")


def fill(app_dir: Path, code: str) -> None:
    app_file = app_dir / f"{code}.json"
    if not app_file.exists():
        print(f"{code}: no {app_file.name} in app dir, skipped")
        return
    en = entries(load_json(locale_path(SOURCE_LOCALE)))
    app_loc = entries(load_json(app_file))
    catalog = load_json(locale_path(code))

    filled = 0
    for key, current in entries(catalog).items():
        if current is not None or key not in en:
            continue
        value = app_loc.get(key)
        en_app = en[key]["plural"] if isinstance(en[key], dict) else en[key]
        if value is None or value == en_app or isinstance(value, dict) != isinstance(en_app, dict):
            continue
        entry = from_app(value)
        catalog[key] = {**entry, "_ai": True} if isinstance(entry, dict) else {"value": entry, "_ai": True}
        filled += 1
    write_json(locale_path(code), catalog)
    print(f"{code}: filled {filled} null key(s) from the app as _ai")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--app-dir", type=Path, required=True)
    parser.add_argument("--fill", default="", help="comma-separated locale codes to fill from the app")
    parser.add_argument("--skip-en", action="store_true", help="do not re-import en.json")
    args = parser.parse_args()

    languages = load_languages()
    if not args.skip_en:
        import_source(args.app_dir, languages)
    for code in filter(None, args.fill.split(",")):
        if code not in languages or code == SOURCE_LOCALE or not locale_path(code).exists():
            print(f"error: cannot fill {code!r} (unknown, en, or no locale file yet)", file=sys.stderr)
            return 1
        fill(args.app_dir, code)
    return 0


if __name__ == "__main__":
    sys.exit(main())
