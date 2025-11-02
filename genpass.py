#!/usr/bin/env python3
"""
Advanced Password Generator
Supports both Diceware passphrases and traditional random passwords
"""
import random
import sys
import argparse
import secrets
import getpass
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
            "456789"
        ]
    
    def _load_wordlist(self, filename):
        """Load a diceware wordlist from file"""
        wordlist = {}
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split(None, 1)
                if len(parts) == 2:
                    code, word = parts
                    wordlist[code] = word
        return wordlist
    
    def _dice_roll(self):
        """Simulate rolling five dice using cryptographically secure random"""
        return ''.join(str(secrets.randbelow(6) + 1) for _ in range(5))
    
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
            word = word[:char_idx] + self._get_random_special_char() + word[char_idx+1:]
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
            word = word[:char_idx] + word[char_idx].upper() + word[char_idx+1:]
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
            word = wordlist.get(dice_code, list(wordlist.values())[secrets.randbelow(len(wordlist))])
            words.append(word)
        
        # Insert symbols
        for _ in range(num_symbols):
            words = self._insert_special_char(words)
        
        # Capitalize letters
        for _ in range(num_capitals):
            words = self._capitalize_random_letter(words)
        
        return ' '.join(words)


class TraditionalPasswordGenerator:
    """Generates traditional random character passwords"""
    
    def __init__(self):
        self.lowercase = 'abcdefghijklmnopqrstuvwxyz'
        self.uppercase = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        self.digits = '0123456789'
        self.symbols = '!@#$%^&*()_+-=[]{}|;:,.<>?'
    
    def generate_password(self, length, min_digits=1, min_symbols=1, min_uppercase=1):
        """
        Generate a traditional random password
        
        Args:
            length: Total length of password
            min_digits: Minimum number of digits
            min_symbols: Minimum number of symbols
            min_uppercase: Minimum number of uppercase letters
            
        Returns:
            Generated password as a string
        """
        if length < (min_digits + min_symbols + min_uppercase + 1):
            raise ValueError("Length too short for specified minimum requirements")
        
        password = []
        
        # Ensure minimum requirements
        password.extend(secrets.choice(self.digits) for _ in range(min_digits))
        password.extend(secrets.choice(self.symbols) for _ in range(min_symbols))
        password.extend(secrets.choice(self.uppercase) for _ in range(min_uppercase))
        
        # Fill remaining with random characters from all sets
        all_chars = self.lowercase + self.uppercase + self.digits + self.symbols
        remaining = length - len(password)
        password.extend(secrets.choice(all_chars) for _ in range(remaining))
        
        # Shuffle to randomize positions
        random.shuffle(password)
        
        return ''.join(password)


