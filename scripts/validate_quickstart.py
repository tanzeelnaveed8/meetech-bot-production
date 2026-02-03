#!/usr/bin/env python3
"""
Quickstart validation script.

Validates that the environment is correctly configured and all
dependencies are available before deployment.
"""

import sys
import os
from pathlib import Path
from typing import List, Tuple

# Color codes for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def check_python_version() -> Tuple[bool, str]:
    """Check Python version is 3.11+."""
    version = sys.version_info
    if version.major == 3 and version.minor >= 11:
        return True, f"Python {version.major}.{version.minor}.{version.micro}"
    return False, f"Python {version.major}.{version.minor}.{version.micro} (requires 3.11+)"


def check_env_file() -> Tuple[bool, str]:
    """Check .env file exists."""
    env_path = Path(".env")
    if env_path.exists():
        return True, ".env file found"
    return False, ".env file not found (copy from .env.example)"


def check_required_env_vars() -> Tuple[bool, str]:
    """Check required environment variables."""
    from dotenv import load_dotenv
    load_dotenv()

    required_vars = [
        "DATABASE_URL",
        "REDIS_URL",
        "WHATSAPP_API_TOKEN",
        "WHATSAPP_PHONE_NUMBER_ID",
        "OPENAI_API_KEY"
    ]

    missing = [var for var in required_vars if not os.getenv(var)]

    if not missing:
        return True, f"All {len(required_vars)} required env vars set"
    return False, f"Missing env vars: {', '.join(missing)}"


def check_dependencies() -> Tuple[bool, str]:
    """Check Python dependencies are installed."""
    try:
        import fastapi
        import sqlalchemy
        import redis
        import celery
        import langchain
        return True, "All core dependencies installed"
    except ImportError as e:
        return False, f"Missing dependency: {str(e)}"


def check_database_connection() -> Tuple[bool, str]:
    """Check database connection."""
    try:
        from sqlalchemy import create_engine
        from dotenv import load_dotenv
        load_dotenv()

        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            return False, "DATABASE_URL not set"

        engine = create_engine(db_url)
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return True, "Database connection successful"
    except Exception as e:
        return False, f"Database connection failed: {str(e)}"


def check_redis_connection() -> Tuple[bool, str]:
    """Check Redis connection."""
    try:
        import redis
        from dotenv import load_dotenv
        load_dotenv()

        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        client = redis.from_url(redis_url)
        client.ping()
        return True, "Redis connection successful"
    except Exception as e:
        return False, f"Redis connection failed: {str(e)}"


def check_directory_structure() -> Tuple[bool, str]:
    """Check required directories exist."""
    required_dirs = [
        "src",
        "tests",
        "alembic",
        "config"
    ]

    missing = [d for d in required_dirs if not Path(d).exists()]

    if not missing:
        return True, "All required directories present"
    return False, f"Missing directories: {', '.join(missing)}"


def check_migrations() -> Tuple[bool, str]:
    """Check database migrations are up to date."""
    try:
        from alembic.config import Config
        from alembic import command
        from alembic.script import ScriptDirectory
        from alembic.runtime.migration import MigrationContext
        from sqlalchemy import create_engine
        from dotenv import load_dotenv
        load_dotenv()

        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            return False, "DATABASE_URL not set"

        # Check if migrations are up to date
        alembic_cfg = Config("alembic.ini")
        script = ScriptDirectory.from_config(alembic_cfg)

        engine = create_engine(db_url)
        with engine.connect() as conn:
            context = MigrationContext.configure(conn)
            current_rev = context.get_current_revision()
            head_rev = script.get_current_head()

            if current_rev == head_rev:
                return True, f"Migrations up to date (revision: {current_rev})"
            return False, f"Migrations out of date (current: {current_rev}, head: {head_rev})"

    except Exception as e:
        return False, f"Migration check failed: {str(e)}"


def main():
    """Run all validation checks."""
    print("=" * 60)
    print("Meetech Lead Qualification Bot - Quickstart Validation")
    print("=" * 60)
    print()

    checks = [
        ("Python Version", check_python_version),
        ("Environment File", check_env_file),
        ("Environment Variables", check_required_env_vars),
        ("Python Dependencies", check_dependencies),
        ("Directory Structure", check_directory_structure),
        ("Database Connection", check_database_connection),
        ("Redis Connection", check_redis_connection),
        ("Database Migrations", check_migrations),
    ]

    results = []
    for name, check_func in checks:
        try:
            passed, message = check_func()
            results.append((name, passed, message))

            status = f"{GREEN}✓{RESET}" if passed else f"{RED}✗{RESET}"
            print(f"{status} {name}: {message}")
        except Exception as e:
            results.append((name, False, str(e)))
            print(f"{RED}✗{RESET} {name}: Error - {str(e)}")

    print()
    print("=" * 60)

    passed_count = sum(1 for _, passed, _ in results if passed)
    total_count = len(results)

    if passed_count == total_count:
        print(f"{GREEN}All checks passed! ({passed_count}/{total_count}){RESET}")
        print("You're ready to start the application.")
        return 0
    else:
        print(f"{RED}Some checks failed ({passed_count}/{total_count}){RESET}")
        print("Please fix the issues above before proceeding.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
