# Advanced Password Generator

A secure password generator that creates both **Diceware-style passphrases** and **traditional random passwords** with encryption support.

## Features

- **Two Generation Modes:**
  - Diceware passphrases: Memorable, secure phrases from word lists
  - Traditional passwords: Random character combinations

- **Security Features:**
  - Uses `secrets` module for cryptographically secure randomness
  - Optional output masking with timed reveal
  - AES encryption for saved passwords
  - Multiple language support for Diceware

- **Customizable Parameters:**
  - Control password length, complexity, and composition
  - Adjustable symbol and uppercase letter insertion
  - Batch generation support

## Installation

1. **Basic usage** (no encryption):
   ```bash
   chmod +x genpass.py
   ```

2. **For encryption features**:
   ```bash
   pip install cryptography
   ```

## Directory Structure

```
project/
├── genpass.py                    # Main script
├── diceware.wordlist.asc         # English wordlist
├── diceware_jp.txt               # Japanese wordlist (optional)
└── DW-Espanol-1.txt              # Spanish wordlist (optional)
```

## Usage Examples

### Diceware Passphrases

**Basic passphrase (6 words):**
```bash
./genpass.py diceware
```
Output: `ability airport alarm already amount anchor`

**Multiple passphrases with symbols:**
```bash
./genpass.py diceware -n 3 -w 5 -s 2
```
Output:
```
1. abacus ab@ndon ability able ab#ut
2. above absent a&sorb abstract ab$urd
3. abuse access accid*nt account acc+se
```

**With capitalization and symbols:**
```bash
./genpass.py diceware -w 6 -s 3 -c 2
```
Output: `Ability airPort al@rm alreaDy am%unt anc^or`

### Traditional Passwords

**Standard 16-character password:**
```bash
./genpass.py traditional -l 16
```
Output: `K9#mP2$xL5@nR8!q`

**Multiple passwords with specific requirements:**
```bash
./genpass.py traditional -n 5 -l 20 -d 3 -s 4 -u 3
```
Output:
```
1. A7#k9P@mX2$nB5!tQ8z
2. M3$x7K@nP9#rT2!jL6&q
3. R5!n8B@mK3$pX7#tL9+j
```

**Explanation:**
- `-n 5`: Generate 5 passwords
- `-l 20`: Each password is 20 characters long
- `-d 3`: At least 3 digits in each
- `-s 4`: At least 4 symbols in each
- `-u 3`: At least 3 uppercase letters in each

### Security Features

**Masked output (reveals after 3 seconds):**
```bash
./genpass.py diceware -n 3 -w 5 --mask
```
Output shows asterisks initially, then reveals:
```
============================================================
GENERATED PASSWORDS (masked)
============================================================
1. ********************
2. ********************
3. ********************

Passwords will be revealed in 3 seconds...
3... 2... 1... 

============================================================
REVEALED PASSWORDS
============================================================
1. ability airport alarm already amount
2. above absent absorb abstract absurd
3. abuse access accident account accuse
============================================================
```

**Save to encrypted file:**
```bash
./genpass.py traditional -n 10 -l 16 -o passwords.enc --encrypt
```
You'll be prompted:
```
Enter encryption password: ********
Confirm password: ********

Passwords encrypted and saved to: passwords.enc
Keep your encryption password safe!
```

**Decrypt saved passwords:**
```bash
./genpass.py decrypt passwords.enc
```
Output:
```
Enter decryption password: ********

Decrypted passwords:
============================================================
1. K9#mP2$xL5@nR8!q
2. X7$nT3@kM9#pL2!r
...
============================================================
```

**Save to plain text file:**
```bash
./genpass.py diceware -n 5 -w 6 -o my_passwords.txt
```

## Real-World Use Cases

### 1. Website Account Creation
Generate a memorable passphrase for a new account:
```bash
./genpass.py diceware -w 4 -s 1 -c 1
```
Example: `Ability airp@rt Alarm already`

### 2. Database Password
Generate a complex traditional password:
```bash
./genpass.py traditional -l 24 -d 4 -s 4 -u 4
```
Example: `K9#mP2$xL5@nR8!qT3&jM7%p`

### 3. Secure Password Vault
Generate 20 passwords and save encrypted:
```bash
./genpass.py traditional -n 20 -l 16 -o vault.enc --encrypt
```

