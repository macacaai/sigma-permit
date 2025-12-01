# IAM Architecture Design: Sigma IAM

## Overview
Transform Sigma Permit 2.0 into a comprehensive, developer-friendly IAM solution that combines the simplicity of Firebase Auth with enterprise-grade protocols and the flexibility of self-hosting.

## Design Principles

### 1. Developer-First
- **Simple setup**: One-command deployment
- **Clear APIs**: Intuitive REST and GraphQL endpoints
- **Rich SDKs**: Framework-specific integration libraries
- **Excellent documentation**: Examples and guides for common use cases

### 2. Progressive Complexity
- **Start simple**: Basic username/password + JWT
- **Add features**: OAuth2, social login, RBAC
- **Enterprise ready**: SAML, audit logs, compliance
- **Configurable**: Opinionated defaults with customization

### 3. Security by Design
- **Zero trust**: Verify everything, trust nothing
- **Principle of least privilege**: Minimal default permissions
- **Defense in depth**: Multiple security layers
- **Compliance ready**: Audit trails and reporting

### 4. Scalability and Performance
- **Stateless architecture**: Horizontal scaling friendly
- **Efficient caching**: Redis for sessions and tokens
- **Database optimization**: Proper indexing and queries
- **CDN integration**: Static asset delivery

## System Architecture

### High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Mobile Apps   │    │   3rd Party     │
│   (React/Next)  │    │   (React Native)│    │   Applications  │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
┌─────────────────────────────────┼─────────────────────────────────┐
│                    Load Balancer (Caddy/Nginx)                     │
└─────────────────────────────────┼─────────────────────────────────┘
                                 │
┌─────────────────────────────────┼─────────────────────────────────┐
│                    FastAPI Application Server                      │
│  ┌─────────────┬─────────────┬─────────────┬─────────────┐         │
│  │ Auth Router │ OAuth Router│ User Router │Admin Router │         │
│  └─────────────┴─────────────┴─────────────┴─────────────┘         │
└─────────────────────────────────┼─────────────────────────────────┘
                                 │
          ┌──────────────────────┼──────────────────────┐
          │                      │                      │
┌─────────▼───────┐    ┌─────────▼───────┐    ┌─────────▼───────┐
│   PostgreSQL    │    │     Redis       │    │   File Storage  │
│   (Primary DB)  │    │   (Sessions/    │    │   (S3/MinIO)    │
│                 │    │    Cache)       │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Component Architecture

#### 1. Authentication Service
- **JWT Management**: Access/refresh token lifecycle
- **OAuth2/OIDC**: Authorization server implementation
- **Social Login**: Provider connectors and user linking
- **MFA**: SMS, Email, TOTP support (Phase 2)

#### 2. Authorization Service
- **RBAC**: Role-based access control with hierarchy
- **Resource Permissions**: Fine-grained access control
- **Context Awareness**: Environment-based authorization
- **Policy Engine**: Dynamic permission evaluation

#### 3. Identity Management
- **User Lifecycle**: Registration, verification, deactivation
- **Profile Management**: Extended user attributes
- **Organization Management**: Multi-tenant organization model
- **External Identities**: Federation and linking

#### 4. Session Management
- **Active Sessions**: Track and manage user sessions
- **Device Management**: Identify and control devices
- **Session Policies**: Concurrent session limits
- **Revocation**: Immediate session termination

#### 5. Audit and Compliance
- **Event Logging**: All authentication and authorization events
- **Audit Trail**: Immutable log of all actions
- **Compliance Reports**: GDPR, SOC2, HIPAA reporting
- **Real-time Monitoring**: Security event detection

## Database Design Extensions

### New Core Tables

