# Reliability implementation

Implemented after the 2026-10-21 review, preserving the existing package migration.
The source changes remain uncommitted for inspection. Version 2.0.2 is deployed
locally to `/home/leon/.local/bin/genpass`; no public release was published.

## Stage 1 — Trustworthy generation and tests

- Replaced boolean-returning demonstrations with pytest assertions. The initial
  28 generator cases exposed 23 failures before repair; all 28 then passed.
- Initially set the default vocabulary to the byte-for-byte EFF 7,776-word list,
  with attribution and SHA-256 checksums (multilingual default restored in 2.0.2). Custom lists are validated
  and their distinct values form a uniform selection pool.
- Replaced the noncryptographic shuffle. Traditional passwords guarantee their
  lowercase minimum. Passphrase punctuation preserves letters and capitalization
  selects distinct eligible positions.
- Added narrow Git ignore exceptions for actual resources and the build spec.
  They are discoverable by Git; they have not been staged or committed.

## Stage 2 — Predictable errors and safe output

- Positive counts/lengths, nonnegative and feasible character minima, and valid
  option combinations are checked before file writes.
- Saving creates a new exclusive file with POSIX mode 0600, refuses existing
  paths/symlinks, flushes and syncs file contents, and removes a partial file on
  normal write failure. The parent directory is not synced; creation is not
  guaranteed to survive a power loss. There is no overwrite option. A process
  killed during writing can still leave an incomplete newly created file;
  existing files remain protected.
- Saving does not print passwords. Errors and save confirmations use stderr.
  Module and console entry points propagate failure statuses.
- Empty new master passwords and confirmation mismatches are rejected. Hidden
  input cannot silently degrade to echoed input. Masking waits for explicit
  Enter in a terminal; cancellation reveals nothing.

## Stage 3 — Encryption and reproducible artifacts

- New files use a versioned Argon2id/Fernet envelope. Key derivation defaults:
  64 MiB, three iterations, four lanes. The header is bound through Argon2id
  associated data. Reader parameters and input sizes are bounded.
- A fixed independent PBKDF2 legacy fixture remains readable. Wrong passwords,
  modified headers/tokens, truncation, and invalid versions are rejected.
- Backend smoke measurement on this host: approximately 0.10 seconds to encrypt
  and 0.08 seconds to decrypt a small file. This is not a portable benchmark.
- Encryption now requires cryptography >=44.0.0. Resolving its actual Python
  constraints required raising the package floor from 3.9 to 3.9.2; the Poetry
  lockfile was refreshed.
- Build scripts explicitly install encryption and verify the frozen executable
  interactively. Wheel smoke checks use a fresh core-only virtual environment
  outside the source checkout. Source distributions explicitly include tests,
  the legacy fixture, build scripts/spec, and format documentation.

## Stage 4 — Small usability improvements and documentation

- Added plain output, explicit language selection, separators, character
  exclusions, configurable lowercase minimum, and installed version reporting.
- Kept three implementation modules: CLI/presentation, generation/validation,
  and optional storage. No runtime dependencies are needed for generation.
- Rewrote usage and format documentation; corrected repository URLs from the
  configured origin, removed the placeholder email, and added the declared
  MIT license text with a separate wordlist notice.
- Added CI configuration for Python 3.9 and 3.14, core and encryption installs,
  lint, package building, and isolated wheel smoke checks.

## Diceware symbol placement fix — 2.0.1

- Corrected `diceware -s`: each symbol is inserted at a securely random position
  in the growing phrase, including inside words and at either end. Previously,
  all symbols were appended to the last word.
- Insertion retains all original letters, capitalization, separators, and prior
  symbols. Adjacent symbols remain possible; zero symbols leaves generation
  unchanged. CLI help and README describe the new behavior.
- Added deterministic regression cases for leading, internal, separator-adjacent,
  and trailing positions, plus repeated insertions at the same position with
  more symbols than letters. All 103 tests, Ruff, and Poetry lock checks pass.
- Rebuilt and deployed the Linux binary to `/home/leon/.local/bin/genpass`, with
  the previous binary backed up alongside it. Verified version 2.0.1, matching
  build/install hashes, symbol placement/counts, and the installed binary's
  generation, hidden-prompt, and encryption/decryption smoke checks.

## Multilingual default restored — 2.0.2

- Restored the original intent of mixing English, Spanish, and Japanese/Romaji
  without requiring options. The 2.0 migration had changed the default to English.
- The default and `--language all` select uniformly from the deduplicated union
  of the three bundled lists. Each word is chosen independently, so every phrase
  is not guaranteed to contain all three languages. This retains the corrected
  uniform selection algorithm rather than the original per-list selection.
- `--language en`, `es`, and `ja` still select one language; explicit custom
  wordlists replace the default and remain mutually exclusive with `--language`.
- Regression tests verify the complete default union, deterministically select a
  word unique to each language through the CLI, and cover all single-language
  choices and option conflicts. README, resource notes, and CLI help are updated.