### 4. Team Password Distribution
Generate passwords with masked display for presentations:
```bash
./genpass.py diceware -n 5 -w 5 -s 1 --mask
```

### 5. API Keys or Tokens
Generate very long, complex passwords:
```bash
./genpass.py traditional -l 32 -d 6 -s 6 -u 6
```

## Command Reference

### Diceware Mode
```
genpass.py diceware [OPTIONS]

Options:
  -n, --num-phrases NUM     Number of passphrases (default: 1)
  -w, --words NUM           Words per passphrase (default: 6)
  -s, --symbols NUM         Random symbols to insert (default: 0)
  -c, --capitals NUM        Letters to capitalize (default: 0)
  --wordlists FILES         Custom wordlist files
  --mask                    Mask output initially
  -o, --output FILE         Save to file
  --encrypt                 Encrypt output file
```

### Traditional Mode
```
genpass.py traditional [OPTIONS]

Options:
  -n, --num-passwords NUM   Number of passwords (default: 1)
  -l, --length NUM          Password length (default: 16)
  -d, --min-digits NUM      Minimum digits (default: 2)
  -s, --min-symbols NUM     Minimum symbols (default: 2)
  -u, --min-uppercase NUM   Minimum uppercase (default: 2)
  --mask                    Mask output initially
  -o, --output FILE         Save to file
  --encrypt                 Encrypt output file
```

### Decrypt Mode
```
genpass.py decrypt FILE
```

## Security Considerations

### Why Diceware?
- **Memorable**: Easier to remember than random characters
- **Secure**: 6 words = ~77 bits of entropy
- **Practical**: Can be typed accurately without copy-paste

### Why Traditional?
- **Maximum entropy**: Pure randomness
- **Length-constrained**: When you have character limits
- **Symbol requirements**: Meets strict password policies

### Best Practices

1. **Passphrase strength**: Use at least 6 words for Diceware
   ```bash
   ./genpass.py diceware -w 6
   ```

2. **Traditional password strength**: Use at least 16 characters
   ```bash
   ./genpass.py traditional -l 16
   ```

3. **Add complexity**: Mix in symbols and capitals
   ```bash
   ./genpass.py diceware -w 6 -s 2 -c 2
   ```

4. **Secure storage**: Always encrypt saved passwords
   ```bash
   ./genpass.py traditional -n 10 -o vault.enc --encrypt
   ```

5. **Never reuse**: Generate unique passwords for each service

## Encryption Details

The encryption feature uses:
- **Algorithm**: AES (via Fernet symmetric encryption)
- **Key derivation**: PBKDF2 with SHA-256
- **Iterations**: 100,000 rounds
- **Salt**: 16 random bytes per file

This means:
- Each encrypted file has a unique salt
- Password-based encryption (you choose the password)
- Industry-standard security
- Safe to store in cloud storage (with strong password)

## Wordlist Format

Diceware wordlists should follow this format:
```
11111	word1
11112	word2
11113	word3
```

Where:
- First column: 5-digit dice roll (1-6 for each digit)
- Second column: Corresponding word
- Separated by tab or space

## Troubleshooting

**"No valid wordlist files found"**
- Ensure wordlist files are in the same directory as the script
- Or specify custom paths: `--wordlists /path/to/wordlist.txt`

**"cryptography library required"**
- Install with: `pip install cryptography`
- Only needed for encryption features

**"Invalid password or corrupted file"**
- Double-check your decryption password
- File may be corrupted (encryption is all-or-nothing)

**"Length too short for specified minimum requirements"**
- Your minimum requirements (digits + symbols + uppercase) exceed total length
- Either increase length or reduce minimum requirements

## Contributing

To add new wordlists:
1. Format as dice-code + word pairs
2. Place in script directory
3. Specify with `--wordlists` option

## Examples Summary

| Use Case | Command |
|----------|---------|
| Quick passphrase | `./genpass.py diceware` |
| Strong passphrase | `./genpass.py diceware -w 7 -s 2 -c 2` |
| Simple password | `./genpass.py traditional` |
| Complex password | `./genpass.py traditional -l 20 -d 4 -s 4` |
| Batch generation | `./genpass.py traditional -n 10` |
| Secure storage | `./genpass.py traditional -n 10 -o vault.enc --encrypt` |
| Team presentation | `./genpass.py diceware -n 5 --mask` |
