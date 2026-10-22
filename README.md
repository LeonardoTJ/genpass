# genpass

A small offline CLI for random passwords and Diceware-style passphrases.
Generation uses operating-system randomness and the Python standard library.
Encrypted files are an optional feature.

## Install

Python **3.9.2 or newer** is required. For development:

```bash
poetry install --extras encryption
poetry run genpass --help
poetry run python -m genpass --version
```

Omit `--extras encryption` for a dependency-free generation runtime. To build and
install a wheel:

```bash
poetry build
pip install 'dist/genpass-2.0.2-py3-none-any.whl[encryption]'
```

The console command and `python -m genpass` have the same behavior. `--version`
comes from installed package metadata; an uninstalled source checkout reports
`0+uninstalled`.

## Generate

```bash
# Six words drawn from the combined English, Spanish, and Japanese/Romaji lists
 genpass diceware

# One password per line, suitable for piping
 genpass traditional -n 3 -l 20 --plain

# Capitalize two letters and insert two punctuation marks at random positions
 genpass diceware -w 6 -c 2 -s 2 --separator '-'

# Select just one language (English uses the complete EFF list)
 genpass diceware --language en
 genpass diceware --language es
 genpass diceware --language ja

# Use your own lists; duplicates across lists do not receive extra weight
 genpass diceware --wordlists /path/to/words.txt /path/to/other.txt

# Exclude characters that are easy to confuse
 genpass traditional --exclude '0O1lI'

# Use an equals sign when the excluded characters start with a hyphen
 genpass traditional --exclude=-_

# Alphanumeric only: zero minimum alone does not exclude punctuation
 genpass traditional --min-symbols 0 --exclude '!@#$%^&*()_+-=[]{}|;:,.<>?'
```

### Passphrase options

| Option | Default | Meaning |
| --- | --- | --- |
| `-n`, `--num-phrases` | 1 | Positive number of passphrases |
| `-w`, `--words` | 6 | Positive number of words per phrase |
| `-s`, `--symbols` | 0 | Punctuation characters inserted at random positions |
| `-c`, `--capitals` | 0 | Distinct lowercase letters to capitalize |
| `--language` | `all` | Combined vocabulary, or one list: `en`, `es`, `ja` |
| `--wordlists` | — | Explicit files, mutually exclusive with `--language` |
| `--separator` | space | One space or ASCII punctuation character |

Each word is selected uniformly, with replacement, from the distinct words in
the selected list or union of lists. Capitalization fails clearly if the chosen
words do not contain enough eligible letters. Unicode case conversions that
expand a character, such as `ß` to `SS`, are not eligible.
Symbols are inserted anywhere in the phrase, including inside words and at
either end. Letters and separators are retained in order; symbols may be adjacent.

The default combines English, Spanish, and Japanese/Romaji into one deduplicated
vocabulary. Each word is selected independently; a phrase need not contain every
language. Use `--language all` to explicitly request this default.
With `--language en`, EFF's complete **7,776-word** English list provides about
**77.55 bits** of selection entropy for six unmodified, space-separated words.
Smaller custom lists provide less entropy. Separators, capitals, and punctuation
should not be treated as a substitute for enough randomly selected words.

The Spanish and Japanese/Romaji files are preserved legacy data; their source
version and redistribution terms need confirmation before public distribution.
See [wordlist provenance and checksums](genpass/data/README.md).

### Traditional password options

| Option | Default | Meaning |
| --- | --- | --- |
| `-n`, `--num-passwords` | 1 | Positive number of passwords |
| `-l`, `--length` | 16 | Exact positive character count |
| `-d`, `--min-digits` | 2 | Minimum digits |
| `-s`, `--min-symbols` | 2 | Minimum punctuation characters |
| `-u`, `--min-uppercase` | 2 | Minimum uppercase letters |
| `--min-lowercase` | 1 | Minimum lowercase letters |
| `--exclude` | empty | Characters removed from every selection alphabet |

Minima must be nonnegative and their sum must fit within the length. Excluding
an entire required category is an error. A minimum of zero permits a category;
use `--exclude` to prohibit its characters. Remaining positions use the union
of allowed ASCII letters, digits, and punctuation, followed by a secure shuffle.
This construction meets minima but is not uniform over all policy-valid strings.

## Output and storage

Both generation modes support `--plain`, `--mask`, `-o/--output`, and `--encrypt`.

