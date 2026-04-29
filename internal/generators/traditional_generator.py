import secrets
import random


class TraditionalPasswordGenerator:
    """Generates traditional random character passwords"""

    def __init__(self):
        self.lowercase = "abcdefghijklmnopqrstuvwxyz"
        self.uppercase = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        self.digits = "0123456789"
        self.symbols = "!@#$%^&*()_+-=[]{}|;:,.<>?"

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

        return "".join(password)


if __name__ == "__main__":
    generator = TraditionalPasswordGenerator()
    password = generator.generate_password(length=16)
    print(f"Generated Password: {password}")
