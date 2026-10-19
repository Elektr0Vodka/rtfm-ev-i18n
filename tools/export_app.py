"""Export every locale in RTFM-EV's runtime format to <out_dir>/<code>.json.

Review flags are dropped and untranslated (null) keys are left out; the
RTFM-EV pull script fills those with the English text. This is what the
release tarball ships under app/.

    python tools/export_app.py dist/app
"""

from __future__ import annotations

import sys
from pathlib import Path

from common import entries, load_json, load_languages, locale_path, status, to_app, write_json


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    out_dir = Path(sys.argv[1])
    out_dir.mkdir(parents=True, exist_ok=True)

    for code, info in load_languages().items():
        catalog = entries(load_json(locale_path(code)))
        stats = {"human": 0, "ai": 0, "stale": 0, "missing": 0}
        out: dict = {}
        for key, value in catalog.items():
            stats[status(value)] += 1
            if value is not None:
                out[key] = to_app(value)
        meta = {"locale": code, "name": info["name"], "source": "rtfm-ev-i18n", **stats}
        write_json(out_dir / f"{code}.json", {"_meta": meta, **out})
        print(f"{code}: {len(out)} keys exported")
    return 0


if __name__ == "__main__":
    sys.exit(main())
