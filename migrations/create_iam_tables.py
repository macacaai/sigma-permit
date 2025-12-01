#!/usr/bin/env python3
"""
Migration script to create IAM extension tables for Sigma Permit 2.0
This script creates all OAuth2, RBAC, and session management tables
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import uuid

# Import all models to ensure they're registered with SQLAlchemy
from app.models import *  # Import existing models
from app.models.oauth import *
from app.models.rbac import *

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database URL - default to SQLite for development
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sigma_permit.db")

def create_tables(engine):
    """Create all IAM extension tables"""
    
    # Import all models to ensure they're registered
    from app.database import Base
    
    logger.info("Creating IAM extension tables...")
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    logger.info("IAM tables created successfully!")

def create_indexes(engine):
    """Create performance indexes for IAM tables"""
    
    indexes = [
        # OAuth2 indexes
        "CREATE INDEX IF NOT EXISTS idx_oauth_clients_client_id ON oauth_clients(client_id)",
        "CREATE INDEX IF NOT EXISTS idx_oauth_clients_tenant_id ON oauth_clients(tenant_id)",
        "CREATE INDEX IF NOT EXISTS idx_oauth_auth_codes_client_user ON oauth_authorization_codes(client_id, user_id)",
        "CREATE INDEX IF NOT EXISTS idx_oauth_auth_codes_expires ON oauth_authorization_codes(expires_at)",
        "CREATE INDEX IF NOT EXISTS idx_oauth_access_tokens_client_user ON oauth_access_tokens(client_id, user_id)",
        "CREATE INDEX IF NOT EXISTS idx_oauth_access_tokens_expires ON oauth_access_tokens(expires_at)",
        "CREATE INDEX IF NOT EXISTS idx_oauth_refresh_tokens_client_user ON oauth_refresh_tokens(client_id, user_id)",
        "CREATE INDEX IF NOT EXISTS idx_oauth_refresh_tokens_expires ON oauth_refresh_tokens(expires_at)",
        
        # Social connections indexes
        "CREATE INDEX IF NOT EXISTS idx_social_connections_user_id ON social_connections(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_social_connections_provider ON social_connections(provider)",
        
        # RBAC indexes
        "CREATE INDEX IF NOT EXISTS idx_roles_tenant_id ON roles(tenant_id)",
        "CREATE INDEX IF NOT EXISTS idx_permissions_resource ON permissions(resource)",
        "CREATE INDEX IF NOT EXISTS idx_role_permissions_role_id ON role_permissions(role_id)",
        "CREATE INDEX IF NOT EXISTS idx_role_permissions_permission_id ON role_permissions(permission_id)",
        "CREATE INDEX IF NOT EXISTS idx_user_roles_user_id ON user_roles(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_user_roles_role_id ON user_roles(role_id)",
        
        # Session management indexes
        "CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_user_sessions_session_id ON user_sessions(session_id)",
        "CREATE INDEX IF NOT EXISTS idx_user_sessions_expires ON user_sessions(expires_at)",
        "CREATE INDEX IF NOT EXISTS idx_user_sessions_active ON user_sessions(is_active)",
        
        # Audit log indexes
        "CREATE INDEX IF NOT EXISTS idx_audit_log_user_created ON audit_log(user_id, created_at)",
        "CREATE INDEX IF NOT EXISTS idx_audit_log_category_created ON audit_log(event_category, created_at)",
        "CREATE INDEX IF NOT EXISTS idx_audit_log_resource_created ON audit_log(resource, created_at)",
        "CREATE INDEX IF NOT EXISTS idx_audit_log_session_id ON audit_log(session_id)",
        
        # Identity provider indexes
        "CREATE INDEX IF NOT EXISTS idx_identity_providers_tenant_id ON identity_providers(tenant_id)",
        "CREATE INDEX IF NOT EXISTS idx_identity_providers_type ON identity_providers(type)",
        "CREATE INDEX IF NOT EXISTS idx_external_identities_user_id ON external_identities(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_external_identities_provider_user ON external_identities(identity_provider_id, external_user_id)",
    ]
    
    logger.info("Creating performance indexes...")
    
    with engine.connect() as conn:
        for index_sql in indexes:
            try:
                conn.execute(text(index_sql))
                logger.debug(f"Created index: {index_sql.split()[-2]} {index_sql.split()[-1]}")
            except Exception as e:
                logger.warning(f"Failed to create index: {e}")
        
        conn.commit()
    
    logger.info("Performance indexes created successfully!")

def seed_system_data(engine):
    """Seed system roles and permissions"""
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        logger.info("Seeding system roles and permissions...")
        
        # Create system permissions
        system_permissions = [
            # User management
            {"name": "users.read", "resource": "users", "action": "read", "description": "Read user information"},
            {"name": "users.create", "resource": "users", "action": "create", "description": "Create new users"},
            {"name": "users.update", "resource": "users", "action": "update", "description": "Update user information"},
            {"name": "users.delete", "resource": "users", "action": "delete", "description": "Delete users"},
            
            # License management
            {"name": "licenses.read", "resource": "licenses", "action": "read", "description": "Read license information"},
            {"name": "licenses.create", "resource": "licenses", "action": "create", "description": "Create licenses"},
            {"name": "licenses.update", "resource": "licenses", "action": "update", "description": "Update licenses"},
            {"name": "licenses.delete", "resource": "licenses", "action": "delete", "description": "Delete licenses"},
            {"name": "licenses.validate", "resource": "licenses", "action": "validate", "description": "Validate licenses"},
            
            # Tenant management
            {"name": "tenants.read", "resource": "tenants", "action": "read", "description": "Read tenant information"},
            {"name": "tenants.create", "resource": "tenants", "action": "create", "description": "Create tenants"},
            {"name": "tenants.update", "resource": "tenants", "action": "update", "description": "Update tenant information"},
            {"name": "tenants.delete", "resource": "tenants", "action": "delete", "description": "Delete tenants"},
            
            # Subscription management
            {"name": "subscriptions.read", "resource": "subscriptions", "action": "read", "description": "Read subscription information"},
            {"name": "subscriptions.create", "resource": "subscriptions", "action": "create", "description": "Create subscriptions"},
            {"name": "subscriptions.update", "resource": "subscriptions", "action": "update", "description": "Update subscriptions"},
            {"name": "subscriptions.delete", "resource": "subscriptions", "action": "delete", "description": "Delete subscriptions"},
            
            # OAuth client management
            {"name": "oauth_clients.read", "resource": "oauth_clients", "action": "read", "description": "Read OAuth client information"},
            {"name": "oauth_clients.create", "resource": "oauth_clients", "action": "create", "description": "Create OAuth clients"},
            {"name": "oauth_clients.update", "resource": "oauth_clients", "action": "update", "description": "Update OAuth clients"},
            {"name": "oauth_clients.delete", "resource": "oauth_clients", "action": "delete", "description": "Delete OAuth clients"},
            
            # Role management
            {"name": "roles.read", "resource": "roles", "action": "read", "description": "Read role information"},
            {"name": "roles.create", "resource": "roles", "action": "create", "description": "Create roles"},
            {"name": "roles.update", "resource": "roles", "action": "update", "description": "Update roles"},
            {"name": "roles.delete", "resource": "roles", "action": "delete", "description": "Delete roles"},
            
            # Audit log access
            {"name": "audit.read", "resource": "audit_log", "action": "read", "description": "Read audit logs"},
            
            # Session management
            {"name": "sessions.read", "resource": "sessions", "action": "read", "description": "Read session information"},
            {"name": "sessions.delete", "resource": "sessions", "action": "delete", "description": "Delete sessions"},
        ]
        
        permissions = {}
        for perm_data in system_permissions:
            permission = Permission(
                name=perm_data["name"],
                resource=perm_data["resource"],
                action=perm_data["action"],
                description=perm_data["description"],
                is_system=True
            )
            session.add(permission)
            permissions[perm_data["name"]] = permission
        
        session.flush()  # Get IDs
        
        # Create system roles
        admin_role = Role(
            name="admin",
            description="System Administrator - Full access to all features",
            is_system=True
        )
        session.add(admin_role)
        session.flush()
        
        # Give admin all permissions
        admin_permissions = list(permissions.values())
        admin_role.permissions = admin_permissions
        
        # Create user role
        user_role = Role(
            name="user",
            description="Regular User - Basic access to own resources",
            is_system=True
        )
        session.add(user_role)
        session.flush()
        
        # Give user basic permissions
        user_permission_names = [
            "users.read", "users.update",
            "licenses.read", "licenses.validate",
            "tenants.read", "subscriptions.read"
        ]
        user_role.permissions = [permissions[name] for name in user_permission_names if name in permissions]
        
        session.commit()
        
        logger.info("System roles and permissions created successfully!")
        
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to seed system data: {e}")
        raise
    finally:
        session.close()

def run_migration():
    """Run the complete migration"""
    
    logger.info("Starting IAM database migration...")
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
        # Create tables
        create_tables(engine)
        
        # Create indexes
        create_indexes(engine)
        
        # Seed system data
        seed_system_data(engine)
        
        logger.info("IAM migration completed successfully!")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise

def rollback_migration():
    """Rollback the migration by dropping IAM tables"""
    
    logger.info("Rolling back IAM migration...")
    
    # This is a simple rollback - in production you'd want more sophisticated handling
    from sqlalchemy import inspect
    
    engine = create_engine(DATABASE_URL)
    
    tables_to_drop = [
        "external_identities",
        "identity_providers", 
        "audit_log",
        "user_sessions",
        "user_roles",
        "role_permissions",
        "permissions",
        "roles",
        "oauth_client_users",
        "social_connections",
        "oauth_refresh_tokens",
        "oauth_access_tokens",
        "oauth_authorization_codes",
        "oauth_clients",
        "user_extensions"
    ]
    
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    with engine.connect() as conn:
        for table in tables_to_drop:
            if table in existing_tables:
                try:
                    conn.execute(text(f'DROP TABLE IF EXISTS "{table}"'))
                    logger.info(f"Dropped table: {table}")
                except Exception as e:
                    logger.warning(f"Failed to drop table {table}: {e}")
        
        conn.commit()
    
    logger.info("IAM migration rollback completed!")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        rollback_migration()
    else:
        run_migration()