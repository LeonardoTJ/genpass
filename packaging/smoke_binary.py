"""Smoke-test a built executable, using a POSIX terminal for hidden input."""

from __future__ import annotations

import os
import select
import subprocess
import sys
import tempfile
import time
from pathlib import Path

binary = Path(sys.argv[1]).resolve()
if not binary.exists():
    binary = binary.with_suffix(".exe")


def terminal(arguments, prompts, cwd):
    import pty

    master, slave = pty.openpty()
    process = subprocess.Popen(
        [str(binary), *arguments],
        stdin=slave,
        stdout=slave,
        stderr=slave,
        cwd=cwd,
        start_new_session=True,
    )
    os.close(slave)
    transcript = b""
    pending = list(prompts)
    deadline = time.monotonic() + 30
    try:
        while time.monotonic() < deadline:
            if select.select([master], [], [], 0.1)[0]:
                try:
                    chunk = os.read(master, 65536)
                except OSError:
                    break
                if not chunk:
                    break
                transcript += chunk
                if pending and pending[0][0].encode() in transcript:
                    _, answer = pending.pop(0)
                    os.write(master, answer.encode() + b"\n")
            elif process.poll() is not None:
                break
        assert not pending, "Executable did not show the expected password prompt"
        assert process.wait(timeout=5) == 0, "Executable failed during interactive smoke test"
        return transcript.decode("utf-8").replace("\r\n", "\n")
    finally:
        os.close(master)
        if process.poll() is None:
            process.kill()
        process.wait()


with tempfile.TemporaryDirectory(prefix="genpass-binary-") as directory:
    for arguments in (["diceware", "--plain"], ["traditional", "--plain"]):
        result = subprocess.run(
            [str(binary), *arguments], cwd=directory, capture_output=True, text=True, timeout=30
        )
        assert result.returncode == 0, result.stderr
        assert len(result.stdout.split()) == (6 if arguments[0] == "diceware" else 1)
    version = subprocess.run(
        [str(binary), "--version"], cwd=directory, capture_output=True, text=True, timeout=30
    )
    assert version.returncode == 0 and "uninstalled" not in version.stdout
    if os.name != "posix":
        raise SystemExit("Generation passed; run encryption smoke with a POSIX terminal")
    path = Path(directory) / "test.enc"
    master_password = "smoke-test-only-master"
    output = terminal(
        ["traditional", "-n", "2", "-o", str(path), "--encrypt"],
        [("Encryption password: ", master_password), ("Confirm password: ", master_password)],
        directory,
    )
    assert "Generated passwords" not in output and master_password not in output
    output = terminal(
        ["decrypt", str(path), "--plain"], [("Decryption password: ", master_password)], directory
    )
    passwords = output.split("Decryption password: ", 1)[1].strip().splitlines()
    assert len(passwords) == 2 and all(len(password) == 16 for password in passwords)
print("Binary smoke passed: bundled wordlist, version, hidden prompts, encryption and decryption.")
