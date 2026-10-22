# Wordlist resources

`eff_large_wordlist.txt` is the bundled English list: 7,776 distinct words,
selected uniformly with replacement. Six unmodified, space-separated words
provide approximately 77.55 bits of selection entropy.

- Author: Electronic Frontier Foundation (EFF), wordlist work by Joseph Bonneau.
- Source: https://www.eff.org/files/2016/07/18/eff_large_wordlist.txt
- Background: https://www.eff.org/deeplinks/2016/07/new-wordlists-random-passphrases
- Retrieved: 2026-10-21. Bytes preserved without modifications.
- License: Creative Commons Attribution 4.0 International,
  https://creativecommons.org/licenses/by/4.0/ under EFF's copyright policy,
  https://www.eff.org/copyright. EFF does not endorse this application.

`diceware_jp.txt` and `DW-Espanol-1.txt` are preserved legacy resources, included
in the default multilingual vocabulary and available individually with
`--language ja` or `--language es`. Their upstream version and redistribution terms
were not recorded in the original project. The Japanese-named list has 7,776
distinct ASCII values; the Spanish-named list has 7,776 codes and 7,773 distinct
values. Repeated values are deduplicated when loading, including across lists.
The default vocabulary is the deduplicated union of all three lists.
Use `--language en` to select only EFF English.

`SHA256SUMS` records the exact reviewed file bytes. Update the manifest and tests
intentionally when updating any list. Custom lists use UTF-8, one five-digit
code (digits 1–6) and one printable, whitespace-free word per line. Empty lines
and lines starting with `#` are allowed; duplicate codes and fewer than two
distinct words are rejected. PGP wrappers must be removed before importing.

The old 72-word `diceware.wordlist.asc` sample is not a production wordlist and
is no longer selected or shipped.
