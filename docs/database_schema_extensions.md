# Database Schema Extensions for IAM Features

## Overview
This document outlines the database schema extensions needed to transform Sigma Permit 2.0 into a comprehensive IAM solution. The extensions build upon the existing models while maintaining backward compatibility.

## New Tables for OAuth2/OIDC Support

### OAuth Clients
```sql
CREATE TABLE oauth_clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id VARCHAR(100) UNIQUE NOT NULL,
    client_secret_hash VARCHAR(255),  -- NULL for public clients
    client_name VARCHAR(255) NOT NULL,
    client_type VARCHAR(20) CHECK (client_type IN ('confidential', 'public')),
    redirect_uris JSONB,  -- List of allowed redirect URIs
    allowed_grant_types JSONB NOT NULL,  -- authorization_code, client_credentials, password, refresh_token
    allowed_scopes JSONB,  -- List of allowed scopes
    logo_uri VARCHAR(500),
    website_uri VARCHAR(500),
    tenant_id UUID REFERENCES tenants(id),  -- NULL for system clients
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_oauth_clients_client_id ON oauth_clients(client_id);
CREATE INDEX idx_oauth_clients_tenant_id ON oauth_clients(tenant_id);
```

### OAuth Authorization Codes
```sql
CREATE TABLE oauth_authorization_codes (
    code VARCHAR(100) PRIMARY KEY,
    client_id UUID REFERENCES oauth_clients(id) NOT NULL,
    user_id UUID REFERENCES users(id) NOT NULL,
    redirect_uri VARCHAR(500),
    scope TEXT,
    code_challenge VARCHAR(128),  -- PKCE
    code_challenge_method VARCHAR(10),  -- S256, plain
    nonce VARCHAR(100),  -- OIDC nonce
    state VARCHAR(100),  -- CSRF protection
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_oauth_auth_codes_client_user ON oauth_authorization_codes(client_id, user_id);
CREATE INDEX idx_oauth_auth_codes_expires ON oauth_authorization_codes(expires_at);
```

### OAuth Access Tokens
```sql
CREATE TABLE oauth_access_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    token VARCHAR(100) UNIQUE NOT NULL,
    client_id UUID REFERENCES oauth_clients(id) NOT NULL,
    user_id UUID REFERENCES users(id) NOT NULL,
    scope TEXT,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_oauth_access_tokens_client_user ON oauth_access_tokens(client_id, user_id);
CREATE INDEX idx_oauth_access_tokens_expires ON oauth_access_tokens(expires_at);
```

### OAuth Refresh Tokens
```sql
CREATE TABLE oauth_refresh_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    token VARCHAR(100) UNIQUE NOT NULL,
    client_id UUID REFERENCES oauth_clients(id) NOT NULL,
    user_id UUID REFERENCES users(id) NOT NULL,
    access_token_id UUID REFERENCES oauth_access_tokens(id),
    scope TEXT,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    revoked_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_oauth_refresh_tokens_client_user ON oauth_refresh_tokens(client_id, user_id);
CREATE INDEX idx_oauth_refresh_tokens_expires ON oauth_refresh_tokens(expires_at);
```

### OAuth Client User Associations
```sql
CREATE TABLE oauth_client_users (
    user_id UUID REFERENCES users(id),
    client_id UUID REFERENCES oauth_clients(id),
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    scope TEXT,
    expires_at TIMESTAMP WITH TIME ZONE,
    PRIMARY KEY (user_id, client_id)
);
```

## Social Login Extensions

### Social Connections
```sql
CREATE TABLE social_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) NOT NULL,
    provider VARCHAR(50) NOT NULL,  -- google, github, facebook, etc.
    provider_user_id VARCHAR(255) NOT NULL,
    provider_username VARCHAR(255),
    provider_email VARCHAR(255),
    provider_name VARCHAR(255),
    provider_avatar_url VARCHAR(500),
    access_token TEXT,
    refresh_token TEXT,
    expires_at TIMESTAMP WITH TIME ZONE,
    profile_data JSONB,  -- Additional provider data
    is_primary BOOLEAN DEFAULT false,  -- Primary external identity
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(provider, provider_user_id)
);

CREATE INDEX idx_social_connections_user_id ON social_connections(user_id);
CREATE INDEX idx_social_connections_provider ON social_connections(provider);
```

