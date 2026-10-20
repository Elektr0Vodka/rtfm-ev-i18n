"""Pull request guard: compare the PR against its base branch.

Fails when a PR
- changes locales/en.json (it is mirrored from the RTFM-EV repo),
- changes the _meta block of any locale file,
- touches state/ (tool bookkeeping), or
- changes a translation but leaves it flagged "_ai" or "_stale". An edited
  value is a human one; a value still flagged "_ai" can be replaced by the
  app's draft in the next nightly run. A new "_ai" draft for a key that was
  null is fine: nothing human is lost if the nightly run replaces it.

    BASE_REF=origin/main python tools/pr_guard.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

from common import LOCALES_DIR, ROOT, SOURCE_LOCALE, entries, load_json, to_app


def base_version(base: str, rel_path: str) -> dict | None:
    result = subprocess.run(
        ["git", "show", f"{base}:{rel_path}"], cwd=ROOT, capture_output=True, text=True, encoding="utf-8"
    )
    return json.loads(result.stdout) if result.returncode == 0 else None


def main() -> int:
    base = os.environ.get("BASE_REF", "origin/main")
    errors: list[str] = []
    touched = subprocess.run(
        ["git", "diff", "--name-only", base, "--", "state/"], cwd=ROOT, capture_output=True, text=True
    ).stdout.split()
    errors += [f"{name}: state/ is maintained by the tools; leave it as is" for name in touched]
    for path in sorted(LOCALES_DIR.glob("*.json")):
        rel = f"locales/{path.name}"
        old = base_version(base, rel)
        new = load_json(path)
        if path.stem == SOURCE_LOCALE:
            if old != new:
                errors.append(f"{rel}: en.json is mirrored from RTFM-EV; change the English text there")
            continue
        if old is None:
            continue
        if old.get("_meta") != new.get("_meta"):
            errors.append(f"{rel}: _meta is maintained by the tools; leave it as is")
        old_entries = entries(old)
        for key, value in entries(new).items():
            old_value = old_entries.get(key)
            if value is None or not isinstance(value, dict) or to_app(value) == to_app(old_value):
                continue
            left = []
            if value.get("_ai") and not value.get("_human") and old_value is not None:
                left.append("_ai")
            if value.get("_stale"):
                left.append("_stale")
            if left:
                errors.append(
                    f"{rel}: {key}: text changed but still flagged {', '.join(left)}; "
                    'use a plain string, or drop "_stale" and set "_human": true'
                )

    for line in errors:
        print(f"error: {line}")
    print(f"pr guard: {len(errors)} error(s) against {base}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
