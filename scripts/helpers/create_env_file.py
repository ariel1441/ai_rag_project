"""
Create .env file for PostgreSQL connection.
"""
import os

print("=" * 70)
print("Create .env File")
print("=" * 70)
print()

host = input("PostgreSQL Host [localhost]: ").strip() or "localhost"
port = input("PostgreSQL Port [5433]: ").strip() or "5433"
database = input("Database [ai_requests_db]: ").strip() or "ai_requests_db"
user = input("Username [postgres]: ").strip() or "postgres"
password = input("Password: ").strip()

if not password:
    print("ERROR: Password is required!")
    exit(1)

env_content = f"""POSTGRES_HOST={host}
POSTGRES_PORT={port}
POSTGRES_DATABASE={database}
POSTGRES_USER={user}
POSTGRES_PASSWORD={password}
"""

env_path = ".env"
with open(env_path, 'w') as f:
    f.write(env_content)

print()
print(f"✅ Created .env file at {env_path}")
print()
print("Contents:")
print(env_content.replace(password, "***"))
print("⚠ Keep this file secure! Don't commit it to git.")