## Role-Based Access Control (RBAC)

### Roles
```sql
CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_system BOOLEAN DEFAULT false,  -- System roles cannot be deleted
    tenant_id UUID REFERENCES tenants(id),  -- NULL for global roles
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(name, tenant_id)
);

CREATE INDEX idx_roles_tenant_id ON roles(tenant_id);
```

### Permissions
```sql
CREATE TABLE permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    resource VARCHAR(100) NOT NULL,  -- users, roles, etc.
    action VARCHAR(50) NOT NULL,  -- read, write, delete, etc.
    description TEXT,
    is_system BOOLEAN DEFAULT false,  -- System permissions cannot be deleted
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(resource, action)
);

CREATE INDEX idx_permissions_resource ON permissions(resource);
```

### Role-Permission Mapping
```sql
CREATE TABLE role_permissions (
    role_id UUID REFERENCES roles(id),
    permission_id UUID REFERENCES permissions(id),
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    granted_by UUID REFERENCES users(id),
    PRIMARY KEY (role_id, permission_id)
);

CREATE INDEX idx_role_permissions_role_id ON role_permissions(role_id);
CREATE INDEX idx_role_permissions_permission_id ON role_permissions(permission_id);
```

### User-Role Assignment
```sql
CREATE TABLE user_roles (
    user_id UUID REFERENCES users(id),
    role_id UUID REFERENCES roles(id),
    assigned_by UUID REFERENCES users(id),
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (user_id, role_id)
);

CREATE INDEX idx_user_roles_user_id ON user_roles(user_id);
CREATE INDEX idx_user_roles_role_id ON user_roles(role_id);
```

## Session Management

### Active User Sessions
```sql
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) NOT NULL,
    session_id VARCHAR(100) UNIQUE NOT NULL,
    device_info JSONB,  -- Browser, OS, device info
    ip_address VARCHAR(45),  -- IPv6 compatible
    user_agent TEXT,
    location JSONB,  -- Geolocation data
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL
);

CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_session_id ON user_sessions(session_id);
CREATE INDEX idx_user_sessions_expires ON user_sessions(expires_at);
CREATE INDEX idx_user_sessions_active ON user_sessions(is_active);
```

## Audit Logging

### Comprehensive Audit Log
```sql
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    session_id UUID REFERENCES user_sessions(id),
    tenant_id UUID REFERENCES tenants(id),
    event_type VARCHAR(50) NOT NULL,  -- login, logout, create_user, etc.
    event_category VARCHAR(50) NOT NULL,  -- authentication, authorization, user_management, etc.
    resource VARCHAR(100),  -- users, roles, etc.
    resource_id VARCHAR(36),  -- ID of affected resource
    action VARCHAR(50),  -- create, read, update, delete
    success BOOLEAN NOT NULL,
    error_message TEXT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    request_id VARCHAR(100),  -- For request tracing
    metadata JSONB,  -- Additional event data
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_audit_log_user_created ON audit_log(user_id, created_at);
CREATE INDEX idx_audit_log_category_created ON audit_log(event_category, created_at);
CREATE INDEX idx_audit_log_resource_created ON audit_log(resource, created_at);
CREATE INDEX idx_audit_log_session_id ON audit_log(session_id);
```

## Enterprise Identity Providers

### Identity Providers
```sql
CREATE TABLE identity_providers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    type VARCHAR(20) CHECK (type IN ('saml', 'oidc', 'ldap', 'active_directory')),
    configuration JSONB NOT NULL,  -- Provider-specific configuration
    tenant_id UUID REFERENCES tenants(id),  -- NULL for global providers
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(name, tenant_id)
);

CREATE INDEX idx_identity_providers_tenant_id ON identity_providers(tenant_id);
CREATE INDEX idx_identity_providers_type ON identity_providers(type);
```

