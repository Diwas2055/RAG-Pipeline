#!/usr/bin/env python3
"""
Generate secure API keys for production use
"""
import secrets
import string
import sys


def generate_api_key(length: int = 32) -> str:
    """
    Generate a cryptographically secure API key

    Args:
        length: Length of the API key (default: 32)

    Returns:
        Secure random API key
    """
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def generate_multiple_keys(count: int = 3, length: int = 32) -> list:
    """
    Generate multiple unique API keys

    Args:
        count: Number of keys to generate
        length: Length of each key

    Returns:
        List of unique API keys
    """
    keys = set()
    while len(keys) < count:
        keys.add(generate_api_key(length))
    return list(keys)


def main():
    """Generate and display API keys"""
    print("=" * 60)
    print("API Key Generator")
    print("=" * 60)
    print()

    # Get number of keys from command line or use default
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 3

    # Generate keys
    keys = generate_multiple_keys(count)

    print(f"Generated {count} secure API keys:\n")

    # Display keys individually
    for i, key in enumerate(keys, 1):
        print(f"Key {i}: {key}")

    print()
    print("-" * 60)
    print("For .env.production file:")
    print("-" * 60)
    print(f"API_KEYS={','.join(keys)}")
    print()

    # Generate other secrets
    print("-" * 60)
    print("Additional secrets:")
    print("-" * 60)
    print(f"GRAFANA_PASSWORD={generate_api_key(24)}")
    print(f"REDIS_PASSWORD={generate_api_key(32)}")
    print(f"JWT_SECRET_KEY={generate_api_key(64)}")
    print()

    print("=" * 60)
    print("⚠️  Store these keys securely!")
    print("=" * 60)


if __name__ == "__main__":
    main()
