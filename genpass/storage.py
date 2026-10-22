"""Versioned Fernet storage, legacy decryption, and private file creation."""

from __future__ import annotations

import base64
import json
import os
import secrets
import struct
from pathlib import Path

# Version 1: magic, version, KDF id, iterations, memory KiB, lanes, salt, token.
MAGIC = b"GENPASS\x00"
HEADER = struct.Struct(">BBIII16s")
ARGON2_PARAMETERS = (3, 65536, 4)
MAX_FILE_BYTES = 16 * 1024 * 1024


class EncryptionError(ValueError):
    """An encryption operation could not be completed safely."""


def require_encryption():
    try:
        from cryptography.fernet import Fernet, InvalidToken
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.argon2 import Argon2id
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    except ImportError as error:
        raise EncryptionError(
            "Install encryption support with: pip install -U 'genpass[encryption]'"
        ) from error
    return Fernet, InvalidToken, Argon2id, hashes, PBKDF2HMAC


def write_private(path: str | Path, content: bytes) -> None:
    """Create a new owner-only file; refuse existing paths, including symlinks."""
    descriptor = os.open(
        path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0), 0o600
    )
    try:
        with os.fdopen(descriptor, "wb") as destination:
            destination.write(content)
            destination.flush()
            os.fsync(destination.fileno())
    except BaseException:
        Path(path).unlink(missing_ok=True)
        raise


def _legacy_key(password: str, salt: bytes) -> bytes:
    _, _, _, hashes, PBKDF2HMAC = require_encryption()
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100_000)
    return base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))


def _argon2_key(
    password: str, salt: bytes, parameters: tuple[int, int, int], header: bytes
) -> bytes:
    _, _, Argon2id, _, _ = require_encryption()
    from cryptography.exceptions import UnsupportedAlgorithm

    iterations, memory, lanes = parameters
    # Bound untrusted file parameters before asking the backend to allocate memory.
    if not (1 <= iterations <= 10 and 8192 <= memory <= 262144 and 1 <= lanes <= 8):
        raise EncryptionError("Unsupported encryption parameters")
    try:
        kdf = Argon2id(
            salt=salt, length=32, iterations=iterations, memory_cost=memory, lanes=lanes, ad=header
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))
    except UnsupportedAlgorithm as error:
        raise EncryptionError(
            "This cryptography backend does not support Argon2id; upgrade cryptography"
        ) from error


def save_encrypted(passwords: list[str], path: str | Path, password: str) -> None:
    Fernet, _, _, _, _ = require_encryption()
    if not password:
        raise EncryptionError("Encryption password must not be empty")
    if (
        not isinstance(passwords, list)
        or not passwords
        or not all(isinstance(value, str) and value for value in passwords)
    ):
        raise EncryptionError("At least one nonempty password is required")
    payload = json.dumps(passwords, ensure_ascii=False).encode("utf-8")
    # Fernet adds padding, authentication, and base64 overhead.
    if len(payload) > (MAX_FILE_BYTES - 256) * 3 // 4:
        raise EncryptionError("Encrypted output exceeds the 16 MiB file limit")
    salt = secrets.token_bytes(16)
    header = MAGIC + HEADER.pack(1, 1, *ARGON2_PARAMETERS, salt)
    key = _argon2_key(password, salt, ARGON2_PARAMETERS, header)
    write_private(path, header + Fernet(key).encrypt(payload))


def load_encrypted(path: str | Path, password: str) -> list[str]:
    Fernet, InvalidToken, _, _, _ = require_encryption()
    with open(path, "rb") as source:
        content = source.read(MAX_FILE_BYTES + 1)
    if len(content) > MAX_FILE_BYTES:
        raise EncryptionError("Encrypted input exceeds the 16 MiB file limit")
    if len(content) < 17:
        raise EncryptionError("Invalid password or corrupted file")
    modern = content.startswith(MAGIC)
    if modern:
        header_length = len(MAGIC) + HEADER.size
        if len(content) <= header_length:
            raise EncryptionError("Truncated encrypted file")
        version, kdf_id, iterations, memory, lanes, salt = HEADER.unpack(
            content[len(MAGIC) : header_length]
        )
        if version != 1 or kdf_id != 1:
            raise EncryptionError("Unsupported encrypted file version or KDF")
        key = _argon2_key(password, salt, (iterations, memory, lanes), content[:header_length])
        token = content[header_length:]
    else:
        # Original format: 16-byte salt + Fernet token, PBKDF2-SHA256/100,000.
        # Empty legacy master passwords remain readable, but cannot be used for new files.
        key = _legacy_key(password, content[:16])
        token = content[16:]
    try:
        plaintext = Fernet(key).decrypt(token).decode("utf-8")
        if not modern:
            return plaintext.split("\n")
        passwords = json.loads(plaintext)
        if (
            not isinstance(passwords, list)
            or not passwords
            or not all(isinstance(value, str) and value for value in passwords)
        ):
            raise EncryptionError("Invalid encrypted password payload")
        return passwords
    except (InvalidToken, UnicodeError, json.JSONDecodeError) as error:
        raise EncryptionError("Invalid password or corrupted file") from error