```sql
-- OAuth2/OIDC Clients
CREATE TABLE oauth_clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id VARCHAR(100) UNIQUE NOT NULL,
    client_secret_hash VARCHAR(255),
    client_name VARCHAR(255) NOT NULL,
    client_type VARCHAR(20) CHECK (client_type IN ('confidential', 'public')),
    redirect_uris JSONB,
    allowed_grant_types JSONB,
    allowed_scopes JSONB,
    logo_uri VARCHAR(500),
    tenant_id UUID REFERENCES tenants(id),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- OAuth2 Authorization Codes
CREATE TABLE oauth_authorization_codes (
    code VARCHAR(100) PRIMARY KEY,
    client_id UUID REFERENCES oauth_clients(id),
    user_id UUID REFERENCES users(id),
    redirect_uri VARCHAR(500),
    scope TEXT,
    code_challenge VARCHAR(128),
    code_challenge_method VARCHAR(10),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- OAuth2 Access Tokens
CREATE TABLE oauth_access_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    token VARCHAR(100) UNIQUE NOT NULL,
    client_id UUID REFERENCES oauth_clients(id),
    user_id UUID REFERENCES users(id),
    scope TEXT,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Refresh Tokens
CREATE TABLE oauth_refresh_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    token VARCHAR(100) UNIQUE NOT NULL,
    client_id UUID REFERENCES oauth_clients(id),
    user_id UUID REFERENCES users(id),
    access_token_id UUID REFERENCES oauth_access_tokens(id),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Social Login Connections
CREATE TABLE social_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    provider VARCHAR(50) NOT NULL,
    provider_user_id VARCHAR(255) NOT NULL,
    provider_username VARCHAR(255),
    provider_email VARCHAR(255),
    access_token TEXT,
    refresh_token TEXT,
    expires_at TIMESTAMP WITH TIME ZONE,
    profile_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(provider, provider_user_id)
);

-- Roles and Permissions
CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_system BOOLEAN DEFAULT false,
    tenant_id UUID REFERENCES tenants(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(name, tenant_id)
);

CREATE TABLE permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    resource VARCHAR(100) NOT NULL,
    action VARCHAR(50) NOT NULL,
    description TEXT,
    is_system BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(resource, action)
);

-- Role-Permission Mapping
CREATE TABLE role_permissions (
    role_id UUID REFERENCES roles(id),
    permission_id UUID REFERENCES permissions(id),
    PRIMARY KEY (role_id, permission_id)
);

-- User-Role Assignment
CREATE TABLE user_roles (
    user_id UUID REFERENCES users(id),
    role_id UUID REFERENCES roles(id),
    assigned_by UUID REFERENCES users(id),
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (user_id, role_id)
);

-- Active Sessions
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    session_id VARCHAR(100) UNIQUE NOT NULL,
    device_info JSONB,
    ip_address INET,
    user_agent TEXT,
    location JSONB,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL
);

-- Audit Log
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    session_id VARCHAR(100),
    event_type VARCHAR(50) NOT NULL,
    event_category VARCHAR(50) NOT NULL,
    resource VARCHAR(100),
    action VARCHAR(50),
    success BOOLEAN NOT NULL,
    error_message TEXT,
    ip_address INET,
    user_agent TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Identity Providers (SAML, OIDC)
CREATE TABLE identity_providers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    type VARCHAR(20) CHECK (type IN ('saml', 'oidc', 'ldap')),
    configuration JSONB NOT NULL,
    tenant_id UUID REFERENCES tenants(id),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Extended User Model

```python
# Enhanced User model fields
class User(Base):
    # Existing fields remain the same
    # ... existing fields
    
    # New IAM-specific fields
    email_verified = Column(Boolean, default=False)
    phone_verified = Column(Boolean, default=False)
    
    # Account settings
    require_password_change = Column(Boolean, default=False)
    password_expires_at = Column(DateTime(timezone=True))
    account_locked_until = Column(DateTime(timezone=True))
    failed_login_attempts = Column(Integer, default=0)
    
    # Privacy settings
    profile_visibility = Column(Enum('public', 'private', 'organization', name='profile_visibility_enum'), default='organization')
    
    # Timestamps
    email_verified_at = Column(DateTime(timezone=True))
    phone_verified_at = Column(DateTime(timezone=True))
    last_password_change = Column(DateTime(timezone=True))
    
    # Relationships
    social_connections = relationship("SocialConnection", back_populates="user", cascade="all, delete-orphan")
    user_roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    oauth_authorized_clients = relationship("OAuthClient", secondary="oauth_client_users", back_populates="authorized_users")
