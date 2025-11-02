#!/usr/bin/env python3
"""
Test suite for the password generator
Run this to verify everything works correctly
"""
import subprocess
import sys
import os
from pathlib import Path


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    RESET = '\033[0m'
    BLUE = '\033[94m'


def print_test(message):
    print(f"\n{Colors.BLUE}▶ {message}{Colors.RESET}")


def print_success(message):
    print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")


def print_error(message):
    print(f"{Colors.RED}✗ {message}{Colors.RESET}")


def print_warning(message):
    print(f"{Colors.YELLOW}⚠ {message}{Colors.RESET}")


def run_command(cmd):
    """Run a command and return output"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"


def test_basic_diceware():
    """Test basic diceware generation"""
    print_test("Testing basic diceware passphrase generation...")
    
    success, stdout, stderr = run_command("./genpass.py diceware")
    
    if success and stdout.strip():
        words = stdout.strip().split('\n')[-1].split()
        if len(words) >= 5:
            print_success(f"Generated passphrase: {stdout.strip()}")
            return True
    
    print_error(f"Failed: {stderr}")
    return False


def test_diceware_with_options():
    """Test diceware with custom options"""
    print_test("Testing diceware with 4 words, 1 symbol, 1 capital...")
    
    success, stdout, stderr = run_command("./genpass.py diceware -n 2 -w 4 -s 1 -c 1")
    
    if success and stdout.strip():
        lines = [l for l in stdout.strip().split('\n') if l and not l.startswith('=')]
        if len(lines) >= 2:
            print_success(f"Generated {len(lines)} passphrases")
            for i, line in enumerate(lines, 1):
                print(f"  {i}. {line}")
            return True
    
    print_error(f"Failed: {stderr}")
    return False


def test_traditional_password():
    """Test traditional password generation"""
    print_test("Testing traditional password generation...")
    
    success, stdout, stderr = run_command("./genpass.py traditional -l 16")
    
    if success and stdout.strip():
        lines = [l for l in stdout.strip().split('\n') if l and not l.startswith('=')]
        password = lines[-1].split('. ')[-1] if lines else ""
        
        if len(password) >= 16:
            print_success(f"Generated 16-char password: {password}")
            return True
    
    print_error(f"Failed: {stderr}")
    return False


def test_traditional_with_requirements():
    """Test traditional password with specific requirements"""
    print_test("Testing traditional with minimum requirements...")
    
    success, stdout, stderr = run_command(
        "./genpass.py traditional -n 3 -l 20 -d 3 -s 3 -u 3"
    )
    
    if success and stdout.strip():
        lines = [l for l in stdout.strip().split('\n') if l and not l.startswith('=')]
        passwords = [l.split('. ')[-1] for l in lines if '. ' in l]
        
        if len(passwords) >= 3:
            print_success(f"Generated {len(passwords)} passwords with requirements")
            for i, pwd in enumerate(passwords, 1):
                # Check length
                has_length = len(pwd) == 20
                # Count digits
                num_digits = sum(c.isdigit() for c in pwd)
                # Count symbols
                symbols = set('!@#$%^&*()_+-=[]{}|;:,.<>?')
                num_symbols = sum(c in symbols for c in pwd)
                # Count uppercase
                num_upper = sum(c.isupper() for c in pwd)
                
                checks = f"Len:{len(pwd)} Dig:{num_digits} Sym:{num_symbols} Up:{num_upper}"
                print(f"  {i}. {pwd} [{checks}]")
                
                if has_length and num_digits >= 3 and num_symbols >= 3 and num_upper >= 3:
                    print_success(f"    Password {i} meets all requirements")
                else:
                    print_warning(f"    Password {i} may not meet all requirements")
            
            return True
    
    print_error(f"Failed: {stderr}")
    return False


def test_file_output():
    """Test saving to file"""
    print_test("Testing file output...")
    
    test_file = "test_passwords.txt"
    
    # Clean up if exists
    if os.path.exists(test_file):
        os.remove(test_file)
    
    success, stdout, stderr = run_command(
        f"./genpass.py traditional -n 5 -l 16 -o {test_file}"
    )
    
    if success and os.path.exists(test_file):
        with open(test_file, 'r') as f:
            passwords = f.read().strip().split('\n')
        
        if len(passwords) == 5:
            print_success(f"Successfully saved 5 passwords to {test_file}")
            os.remove(test_file)  # Clean up
            return True
        else:
            print_error(f"Expected 5 passwords, found {len(passwords)}")
            os.remove(test_file)
            return False
    
    print_error(f"Failed to create file: {stderr}")
    return False


def test_help_commands():
    """Test help commands work"""
    print_test("Testing help commands...")
    
    commands = [
        "./genpass.py -h",
        "./genpass.py diceware -h",
        "./genpass.py traditional -h"
    ]
    
    all_passed = True
    for cmd in commands:
        success, stdout, stderr = run_command(cmd)
        if success and "usage:" in stdout.lower():
            print_success(f"Help works: {cmd}")
        else:
            print_error(f"Help failed: {cmd}")
            all_passed = False
    
    return all_passed


def test_wordlist_existence():
    """Check if wordlist files exist"""
    print_test("Checking for wordlist files...")
    
    wordlists = [
        "diceware.wordlist.asc",
        "diceware_jp.txt",
        "DW-Espanol-1.txt"
    ]
    
    found = []
    for wl in wordlists:
        if os.path.exists(wl):
            print_success(f"Found: {wl}")
            found.append(wl)
        else:
            print_warning(f"Missing: {wl} (optional)")
    
    if found:
        print_success(f"At least one wordlist found ({len(found)} total)")
        return True
    else:
        print_error("No wordlist files found!")
        return False


def test_encryption_support():
    """Check if encryption is available"""
    print_test("Checking encryption support...")
    
    try:
        import cryptography
        print_success("Cryptography library installed - encryption available")
        return True
    except ImportError:
        print_warning("Cryptography library not installed - encryption unavailable")
        print_warning("Install with: pip install cryptography")
        return False


def test_password_strength():
    """Test password strength heuristics"""
    print_test("Testing password strength...")
    
    # Generate a strong traditional password
    success, stdout, stderr = run_command("./genpass.py traditional -l 24")
    
    if success and stdout.strip():
        lines = [l for l in stdout.strip().split('\n') if l and not l.startswith('=')]
        password = lines[-1].split('. ')[-1] if lines else ""
        
        # Check entropy indicators
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_symbol = any(not c.isalnum() for c in password)
        
        strength_score = sum([has_upper, has_lower, has_digit, has_symbol])
        
        print(f"  Password: {password}")
        print(f"  Length: {len(password)}")
        print(f"  Has uppercase: {has_upper}")
        print(f"  Has lowercase: {has_lower}")
        print(f"  Has digits: {has_digit}")
        print(f"  Has symbols: {has_symbol}")
        
        if strength_score >= 3 and len(password) >= 24:
            print_success("Strong password generated")
            return True
        else:
            print_warning(f"Password strength could be better (score: {strength_score}/4)")
            return False
    
    print_error(f"Failed to generate password: {stderr}")
    return False


def main():
    print("\n" + "="*60)
    print("Password Generator Test Suite")
    print("="*60)
    
    # Make script executable
    if os.path.exists("genpass.py"):
        os.chmod("genpass.py", 0o755)
    
    tests = [
        ("Wordlist Files", test_wordlist_existence),
        ("Basic Diceware", test_basic_diceware),
        ("Diceware Options", test_diceware_with_options),
        ("Traditional Password", test_traditional_password),
        ("Password Requirements", test_traditional_with_requirements),
        ("File Output", test_file_output),
        ("Help Commands", test_help_commands),
        ("Password Strength", test_password_strength),
        ("Encryption Support", test_encryption_support),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print_error(f"Test crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*60)
    print("Test Results Summary")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = f"{Colors.GREEN}PASS{Colors.RESET}" if result else f"{Colors.RED}FAIL{Colors.RESET}"
        print(f"{status} - {name}")
    
    print("="*60)
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print_success("All tests passed! 🎉")
        return 0
    else:
        print_warning(f"{total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
