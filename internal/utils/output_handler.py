import time
import sys
import secrets
import getpass
from typing import List


class OutputHandler:
    """Handles password output with masking and encryption options"""

    @staticmethod
    def print_masked(passwords: List[str], reveal_after: int = 3) -> None:
        """
        Print passwords masked, then reveal after countdown
        """
        print("\n" + "=" * 60)
        print("GENERATED PASSWORDS (masked)")
        print("=" * 60)
        for i, pwd in enumerate(passwords, 1):
            print(f"{i}. {'*' * min(len(pwd), 20)}")

        print(f"\nPasswords will be revealed in {reveal_after} seconds...")
        for i in range(reveal_after, 0, -1):
            print(f"{i}...", end=" ", flush=True)
            time.sleep(1)
        print("\n")

        print("=" * 60)
        print("REVEALED PASSWORDS")
        print("=" * 60)
        for i, pwd in enumerate(passwords, 1):
            print(f"{i}. {pwd}")
        print("=" * 60 + "\n")

    @staticmethod
    def save_encrypted(
        passwords: List[str], output_file: str, password: str = None
    ) -> bool:
        """
        Save passwords to an encrypted file using AES encryption
        """
        try:
            # These imports are needed for the functionality, moved to where they are used
            from cryptography.fernet import Fernet
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
            import base64
        except ImportError:
            print(
                "Error: cryptography library required for encryption", file=sys.stderr
            )
            print("Install with: pip install cryptography", file=sys.stderr)
            return False

        if password is None:
            # Note: getpass is imported at the top level now
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
        content = "\n".join(passwords).encode()
        encrypted = fernet.encrypt(content)

        # Save with salt
        with open(output_file, "wb") as f:
            f.write(salt)
            f.write(encrypted)

        print(f"\nPasswords encrypted and saved to: {output_file}")
        print("Keep your encryption password safe!")
        return True

    @staticmethod
    def load_encrypted(input_file: str, password: str = None) -> List[str] | None:
        """
        Load and decrypt passwords from an encrypted file
        """
        try:
            from cryptography.fernet import Fernet, InvalidToken
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
            import base64
        except ImportError:
            print(
                "Error: cryptography library required for decryption", file=sys.stderr
            )
            return None

        if password is None:
            # Note: getpass is imported at the top level now
            password = getpass.getpass("Enter decryption password: ")

        try:
            with open(input_file, "rb") as f:
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

            passwords = decrypted.decode().split("\n")
            # Filter out empty strings that might result from trailing newlines
            return [p for p in passwords if p]

        except InvalidToken:
            print("Error: Invalid password or corrupted file", file=sys.stderr)
            return None
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return None
