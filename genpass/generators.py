"""Local password generation using only operating-system randomness."""

from __future__ import annotations

import re
import secrets
import string
from pathlib import Path

SYMBOLS = "!@#$%^&*()_+-=[]{}|;:,.<>?"


def validate_count(value: int, name: str, minimum: int = 0) -> None:
    if type(value) is not int or value < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")


def load_wordlist(filename: str | Path) -> tuple[str, ...]:
    """Read code/word pairs; deduplicate values without weighting repeated words."""
    words = {}
    codes = set()
    with open(filename, encoding="utf-8") as source:
        for line_number, line in enumerate(source, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            fields = line.split()
            if (
                len(fields) != 2
                or not re.fullmatch(r"[1-6]{5}", fields[0])
                or not fields[1].isprintable()
            ):
                raise ValueError(
                    f"{filename}:{line_number}: expected a five-dice code and one word"
                )
            code, word = fields
            if code in codes:
                raise ValueError(f"{filename}:{line_number}: duplicate dice code {code}")
            codes.add(code)
            words[word] = None
    if len(words) < 2:
        raise ValueError(f"{filename}: wordlist must contain at least two distinct words")
    return tuple(words)


class DicewareGenerator:
    """Choose uniformly from the distinct words in explicitly selected lists."""

    def __init__(self, wordlist_files):
        words = {}
        for filename in wordlist_files:
            words.update(dict.fromkeys(load_wordlist(filename)))
        if not words:
            raise ValueError("At least one wordlist is required")
        self.words = tuple(words)

    def generate_passphrase(self, num_words, num_symbols=0, num_capitals=0, *, separator=" "):
        validate_count(num_words, "Word count", 1)
        validate_count(num_symbols, "Symbol count")
        validate_count(num_capitals, "Capital count")
        if len(separator) != 1 or separator not in string.punctuation + " ":
            raise ValueError("Separator must be one space or ASCII punctuation character")
        words = [list(secrets.choice(self.words)) for _ in range(num_words)]
        eligible = [
            (i, j)
            for i, word in enumerate(words)
            for j, char in enumerate(word)
            if char.islower() and len(char.upper()) == 1
        ]
        if num_capitals > len(eligible):
            raise ValueError("Not enough lowercase letters for the requested capitals")
        for i, j in secrets.SystemRandom().sample(eligible, num_capitals):
            words[i][j] = words[i][j].upper()
        phrase = list(separator.join("".join(word) for word in words))
        for _ in range(num_symbols):
            phrase.insert(secrets.randbelow(len(phrase) + 1), secrets.choice(SYMBOLS))
        return "".join(phrase)


class TraditionalPasswordGenerator:
    """Meet character minima, then securely shuffle the completed password."""

    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    symbols = SYMBOLS

    def __init__(self, exclude=""):
        for name in ("lowercase", "uppercase", "digits", "symbols"):
            setattr(
                self, name, "".join(char for char in getattr(self, name) if char not in exclude)
            )
        if not self.lowercase + self.uppercase + self.digits + self.symbols:
            raise ValueError("Exclusions leave no allowed characters")

    def generate_password(
        self, length, min_digits=1, min_symbols=1, min_uppercase=1, *, min_lowercase=1
    ):
        validate_count(length, "Length", 1)
        groups = [
            (self.digits, min_digits, "Minimum digits"),
            (self.symbols, min_symbols, "Minimum symbols"),
            (self.uppercase, min_uppercase, "Minimum uppercase"),
            (self.lowercase, min_lowercase, "Minimum lowercase"),
        ]
        for alphabet, count, name in groups:
            validate_count(count, name)
            if count and not alphabet:
                raise ValueError(f"{name} cannot be satisfied after character exclusions")
        if length < sum(count for _, count, _ in groups):
            raise ValueError(
                "Length too short for specified minimum requirements (including lowercase)"
            )
        password = []
        for alphabet, count, _ in groups:
            password.extend(secrets.choice(alphabet) for _ in range(count))
        alphabet = self.lowercase + self.uppercase + self.digits + self.symbols
        password.extend(secrets.choice(alphabet) for _ in range(length - len(password)))
        secrets.SystemRandom().shuffle(password)
        return "".join(password)
