# genpassv2 project review

Reviewed 2026-10-21. Scope: current working tree, ignored runtime/build resources, all local Git branches, tests, package metadata, and existing distribution artifacts. Priority: simplicity and reliability.

This document preserves the pre-implementation findings. See [IMPLEMENTATION.md](IMPLEMENTATION.md) for the subsequent repairs and verification; the findings below describe the reviewed baseline, not the updated code.

The project has a useful, small foundation: local generation, mostly standard-library code, secure character/word selection through `secrets`, and optional authenticated encryption through Fernet. Its immediate needs are trustworthy wordlists, correct failure behavior, safe file output, and tests that actually fail. New features should follow those repairs.

This is a review, not an implementation change. Existing uncommitted work was preserved. Reproduction files and fresh build artifacts were created in temporary directories.

**Component map**

```text
genpass console entry point / python -m genpass
                       |
                 cli.main(argv)
                       |
                 argparse validation
                 /       |        \
          Diceware   Traditional   Decrypt
             |           |           |
      wordlist loader    |      OutputHandler
             |           |       Fernet + KDF
        package data     |           |
             +-----------+-----------+
                         |
             terminal / plaintext file /
                 encrypted file
```

| Component | Current responsibility | Assessment |
| --- | --- | --- |
| `genpass/__main__.py` | Module entry point | Thin and appropriate; will need to propagate an explicit exit status if `main()` returns one. |
| `genpass/__init__.py` | Version and package/frozen resource paths | Removes dependence on the caller's working directory; default selection silently includes every available language. |
| `genpass/cli.py:20` | `DicewareGenerator`: load lists, choose words, modify characters | Resource validation and selection policy need repair. |
| `genpass/cli.py:141` | `TraditionalPasswordGenerator`: meet character minima and shuffle | Secure character selection; insecure shuffle source; incomplete input validation. |
| `genpass/cli.py:183` | `OutputHandler`: timed display, password prompting, encryption and decryption | Mixes presentation, interactive input, cryptography, and persistence. |
| `genpass/cli.py:302` | Parser and orchestration | Useful `main(argv=None)` seam; failure statuses and output destinations are inconsistent. |
| `tests/test_genpass.py` | Nine subprocess/demo checks and a custom runner | Works as a rough smoke script; pytest does not interpret returned booleans as assertions. |
| `pyproject.toml`, `poetry.lock` | Packaging, extras, development tools | Core has no third-party runtime dependencies; `cryptography` is optional. |
| `packaging/build_binary.sh`, `packaging/genpass.spec` | PyInstaller executable build | Spec exists but is ignored by Git; encryption availability depends on build environment. |
| `.magi/config.yml` | External review-tool configuration | Development infrastructure; no application runtime dependency found. |

**Resources and distribution**

| Resource | Observed contents | Concern |
| --- | --- | --- |
| `genpass/data/diceware.wordlist.asc` | 72 codes, 72 distinct words; 909 bytes | A small sample, not a complete five-dice list. |
| `genpass/data/diceware_jp.txt` | 7,776 codes and distinct values; 100,784 bytes | ASCII entries, including numbers; source/version/license not recorded in the project. |
| `genpass/data/DW-Espanol-1.txt` | 7,776 codes, 7,773 distinct values; 102,293 bytes | `7`, `Don`, and `Tito` each occur twice. Source/version/license not recorded. |
| `dist/genpass-2.0.0-py3-none-any.whl` | Existing wheel includes all three lists | Its three Python package files match the current working tree. |
| `dist/genpass-2.0.0.tar.gz` | Existing source distribution | A fresh source distribution also builds locally. |
| `dist/genpass` | Existing approximately 14.9 MB executable | Diceware smoke test succeeds from a temporary working directory on this host. |

All three package wordlists and `packaging/genpass.spec` are ignored and untracked. `.gitignore:123` ignores all `*.txt`, line 124 all `*.asc`, and line 38 all `*.spec`. Explicit Poetry inclusion successfully bundles resources when they exist locally; it does not make those resources available in Git.

A temporary snapshot of existing tracked and non-ignored untracked files reproduced a failing Diceware command and a missing build spec. This models committing the migration with normal Git discovery; it is distinct from a clone of today's committed `main`, which still contains the original root-level script and 72-word sample.

Commit the intended data and spec through narrow ignore exceptions. Record each list's source, license, expected entry count, and checksum. Verify those assets in both wheel and source distribution. The project declares MIT licensing but has no LICENSE file; author email and project URLs in the metadata also need verification before publishing.

**Implementation history**

