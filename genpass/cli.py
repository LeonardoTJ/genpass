"""Argument parsing and terminal interaction for the local password generator."""

from __future__ import annotations

import argparse
import getpass
import sys
import warnings

from genpass import __version__, default_wordlists
from genpass.generators import DicewareGenerator, TraditionalPasswordGenerator, validate_count
from genpass.storage import (
    EncryptionError,
    load_encrypted,
    require_encryption,
    save_encrypted,
    write_private,
)


def positive(value):
    number = int(value)
    validate_count(number, "Value", 1)
    return number


def nonnegative(value):
    number = int(value)
    validate_count(number, "Value")
    return number


def build_parser():
    parser = argparse.ArgumentParser(
        description="Generate local Diceware passphrases or random passwords"
    )
    parser.add_argument("--version", action="version", version=f"genpass {__version__}")
    modes = parser.add_subparsers(dest="mode")
    dice = modes.add_parser("diceware", help="Generate passphrases (default: English/Spanish/Japanese)")
    dice.add_argument("-n", "--num-phrases", type=positive, default=1)
    dice.add_argument("-w", "--words", type=positive, default=6)
    dice.add_argument(
        "-s", "--symbols", type=nonnegative, default=0,
        help="Punctuation characters to insert at random positions",
    )
    dice.add_argument(
        "-c",
        "--capitals",
        type=nonnegative,
        default=0,
        help="Distinct lowercase letters to capitalize",
    )
    lists = dice.add_mutually_exclusive_group()
    lists.add_argument(
        "--language",
        choices=("all", "en", "ja", "es"),
        help="Bundled language (default: all; ja/es are legacy lists)",
    )
    lists.add_argument(
        "--wordlists",
        nargs="+",
        help="Explicit wordlist files; select from their distinct-word union",
    )
    dice.add_argument(
        "--separator", default=" ", help="One space or punctuation character (default: space)"
    )
    traditional = modes.add_parser("traditional", help="Generate random character passwords")
    traditional.add_argument("-n", "--num-passwords", type=positive, default=1)
    traditional.add_argument("-l", "--length", type=positive, default=16)
    traditional.add_argument("-d", "--min-digits", type=nonnegative, default=2)
    traditional.add_argument("-s", "--min-symbols", type=nonnegative, default=2)
    traditional.add_argument("-u", "--min-uppercase", type=nonnegative, default=2)
    traditional.add_argument("--min-lowercase", type=nonnegative, default=1)
    traditional.add_argument(
        "--exclude", default="", help="Characters to remove from every alphabet"
    )
    for mode in (dice, traditional):
        mode.add_argument(
            "-o", "--output", help="Save privately to a new file without displaying passwords"
        )
        mode.add_argument(
            "--encrypt", action="store_true", help="Encrypt the output file (requires -o)"
        )
        mode.add_argument(
            "--mask",
            action="store_true",
            help="Wait for Enter before revealing on an interactive terminal",
        )
        mode.add_argument(
            "--plain", action="store_true", help="Print one password per line without decoration"
        )
    decrypt = modes.add_parser("decrypt", help="Decrypt a saved file")
    decrypt.add_argument("input_file")
    decrypt.add_argument(
        "--plain", action="store_true", help="Print one password per line without decoration"
    )
    return parser


def _read_password(confirm=False):
    # getpass otherwise falls back to echoing input on a noninteractive stream.
    with warnings.catch_warnings():
        warnings.simplefilter("error", getpass.GetPassWarning)
        try:
            password = getpass.getpass(
                "Encryption password: " if confirm else "Decryption password: "
            )
            if confirm:
                if not password:
                    raise EncryptionError("Encryption password must not be empty")
                if password != getpass.getpass("Confirm password: "):
                    raise EncryptionError("Passwords do not match")
            return password
        except getpass.GetPassWarning as error:
            raise EncryptionError(
                "A terminal with hidden input is required for the password prompt"
            ) from error


def _display(passwords, plain=False):
    if plain:
        print("\n".join(passwords))
        return
    print("\nGenerated passwords:")
    for index, password in enumerate(passwords, 1):
        print(f"{index}. {password}")


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.mode is None:
        parser.print_help()
        return 0
    if args.mode != "decrypt":
        if args.encrypt and not args.output:
            parser.error("--encrypt requires --output")
        if args.mask and args.output:
            parser.error("--mask is only available for terminal output")
        if args.mask and args.plain:
            parser.error("--mask cannot be combined with --plain")
    try:
        if args.mode == "decrypt":
            require_encryption()
            passwords = load_encrypted(args.input_file, _read_password())
            _display(passwords, args.plain)
            return 0
        if args.mask and not (sys.stdin.isatty() and sys.stdout.isatty()):
            raise ValueError("--mask requires an interactive terminal")
        try:
            if args.mode == "diceware":
                generator = DicewareGenerator(
                    args.wordlists or default_wordlists(args.language or "all")
                )
                passwords = [
                    generator.generate_passphrase(
                        args.words, args.symbols, args.capitals, separator=args.separator
                    )
                    for _ in range(args.num_phrases)
                ]
            else:
                generator = TraditionalPasswordGenerator(exclude=args.exclude)
                passwords = [
                    generator.generate_password(
                        args.length,
                        args.min_digits,
                        args.min_symbols,
                        args.min_uppercase,
                        min_lowercase=args.min_lowercase,
                    )
                    for _ in range(args.num_passwords)
                ]
        except ValueError as error:
            parser.error(str(error))
        if args.output:
            if args.encrypt:
                require_encryption()
                save_encrypted(passwords, args.output, _read_password(confirm=True))
            else:
                write_private(args.output, ("\n".join(passwords) + "\n").encode("utf-8"))
            print(f"Saved to: {args.output}", file=sys.stderr)
            return 0
        if args.mask:
            print("Passwords ready. Press Enter to reveal, or Ctrl-C to cancel.", file=sys.stderr)
            if sys.stdin.readline() != "\n":
                raise ValueError("Reveal cancelled")
        _display(passwords, args.plain)
        return 0
    except (OSError, ValueError, EOFError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Cancelled.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
