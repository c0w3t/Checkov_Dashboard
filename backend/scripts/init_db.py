"""
Initialize Database Script
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.database import engine, Base
import app.models  # ensure all model modules are loaded and registered with Base.metadata
from sqlalchemy import inspect, text
from pathlib import Path
import os
import sys

def init_db():
    """Initialize database with all tables"""
    backend_root = Path(__file__).resolve().parents[1]
    sql_file = backend_root / 'database_schema.sql'

    # If a SQL schema file exists, execute it first (idempotent statements)
    if sql_file.exists():
        print(f"Applying SQL schema from: {sql_file}")
        sql_text = sql_file.read_text()
        try:
            # Use a raw DBAPI connection in autocommit mode to execute the whole
            # SQL file. This avoids naive splitting on ';' which breaks
            # dollar-quoted blocks (DO $$ ... $$) and PL/pgSQL functions.
            raw_conn = engine.raw_connection()
            try:
                # Set autocommit so multi-statement / DDL blocks execute properly.
                # For psycopg2, prefer setting ISOLATION_LEVEL_AUTOCOMMIT.
                try:
                    # psycopg2 (most common) - import here to avoid hard dependency
                    from psycopg2 import extensions as _pg_ext
                    try:
                        raw_conn.set_isolation_level(_pg_ext.ISOLATION_LEVEL_AUTOCOMMIT)
                    except Exception:
                        # Some DBAPIs expose autocommit attr
                        try:
                            raw_conn.autocommit = True
                        except Exception:
                            pass
                except Exception:
                    # Fallbacks for other DBAPIs
                    try:
                        raw_conn.autocommit = True
                    except Exception:
                        try:
                            raw_conn.set_isolation_level(0)
                        except Exception:
                            pass

                cur = raw_conn.cursor()
                try:
                    cur.execute(sql_text)
                finally:
                    cur.close()
            finally:
                try:
                    raw_conn.close()
                except Exception:
                    pass

            print("✅ Applied SQL schema file (best-effort)")
        except Exception as e:
            print(f"Error applying SQL schema file: {e}")

    print("Creating database tables via SQLAlchemy metadata (create_all)...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created via metadata.create_all")
    except Exception as e:
        print(f"Error running metadata.create_all: {e}")

    # Print expected tables
    print("\nExpected tables from models:")
    expected_tables = [t.name for t in Base.metadata.sorted_tables]
    for name in expected_tables:
        print(f"  - {name}")

    # Verify created tables exist in the target database
    try:
        inspector = inspect(engine)
        existing = set(inspector.get_table_names(schema='public'))
        expected = set(expected_tables)
        missing = expected - existing
        if missing:
            print("\nWarning: The following expected tables are missing from the database:")
            for t in sorted(missing):
                print(f"  - {t}")
            print("Please ensure the database exists and the DB user has CREATE privileges on the schema, or run this script as a superuser to initialize the DB.")
            sys.exit(2)
        else:
            print("All expected tables verified in the database.")
    except Exception as e:
        print(f"Warning: failed to verify tables due to: {e}")

if __name__ == "__main__":
    init_db()
