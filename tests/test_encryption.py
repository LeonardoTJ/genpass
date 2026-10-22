import base64
import json
from pathlib import Path

import pytest

from genpass import storage
from genpass.cli import main

pytest.importorskip("cryptography")


@pytest.fixture
def encrypted(tmp_path):
    path = tmp_path / "passwords.enc"
    storage.save_encrypted(["test-only-password", "árbol 雪"], path, "test-master")
    return path


def test_new_format_roundtrip(encrypted):
    assert encrypted.read_bytes().startswith(b"GENPASS\x00")
    assert storage.load_encrypted(encrypted, "test-master") == ["test-only-password", "árbol 雪"]


def test_old_format_fixture(tmp_path):
    fixture = json.loads((Path(__file__).parent / "fixtures/legacy.json").read_text())
    path = tmp_path / "legacy.enc"
    path.write_bytes(base64.b64decode(fixture["file_base64"]))
    assert storage.load_encrypted(path, fixture["password"]) == fixture["passwords"]


def test_each_file_has_fresh_salt_and_token(encrypted, tmp_path):
    other = tmp_path / "other.enc"
    storage.save_encrypted(["test-only-password", "árbol 雪"], other, "test-master")
    assert other.read_bytes() != encrypted.read_bytes()


def test_wrong_password(encrypted):
    with pytest.raises(storage.EncryptionError):
        storage.load_encrypted(encrypted, "wrong")


@pytest.mark.parametrize("length", [0, 1, 8, 16, 30, 40, 80])
def test_truncated_file(encrypted, length):
    encrypted.write_bytes(encrypted.read_bytes()[:length])
    with pytest.raises(storage.EncryptionError):
        storage.load_encrypted(encrypted, "test-master")


@pytest.mark.parametrize("offset", [8, 9, 10, 14, 18, 22, -1])
def test_tampered_header_or_token(encrypted, offset):
    content = bytearray(encrypted.read_bytes())
    content[offset] ^= 0xFF
    encrypted.write_bytes(content)
    with pytest.raises(storage.EncryptionError):
        storage.load_encrypted(encrypted, "test-master")


def test_empty_master_password_does_not_create_file(tmp_path):
    path = tmp_path / "empty.enc"
    with pytest.raises(storage.EncryptionError):
        storage.save_encrypted(["test-only"], path, "")
    assert not path.exists()


def test_wrong_password_cli_returns_failure_without_plaintext(encrypted, monkeypatch, capsys):
    monkeypatch.setattr("getpass.getpass", lambda prompt: "wrong")
    assert main(["decrypt", str(encrypted)]) == 1
    assert capsys.readouterr().out == ""


def test_successful_encrypted_save_does_not_echo(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("getpass.getpass", lambda prompt: "test-master")
    path = tmp_path / "saved.enc"
    assert main(["traditional", "--encrypt", "-o", str(path)]) == 0
    assert capsys.readouterr().out == ""
    assert len(storage.load_encrypted(path, "test-master")[0]) == 16


def test_header_changed_to_valid_parameters_fails_authentication(encrypted):
    import struct

    content = bytearray(encrypted.read_bytes())
    content[10:14] = struct.pack(">I", 2)  # valid iteration count, but not the authenticated one
    encrypted.write_bytes(content)
    with pytest.raises(storage.EncryptionError, match="Invalid password or corrupted"):
        storage.load_encrypted(encrypted, "test-master")


def test_parameter_bounds_precede_key_derivation(encrypted, monkeypatch):
    import struct

    from cryptography.hazmat.primitives.kdf import argon2

    content = bytearray(encrypted.read_bytes())
    content[14:18] = struct.pack(">I", 2**32 - 1)
    encrypted.write_bytes(content)

    def forbidden(**kwargs):
        pytest.fail("Must reject excessive memory before creating a KDF")

    monkeypatch.setattr(argon2, "Argon2id", forbidden)
    with pytest.raises(storage.EncryptionError, match="parameters"):
        storage.load_encrypted(encrypted, "test-master")


@pytest.mark.parametrize("passwords", [[], [""], [1], "not-a-list"])
def test_invalid_password_list_does_not_create_file(tmp_path, passwords):
    path = tmp_path / "empty.enc"
    with pytest.raises(storage.EncryptionError):
        storage.save_encrypted(passwords, path, "test-master")
    assert not path.exists()