```

## API Architecture

### RESTful Endpoint Structure

#### Authentication Endpoints
```
POST /api/auth/login              # Username/password login
POST /api/auth/logout             # Logout and revoke tokens
POST /api/auth/refresh            # Refresh access token
POST /api/auth/forgot-password    # Initiate password reset
POST /api/auth/reset-password     # Complete password reset
POST /api/auth/verify-email       # Verify email address
POST /api/auth/resend-verification # Resend verification email
```

#### OAuth2/OIDC Endpoints
```
GET  /oauth/authorize             # Authorization endpoint
POST /oauth/token                 # Token endpoint
POST /oauth/introspect           # Token introspection
POST /oauth/revoke               # Token revocation
GET  /oauth/jwks                 # JSON Web Key Set
GET  /.well-known/openid-configuration # OIDC discovery
```

#### Social Login Endpoints
```
GET  /api/auth/social/{provider}         # Initiate social login
GET  /api/auth/social/{provider}/callback # Social login callback
POST /api/auth/social/link               # Link external identity
DELETE /api/auth/social/{provider}       # Unlink external identity
```

#### User Management Endpoints
```
GET    /api/users                       # List users (paginated)
POST   /api/users                       # Create user
GET    /api/users/{user_id}             # Get user details
PUT    /api/users/{user_id}             # Update user
DELETE /api/users/{user_id}             # Delete user
GET    /api/users/me                    # Current user profile
PUT    /api/users/me                    # Update current user
```

#### Client Application Endpoints
```
GET    /api/applications               # List OAuth clients
POST   /api/applications               # Create OAuth client
GET    /api/applications/{client_id}   # Get client details
PUT    /api/applications/{client_id}   # Update client
DELETE /api/applications/{client_id}   # Delete client
POST   /api/applications/{client_id}/secret # Rotate client secret
```

#### Role and Permission Endpoints
```
GET    /api/roles                      # List roles
POST   /api/roles                      # Create role
GET    /api/roles/{role_id}            # Get role details
PUT    /api/roles/{role_id}            # Update role
DELETE /api/roles/{role_id}            # Delete role
GET    /api/permissions                # List permissions
POST   /api/roles/{role_id}/permissions # Assign permissions
DELETE /api/roles/{role_id}/permissions/{perm_id} # Remove permission
POST   /api/users/{user_id}/roles      # Assign role to user
DELETE /api/users/{user_id}/roles/{role_id} # Remove role from user
```

#### Session Management Endpoints
```
GET    /api/sessions                   # List user sessions
GET    /api/sessions/{session_id}      # Get session details
DELETE /api/sessions/{session_id}      # Revoke specific session
DELETE /api/sessions                   # Revoke all sessions
PUT    /api/sessions/{session_id}/refresh # Refresh session
```

#### Audit and Monitoring Endpoints
```
GET    /api/audit/logs                 # List audit events
GET    /api/audit/logs/{event_id}      # Get audit event details
GET    /api/audit/reports              # Generate compliance reports
GET    /api/metrics                    # System metrics
GET    /api/health                     # Health check
```

### GraphQL API (Optional Phase 2)
```graphql
type User {
  id: ID!
  email: String!
  username: String!
  roles: [Role!]!
  permissions: [Permission!]!
  sessions: [Session!]!
  socialConnections: [SocialConnection!]!
}

type AuthPayload {
  accessToken: String!
  refreshToken: String!
  user: User!
}

type Query {
  me: User
  user(id: ID!): User
  users(filter: UserFilter): [User!]!
  roles: [Role!]!
  permissions: [Permission!]!
  auditLogs(filter: AuditFilter): [AuditLog!]!
}