### External Identity Mappings
```sql
CREATE TABLE external_identities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) NOT NULL,
    identity_provider_id UUID REFERENCES identity_providers(id) NOT NULL,
    external_user_id VARCHAR(255) NOT NULL,
    external_username VARCHAR(255),
    external_email VARCHAR(255),
    external_groups JSONB,  -- Group memberships from external provider
    attributes JSONB,  -- Additional attributes
    is_primary BOOLEAN DEFAULT false,  -- Primary external identity
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(identity_provider_id, external_user_id)
);

CREATE INDEX idx_external_identities_user_id ON external_identities(user_id);
CREATE INDEX idx_external_identities_provider_user ON external_identities(identity_provider_id, external_user_id);
```

## User Model Extensions

### User Extension Fields
```sql
CREATE TABLE user_extensions (
    user_id UUID REFERENCES users(id) PRIMARY KEY,
    email_verified BOOLEAN DEFAULT false,
    phone_verified BOOLEAN DEFAULT false,
    
    -- Account security
    require_password_change BOOLEAN DEFAULT false,
    password_expires_at TIMESTAMP WITH TIME ZONE,
    account_locked_until TIMESTAMP WITH TIME ZONE,
    failed_login_attempts INTEGER DEFAULT 0,
    
    -- Privacy and preferences
    profile_visibility VARCHAR(20) DEFAULT 'organization' CHECK (profile_visibility IN ('public', 'private', 'organization')),
    preferred_language VARCHAR(10) DEFAULT 'en',
    timezone VARCHAR(50) DEFAULT 'UTC',
    
    -- Timestamps
    email_verified_at TIMESTAMP WITH TIME ZONE,
    phone_verified_at TIMESTAMP WITH TIME ZONE,
    last_password_change TIMESTAMP WITH TIME ZONE,
    last_login_at TIMESTAMP WITH TIME ZONE
);
```

## SQLAlchemy Model Definitions

### OAuth2 Models
```python
# app/models/oauth.py
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.database import Base

class OAuthClient(Base):
    __tablename__ = "oauth_clients"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    client_id = Column(String(100), unique=True, nullable=False, index=True)
    client_secret_hash = Column(String(255), nullable=True)
    client_name = Column(String(255), nullable=False)
    client_type = Column(Enum('confidential', 'public', name='client_type_enum'), nullable=False)
    redirect_uris = Column(JSON, nullable=True)
    allowed_grant_types = Column(JSON, nullable=False)
    allowed_scopes = Column(JSON, nullable=True)
    logo_uri = Column(String(500), nullable=True)
    website_uri = Column(String(500), nullable=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    authorization_codes = relationship("OAuthAuthorizationCode", back_populates="client", cascade="all, delete-orphan")
    access_tokens = relationship("OAuthAccessToken", back_populates="client", cascade="all, delete-orphan")
    refresh_tokens = relationship("OAuthRefreshToken", back_populates="client", cascade="all, delete-orphan")

class OAuthAuthorizationCode(Base):
    __tablename__ = "oauth_authorization_codes"

    code = Column(String(100), primary_key=True, index=True)
    client_id = Column(String(36), ForeignKey("oauth_clients.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    redirect_uri = Column(String(500), nullable=True)
    scope = Column(Text, nullable=True)
    code_challenge = Column(String(128), nullable=True)
    code_challenge_method = Column(String(10), nullable=True)
    nonce = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    client = relationship("OAuthClient", back_populates="authorization_codes")
    user = relationship("User")

class OAuthAccessToken(Base):
    __tablename__ = "oauth_access_tokens"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    token = Column(String(100), unique=True, nullable=False, index=True)
    client_id = Column(String(36), ForeignKey("oauth_clients.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    scope = Column(Text, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    client = relationship("OAuthClient", back_populates="access_tokens")
    user = relationship("User")
    refresh_tokens = relationship("OAuthRefreshToken", back_populates="access_token")

class OAuthRefreshToken(Base):
    __tablename__ = "oauth_refresh_tokens"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    token = Column(String(100), unique=True, nullable=False, index=True)
    client_id = Column(String(36), ForeignKey("oauth_clients.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    access_token_id = Column(String(36), ForeignKey("oauth_access_tokens.id"), nullable=True)
    scope = Column(Text, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    revoked_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    client = relationship("OAuthClient", back_populates="refresh_tokens")
    user = relationship("User")
    access_token = relationship("OAuthAccessToken", back_populates="refresh_tokens")
```