| Date / commit | Change | Implication |
| --- | --- | --- |
| 2025-11-02, `dc4ea5d` | Initial 440-line script, 326-line test script, README, optional requirements, 72-word English sample | Most generation, output, and test weaknesses already exist here. |
| 2025-11-02, `9a0092a`, `81fec0a`, `3f5427a` | Ignore rules and README changes | Broad resource exclusions become part of the repository. |
| 2026-04-27, `22d0993`, branch `test-change` | One-line experimental change | Separate branch; not evidence of a substantive released feature. |
| 2026-04-28, `063f9a9`, branch `feature/modular` | Splits Diceware, traditional generation, and output into packages | Unmerged. Mostly structural; retains the insecure shuffle and wordlist fallback. |
| 2026-04-28–29, `a451b26` through `12c0966` | Magi configuration, model routing, sequential dispatch | Current `main` history changes review tooling rather than generator behavior. |
| Current uncommitted working tree | Package migration, version 2.0.0, Poetry, console/module entry points, optional encryption extra, resource resolution, binary packaging | Valuable work, but not yet represented by a reproducible commit. |

The working tree also corrects the old encryption import from `PBKDF2` to `PBKDF2HMAC`. Current encryption round trips work. The committed script used a nonexistent imported class name and could misleadingly report a missing dependency. This is an improvement in the migration, not a remaining current-code defect.

No local release tags were found. The uncommitted migration has no Git commit date; existing artifact timestamps are not an authoritative implementation history. The modular branch should be treated as reference material, not merged wholesale over the newer packaging work.

**Confirmed findings, ordered by priority**

P1 means repair before relying on or distributing the tool for password generation. P2 means a concrete correctness or maintenance gap to address next.

