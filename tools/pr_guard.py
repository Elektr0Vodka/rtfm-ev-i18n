"""Pull request guard: compare the PR against its base branch.

Fails when a PR
- changes locales/en.json (it is mirrored from the RTFM-EV repo), or
- changes the _meta block of any locale file.

    BASE_REF=origin/main python tools/pr_guard.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

from common import LOCALES_DIR, ROOT, SOURCE_LOCALE, load_json


def base_version(base: str, rel_path: str) -> dict | None:
    result = subprocess.run(
        ["git", "show", f"{base}:{rel_path}"], cwd=ROOT, capture_output=True, text=True, encoding="utf-8"
    )
    return json.loads(result.stdout) if result.returncode == 0 else None


def main() -> int:
    base = os.environ.get("BASE_REF", "origin/main")
    errors: list[str] = []
    for path in sorted(LOCALES_DIR.glob("*.json")):
        rel = f"locales/{path.name}"
        old = base_version(base, rel)
        new = load_json(path)
        if path.stem == SOURCE_LOCALE:
            if old != new:
                errors.append(f"{rel}: en.json is mirrored from RTFM-EV; change the English text there")
            continue
        if old is not None and old.get("_meta") != new.get("_meta"):
            errors.append(f"{rel}: _meta is maintained by the tools; leave it as is")

    for line in errors:
        print(f"error: {line}")
    print(f"pr guard: {len(errors)} error(s) against {base}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