class OutputHandler:
    """Handles password output with masking and encryption options"""
    
    @staticmethod
    def print_masked(passwords, reveal_after=3):
        """
        Print passwords masked, then reveal after countdown
        
        Args:
            passwords: List of passwords to display
            reveal_after: Seconds to wait before revealing
        """
        import time
        
        print("\n" + "="*60)
        print("GENERATED PASSWORDS (masked)")
        print("="*60)
        for i, pwd in enumerate(passwords, 1):
            print(f"{i}. {'*' * min(len(pwd), 20)}")
        
        print(f"\nPasswords will be revealed in {reveal_after} seconds...")
        for i in range(reveal_after, 0, -1):
            print(f"{i}...", end=' ', flush=True)
            time.sleep(1)
        print("\n")
        
        print("="*60)
        print("REVEALED PASSWORDS")
        print("="*60)
        for i, pwd in enumerate(passwords, 1):
            print(f"{i}. {pwd}")
        print("="*60 + "\n")
    
    @staticmethod
    def save_encrypted(passwords, output_file, password=None):
        """
        Save passwords to an encrypted file using AES encryption
        
        Args:
            passwords: List of passwords to save
            output_file: Path to output file
            password: Encryption password (will prompt if not provided)
        """
        try:
            from cryptography.fernet import Fernet
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
            import base64
        except ImportError:
            print("Error: cryptography library required for encryption", file=sys.stderr)
            print("Install with: pip install cryptography", file=sys.stderr)
            return False
        
        if password is None:
            password = getpass.getpass("Enter encryption password: ")
            confirm = getpass.getpass("Confirm password: ")
            if password != confirm:
                print("Passwords don't match!", file=sys.stderr)
                return False
        
        # Generate key from password
        salt = secrets.token_bytes(16)
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        
        # Encrypt content
        fernet = Fernet(key)
        content = '\n'.join(passwords).encode()
        encrypted = fernet.encrypt(content)
        
        # Save with salt
        with open(output_file, 'wb') as f:
            f.write(salt)
            f.write(encrypted)
        
        print(f"\nPasswords encrypted and saved to: {output_file}")
        print("Keep your encryption password safe!")
        return True
    
    @staticmethod
    def load_encrypted(input_file, password=None):
        """
        Load and decrypt passwords from an encrypted file
        
        Args:
            input_file: Path to encrypted file
            password: Decryption password (will prompt if not provided)
            
        Returns:
            List of decrypted passwords
        """
        try:
            from cryptography.fernet import Fernet, InvalidToken
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
            import base64
        except ImportError:
            print("Error: cryptography library required for decryption", file=sys.stderr)
            return None
        
        if password is None:
            password = getpass.getpass("Enter decryption password: ")
        
        try:
            with open(input_file, 'rb') as f:
                salt = f.read(16)
                encrypted = f.read()
            
            # Derive key from password
            kdf = PBKDF2(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            
            # Decrypt
            fernet = Fernet(key)
            decrypted = fernet.decrypt(encrypted)
            
            passwords = decrypted.decode().split('\n')
            return passwords
            
        except InvalidToken:
            print("Error: Invalid password or corrupted file", file=sys.stderr)
            return None
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return None


def main():
    parser = argparse.ArgumentParser(
        description='Advanced Password Generator - Diceware and Traditional',
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
        """
    )
    
    subparsers = parser.add_subparsers(dest='mode', help='Generation mode')
    
    # Diceware passphrase mode
    diceware_parser = subparsers.add_parser('diceware', help='Generate diceware passphrases')
    diceware_parser.add_argument('-n', '--num-phrases', type=int, default=1,
                                 help='Number of passphrases to generate (default: 1)')
    diceware_parser.add_argument('-w', '--words', type=int, default=6,
                                 help='Number of words per passphrase (default: 6)')
    diceware_parser.add_argument('-s', '--symbols', type=int, default=0,
                                 help='Number of random symbols to insert (default: 0)')
    diceware_parser.add_argument('-c', '--capitals', type=int, default=0,
                                 help='Number of letters to capitalize (default: 0)')
    diceware_parser.add_argument('--wordlists', nargs='+',
                                 default=['diceware.wordlist.asc', 'diceware_jp.txt', 'DW-Espanol-1.txt'],
                                 help='Wordlist files to use')
    
    # Traditional password mode
    trad_parser = subparsers.add_parser('traditional', help='Generate traditional passwords')
    trad_parser.add_argument('-n', '--num-passwords', type=int, default=1,
                            help='Number of passwords to generate (default: 1)')
    trad_parser.add_argument('-l', '--length', type=int, default=16,
                            help='Password length (default: 16)')
    trad_parser.add_argument('-d', '--min-digits', type=int, default=2,
                            help='Minimum number of digits (default: 2)')
    trad_parser.add_argument('-s', '--min-symbols', type=int, default=2,
                            help='Minimum number of symbols (default: 2)')
    trad_parser.add_argument('-u', '--min-uppercase', type=int, default=2,
                            help='Minimum uppercase letters (default: 2)')
    
    # Decrypt mode
    decrypt_parser = subparsers.add_parser('decrypt', help='Decrypt saved passwords')
    decrypt_parser.add_argument('input_file', help='Encrypted file to decrypt')
    
    # Common options
    for subparser in [diceware_parser, trad_parser]:
        subparser.add_argument('--mask', action='store_true',
                              help='Mask output initially, reveal after countdown')
        subparser.add_argument('-o', '--output', help='Save to file')
        subparser.add_argument('--encrypt', action='store_true',
                              help='Encrypt output file (requires -o)')
    
    args = parser.parse_args()
    
    if args.mode == 'decrypt':
        passwords = OutputHandler.load_encrypted(args.input_file)
        if passwords:
            print("\nDecrypted passwords:")
            print("="*60)
            for i, pwd in enumerate(passwords, 1):
                print(f"{i}. {pwd}")
            print("="*60)
        return
    
    if not args.mode:
        parser.print_help()
        return
    
    # Generate passwords
    passwords = []
    
    try:
        if args.mode == 'diceware':
            generator = DicewareGenerator(args.wordlists)
            for _ in range(args.num_phrases):
                passphrase = generator.generate_passphrase(
                    args.words,
                    args.symbols,
                    args.capitals
                )
                passwords.append(passphrase)
        
        elif args.mode == 'traditional':
            generator = TraditionalPasswordGenerator()
            for _ in range(args.num_passwords):
                password = generator.generate_password(
                    args.length,
                    args.min_digits,
                    args.min_symbols,
                    args.min_uppercase
                )
                passwords.append(password)
    
    except Exception as e:
        print(f"Error generating passwords: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Handle output
    if args.output:
        if args.encrypt:
            OutputHandler.save_encrypted(passwords, args.output)
        else:
            with open(args.output, 'w') as f:
                f.write('\n'.join(passwords))
            print(f"\nPasswords saved to: {args.output}")
    
    # Display passwords
    if args.mask:
        OutputHandler.print_masked(passwords)
    else:
        print("\nGenerated Passwords:")
        print("="*60)
        for i, pwd in enumerate(passwords, 1):
            print(f"{i}. {pwd}")
        print("="*60 + "\n")


if __name__ == '__main__':
    main()
