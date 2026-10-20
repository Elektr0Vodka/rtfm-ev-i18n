# Contributing translations

Thanks for helping translate RTFM-EV. This page covers the file format,
what to leave alone, and how to check your change.

## Quick reference

```
locales/
  en.json     source of truth, do not edit (comes from the RTFM-EV repo)
  nl.json     edit this for Dutch
  de.json     edit this for German
  <code>.json edit the file for your language
```

## File format

Each locale file is a flat JSON object. Keys are stable identifiers; never
rename, add or delete a key. A value has one of these shapes.

### 1. Plain string

```json
"chat_send": "Verzenden"
```

Human-approved and ready to ship.

### 2. Object with review flags

```json
"chat_send": {
  "value": "Verzenden",
  "_ai": true
}
```

| Field     | Meaning                                         |
|-----------|-------------------------------------------------|
| `_human`  | A person reviewed and approved this value       |
| `_ai`     | Machine-drafted, waiting for review             |
| `_stale`  | The English text changed after this was written |
| `_seeded` | Optional ISO date (YYYY-MM-DD) the draft was made |

When you check an `_ai` or `_stale` value, fix the text if needed, then
either replace the whole object with a plain string or drop `_ai` / `_stale`
and set `"_human": true`. If you change the text, CI requires this: an
edited value still flagged `_ai` could be replaced by a developer's draft
in the next nightly run. A `_stale` value that is still right only needs the
flag removed.

### 3. Plural

```json
"a11y_unread_messages": {
  "plural": {
    "one": "{count} ongelezen bericht",
    "other": "{count} ongelezen berichten"
  }
}
```

The app picks the form with the browser's plural rules for your language
(`Intl.PluralRules`). Use the categories your language needs (`zero`, `one`,
`two`, `few`, `many`, `other`); `other` is required. A plural can carry the
same `_ai` / `_human` flags as a string. A key is a plural in your file only
when it is a plural in `en.json`.

### 4. `null`

```json
"chat_send": null
```

Not translated yet; the app shows English. Leave `null` in place if you
cannot translate a key. Do not delete it.

## Placeholders

Text in single braces is filled in by the app:

```
en: "Battery {pct} percent"
nl: "Batterij {pct} procent"
```

- Keep every placeholder from the English text, spelled the same. You may
  move it within the sentence.
- Do not add placeholders that the English text does not have.
- In a plural, a form may leave out `{count}` when your language spells the
  number out ("one message").

## Brand and protocol names

Names in [`glossary/do-not-translate.txt`](glossary/do-not-translate.txt)
(RTFM-EV, MeshCore, OpenHop, MQTT, ...) stay as they are. Compounds such as
"OpenHop-beheer" are fine. Also keep channel names like `#public`, hex keys,
and command names unchanged.

## Glossary

[`glossary/<code>.tsv`](glossary/) lists the agreed translation of recurring
terms (node, repeater, channel, ...). Use them so the same word reads the
same on every screen. To change or add a term, open a PR that updates the
glossary and the strings using it.

## What CI rejects

- A key that does not exist in `en.json`
- Any change to `locales/en.json`
- Any change to a file's `_meta` block
- Changed text that is still flagged `_ai` or `_stale` (a new `_ai` draft
  for a key that was `null` is fine)
- A placeholder that is missing or not in the English text
- A plural without `other`, or a plural where English has a plain string
  (or the other way round)
- A dropped brand or protocol name

## Checking locally

You do not need the app to translate. CI checks every PR. To check before
pushing (Python 3.12 or newer):

```sh
pip install jsonschema
python tools/validate.py
```

## Pull request etiquette

- One language per PR.
- Group related keys (for example one screen or feature).
- If you change many keys, say why in the PR description.
- Reviews are best effort; please be patient.

## Code of conduct

Be kind. Translation is judgement and reasonable people disagree. Defer to
native speakers, and argue about the term, not the person.
