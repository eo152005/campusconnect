"""Run lightweight migrations and print the schema for verification.

Usage:
    python -m campusconnect.scripts.ensure_schema

This will import the Flask app, create tables if missing, call ensure_schema() from app.py,
then print PRAGMA table_info for 'user' and 'event'.
"""
from sqlalchemy import text

from campusconnect.app import app, ensure_schema
from campusconnect.database import db

if __name__ == '__main__':
    with app.app_context():
        # Create tables if missing
        db.create_all()

        # Run the app-level ensure_schema migration helper (best-effort)
        try:
            ensure_schema()
        except Exception:
            pass

        engine = db.engine
        with engine.connect() as conn:
            print("user table columns:")
            for row in conn.execute(text("PRAGMA table_info('user')")):
                print(row)

            print("\nevent table columns:")
            for row in conn.execute(text("PRAGMA table_info('event')")):
                print(row)