### RBAC Models
```python
# app/models/rbac.py
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, JSON, Table, Enum, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.database import Base

# Association tables
role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', String(36), ForeignKey('roles.id'), primary_key=True),
    Column('permission_id', String(36), ForeignKey('permissions.id'), primary_key=True),
    Column('granted_at', DateTime(timezone=True), server_default=func.now()),
    Column('granted_by', String(36), ForeignKey('users.id'))
)

user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', String(36), ForeignKey('users.id'), primary_key=True),
    Column('role_id', String(36), ForeignKey('roles.id'), primary_key=True),
    Column('assigned_by', String(36), ForeignKey('users.id')),
    Column('expires_at', DateTime(timezone=True)),
    Column('created_at', DateTime(timezone=True), server_default=func.now())
)

class Role(Base):
    __tablename__ = "roles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    is_system = Column(Boolean, default=False)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")
    users = relationship("User", secondary=user_roles, back_populates="roles")

    __table_args__ = (UniqueConstraint('name', 'tenant_id', name='uq_role_name_tenant'),)

class Permission(Base):
    __tablename__ = "permissions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    name = Column(String(100), nullable=False)
    resource = Column(String(100), nullable=False)
    action = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    is_system = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")

    __table_args__ = (UniqueConstraint('resource', 'action', name='uq_permission_resource_action'),)
```

## Migration Strategy

### Phase 1: Core OAuth2 Support
1. Create oauth_clients table
2. Create oauth_authorization_codes table
3. Create oauth_access_tokens table
4. Create oauth_refresh_tokens table
5. Create social_connections table

### Phase 2: RBAC Implementation
1. Create roles table
2. Create permissions table
3. Create role_permissions association table
4. Create user_roles association table
5. Create default system roles and permissions

### Phase 3: Session Management
1. Create user_sessions table
2. Create audit_log table
3. Create user_extensions table

### Phase 4: Enterprise Features
1. Create identity_providers table
2. Create external_identities table
3. Add advanced audit and compliance features

## Backward Compatibility

The schema extensions are designed to be additive only:
- **No existing tables are modified**
- **No existing columns are changed**
- **All existing functionality remains intact**
- **New features are opt-in**

Default system roles and permissions will be created to match current admin/user functionality:
- **admin role**: Full access to all resources
- **user role**: Basic user permissions
- **System permissions**: Read/write/delete for all existing resources

## Performance Considerations

### Indexing Strategy
- **Primary keys**: UUIDs for security and distribution
- **Foreign keys**: Indexed for join performance
- **Composite indexes**: For multi-column queries
- **Timestamp indexes**: For time-based queries

### Data Retention
- **OAuth tokens**: Automatically cleaned up when expired
- **Audit logs**: Configurable retention periods
- **User sessions**: Automatic cleanup of expired sessions
- **Social connections**: Retained until explicitly removed

### Scaling Considerations
- **Token storage**: Consider Redis for high-traffic deployments
- **Audit logging**: Partition by date for large volumes
- **Session storage**: Redis cluster for distributed deployments
- **User data**: Database sharding by tenant if needed

This comprehensive schema design provides the foundation for a feature-rich IAM solution while maintaining the simplicity and performance of the current system.