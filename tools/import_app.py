"""Import catalogs from RTFM-EV's runtime format into locales/.

    python tools/import_app.py --app-dir <dir with en.json>
        Mirror en.json (the source of truth lives in the RTFM-EV repo).

    python tools/import_app.py --app-dir <dir> --seed nl,de
        One-time seed: also import those locales, every value flagged
        "_ai": true. Values identical to English become null, since the
        app copies English for keys nobody has translated yet.

Run tools/sync_keys.py afterwards so every locale gets the new key set.
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


def seed(app_dir: Path, code: str, languages: dict) -> None:
    app_en = entries(load_json(app_dir / f"{SOURCE_LOCALE}.json"))
    app_loc = entries(load_json(app_dir / f"{code}.json"))
    out: dict = {}
    for key, en_value in app_en.items():
        value = app_loc.get(key)
        if value is None or value == en_value or isinstance(value, dict) != isinstance(en_value, dict):
            out[key] = None
            continue
        entry = from_app(value)
        out[key] = {**entry, "_ai": True} if isinstance(entry, dict) else {"value": entry, "_ai": True}
    meta = {"language": code, "name": languages[code]["name"], "managed_by": languages[code]["managed_by"]}
    write_json(locale_path(code), {"_meta": meta, **out})
    filled = sum(1 for v in out.values() if v is not None)
    print(f"{code}: seeded {filled}/{len(out)} keys as _ai")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--app-dir", type=Path, required=True)
    parser.add_argument("--seed", default="", help="comma-separated locale codes to seed")
    args = parser.parse_args()

    languages = load_languages()
    import_source(args.app_dir, languages)
    for code in filter(None, args.seed.split(",")):
        if code not in languages or code == SOURCE_LOCALE:
            print(f"error: cannot seed {code!r}", file=sys.stderr)
            return 1
        seed(args.app_dir, code, languages)
    return 0


if __name__ == "__main__":
    sys.exit(main())
