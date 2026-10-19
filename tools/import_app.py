"""Import catalogs from RTFM-EV's runtime format into locales/.

    python tools/import_app.py --app-dir <dir with en.json>
        Mirror en.json (the source of truth lives in the RTFM-EV repo).
        When the English text of a key changed, every translation of that
        key gets "_stale": true: it was written for the old text.

    python tools/import_app.py --app-dir <dir> --fill nl,de
        Take the draft a developer wrote in the app's nl.json / de.json,
        flagged "_ai": true, for a key that here is
          - null, or
          - "_stale" or "_ai" (and not "_human" without "_stale"),
        when the app value changed since the last run (or is new), and
        differs from the English text and from the value here. A current
        human translation is never replaced.

        "Changed since the last run" uses state/app-seen/<code>.json: a hash
        of every app value seen last time, written by this tool. Without that
        file every app value counts as new. A copy of English left behind
        after the English text changed is therefore not taken as a draft.

Run tools/sync_keys.py afterwards: it puts new keys in en.json's order.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from common import (
    ROOT,
    SOURCE_LOCALE,
    entries,
    from_app,
    load_json,
    load_languages,
    locale_path,
    mark_stale,
    to_app,
    write_json,
)


def import_source(app_dir: Path, languages: dict) -> list[str]:
    """Mirror en.json; return the keys whose English text changed."""
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
    return changed


def mark_changed_stale(changed: list[str], languages: dict) -> None:
    if not changed:
        return
    for code in languages:
        path = locale_path(code)
        if code == SOURCE_LOCALE or not path.exists():
            continue
        catalog = load_json(path)
        marked = 0
        for key in changed:
            value = catalog.get(key)
            if value is not None and not (isinstance(value, dict) and value.get("_stale")):
                catalog[key] = mark_stale(value)
                marked += 1
        if marked:
            write_json(path, catalog)
            print(f"{code}: {marked} translation(s) marked _stale")


def replaceable(current) -> bool:
    if current is None:
        return True
    if not isinstance(current, dict):
        return False
    return bool(current.get("_stale") or (current.get("_ai") and not current.get("_human")))


SEEN_DIR = ROOT / "state" / "app-seen"


def value_hash(value) -> str:
    text = json.dumps(value, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def fill(app_dir: Path, code: str) -> None:
    app_file = app_dir / f"{code}.json"
    if not app_file.exists():
        print(f"{code}: no {app_file.name} in app dir, skipped")
        return
    en = entries(load_json(locale_path(SOURCE_LOCALE)))
    app_loc = entries(load_json(app_file))
    catalog = load_json(locale_path(code))
    seen_path = SEEN_DIR / f"{code}.json"
    seen = load_json(seen_path) if seen_path.exists() else {}

    filled = 0
    for key in en:
        current = catalog.get(key)
        if not replaceable(current):
            continue
        value = app_loc.get(key)
        en_app = to_app(en[key])
        if value is None or value == en_app or isinstance(value, dict) != isinstance(en_app, dict):
            continue
        if seen.get(key) == value_hash(value):
            continue
        if current is not None and value == to_app(current):
            continue
        entry = from_app(value)
        catalog[key] = {**entry, "_ai": True} if isinstance(entry, dict) else {"value": entry, "_ai": True}
        filled += 1
    write_json(locale_path(code), catalog)
    SEEN_DIR.mkdir(parents=True, exist_ok=True)
    write_json(seen_path, {key: value_hash(value) for key, value in sorted(app_loc.items())})
    print(f"{code}: took {filled} draft(s) from the app as _ai")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--app-dir", type=Path, required=True)
    parser.add_argument("--fill", default="", help="comma-separated locale codes to fill from the app")
    parser.add_argument("--skip-en", action="store_true", help="do not re-import en.json")
    args = parser.parse_args()

    languages = load_languages()
    if not args.skip_en:
        mark_changed_stale(import_source(args.app_dir, languages), languages)
    for code in filter(None, args.fill.split(",")):
        if code not in languages or code == SOURCE_LOCALE or not locale_path(code).exists():
            print(f"error: cannot fill {code!r} (unknown, en, or no locale file yet)", file=sys.stderr)
            return 1
        fill(args.app_dir, code)
    return 0


if __name__ == "__main__":
    sys.exit(main())
