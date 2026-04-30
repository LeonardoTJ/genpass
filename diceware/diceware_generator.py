import random
import secrets
import sys
from pathlib import Path


class DicewareGenerator:
    """Generates secure passphrases using the Diceware method"""

    def __init__(self, wordlist_files):
        """
        Initialize with word list files

        Args:
            wordlist_files: List of paths to diceware word list files
        """
        self.wordlists = []
        for filepath in wordlist_files:
            if Path(filepath).exists():
                self.wordlists.append(self._load_wordlist(filepath))
            else:
                print(f"Warning: {filepath} not found, skipping", file=sys.stderr)

        if not self.wordlists:
            raise FileNotFoundError("No valid wordlist files found")

        self.special_chars = [
            "~!#$%^",
            "&*()-=",
            "+[]\\{}",
            ":;\"'<>",
            "?/0123",
            "456789",
        ]

    def _load_wordlist(self, filename):
        """Load a diceware wordlist from file"""
        wordlist = {}
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split(None, 1)
                if len(parts) == 2:
                    code, word = parts
                    wordlist[code] = word
        return wordlist

    def _dice_roll(self):
        """Simulate rolling five dice using cryptographically secure random"""
        return "".join(str(secrets.randbelow(6) + 1) for _ in range(5))

    def _get_random_special_char(self):
        """Get a random special character"""
        row = secrets.randbelow(len(self.special_chars))
        col = secrets.randbelow(len(self.special_chars[row]))
        return self.special_chars[row][col]

    def _insert_special_char(self, words):
        """Insert a random special character into a random word"""
        if not words:
            return words

        word_idx = secrets.randbelow(len(words))
        word = words[word_idx]

        if len(word) > 0:
            char_idx = secrets.randbelow(len(word))
            word = (
                word[:char_idx] + self._get_random_special_char() + word[char_idx + 1 :]
            )
            words[word_idx] = word

        return words

    def _capitalize_random_letter(self, words):
        """Capitalize a random letter in a random word"""
        if not words:
            return words

        word_idx = secrets.randbelow(len(words))
        word = words[word_idx]

        if len(word) > 0:
            char_idx = secrets.randbelow(len(word))
            word = word[:char_idx] + word[char_idx].upper() + word[char_idx + 1 :]
            words[word_idx] = word

        return words

    def generate_passphrase(self, num_words, num_symbols=0, num_capitals=0):
        """
        Generate a single diceware passphrase

        Args:
            num_words: Number of words in the passphrase
            num_symbols: Number of random symbols to insert
            num_capitals: Number of letters to capitalize

        Returns:
            Generated passphrase as a string
        """
        words = []

        # Generate words
        for _ in range(num_words):
            dice_code = self._dice_roll()
            wordlist = secrets.choice(self.wordlists)
            # If exact code not found, try to find closest match
            word = wordlist.get(
                dice_code, list(wordlist.values())[secrets.randbelow(len(wordlist))]
            )
            words.append(word)

        # Insert symbols
        for _ in range(num_symbols):
            words = self._insert_special_char(words)

        # Capitalize letters
        for _ in range(num_capitals):
            words = self._capitalize_random_letter(words)

        return " ".join(words)
