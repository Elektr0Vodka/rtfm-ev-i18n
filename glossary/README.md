# Glossary

Canonical translations for recurring mesh and radio terms, so the same
word reads the same on every screen.

- `<code>.tsv`: two tab-separated columns, no header. Left is the English
  term (lower case), right is the translation in that language. A term
  that stays English in that language is listed with itself.
- `do-not-translate.txt`: brand and protocol names that stay as-is in every
  language. `tools/validate.py` fails a translation that drops one of them.
  Compounds are fine ("OpenHop-beheer", "MQTT-Slots").

The first `nl.tsv` and `de.tsv` were taken from the existing RTFM-EV
catalogs: only terms that a whole UI label translates the same way every
time made the list. Those catalogs are machine-drafted, so treat the lists
as a starting point and correct them if a native speaker disagrees.

Add a term when you notice it being translated two ways. Open a PR that
changes the glossary and, in the same PR, the strings that use the term.