```bash
# New private plaintext file; passwords are not printed
 genpass traditional -n 5 -o passwords.txt

# New encrypted file; asks for a hidden master password and confirmation
 genpass traditional -n 5 -o vault.enc --encrypt

# Explicitly display decrypted passwords
 genpass decrypt vault.enc
 genpass decrypt vault.enc --plain

# Wait for Enter before displaying, or Ctrl-C to cancel
 genpass diceware --mask
```

- File saves **refuse all existing destinations**, including symlinks. There is
  deliberately no overwrite option. Choose a new filename.
- New files use mode **0600 on POSIX**, subject to the user's umask. On Windows,
  directory/account ACLs govern access; a POSIX mode is not an ACL guarantee.
- File contents are flushed and synced before success is reported. The parent
  directory is not synced, so creation is not guaranteed to survive a power loss.
  An interrupted write can leave an incomplete newly created file.
- Saving suppresses password output, including with `--plain`. Confirmation
  messages and errors go to stderr. Text files use UTF-8 with one password per line.
- `--encrypt` requires `--output`. Encryption failures return a nonzero status
  and do not print generated passwords or fall back to plaintext storage.
- `--mask` requires interactive stdin and stdout and cannot be combined with
  `--plain` or `--output`. It waits for Enter, then reveals permanently; it does
  not erase terminal scrollback. It no longer reveals automatically on a timer.
- Hidden master-password prompts require a terminal. No master-password option
  is accepted on the command line. The storage API accepts a supplied password
  for programmatic callers.

Exit status: `0` success/help, `2` invalid arguments or generation parameters,
`1` file/encryption/runtime failure, `130` interruption.

### Encryption format and compatibility

Encryption requires `cryptography>=44.0.0`. New files use Fernet authenticated
encryption with an Argon2id-derived key: **64 MiB memory, 3 iterations, 4 lanes**,
a fresh 16-byte salt, and a versioned header. The header is bound into key
derivation through Argon2id's associated data. New master passwords cannot be empty.

Existing files using the original `salt + Fernet token` format and
PBKDF2-SHA256/100,000 remain readable, including those originally made with an
empty master password. New files require this updated reader; older versions of
genpass cannot decrypt them. Keep a copy of older files when migrating.

Files are limited to 16 MiB. Readers bound KDF parameters before allocating
memory. Wrong passwords, invalid tokens, truncation, unsupported versions, and
invalid payloads fail without displaying partial plaintext. See
[the file format](docs/encrypted-format.md) for implementation details.

## Development and portable builds

```bash
poetry run pytest
poetry run ruff check genpass tests packaging
poetry check
poetry build
poetry run python packaging/smoke_wheel.py dist/*.whl dist/*.tar.gz
./packaging/build_binary.sh
```

Tests cover generation invariants, invalid inputs, resource checksums, file
permissions and overwrite refusal, failure exit codes, optional-dependency
absence, encryption tampering, and a fixed legacy-file fixture. Encryption tests
are skipped in core-only environments. CI checks Python 3.9 and 3.14 with and
without encryption, builds packages, and installs the wheel in an isolated environment.

The binary script installs the encryption extra explicitly, builds with
PyInstaller, and exercises the executable from outside the source checkout,
including hidden password prompts and an encryption/decryption round trip.
The build script and interactive binary smoke check target POSIX hosts. The
Python package is portable; Windows/macOS behavior still needs platform testing.
Build using a Python version supported by PyInstaller (currently below 3.16).
Linux binaries also depend on a compatible system libc; matching CPU/OS alone
is not sufficient. Build on the oldest system you intend to support.

```text
genpass/
  __init__.py       installed version and explicit resource lookup
  __main__.py       module entry point and process status
  cli.py            argument parsing, prompts, presentation
  generators.py     wordlist validation and secure generation
  storage.py        private files, encryption, legacy decryption
  data/             bundled lists, provenance, checksums
packaging/          binary build and isolated artifact smoke checks
tests/              pytest assertions and legacy fixture
```

The [original project review](PROJECT_REVIEW.md) records the findings that led
to these changes. [Implementation notes](IMPLEMENTATION.md) track the completed
stages, independent review results, and remaining release checks. The
[review follow-ups](IMPLEMENTATION.md#remaining-review-follow-ups) distinguish
documented limitations from fixes still to implement.
