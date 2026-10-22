"""CLI failure, output, and subprocess exit-status contracts."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

from genpass.cli import main


@pytest.mark.parametrize(
    "args",
    [
        ["diceware", "-w", "0"],
        ["diceware", "-n", "-1"],
        ["traditional", "-n", "0"],
        ["traditional", "-l", "1", "-d", "-10"],
        ["traditional", "--encrypt"],
    ],
)
def test_invalid_arguments_do_not_write(args, tmp_path, capsys):
    path = tmp_path / "passwords.txt"
    # --encrypt without -o must remain a missing-output case.
    argv = args if "--encrypt" in args else [*args, "-o", str(path)]
    with pytest.raises(SystemExit) as error:
        main(argv)
    assert error.value.code == 2
    assert not path.exists()
    assert capsys.readouterr().out == ""


def test_save_does_not_echo_secret(tmp_path, capsys):
    path = tmp_path / "passwords.txt"
    assert main(["traditional", "-n", "3", "-o", str(path)]) == 0
    passwords = path.read_text().splitlines()
    assert len(passwords) == 3
    assert all(len(p) == 16 for p in passwords)
    captured = capsys.readouterr()
    assert captured.out == ""
    assert all(p not in captured.err for p in passwords)
    if os.name == "posix":
        assert path.stat().st_mode & 0o777 == 0o600


def test_existing_file_is_preserved(tmp_path, capsys):
    path = tmp_path / "passwords.txt"
    path.write_text("keep me")
    assert main(["traditional", "-o", str(path)]) == 1
    assert path.read_text() == "keep me"
    assert capsys.readouterr().out == ""


def test_mismatched_encryption_passwords_do_not_write_or_display(tmp_path, monkeypatch, capsys):
    pytest.importorskip("cryptography")
    answers = iter(["first", "second"])
    monkeypatch.setattr("getpass.getpass", lambda prompt: next(answers))
    path = tmp_path / "passwords.enc"
    assert main(["traditional", "--encrypt", "-o", str(path)]) == 1
    assert not path.exists()
    assert capsys.readouterr().out == ""


def test_blank_encryption_password_is_rejected(tmp_path, monkeypatch, capsys):
    pytest.importorskip("cryptography")
    monkeypatch.setattr("getpass.getpass", lambda prompt: "")
    path = tmp_path / "passwords.enc"
    assert main(["traditional", "--encrypt", "-o", str(path)]) == 1
    assert not path.exists()
    assert capsys.readouterr().out == ""


def test_mask_requires_terminal(capsys):
    assert main(["traditional", "--mask"]) == 1
    assert capsys.readouterr().out == ""


def test_missing_encryption_dependency_returns_failure(tmp_path):
    repo = str(Path(__file__).resolve().parents[1])
    path = tmp_path / "passwords.enc"
    result = subprocess.run(
        [sys.executable, "-S", "-m", "genpass", "traditional", "--encrypt", "-o", str(path)],
        env={**os.environ, "PYTHONPATH": repo},
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 1
    assert result.stdout == ""
    assert "encryption" in result.stderr
    assert not path.exists()


@pytest.mark.parametrize(
    "args", [["--help"], ["diceware", "--help"], ["traditional", "--help"], ["decrypt", "--help"]]
)
def test_help(args):
    with pytest.raises(SystemExit) as error:
        main(args)
    assert error.value.code == 0


def test_plain_output(capsys):
    assert main(["traditional", "--plain", "-n", "3"]) == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert len(captured.out.splitlines()) == 3
    assert all(len(line) == 16 for line in captured.out.splitlines())


@pytest.mark.parametrize("language", ["en", "es", "ja"])
def test_language_is_explicit(capsys, language):
    from genpass import default_wordlists
    from genpass.generators import load_wordlist

    assert main(["diceware", "--plain", "--language", language]) == 0
    words = capsys.readouterr().out.split()
    assert len(words) == 6
    assert set(words) <= set(load_wordlist(default_wordlists(language)[0]))


@pytest.mark.parametrize("options", [[], ["--language", "all"]])
def test_default_language_pool_includes_every_language(capsys, monkeypatch, options):
    from genpass import default_wordlists
    from genpass.generators import load_wordlist

    pools = [set(load_wordlist(default_wordlists(language)[0])) for language in ("en", "es", "ja")]
    # Pick a word unique to each language so this cannot pass with an English-only pool.
    chosen = [sorted(pool - set().union(*(other for other in pools if other is not pool)))[0]
              for pool in pools]
    selections = iter(chosen)

    def choose_word(pool):
        word = next(selections)
        assert word in pool
        return word

    monkeypatch.setattr("secrets.choice", choose_word)
    assert main(["diceware", "--plain", "-w", "3", *options]) == 0
    assert capsys.readouterr().out.split() == chosen


@pytest.mark.parametrize("language", ["en", "all"])
def test_language_and_custom_lists_are_mutually_exclusive(language):
    with pytest.raises(SystemExit) as error:
        main(["diceware", "--language", language, "--wordlists", "example.txt"])
    assert error.value.code == 2


def test_version(capsys):
    from genpass import __version__

    with pytest.raises(SystemExit) as error:
        main(["--version"])
    assert error.value.code == 0
    assert capsys.readouterr().out.strip() == f"genpass {__version__}"


def test_mask_waits_for_explicit_reveal(monkeypatch):
    import io

    class Terminal(io.StringIO):
        def isatty(self):
            return True

    output = Terminal()

    class Input(Terminal):
        def readline(self):
            assert output.getvalue() == ""
            return "\n"

    monkeypatch.setattr(sys, "stdin", Input())
    monkeypatch.setattr(sys, "stdout", output)
    assert main(["traditional", "--mask"]) == 0
    assert "Generated passwords:" in output.getvalue()


def test_hidden_input_failure_is_not_echoed(tmp_path, monkeypatch, capsys):
    import getpass
    import warnings

    pytest.importorskip("cryptography")

    def unavailable(prompt):
        warnings.warn("No hidden input", getpass.GetPassWarning)
        pytest.fail("Must stop before reading a password with echo enabled")

    monkeypatch.setattr(getpass, "getpass", unavailable)
    path = tmp_path / "hidden.enc"
    assert main(["traditional", "--encrypt", "-o", str(path)]) == 1
    assert not path.exists()
    assert capsys.readouterr().out == ""


def test_mask_cancel_does_not_display(monkeypatch, capsys):
    import io

    class Terminal(io.StringIO):
        def isatty(self):
            return True

    output = Terminal()
    monkeypatch.setattr(sys, "stdin", Terminal("no\n"))
    monkeypatch.setattr(sys, "stdout", output)
    assert main(["traditional", "--mask"]) == 1
    assert output.getvalue() == ""


def test_bad_wordlist_is_usage_error(tmp_path, capsys):
    path = tmp_path / "invalid.txt"
    path.write_text("not a wordlist")
    with pytest.raises(SystemExit) as error:
        main(["diceware", "--wordlists", str(path)])
    assert error.value.code == 2
    assert capsys.readouterr().out == ""
