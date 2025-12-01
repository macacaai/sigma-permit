# API Expansion Plan for IAM Features

## Overview
Comprehensive plan to extend the current Sigma Permit 2.0 API with enterprise-grade IAM capabilities while maintaining backward compatibility and developer-friendly design.

## Design Principles

### 1. Backward Compatibility
- **Existing endpoints remain unchanged**
- **New features are additive only**
- **Deprecation policy**: 12-month notice for any breaking changes
- **Version compatibility**: Support multiple API versions

### 2. RESTful Design
- **Consistent resource naming**: `/api/v1/users`, `/api/v1/oauth/clients`
- **Proper HTTP methods**: GET, POST, PUT, DELETE, PATCH
- **Standard status codes**: 200, 201, 400, 401, 403, 404, 422, 429, 500
- **Consistent error format**: JSON with error code, message, details

### 3. Security First
- **OAuth2 Bearer tokens** for all protected endpoints
- **Rate limiting**: Per-user and per-client limits
- **Input validation**: Comprehensive request validation
- **Audit logging**: All security-relevant events logged

### 4. Developer Experience
- **OpenAPI 3.0 documentation**: Complete API specification
- **SDK-ready**: Design for easy SDK generation
- **Pagination**: Consistent across all list endpoints
- **Filtering and sorting**: Query parameters for data manipulation

## API Versioning Strategy

### Version Header Approach
```
Accept: application/vnd.sigma-iam.v1+json
```

### Endpoint Structure
```
/api/v1/auth/...          # Authentication endpoints
/api/v1/oauth/...         # OAuth2/OIDC endpoints  
/api/v1/users/...         # User management
/api/v1/applications/...  # OAuth client management
/api/v1/roles/...         # Role and permission management
/api/v1/sessions/...      # Session management
/api/v1/audit/...         # Audit and monitoring
/api/v1/admin/...         # Administrative endpoints
```

## Enhanced Authentication Endpoints

### Current Endpoints (Maintained)
```
POST /api/auth/login              # Username/password login
POST /api/auth/logout             # Logout and revoke tokens
POST /api/auth/refresh            # Refresh access token
GET  /api/auth/me                 # Get current user
POST /api/auth/change-password    # Change password
```

### New Authentication Endpoints
```http
# Password Management
POST /api/v1/auth/forgot-password      # Initiate password reset
POST /api/v1/auth/reset-password       # Complete password reset
POST /api/v1/auth/verify-email         # Verify email address
POST /api/v1/auth/resend-verification  # Resend verification email
POST /api/v1/auth/verify-phone         # Verify phone number
POST /api/v1/auth/resend-phone-code    # Resend SMS verification

# Account Management  
POST /api/v1/auth/delete-account       # Delete user account
POST /api/v1/auth/deactivate-account   # Deactivate account
POST /api/v1/auth/reactivate-account   # Reactivate account
GET  /api/v1/auth/account-status       # Get account status

# Multi-Factor Authentication (Phase 2)
POST /api/v1/auth/mfa/enable           # Enable MFA
POST /api/v1/auth/mfa/disable          # Disable MFA
POST /api/v1/auth/mfa/verify           # Verify MFA code
GET  /api/v1/auth/mfa/methods          # Get available MFA methods
```

### Enhanced Request/Response Formats

#### Current Login Response
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "user@example.com",
    "username": "johndoe",
    "full_name": "John Doe"
  }
}
```

#### Enhanced Login Response
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 1800,
  "scope": "read write",
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "user@example.com",
    "email_verified": false,
    "username": "johndoe",
    "full_name": "John Doe",
    "roles": ["user"],
    "permissions": ["users:read", "users:write"],
    "tenant_id": "tenant-uuid",
    "last_login": "2025-11-30T07:59:00Z"
  }
}
```

## OAuth2/OIDC Endpoints

### Authorization Endpoint
```http
GET /oauth/v1/authorize
    ?response_type=code                    # code, token, id_token
    &client_id=CLIENT_ID
    &redirect_uri=https://app.example.com/callback
    &scope=read write openid
    &state=RANDOM_STATE
    &code_challenge=CHALLENGE             # For PKCE
    &code_challenge_method=S256           # S256 or plain
    &nonce=RANDOM_NONCE                   # For OIDC
```

**Response**: Redirect to login page or consent screen

