#!/usr/bin/env python3
"""
Generate a secure random API_SECRET_KEY for use in .env.local.

Run:  python scripts/generate_secret_key.py
"""
import secrets


def main() -> None:
    key = secrets.token_urlsafe(32)
    print("# Add this to your .env.local file:")
    print(f"API_SECRET_KEY={key}")
    print()
    print("# Or for SUPABASE_SERVICE_ROLE_KEY rotation:")
    print(f"# (Note: real Supabase service keys must come from Supabase Dashboard)")


if __name__ == "__main__":
    main()
