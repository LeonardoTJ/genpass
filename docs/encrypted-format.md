# Encrypted password file format

The writer creates a new file exclusively with owner-only POSIX permissions.
No temporary plaintext file is created. Encryption is Fernet from `cryptography`;
the following envelope only records version and key-derivation metadata.

The writer flushes and syncs file contents before reporting success, but does
not sync the parent directory. Creation is therefore not guaranteed to survive
a power loss. Normal write failures trigger cleanup; process termination can
leave an incomplete new file. Existing destinations are never overwritten.

## Version 1

All integers are unsigned, big-endian. Offsets are zero-based.

| Offset | Bytes | Content |
| --- | --- | --- |
| 0 | 8 | Magic: `GENPASS` followed by a zero byte |
| 8 | 1 | Format version: `1` |
| 9 | 1 | KDF identifier: `1` = Argon2id |
| 10 | 4 | Argon2id iterations; writer uses `3` |
| 14 | 4 | Memory in KiB; writer uses `65536` |
| 18 | 4 | Lanes; writer uses `4` |
| 22 | 16 | Random salt |
| 38 | remaining | Fernet token in its standard URL-safe base64 representation |

Derive 32 key bytes using the UTF-8 master password, the salt, and these Argon2id
parameters. Set Argon2id `ad` to the entire 38-byte header, including magic.
Encode the derived bytes with URL-safe base64 to construct the Fernet key.
Changing even otherwise valid header parameters prevents authentication.

The authenticated plaintext is a UTF-8 JSON array of nonempty strings. No
plaintext is returned until Fernet authentication and JSON schema checks pass.
The writer rejects an empty list, empty password entries, and an empty master
password. The reader accepts at most 16 MiB per encrypted file and validates
iterations (1–10), memory (8192–262144 KiB), and lanes (1–8) before key derivation.
Unsupported format/KDF identifiers are rejected. Parameters outside these
bounds require a deliberate future format/reader update.

These bounds limit requested work; they do not guarantee sufficient host memory.
The current CLI does not translate an Argon2 backend `MemoryError` into its usual
concise encryption error. This remains an implementation follow-up recorded in
[the review notes](../IMPLEMENTATION.md#remaining-review-follow-ups).

## Legacy format

Files without the magic prefix are interpreted as the original format:
16-byte salt followed by a Fernet token. Derive 32 bytes using
PBKDF2-HMAC-SHA256 with 100,000 iterations and the UTF-8 master password,
then URL-safe-base64 encode the key. Authenticated plaintext is UTF-8,
with passwords separated by newline characters.

The legacy reader is retained for compatibility; all new files use version 1.
`tests/fixtures/legacy.json` contains a fixed test-only legacy ciphertext,
master password, and expected Unicode plaintext, generated independently of
the current storage module. It must remain readable when the writer changes.

The format has no TTL. Fernet authenticates the embedded creation timestamp,
but this program does not expire password files. Authentication does not hide
the file's approximate size or Fernet timestamp. This format is for small local
password exports, not a password-manager database or a streaming archive.
