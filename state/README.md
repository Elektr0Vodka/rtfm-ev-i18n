# state/

Bookkeeping for the tools. Do not edit; pull requests that touch this folder
fail CI.

- `app-seen/<code>.json`: a hash of every value in RTFM-EV's own
  `<code>.json` as seen by the last workflow run. `tools/import_app.py --fill`
  only takes an app draft whose value changed since then, so a developer's
  new draft is picked up once and an untouched value is never re-imported.