### Token Endpoint
```http
POST /oauth/v1/token
Content-Type: application/x-www-form-urlencoded
Authorization: Basic CLIENT_ID:CLIENT_SECRET  # For confidential clients

grant_type=authorization_code
    &code=AUTH_CODE
    &redirect_uri=https://app.example.com/callback
    &code_verifier=CODE_VERIFIER              # For PKCE
```

**Response**:
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "Bearer",
  "expires_in": 1800,
  "scope": "read write openid",
  "id_token": "eyJ..."  # OIDC only
}
```

### Token Introspection Endpoint
```http
POST /oauth/v1/introspect
Content-Type: application/x-www-form-urlencoded
Authorization: Basic CLIENT_ID:CLIENT_SECRET

token=ACCESS_TOKEN
```

**Response**:
```json
{
  "active": true,
  "client_id": "CLIENT_ID",
  "sub": "USER_ID",
  "exp": 1234567890,
  "iat": 1234567890,
  "scope": "read write openid",
  "token_type": "Bearer",
  "tenant_id": "tenant-uuid"
}
```

### Token Revocation Endpoint
```http
POST /oauth/v1/revoke
Content-Type: application/x-www-form-urlencoded
Authorization: Basic CLIENT_ID:CLIENT_SECRET

token=ACCESS_TOKEN
```

### Discovery Endpoint
```http
GET /.well-known/openid-configuration
```

**Response**:
```json
{
  "issuer": "https://iam.example.com",
  "authorization_endpoint": "https://iam.example.com/oauth/v1/authorize",
  "token_endpoint": "https://iam.example.com/oauth/v1/token",
  "userinfo_endpoint": "https://iam.example.com/oauth/v1/userinfo",
  "jwks_uri": "https://iam.example.com/oauth/v1/jwks",
  "response_types_supported": ["code", "token", "id_token"],
  "subject_types_supported": ["public"],
  "id_token_signing_alg_values_supported": ["RS256"],
  "scopes_supported": ["openid", "profile", "email", "read", "write"],
  "token_endpoint_auth_methods_supported": ["client_secret_basic", "client_secret_post"],
  "claims_supported": ["sub", "name", "email", "email_verified", "preferred_username"]
}
```

## Social Login Endpoints

### Initiate Social Login
```http
GET /api/v1/auth/social/{provider}
    ?redirect_uri=https://app.example.com/callback
    &state=RANDOM_STATE
```

**Supported Providers**: Google, GitHub, Facebook, Microsoft, LinkedIn

### Social Login Callback
```http
GET /api/v1/auth/social/{provider}/callback
    ?code=AUTH_CODE
    &state=RANDOM_STATE
