# Build with: poetry run pyinstaller packaging/genpass.spec --clean --noconfirm
from pathlib import Path
from PyInstaller.utils.hooks import copy_metadata

PROJECT_ROOT = Path(SPECPATH).resolve().parent
resource_names = [
    "eff_large_wordlist.txt", "diceware_jp.txt", "DW-Espanol-1.txt", "README.md", "SHA256SUMS",
]
analysis = Analysis(
    [str(PROJECT_ROOT / "genpass" / "__main__.py")],
    pathex=[str(PROJECT_ROOT)],
    datas=[(str(PROJECT_ROOT / "genpass" / "data" / name), "genpass/data") for name in resource_names] + copy_metadata("genpass"),
    hiddenimports=["cryptography"],
    excludes=["tkinter", "unittest", "test", "tests"],
)
pyz = PYZ(analysis.pure)
exe = EXE(
    pyz, analysis.scripts, analysis.binaries, analysis.datas, [],
    name="genpass", debug=False, strip=False, upx=False, console=True,
)