- All 109 tests, Ruff, and Poetry lock checks pass. Rebuilt wheel/sdist and Linux
  executable pass isolated installation and binary smoke checks. Deployed 2.0.2
  to PATH with a backup; verified matching build/install hashes, default/all
  multilingual output, individual language selection, and encryption round trips.

## Verification and remaining release checks

- 90 pytest cases pass with encryption on Python 3.9.25 and 3.14.8; Ruff and Poetry metadata checks pass.
- The Linux executable passes generation, version, hidden-prompt, and encrypted
  save/decrypt smoke tests outside the source checkout.
- Installed wheel smoke checks cover both entry points, all three language
  resources, plain output, and failure without the optional encryption dependency.
- Core-only environments on both Python versions pass 60 cases, with the
  encryption-only checks skipped. The Python 3.9 run caught and verified a fix
  for argparse treating an explicitly supplied default as absent in a mutually
  exclusive group. CI has not run remotely; Windows/macOS still need testing.
- Legacy Japanese/Romaji and Spanish resource provenance and redistribution
  terms remain unverified. Their bytes are preserved with checksums and clear
  documentation; all three lists are included in the multilingual default. Confirm those legacy
  terms before public distribution, or omit those resources from a release.
- The earlier PROJECT_REVIEW.md is intentionally retained as a historical
  baseline, not rewritten to pretend these defects were never present.

## Independent implementation review — 2026-10-21

The existing Claude session was contacted through Herdr to review the complete
working tree, including untracked package files, tests, resources, and build
configuration. Acceptance criteria were the four stages above, with
PROJECT_REVIEW.md as the historical baseline and README.md and
docs/encrypted-format.md as the public contracts. The review prioritized
simplicity and reliability. No blocking issues were found; the implementation
matches these notes. No source changes were made during the review.

Independent verification reported:

| Check | Result |
| --- | --- |
| Encryption-enabled tests | 90 passed on Python 3.14.8 with cryptography 49.0.0 and Python 3.9.25 with the declared minimum, cryptography 44.0.0. |
| Core-only tests | 60 passed, four encryption-only checks skipped on each Python version. |
| Lint and metadata | Ruff, `poetry check`, and `poetry check --lock` passed. |
| Packaging | Clean source snapshots built with Poetry and `python -m build`; wheel smoke checks passed and required resources, tests, fixture, documentation, and build spec were included. |
| Existing Linux binary | Generation and interactive encryption/decryption smoke checks passed. The reviewer did not rebuild the executable; it had been rebuilt during implementation. |
| Encryption interoperability | A file written with Python 3.14 / cryptography 49 decrypted with Python 3.9 / cryptography 44. The fixed legacy fixture remained readable. |
| CLI failure behavior | Terminal and nonterminal checks confirmed hidden-input requirements, nonzero failures, and protection of existing destinations. |

This is local verification, not evidence of remote CI or Windows/macOS support.
Power-loss durability and real memory exhaustion were not exercised. Legacy
wordlist redistribution terms remain unresolved as described above.

## Remaining review follow-ups

All five findings were assessed as low priority. Documentation updates below do
not imply that the corresponding runtime behavior or CI configuration changed.

| Finding | Evidence and impact | Status / smallest next step |
| --- | --- | --- |
| Argon2 allocation failure escapes the CLI handler | A simulated backend `MemoryError` propagates from `storage._argon2_key` through `cli.main`, producing a traceback. Actual memory exhaustion was not reproduced. | Open: translate backend allocation failure into `EncryptionError` and verify a concise nonzero CLI failure. Bounded KDF parameters do not guarantee that memory is available. |
| Password prompts precede path failures | A missing decrypt input prompts once; an existing encrypted destination prompts twice and performs key derivation before failing. Existing files remain intact. | Open: check/read the input before prompting and precheck the destination for usability. Keep exclusive creation as the authoritative protection against races. |
| Exclusion values starting with a hyphen need special syntax | `--exclude '-_'` is rejected by argparse; `--exclude=-_` works. | Documented in README.md with an equals-sign example; no parser change needed. |
| CI does not exercise the dependency floor or locked dependency set | CI resolves compatible dependencies from declared ranges rather than poetry.lock. cryptography 44.0.0 passed locally but has no dedicated CI case. | Open: add an encryption job pinned to cryptography 44.0.0 on Python 3.9; consider a separate locked-environment check if reproducibility needs it. |
| File syncing does not include directory creation metadata | `storage.write_private` syncs the file, not its parent directory. A power loss can lose the new directory entry. This was identified by inspection, not a power-loss test. | Documented in README.md, these notes, and the format document. Add platform-appropriate directory syncing only if durable creation becomes a requirement. |

The next small runtime changes should address allocation errors and prompt
ordering, followed by the CI dependency-floor check. Keep the existing module
boundaries and avoid expanding the CLI for these repairs.