```

**Response**: Same format as regular login

### Social Account Management
```http
GET    /api/v1/users/me/social-connections     # List linked accounts
POST   /api/v1/auth/social/link               # Link external account
DELETE /api/v1/auth/social/{provider}         # Unlink external account
PUT    /api/v1/users/me/social-connections/{id}/primary  # Set primary identity
```

## Enhanced User Management

### User CRUD Operations
```http
GET    /api/v1/users?page=1&size=20&sort=created_at,desc&filter=role:admin
POST   /api/v1/users
GET    /api/v1/users/{user_id}
PUT    /api/v1/users/{user_id}
DELETE /api/v1/users/{user_id}
PATCH  /api/v1/users/{user_id}/activate       # Activate/deactivate user
PATCH  /api/v1/users/{user_id}/verify-email   # Verify email manually
```

### Enhanced User Filtering
```
GET /api/v1/users?filter=role:admin,status:active&sort=created_at&fields=id,email,full_name
```

**Filter Parameters**:
- `role`: Filter by role
- `status`: active, inactive, pending_verification
- `verified`: true, false
- `created_after`: ISO date
- `last_login_after`: ISO date
- `tenant_id`: Filter by tenant

### Bulk Operations
```http
POST /api/v1/users/bulk-create                 # Create multiple users
PUT  /api/v1/users/bulk-update                 # Update multiple users
DELETE /api/v1/users/bulk-delete               # Delete multiple users
POST /api/v1/users/bulk-import                 # Import from CSV
GET  /api/v1/users/export?format=csv           # Export users
```

### User Profile Management
```http
GET    /api/v1/users/me/profile                # Get my profile
PUT    /api/v1/users/me/profile                # Update my profile
POST   /api/v1/users/me/avatar                 # Upload avatar
DELETE /api/v1/users/me/avatar                 # Remove avatar
GET    /api/v1/users/me/preferences            # Get user preferences
PUT    /api/v1/users/me/preferences            # Update user preferences
```

## Client Application Management

### OAuth Client CRUD
```http
GET    /api/v1/applications?page=1&size=20&sort=created_at,desc
POST   /api/v1/applications
GET    /api/v1/applications/{client_id}
PUT    /api/v1/applications/{client_id}
DELETE /api/v1/applications/{client_id}
PATCH  /api/v1/applications/{client_id}/activate  # Activate/deactivate
```

### Client Configuration
```http
POST /api/v1/applications/{client_id}/secret          # Generate new secret
GET  /api/v1/applications/{client_id}/authorized-users # List authorized users
POST /api/v1/applications/{client_id}/authorized-users # Grant user access
DELETE /api/v1/applications/{client_id}/authorized-users/{user_id} # Revoke access
POST /api/v1/applications/{client_id}/consent          # Grant user consent
GET  /api/v1/applications/{client_id}/sessions         # Get active sessions
```

### Application Creation Request
```json
{
  "client_name": "My Application",
  "client_type": "confidential",
  "redirect_uris": [
    "https://app.example.com/callback",
    "https://app.example.com/callback2"
  ],
  "allowed_grant_types": [
    "authorization_code",
    "refresh_token"
  ],
  "allowed_scopes": [
    "read",
    "write",
    "profile"
  ],
  "logo_uri": "https://app.example.com/logo.png",
  "website_uri": "https://app.example.com",
  "description": "My awesome application"
}
```

### Application Response
```json
{
  "id": "client-uuid",
  "client_id": "generated-client-id",
  "client_secret": "generated-client-secret",  # Only shown on creation
  "client_name": "My Application",
  "client_type": "confidential",
  "redirect_uris": [
    "https://app.example.com/callback"
  ],
  "allowed_grant_types": [
    "authorization_code",
    "refresh_token"
  ],
  "allowed_scopes": [
    "read",
    "write",
    "profile"
  ],
  "is_active": true,
  "created_at": "2025-11-30T07:59:00Z",
  "updated_at": "2025-11-30T07:59:00Z"
}
```

## Role and Permission Management

### Roles CRUD
```http
GET    /api/v1/roles?page=1&size=20&sort=name,asc
POST   /api/v1/roles
GET    /api/v1/roles/{role_id}
PUT    /api/v1/roles/{role_id}
DELETE /api/v1/roles/{role_id}
```

### Permissions Management
```http
GET    /api/v1/permissions?resource=users&action=read
POST   /api/v1/roles/{role_id}/permissions        # Assign permissions
DELETE /api/v1/roles/{role_id}/permissions/{perm_id} # Remove permission
GET    /api/v1/roles/{role_id}/permissions        # Get role permissions
GET    /api/v1/permissions/effective?user_id={id} # Get user effective permissions
```

### User Role Assignment
```http
POST   /api/v1/users/{user_id}/roles              # Assign role to user
DELETE /api/v1/users/{user_id}/roles/{role_id}    # Remove role from user
GET    /api/v1/users/{user_id}/roles              # Get user roles
GET    /api/v1/roles/{role_id}/users              # Get users with role
```

### Role Template Management
```http
GET /api/v1/roles/templates                       # Get role templates
POST /api/v1/roles/{role_id}/clone                # Clone role
GET /api/v1/roles/{role_id}/inheritance           # Get role hierarchy
```

## Session Management

### Session CRUD
```http
GET    /api/v1/sessions?page=1&size=20&sort=last_activity,desc
GET    /api/v1/sessions/{session_id}
DELETE /api/v1/sessions/{session_id}
DELETE /api/v1/sessions                            # Revoke all sessions
PUT    /api/v1/sessions/{session_id}/refresh       # Extend session
POST   /api/v1/sessions/{session_id}/terminate     # Terminate session
```

### Device Management
```http
GET    /api/v1/devices                             # Get user devices
PUT    /api/v1/devices/{device_id}/trust           # Trust device
DELETE /api/v1/devices/{device_id}                 # Remove device
```

### Session Security
```http
POST /api/v1/sessions/{session_id}/lock            # Lock session
POST /api/v1/sessions/{session_id}/unlock          # Unlock session
POST /api/v1/sessions/require-mfa                  # Require MFA for session
```

## Audit and Monitoring

### Audit Log Management
```http
GET    /api/v1/audit/logs?page=1&size=20&sort=created_at,desc
GET    /api/v1/audit/logs/{event_id}
GET    /api/v1/audit/logs/export?format=json&start_date=2025-01-01&end_date=2025-01-31
```

### Audit Filtering
```
GET /api/v1/audit/logs?filter=user_id:123,event_type:login,success:true&start_date=2025-01-01&end_date=2025-01-31
```

**Filter Parameters**:
- `user_id`: Filter by user
- `event_type`: login, logout, create_user, etc.
- `event_category`: authentication, authorization, user_management
- `success`: true, false
- `resource`: Filter by resource type
- `ip_address`: Filter by IP address
- `start_date`, `end_date`: Date range filtering

### Compliance Reporting
```http
GET /api/v1/audit/reports/gdpr?start_date=2025-01-01&end_date=2025-01-31
GET /api/v1/audit/reports/soc2?format=pdf
GET /api/v1/audit/reports/user-activity?user_id=123&days=30
GET /api/v1/audit/reports/security-events?severity=high&days=7
```

### Real-time Events
```http
GET /api/v1/audit/events/stream                   # Server-sent events for real-time monitoring
GET /api/v1/audit/alerts                         # Security alerts
POST /api/v1/audit/alerts/{alert_id}/acknowledge  # Acknowledge alert
```

## System Monitoring

### Health and Metrics
```http
GET /api/v1/health/detailed                      # Detailed health check
GET /api/v1/metrics                              # Prometheus metrics
GET /api/v1/metrics/export                       # Export metrics
GET /api/v1/status                               # System status dashboard
```

### Performance Monitoring
```http
GET /api/v1/performance/auth-latency             # Authentication performance
GET /api/v1/performance/api-latency              # API performance metrics
GET /api/v1/performance/database-performance     # Database performance
GET /api/v1/performance/cache-performance        # Cache performance
```

## Administrative Endpoints

### Tenant Management
```http
GET    /api/v1/admin/tenants?page=1&size=20
POST   /api/v1/admin/tenants
GET    /api/v1/admin/tenants/{tenant_id}
PUT    /api/v1/admin/tenants/{tenant_id}
DELETE /api/v1/admin/tenants/{tenant_id}
POST   /api/v1/admin/tenants/{tenant_id}/suspend      # Suspend tenant
POST   /api/v1/admin/tenants/{tenant_id}/activate     # Activate tenant
```

### System Configuration
```http
GET /api/v1/admin/config                          # Get system configuration
PUT /api/v1/admin/config                          # Update system configuration
POST /api/v1/admin/config/reset                   # Reset to defaults
GET /api/v1/admin/config/export                   # Export configuration
POST /api/v1/admin/config/import                  # Import configuration
```

### Backup and Maintenance
```http
POST /api/v1/admin/backup/create                  # Create backup
GET  /api/v1/admin/backup/list                    # List backups
POST /api/v1/admin/backup/{backup_id}/restore     # Restore backup
POST /api/v1/admin/maintenance/start              # Start maintenance mode
POST /api/v1/admin/maintenance/stop               # Stop maintenance mode
```

## Error Handling and Status Codes

### Standard Error Response Format
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": [
      {
        "field": "email",
        "message": "Email format is invalid"
      }
    ],
    "request_id": "req_123456789"
  }
}
```

### Common Error Codes
- `AUTHENTICATION_REQUIRED`: 401
- `INSUFFICIENT_PERMISSIONS`: 403
- `RESOURCE_NOT_FOUND`: 404
- `VALIDATION_ERROR`: 422
- `RATE_LIMIT_EXCEEDED`: 429
- `SERVER_ERROR`: 500

### Rate Limiting Headers
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
Retry-After: 60
```

## API Security Best Practices

### 1. Authentication and Authorization
- All endpoints require Bearer token authentication
- Permission-based access control
- Tenant isolation enforced at API level
- Client application scoping

### 2. Input Validation
- Comprehensive request validation
- SQL injection prevention via ORM
- XSS protection via output encoding
- CSRF protection for state-changing operations

### 3. Rate Limiting
- Per-user rate limits: 1000 requests/hour
- Per-client rate limits: 10000 requests/hour
- Per-IP rate limits: 100 requests/minute
- Burst protection for authentication endpoints

### 4. Audit and Monitoring
- All security events logged
- Request/response logging for debugging
- Real-time security monitoring
- Automated alerting for suspicious activity

This comprehensive API expansion plan provides the foundation for a feature-rich IAM solution that maintains developer-friendly design while delivering enterprise-grade capabilities.