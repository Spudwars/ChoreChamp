#!/usr/bin/env python3
"""
ChoreChamp Database Migration Script

This script applies any pending database migrations.
It's safe to run multiple times - it only applies migrations that haven't been run yet.
"""

from app import create_app, db
from sqlalchemy import text, inspect

app = create_app()


def column_exists(table_name, column_name):
    """Check if a column exists in a table."""
    with app.app_context():
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        return column_name in columns


def table_exists(table_name):
    """Check if a table exists."""
    with app.app_context():
        inspector = inspect(db.engine)
        return table_name in inspector.get_table_names()


def run_migrations():
    """Run all pending migrations."""
    migrations_applied = 0

    with app.app_context():
        # Migration 1: Add avatar_style to users
        if not column_exists('users', 'avatar_style'):
            print("  - Adding avatar_style column to users table...")
            db.session.execute(text('ALTER TABLE users ADD COLUMN avatar_style VARCHAR(50) DEFAULT "bottts"'))
            db.session.commit()
            migrations_applied += 1

        # Migration 2: Add avatar_seed to users
        if not column_exists('users', 'avatar_seed'):
            print("  - Adding avatar_seed column to users table...")
            db.session.execute(text('ALTER TABLE users ADD COLUMN avatar_seed VARCHAR(100)'))
            db.session.commit()
            migrations_applied += 1

        # Migration 3: Add is_active to users
        if not column_exists('users', 'is_active'):
            print("  - Adding is_active column to users table...")
            db.session.execute(text('ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT 1 NOT NULL'))
            db.session.commit()
            migrations_applied += 1

        # Migration 4: Create app_settings table
        if not table_exists('app_settings'):
            print("  - Creating app_settings table...")
            db.session.execute(text('''
                CREATE TABLE app_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key VARCHAR(100) UNIQUE NOT NULL,
                    value TEXT,
                    is_encrypted BOOLEAN DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
                )
            '''))
            db.session.commit()
            migrations_applied += 1

        # Add future migrations here...
        # Migration N: Description
        # if not column_exists('table', 'column'):
        #     db.session.execute(text('ALTER TABLE ...'))
        #     db.session.commit()
        #     migrations_applied += 1

    return migrations_applied


if __name__ == '__main__':
    print("ChoreChamp Database Migration")
    print("=" * 40)

    try:
        count = run_migrations()
        if count > 0:
            print(f"\n{count} migration(s) applied successfully!")
        else:
            print("\nDatabase is up to date. No migrations needed.")
    except Exception as e:
        print(f"\nError during migration: {e}")
        exit(1)
