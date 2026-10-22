#!/usr/bin/env bash
# Build a portable, distributable single-file binary for genpass.
#
# Usage:
#   ./packaging/build_binary.sh     # produces dist/genpass (or .exe)
set -euo pipefail

cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."

if ! command -v poetry >/dev/null 2>&1; then
    echo "poetry is not installed. Install it first: https://python-poetry.org/docs/" >&2
    exit 1
fi

# Ensure the project + dev tooling are installed in the current venv.
poetry install --with dev --extras encryption --no-interaction --no-ansi
poetry run python -c 'from genpass.storage import require_encryption; require_encryption()'
poetry run python -c 'import PyInstaller' || {
    echo "Build on a Python version supported by PyInstaller (currently <3.16)." >&2
    exit 1
}

# Build the wheel/sdist first (optional, but verifies the package metadata).
poetry build

# Produce the portable binary. --clean wipes prior build dirs.
poetry run pyinstaller packaging/genpass.spec --clean --noconfirm

# Check the frozen code and bundled resources, including encryption, in isolation.
poetry run python packaging/smoke_binary.py dist/genpass

echo
echo "Build complete:"
if [[ -f dist/genpass.exe ]]; then
    echo "  dist/genpass.exe"
else
    echo "  dist/genpass"
fi
echo "No Python needed; the target must have a compatible OS, architecture, and system libraries."
