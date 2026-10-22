import os

import pytest

from genpass.storage import write_private


def test_exclusive_creation(tmp_path):
    path = tmp_path / "saved.txt"
    path.write_bytes(b"original")
    with pytest.raises(FileExistsError):
        write_private(path, b"replacement")
    assert path.read_bytes() == b"original"


@pytest.mark.skipif(os.name != "posix", reason="POSIX file modes and symlinks")
def test_symlink_is_not_followed(tmp_path):
    target = tmp_path / "target"
    target.write_bytes(b"original")
    link = tmp_path / "link"
    link.symlink_to(target)
    with pytest.raises(FileExistsError):
        write_private(link, b"replacement")
    assert target.read_bytes() == b"original"
    assert link.is_symlink()


@pytest.mark.skipif(os.name != "posix", reason="POSIX file modes")
def test_private_even_under_permissive_umask(tmp_path):
    path = tmp_path / "private"
    previous = os.umask(0)
    try:
        write_private(path, b"test only")
    finally:
        os.umask(previous)
    assert path.stat().st_mode & 0o777 == 0o600


def test_failed_write_removes_partial_file(tmp_path, monkeypatch):
    def fail(_):
        raise OSError("simulated disk failure")

    monkeypatch.setattr(os, "fsync", fail)
    path = tmp_path / "failed"
    with pytest.raises(OSError, match="simulated"):
        write_private(path, b"test only")
    assert not path.exists()
