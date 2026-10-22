"""Install a wheel into an isolated core-only environment and exercise entry points."""

from __future__ import annotations

import os
import subprocess
import sys
import tarfile
import tempfile
import venv
import zipfile
from pathlib import Path

wheel = Path(sys.argv[1]).resolve()
with zipfile.ZipFile(wheel) as archive:
    names = archive.namelist()
    assert "genpass/data/eff_large_wordlist.txt" in names
    assert "genpass/data/README.md" in names
    assert not any(name.endswith(".asc") for name in names), "Obsolete sample included"
if len(sys.argv) > 2:
    with tarfile.open(sys.argv[2]) as archive:
        names = archive.getnames()
        for required in (
            "packaging/genpass.spec",
            "packaging/build_binary.sh",
            "tests/fixtures/legacy.json",
            "genpass/data/eff_large_wordlist.txt",
            "docs/encrypted-format.md",
            "LICENSE",
        ):
            assert any(
                name.endswith("/" + required) for name in names
            ), f"Missing from sdist: {required}"
with tempfile.TemporaryDirectory(prefix="genpass-wheel-") as directory:
    root = Path(directory)
    venv.EnvBuilder(with_pip=True).create(root / "env")
    scripts = root / "env" / ("Scripts" if os.name == "nt" else "bin")
    python = scripts / ("python.exe" if os.name == "nt" else "python")
    console = scripts / ("genpass.exe" if os.name == "nt" else "genpass")
    environment = {
        key: value for key, value in os.environ.items() if key not in {"PYTHONPATH", "PYTHONHOME"}
    }

    def run(*arguments):
        return subprocess.run(
            arguments, cwd=root, env=environment, capture_output=True, text=True, timeout=30
        )

    installed = run(str(python), "-m", "pip", "install", "--no-index", "--no-deps", str(wheel))
    assert installed.returncode == 0, installed.stderr
    for entry in ([str(console)], [str(python), "-m", "genpass"]):
        for language in ("all", "en", "ja", "es"):
            result = run(*entry, "diceware", "--plain", "--language", language)
            assert result.returncode == 0, result.stderr
            assert len(result.stdout.split()) == 6
        result = run(*entry, "traditional", "--plain", "-n", "2")
        assert result.returncode == 0, result.stderr
        assert len(result.stdout.splitlines()) == 2
        assert all(len(line) == 16 for line in result.stdout.splitlines())
        result = run(*entry, "traditional", "--encrypt", "-o", str(root / "missing.enc"))
        assert result.returncode == 1 and not result.stdout
        assert "encryption" in result.stderr
        assert not (root / "missing.enc").exists()
    result = run(str(console), "--version")
    assert result.returncode == 0 and "uninstalled" not in result.stdout
print(
    "Wheel smoke passed: isolated installation, both entry points, all languages, core-only errors."
)
