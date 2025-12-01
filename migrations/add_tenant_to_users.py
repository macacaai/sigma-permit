#!/usr/bin/env python3
"""
Migration script to add tenant_id to users table for multi-tenancy support
"""

import os
import sys
import logging
from datetime import datetime
from sqlalchemy import create_engine, text, String
from sqlalchemy.orm import sessionmaker

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database URL - default to SQLite for development
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sigma_permit.db")

def add_tenant_column(engine):
    """Add tenant_id column to users table"""
    logger.info("Adding tenant_id column to users table...")

    with engine.connect() as conn:
        # Add tenant_id column
        conn.execute(text("ALTER TABLE users ADD COLUMN tenant_id VARCHAR(36)"))
        conn.commit()

        # Create index on tenant_id
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_users_tenant_id ON users(tenant_id)"))
        conn.commit()

        # For existing users, assign them to a default tenant
        # First, check if any tenants exist
        result = conn.execute(text("SELECT id FROM tenants LIMIT 1"))
        default_tenant = result.fetchone()

        if default_tenant:
            # Assign existing users to the first tenant
            conn.execute(text(f"UPDATE users SET tenant_id = '{default_tenant[0]}' WHERE tenant_id IS NULL"))
            conn.commit()
        else:
            logger.warning("No tenants found! Existing users will have NULL tenant_id")

        # Add foreign key constraint
        try:
            conn.execute(text("ALTER TABLE users ADD CONSTRAINT fk_users_tenant_id FOREIGN KEY (tenant_id) REFERENCES tenants(id)"))
            conn.commit()
        except Exception as e:
            logger.warning(f"Could not add foreign key constraint: {e}")

        # Add unique constraints for tenant-specific uniqueness
        try:
            # Drop existing unique constraints if they exist
            conn.execute(text("DROP INDEX IF EXISTS idx_users_email"))
            conn.execute(text("DROP INDEX IF EXISTS idx_users_username"))
            conn.commit()
        except Exception as e:
            logger.warning(f"Could not drop existing indexes: {e}")

        # Create composite unique constraints
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_user_tenant_email ON users(tenant_id, email)"))
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_user_tenant_username ON users(tenant_id, username)"))
        conn.commit()

    logger.info("Tenant column added successfully!")

def run_migration():
    """Run the migration"""
    logger.info("Starting tenant migration...")
    logger.info(f"Database URL: {DATABASE_URL}")

    # Create engine
    if DATABASE_URL.startswith("sqlite"):
        from sqlalchemy.pool import StaticPool
        engine = create_engine(
            DATABASE_URL,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool
        )
    else:
        engine = create_engine(DATABASE_URL)

    try:
        add_tenant_column(engine)
        logger.info("Migration completed successfully!")
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise

if __name__ == "__main__":
    run_migration()