"""Generator contracts: assertions, deterministic edge cases, and real invariants."""

import hashlib

import pytest

from genpass import DATA_DIR, default_wordlists
from genpass.generators import DicewareGenerator, TraditionalPasswordGenerator


@pytest.fixture
def wordlist(tmp_path):
    path = tmp_path / "words.txt"
    path.write_text("11111 abacus\n11112 banana\n", encoding="utf-8")
    return path


def test_english_list_is_complete_and_unique():
    paths = default_wordlists("en")
    assert len(paths) == 1
    generator = DicewareGenerator(paths)
    assert len(generator.words) == len(set(generator.words)) == 7776


def test_default_pool_is_union_of_all_bundled_languages():
    paths = default_wordlists()
    assert len(paths) == 3
    assert paths == default_wordlists("all")
    expected = set()
    for language in ("en", "es", "ja"):
        expected.update(DicewareGenerator(default_wordlists(language)).words)
    actual = DicewareGenerator(paths).words
    assert len(actual) == len(set(actual))
    assert set(actual) == expected


def test_wordlist_checksum():
    for line in (DATA_DIR / "SHA256SUMS").read_text().splitlines():
        digest, name = line.split()
        assert hashlib.sha256((DATA_DIR / name).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize(
    "content",
    [
        "",
        "# comment\n",
        "header arbitrary prose\n",
        "00000 word\n",
        "11111 one\n11111 two\n",
        "11111 one\n11112 one\n",
        "11111 ab\x1bcd\n",
    ],
)
def test_invalid_wordlist_is_rejected(tmp_path, content):
    path = tmp_path / "invalid.txt"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(ValueError):
        DicewareGenerator([path])


def test_missing_explicit_wordlist_is_not_skipped(wordlist):
    with pytest.raises(FileNotFoundError):
        DicewareGenerator([wordlist, wordlist.parent / "missing.txt"])


def test_multiple_lists_form_unique_pool(wordlist, tmp_path):
    other = tmp_path / "other.txt"
    other.write_text("11111 abacus\n11112 cherry\n", encoding="utf-8")
    generator = DicewareGenerator([wordlist, other])
    assert generator.words == ("abacus", "banana", "cherry")


def test_diceware_uses_selected_words(wordlist):
    generator = DicewareGenerator([wordlist])
    for _ in range(20):
        words = generator.generate_passphrase(6).split()
        assert len(words) == 6
        assert set(words) <= {"abacus", "banana"}


def test_modifications_preserve_words_and_requested_counts(wordlist, monkeypatch):
    monkeypatch.setattr("secrets.choice", lambda sequence: sequence[0])
    phrase = DicewareGenerator([wordlist]).generate_passphrase(2, 3, 4)
    assert sum(c.isupper() for c in phrase) == 4
    assert sum(not c.isalnum() and c != " " for c in phrase) == 3
    assert "".join(c for c in phrase.lower() if c.isalpha()) == "abacusabacus"


def test_impossible_capitalization_is_rejected(wordlist):
    with pytest.raises(ValueError, match="capital"):
        DicewareGenerator([wordlist]).generate_passphrase(1, num_capitals=100)


@pytest.mark.parametrize("position", [0, 3, 6, 7, 10, 13])
@pytest.mark.parametrize("separator", [" ", "-"])
def test_diceware_symbols_can_appear_throughout_phrase(wordlist, monkeypatch, position, separator):
    monkeypatch.setattr("secrets.choice", lambda sequence: sequence[0])

    def choose_position(bound):
        assert bound == 14  # Every gap, including before and after the phrase.
        return position

    monkeypatch.setattr("secrets.randbelow", choose_position)
    phrase = DicewareGenerator([wordlist]).generate_passphrase(2, 1, separator=separator)
    original = f"abacus{separator}abacus"
    assert phrase == original[:position] + "!" + original[position:]


def test_diceware_repeated_symbol_positions_preserve_every_addition(wordlist, monkeypatch):
    monkeypatch.setattr("secrets.choice", lambda sequence: sequence[0])
    monkeypatch.setattr("secrets.randbelow", lambda bound: 3)
    phrase = DicewareGenerator([wordlist]).generate_passphrase(1, 20, 6)
    assert phrase == "ABA" + "!" * 20 + "CUS"


@pytest.mark.parametrize("arguments", [(0,), (-1,), (6, -1), (6, 0, -1)])
def test_invalid_diceware_counts(wordlist, arguments):
    with pytest.raises(ValueError):
        DicewareGenerator([wordlist]).generate_passphrase(*arguments)


def test_traditional_requirements():
    generator = TraditionalPasswordGenerator()
    for _ in range(50):
        password = generator.generate_password(20, 3, 4, 3)
        assert len(password) == 20
        assert sum(c in generator.digits for c in password) >= 3
        assert sum(c in generator.symbols for c in password) >= 4
        assert sum(c in generator.uppercase for c in password) >= 3
        assert any(c in generator.lowercase for c in password)


def test_minimum_length_enforces_lowercase(monkeypatch):
    monkeypatch.setattr("secrets.choice", lambda sequence: sequence[0])
    password = TraditionalPasswordGenerator().generate_password(7, 2, 2, 2)
    assert len(password) == 7
    assert sum(c.islower() for c in password) == 1


@pytest.mark.parametrize(
    "arguments", [(0,), (-1,), (1, -10, 2, 2), (16, -1), (16, 1, -1), (16, 1, 1, -1), (3, 1, 1, 1)]
)
def test_invalid_traditional_counts(arguments):
    with pytest.raises(ValueError):
        TraditionalPasswordGenerator().generate_password(*arguments)


def test_global_prng_is_not_used(monkeypatch):
    import random

    def insecure_shuffle(_):
        pytest.fail("Password generation used the global noncryptographic PRNG")

    monkeypatch.setattr(random, "shuffle", insecure_shuffle)
    assert len(TraditionalPasswordGenerator().generate_password(16)) == 16


def test_separator_preserves_word_boundaries(wordlist):
    phrase = DicewareGenerator([wordlist]).generate_passphrase(4, separator="-")
    assert len(phrase.split("-")) == 4
    assert set(phrase.split("-")) <= {"abacus", "banana"}


@pytest.mark.parametrize("separator", ["", "\n", "\t", "ab"])
def test_invalid_separator(wordlist, separator):
    with pytest.raises(ValueError):
        DicewareGenerator([wordlist]).generate_passphrase(4, separator=separator)


def test_character_exclusions():
    generator = TraditionalPasswordGenerator(exclude="0O1lI" + TraditionalPasswordGenerator.symbols)
    for _ in range(20):
        password = generator.generate_password(20, min_symbols=0)
        assert len(password) == 20
        assert not set(password) & set("0O1lI" + TraditionalPasswordGenerator.symbols)


def test_excluded_required_category_is_rejected():
    generator = TraditionalPasswordGenerator(exclude="0123456789")
    with pytest.raises(ValueError, match="digits"):
        generator.generate_password(16)


def test_explicitly_no_lowercase():
    generator = TraditionalPasswordGenerator(exclude="abcdefghijklmnopqrstuvwxyz")
    password = generator.generate_password(16, min_lowercase=0)
    assert not any(char.islower() for char in password)
