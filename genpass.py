#!/usr/bin/env python3
"""
Advanced Password Generator
Supports both Diceware passphrases and traditional random passwords
"""

import sys
import argparse
from diceware.diceware_generator import DicewareGenerator
from internal.generators.traditional_generator import TraditionalPasswordGenerator
from internal.utils.output_handler import OutputHandler


def main():
    parser = argparse.ArgumentParser(
        description="Advanced Password Generator - Diceware and Traditional",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate 3 diceware passphrases with 6 words, 2 symbols each
  %(prog)s diceware -n 3 -w 6 -s 2

  # Generate 5 traditional passwords, 16 chars long
  %(prog)s traditional -n 5 -l 16

  # Generate with masked output
  %(prog)s diceware -n 3 -w 5 --mask

  # Generate and save encrypted
  %(prog)s traditional -n 10 -l 20 -o passwords.enc --encrypt

  # Decrypt and view saved passwords
  %(prog)s decrypt passwords.enc
        """,
    )

    subparsers = parser.add_subparsers(dest="mode", help="Generation mode")

    diceware_parser = subparsers.add_parser(
        "diceware", help="Generate diceware passphrases"
    )
    diceware_parser.add_argument(
        "-n", "--num-phrases", type=int, default=1,
        help="Number of passphrases to generate (default: 1)",
    )
    diceware_parser.add_argument(
        "-w", "--words", type=int, default=6,
        help="Number of words per passphrase (default: 6)",
    )
    diceware_parser.add_argument(
        "-s", "--symbols", type=int, default=0,
        help="Number of random symbols to insert (default: 0)",
    )
    diceware_parser.add_argument(
        "-c", "--capitals", type=int, default=0,
        help="Number of letters to capitalize (default: 0)",
    )
    diceware_parser.add_argument(
        "--wordlists", nargs="+",
        default=["diceware.wordlist.asc", "diceware_jp.txt", "DW-Espanol-1.txt"],
        help="Wordlist files to use",
    )

    trad_parser = subparsers.add_parser(
        "traditional", help="Generate traditional passwords"
    )
    trad_parser.add_argument(
        "-n", "--num-passwords", type=int, default=1,
        help="Number of passwords to generate (default: 1)",
    )
    trad_parser.add_argument(
        "-l", "--length", type=int, default=16,
        help="Password length (default: 16)",
    )
    trad_parser.add_argument(
        "-d", "--min-digits", type=int, default=2,
        help="Minimum number of digits (default: 2)",
    )
    trad_parser.add_argument(
        "-s", "--min-symbols", type=int, default=2,
        help="Minimum number of symbols (default: 2)",
    )
    trad_parser.add_argument(
        "-u", "--min-uppercase", type=int, default=2,
        help="Minimum uppercase letters (default: 2)",
    )

    decrypt_parser = subparsers.add_parser("decrypt", help="Decrypt saved passwords")
    decrypt_parser.add_argument("input_file", help="Encrypted file to decrypt")

    for subparser in [diceware_parser, trad_parser]:
        subparser.add_argument(
            "--mask", action="store_true",
            help="Mask output initially, reveal after countdown",
        )
        subparser.add_argument("-o", "--output", help="Save to file")
        subparser.add_argument(
            "--encrypt", action="store_true",
            help="Encrypt output file (requires -o)",
        )

    args = parser.parse_args()

    if not args.mode:
        parser.print_help()
        return

    if args.mode == "decrypt":
        passwords = OutputHandler.load_encrypted(args.input_file)
        if passwords:
            print("\nDecrypted passwords:")
            print("=" * 60)
            for i, pwd in enumerate(passwords, 1):
                print(f"{i}. {pwd}")
            print("=" * 60)
        return

    passwords = []

    try:
        if args.mode == "diceware":
            generator = DicewareGenerator(args.wordlists)
            for _ in range(args.num_phrases):
                passwords.append(generator.generate_passphrase(
                    args.words, args.symbols, args.capitals
                ))

        elif args.mode == "traditional":
            generator = TraditionalPasswordGenerator()
            for _ in range(args.num_passwords):
                passwords.append(generator.generate_password(
                    args.length, args.min_digits, args.min_symbols, args.min_uppercase
                ))

    except Exception as e:
        print(f"Error generating passwords: {e}", file=sys.stderr)
        sys.exit(1)

    if args.output:
        if args.encrypt:
            OutputHandler.save_encrypted(passwords, args.output)
        else:
            with open(args.output, "w") as f:
                f.write("\n".join(passwords))
            print(f"\nPasswords saved to: {args.output}")

    if args.mask:
        OutputHandler.print_masked(passwords)
    else:
        print("\nGenerated Passwords:")
        print("=" * 60)
        for i, pwd in enumerate(passwords, 1):
            print(f"{i}. {pwd}")
        print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