1. **P1 — Passphrase strength is overstated and defaults mix unequal lists.** `genpass/cli.py:123` and `genpass/__init__.py:25` choose a list uniformly for every word and silently fall back to a random value when a dice code is absent. With the English list alone, six unmodified words have only `6 × log2(72) ≈ 37.02` bits, not the README's roughly 77.5 bits for a complete 7,776-word list. The original committed default effectively uses this small list because the other languages are absent there. The current local default uses all three lists, so its words are not uniformly selected from their union. Under the current unmodified six-word sampling model, I calculated approximately 73.37 bits of Shannon entropy and 46.45 bits of min-entropy. These measure different aspects of a nonuniform distribution; neither is an average cracking-time claim. Fix: ship a complete vetted default list, make language choice explicit, and select uniformly from validated distinct words. A suitable upstream candidate is [EFF's published wordlists](https://www.eff.org/deeplinks/2016/07/new-wordlists-random-passphrases/).

2. **P1 — Encryption failures return success and plaintext is still printed.** `genpass/cli.py:404`, `:445`, and `:454` ignore failure results and always display generated passwords after saving. Reproduced: missing `cryptography` reports an error but exits 0 and prints the generated password; confirmation mismatch does the same; wrong-password decryption returns normally. `traditional --encrypt` without `-o` also succeeds and prints plaintext despite help saying an output file is required. Even successful encrypted saves print plaintext to stdout, exposing it to logs or redirection. Fix: validate option combinations before generation, propagate nonzero status, stop on failed persistence, and make an output-file destination suppress secret display unless explicitly requested.

3. **P1 — File writes can disclose or destroy passwords.** `genpass/cli.py:248` and `:450` use ordinary truncating `open()`. Under umask 022, a new plaintext file was mode 0644; others may read it where directory permissions allow. Existing paths are overwritten without an explicit overwrite choice, and symlinks are followed. A reproduced `traditional -n 0 -o existing.txt` exits successfully after erasing the file. Fix: validate before opening, create files exclusively with owner-only permissions on POSIX, use explicit UTF-8, and refuse existing destinations by default. If overwrite support is added, use a restrictive temporary file and atomic replacement. Handle I/O errors as concise CLI failures.

4. **P1 — The pytest suite produces false passes.** `tests/test_genpass.py:49` onward returns `True` or `False` rather than asserting. I replaced every subprocess result with a forced failure in a temporary copy: pytest still reported **9 passed, 9 warnings**, exit 0. The custom runner checks returned booleans, but its requirements test only warns about invalid passwords and still returns `True` at line 137. Encryption coverage checks import availability rather than encryption behavior. Fix: convert checks to assertions, use `tmp_path` and `sys.executable`, and test invariants and failure cases. Treat return-value warnings as errors. This behavior is documented in [pytest's assertion guide](https://docs.pytest.org/en/stable/how-to/assert.html#return-not-none).

5. **P1 — Resource/build completeness depends on ignored local files.** The migration's default wordlists and PyInstaller spec disappear from a normal non-ignored snapshot. The fresh local wheel works, so this is a source-control completeness problem rather than a failing local package-data rule. Fix the ignore exceptions and add a fresh-checkout package smoke test.

6. **P2 — Traditional passwords use a noncryptographic shuffle.** `genpass/cli.py:178` calls global `random.shuffle`. The characters themselves come from `secrets`, so this finding does not imply that entire passwords can be predicted from a seed. It does mean the permutation uses an inappropriate random source and may expose positional structure if that PRNG state is known. The small fix is `secrets.SystemRandom().shuffle(password)`. [Python's secrets documentation](https://docs.python.org/3/library/secrets.html) explicitly distinguishes the security-oriented source from the default `random` generator.

7. **P2 — Invalid numeric options silently violate the contract.** The parser accepts arbitrary integers, and generator checks are incomplete. Reproduced: `diceware -w 0` produces an empty password with exit 0; negative counts produce no passwords; `traditional -l 1 -d -10 -s 2 -u 2` produces four characters despite the requested length of one. Fix: positive counts/lengths, nonnegative minima/modification counts, and feasible composition totals. Enforce the same invariants in generator APIs. The existing `+1` length reservation also does not guarantee lowercase: deterministic secure-choice substitution demonstrated a seven-character result with two digits, two symbols, and no lowercase. Decide whether lowercase is required, then enforce it explicitly or remove the unexplained reservation.

8. **P2 — Wordlist parsing accepts malformed data and fails late on empty lists.** `genpass/cli.py:49` accepts any two-field line, overwrites duplicate codes, permits duplicate values, and stores empty dictionaries as usable lists. A file containing `header arbitrary prose` generated `arbitrary prose arbitrary prose`; an empty file failed later with `Upper bound must be positive`. Missing explicitly requested files are only skipped. Fix: validate files once, report filename/line errors, reject empty lists and malformed codes, define duplicate handling, and fail on missing explicitly requested resources. If signed `.asc` lists are supported, recognize their wrapper explicitly. Precompute the values tuple: the current `dict.get` default eagerly builds a full list and draws a fallback even when the code exists.

9. **P2 — Passphrase symbol/capital counts are not guaranteed.** `genpass/cli.py:73` replaces letters rather than inserting characters. Repeated operations may hit the same position; the symbol table includes digits; capitalization can hit an existing uppercase letter, punctuation, or a digit. With controlled choices, requesting two symbols and two capitals on `abacus` produced `5bacus`: zero punctuation and zero uppercase letters. Fix: preserve whole words, insert requested punctuation separately, and choose distinct eligible lowercase positions when capitals are requested. Reject impossible requests, or deliberately redefine the options as attempts and document that weaker contract.

10. **P2 — Encryption accepts an empty master password and has no format version.** `genpass/cli.py:228` accepts two blank confirmations. A test file encrypted and decrypted with `password=''`. The format is a 16-byte salt followed by a Fernet token, with PBKDF2-SHA256 fixed at 100,000 iterations in both methods. Increasing that constant alone would make existing files unreadable. Fix: reject empty passwords; define a small versioned envelope that records the KDF and parameters, retains a reader for the current format, and validates parameter bounds. Then benchmark a stronger KDF configuration on supported machines. Current [cryptography documentation recommends Argon2id](https://cryptography.io/en/stable/fernet/#using-passwords-with-fernet); adopting it requires aligning the dependency floor and testing old-file compatibility. Keep Fernet as the authenticated encryption primitive.

11. **P2 — Binary builds do not explicitly request encryption.** `packaging/build_binary.sh:15` runs `poetry install` without the encryption extra, while the spec only names a hidden import. A hidden import cannot install a missing dependency. A fresh build environment therefore has no explicit guarantee of encryption support, although the README promises it after a prerequisite install. Fix: request `--extras encryption` in the build script and verify import/round-trip support before declaring success. [Poetry's install documentation](https://python-poetry.org/docs/cli/#install) describes extras as explicitly selected installation features. No claim is made here that a fresh dependency installation or binary rebuild was performed.

**A small design to keep**

Keep a local CLI and a dependency-free generation core. A modest layout is enough: `cli.py` for parsing and presentation, `generators.py` for the two generators and wordlist validation, and `storage.py` for optional encrypted persistence and safe writes. Keep resource files under `genpass/data`. No plugin framework, inheritance hierarchy, service layer, or database is needed.

Generators should return values or raise specific validation exceptions. Storage should accept a supplied password and return data or raise a specific failure; the CLI should own `getpass`, error messages, output destinations, and process status. Centralize key derivation so writer and reader cannot silently diverge. Use `main(argv) -> int` and propagate that result consistently through the console and module entry points.

The existing traditional minimum-fill algorithm is not uniform over all strings satisfying its constraints, even with a secure shuffle. That is not evidence that default passwords are weak, but it means a future entropy display must not simply claim `length × log2(alphabet size)` for this constrained distribution. Avoid adding an elaborate estimator before defining the sampling policy.

**Useful features, after repairs**

| Feature | Benefit | Keep it small |
| --- | --- | --- |
| `--plain` output | Reliable piping into other local tools | One password per line on stdout; diagnostics on stderr; no headings or numbering. |
| Explicit language/list selection | Predictable memorable passphrases | One documented default; mix lists only when explicitly requested. |
| `--separator` | Works with sites that reject spaces | Start with space and hyphen; avoid ambiguous entropy claims if separators are removed. |
| Allowed-character/exclusion option | Handles site-specific restrictions and ambiguous characters | Apply exclusions before selection and validate that required categories remain possible. A minimum of zero currently does not exclude a category. |
| `--version` | Support and artifact identification | Use a single source of version metadata. |
| Simple wordlist information | Makes strength assumptions inspectable | Show selected list, distinct count, provenance, and entropy only for the validated uniform sampling model. |

Timed masking is only delayed disclosure: it reveals automatically after three seconds and leaves plaintext in terminal output. The README's suggestion to use it for team presentations is misleading. Prefer explicit reveal for an interactive terminal, or remove the feature. Password-manager storage, sync, account databases, and clipboard automation would substantially expand this project's responsibilities; they are poor priorities for this small generator.

Documentation should also correct the old script-directory wordlist instructions, inaccurate example lengths/counts, and the implication that composition checks establish entropy. Make failure behavior, default language, file overwrite rules, and the optional encryption dependency explicit.

**Suggested implementation order and acceptance checks**

| Stage | Changes | Acceptance check |
| --- | --- | --- |
| 1: Trustworthy baseline | Real pytest assertions; regression tests for findings; track resources/spec; complete vetted default list; secure shuffle | A fresh checkout builds and generates offline; deliberate broken behavior fails tests; expected wordlist size/uniqueness verified. |
| 2: Reliable CLI/output | Validate options; consistent exit codes; suppress display when saving; safe file creation; empty master-password rejection | No secret emitted on failed encryption; invalid requests do not create/truncate files; output permissions and existing-path rejection tested. |
| 3: Stable storage/builds | Versioned envelope and legacy reader; stronger measured KDF; explicit binary encryption dependency | Fixed legacy fixture, Unicode round trip, wrong password, corruption, truncation, and missing-extra tests; package/binary smoke tests. |
| 4: Small usability improvements | Plain output, explicit list selection, separator, character exclusions, version | Contract tests verify exact output counts/lengths, allowed sets, stderr/stdout separation, and consistent entry points. |

Use a small CI matrix covering the oldest actually supported Python version and a current version. Run core-only and encryption-enabled cases separately so optional dependencies remain optional. Add lint and package-install smoke checks; execute the installed wheel from outside the source checkout. Build binaries only for platforms actually distributed. Keep randomized tests about invariants; use deterministic choices to reproduce collisions and edge cases rather than asserting exact random passwords or using flaky statistical thresholds.

**Verification record and limits**

| Check | Result |
| --- | --- |
| `poetry check` | Pass. |
| Existing nine tests through pytest | Nine apparent passes; nine non-None return warnings. |
| Existing custom test runner | 9/9 in this environment. |
| Temporary tests with every CLI subprocess forced to fail | Pytest still reports 9 passed, 9 warnings, exit 0. |
| `poetry run ruff check genpass tests --output-format concise` | Seven findings, all in tests: six ambiguous `l` variables and an unused import. |
| Resource inventory | All local counts, duplicate values, and ignore status verified. |
| Fresh wheel and sdist via Poetry build backend | Build successfully in a temporary directory; wheel includes all three local lists. |
| Fresh extracted wheel, outside source checkout | Diceware succeeds. This is a module/resource smoke test, not a clean pip-install/console-script test. |
| Existing binary, outside source checkout | Diceware succeeds on this Linux host. |
| Snapshot excluding ignored local resources | Diceware fails; PyInstaller spec absent. |
| Current encryption API | Round trip succeeds; wrong password and modified token rejected; empty master password accepted. |
| CLI/storage edge cases | Empty generation, negative minima/length mismatch, successful status after crypto failure, automatic plaintext display, 0644 output, and zero-count truncation reproduced. |

Runtime verification used Python 3.14.8 on this host. The Poetry environment reports cryptography 49.0.0 and PyInstaller 6.21.0. Python 3.9 compatibility, Windows/macOS behavior, fresh dependency installation, a full binary rebuild, and a clean installed console entry point were not exercised. Existing artifact presence and metadata validation do not establish release reproducibility or cross-platform support.