type Mutation {
  login(email: String!, password: String!): AuthPayload!
  logout: Boolean!
  register(user: CreateUserInput!): AuthPayload!
  updateProfile(user: UpdateUserInput!): User!
  createRole(role: CreateRoleInput!): Role!
  assignRole(userId: ID!, roleId: ID!): Boolean!
  revokeSession(sessionId: ID!): Boolean!
}
```

## Security Model

### Authentication Security
1. **Multi-layer Token Validation**
   - JWT signature verification
   - Expiration time checking
   - Audience and issuer validation
   - Scope verification

2. **Session Security**
   - Secure session ID generation
   - Session fixation protection
   - Concurrent session management
   - Automatic session expiration

3. **Password Security**
   - Bcrypt hashing with salt
   - Minimum complexity requirements
   - Password history checking
   - Account lockout after failed attempts

### Authorization Security
1. **Role-Based Access Control**
   - Hierarchical role system
   - Permission inheritance
   - Dynamic role assignment
   - Context-aware authorization

2. **Resource Protection**
   - URL-based access control
   - Method-level permissions
   - Field-level security
   - Data filtering

### Audit and Monitoring
1. **Comprehensive Logging**
   - Authentication events
   - Authorization decisions
   - User actions
   - System events

2. **Real-time Monitoring**
   - Suspicious activity detection
   - Brute force attack prevention
   - Unusual pattern recognition
   - Security alerting

## Integration Patterns

### Framework SDKs

#### JavaScript/TypeScript SDK
```typescript
import { SigmaIAM } from '@sigma/iam-js';

const iam = new SigmaIAM({
  baseURL: 'https://your-iam-instance.com',
  clientId: 'your-client-id',
  clientSecret: 'your-client-secret'
});

// Authentication
const user = await iam.login('user@example.com', 'password');
const user = await iam.loginWithGoogle();

// User management
const profile = await iam.getProfile();
await iam.updateProfile({ fullName: 'John Doe' });

// Role management
const roles = await iam.getUserRoles();
await iam.assignRole(userId, 'admin');
```

#### Python SDK
```python
from sigma_iam import SigmaIAM

iam = SigmaIAM(
    base_url='https://your-iam-instance.com',
    client_id='your-client-id',
    client_secret='your-client-secret'
)

# Authentication
user = iam.login('user@example.com', 'password')
user = iam.login_with_google()

# User management
profile = iam.get_profile()
iam.update_profile({'full_name': 'John Doe'})

# Role management
roles = iam.get_user_roles()
iam.assign_role(user_id, 'admin')
```

#### React Integration
```tsx
import { useSigmaAuth } from '@sigma/iam-react';

function MyApp() {
  const { user, login, logout, isLoading } = useSigmaAuth();

  if (isLoading) return <div>Loading...</div>;
  
  if (!user) {
    return (
      <form onSubmit={login}>
        <input type="email" name="email" />
        <input type="password" name="password" />
        <button>Login</button>
      </form>
    );
  }

  return (
    <div>
      <h1>Welcome, {user.fullName}</h1>
      <button onClick={logout}>Logout</button>
    </div>
  );
}
```

### Docker Deployment

#### docker-compose.yml
```yaml
version: '3.8'

services:
  sigma-iam:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@postgres:5432/sigma_iam
      - REDIS_URL=redis://redis:6379
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - ADMIN_EMAIL=${ADMIN_EMAIL}
      - ADMIN_PASSWORD=${ADMIN_PASSWORD}
    depends_on:
      - postgres
      - redis
    volumes:
      - ./uploads:/app/uploads

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=sigma_iam
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  caddy:
    image: caddy:latest
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - caddy_data:/data
      - caddy_config:/config

volumes:
  postgres_data:
  redis_data:
  caddy_data:
  caddy_config:
```

## Performance Optimization

### Caching Strategy
1. **Redis for Sessions**: Store active sessions and refresh tokens
2. **User Data Caching**: Cache user profiles and permissions
3. **Permission Caching**: Cache role-permission mappings
4. **Rate Limiting**: Implement per-user and per-IP rate limits

### Database Optimization
1. **Proper Indexing**: Index on user_id, client_id, timestamps
2. **Connection Pooling**: Use async connection pools
3. **Query Optimization**: Avoid N+1 queries, use joins
4. **Data Archiving**: Archive old audit logs and sessions

### API Optimization
1. **Response Compression**: Enable gzip compression
2. **Pagination**: Always paginate list endpoints
3. **Selective Loading**: Support field selection in responses
4. **Etag Support**: Implement ETags for caching

This architecture design provides a comprehensive foundation for transforming Sigma Permit 2.0 into a competitive IAM solution while maintaining simplicity and developer-friendliness.