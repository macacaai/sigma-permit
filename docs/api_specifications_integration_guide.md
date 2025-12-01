# API Specifications and Integration Guidelines

## Overview
Comprehensive API specifications and integration guide for the Sigma IAM solution, designed to provide developers with everything they need to integrate IAM capabilities into their applications quickly and securely.

## API Architecture Overview

### API Design Principles

#### 1. RESTful Design
- **Resource-based URLs**: `/api/v1/users`, `/api/v1/applications`
- **HTTP methods**: GET, POST, PUT, DELETE, PATCH
- **Stateless**: Each request contains all necessary information
- **Consistent responses**: Standardized response formats

#### 2. Versioning Strategy
- **URL versioning**: `/api/v1/` for current version
- **Header versioning**: `Accept: application/vnd.sigma-iam.v1+json`
- **Backward compatibility**: Support for previous versions
- **Deprecation policy**: 12-month notice for breaking changes

#### 3. Security by Default
- **OAuth2 Bearer tokens**: All requests require authentication
- **HTTPS only**: All communication encrypted in transit
- **CORS configuration**: Configurable cross-origin policies
- **Rate limiting**: Built-in protection against abuse

## OpenAPI 3.0 Specification

### Authentication Endpoints

#### User Authentication
```yaml
# /api/v1/auth/login
post:
  summary: Authenticate user with username and password
  tags: [Authentication]
  requestBody:
    required: true
    content:
      application/x-www-form-urlencoded:
        schema:
          type: object
          required:
            - credentials
          properties:
            credentials:
              type: string
              description: Base64 encoded username:password
              example: dXNlcjpwYXNzd29yZA==
  responses:
    '200':
      description: Successful authentication
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/LoginResponse'
    '401':
      description: Invalid credentials
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
    '429':
      description: Rate limit exceeded
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/RateLimitErrorResponse'

# /api/v1/auth/refresh
post:
  summary: Refresh access token using refresh token
  tags: [Authentication]
  requestBody:
    required: true
    content:
      application/x-www-form-urlencoded:
        schema:
          type: object
          required:
            - refresh_token
          properties:
            refresh_token:
              type: string
              description: Refresh token to use for obtaining new access token
  responses:
    '200':
      description: Token refreshed successfully
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/TokenResponse'
    '401':
      description: Invalid or expired refresh token
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
```

#### Social Authentication
```yaml
# /api/v1/auth/social/{provider}
get:
  summary: Initiate social authentication
  tags: [Authentication]
  parameters:
    - name: provider
      in: path
      required: true
      schema:
        type: string
        enum: [google, github, facebook, microsoft, linkedin]
    - name: redirect_uri
      in: query
      required: true
      schema:
        type: string
        format: uri
      description: URI to redirect to after authentication
    - name: state
      in: query
      schema:
        type: string
      description: CSRF protection state parameter
  responses:
    '302':
      description: Redirect to social provider
    '400':
      description: Invalid provider or redirect URI
```

### OAuth2/OIDC Endpoints

#### Authorization Endpoint
```yaml
# /oauth/v1/authorize
get:
  summary: OAuth2 authorization endpoint
  tags: [OAuth2]
  parameters:
    - name: response_type
      in: query
      required: true
      schema:
        type: string
        enum: [code, token, id_token]
      description: Type of response expected
    - name: client_id
      in: query
      required: true
      schema:
        type: string
      description: OAuth2 client identifier
    - name: redirect_uri
      in: query
      required: true
      schema:
        type: string
        format: uri
      description: Redirect URI registered with the client
    - name: scope
      in: query
      schema:
        type: string
      description: Requested scopes (space-separated)
    - name: state
      in: query
      schema:
        type: string
      description: CSRF protection state parameter
    - name: nonce
      in: query
      schema:
        type: string
      description: OIDC nonce for ID token validation
    - name: code_challenge
      in: query
      schema:
        type: string
      description: PKCE code challenge for public clients
    - name: code_challenge_method
      in: query
      schema:
        type: string
        enum: [S256, plain]
      description: Method used to generate code challenge
  responses:
    '302':
      description: Redirect to login/consent page or redirect URI
    '400':
      description: Invalid request parameters
    '401':
      description: Authentication required

# /oauth/v1/token
post:
  summary: OAuth2 token endpoint
  tags: [OAuth2]
  requestBody:
    required: true
    content:
      application/x-www-form-urlencoded:
        schema:
          oneOf:
            - $ref: '#/components/schemas/AuthorizationCodeGrant'
            - $ref: '#/components/schemas/ClientCredentialsGrant'
            - $ref: '#/components/schemas/RefreshTokenGrant'
        discriminator:
          propertyName: grant_type
  responses:
    '200':
      description: Token issued successfully
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/TokenResponse'
    '400':
      description: Invalid grant request
    '401':
      description: Invalid client credentials
```

### User Management Endpoints

#### User CRUD Operations
```yaml
# /api/v1/users
get:
  summary: List users with filtering and pagination
  tags: [Users]
  parameters:
    - name: page
      in: query
      schema:
        type: integer
        minimum: 1
        default: 1
    - name: size
      in: query
      schema:
        type: integer
        minimum: 1
        maximum: 100
        default: 20
    - name: sort
      in: query
      schema:
        type: string
        pattern: '^[a-zA-Z_]+:(asc|desc)$'
      description: Sort criteria (field:direction)
    - name: filter
      in: query
      schema:
        type: string
        pattern: '^[a-zA-Z_]+:[^:]+(,[a-zA-Z_]+:[^:]+)*$'
      description: Filter criteria (key:value,key2:value2)
  responses:
    '200':
      description: List of users
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/UserListResponse'

post:
  summary: Create a new user
  tags: [Users]
  requestBody:
    required: true
    content:
      application/json:
        schema:
          $ref: '#/components/schemas/UserCreateRequest'
  responses:
    '201':
      description: User created successfully
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/UserResponse'
    '400':
      description: Invalid input data
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ValidationErrorResponse'
    '409':
      description: User already exists
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ConflictErrorResponse'

# /api/v1/users/{user_id}
get:
  summary: Get user by ID
  tags: [Users]
  parameters:
    - name: user_id
      in: path
      required: true
      schema:
        type: string
        format: uuid
  responses:
    '200':
      description: User details
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/UserResponse'
    '404':
      description: User not found

put:
  summary: Update user
  tags: [Users]
  parameters:
    - name: user_id
      in: path
      required: true
      schema:
        type: string
        format: uuid
  requestBody:
    required: true
    content:
      application/json:
        schema:
          $ref: '#/components/schemas/UserUpdateRequest'
  responses:
    '200':
      description: User updated successfully
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/UserResponse'

delete:
  summary: Delete user
  tags: [Users]
  parameters:
    - name: user_id
      in: path
      required: true
      schema:
        type: string
        format: uuid
  responses:
    '204':
      description: User deleted successfully
    '404':
      description: User not found
```

### Client Application Management

#### OAuth2 Client Management
```yaml
# /api/v1/applications
get:
  summary: List OAuth2 client applications
  tags: [Applications]
  parameters:
    - name: page
      in: query
      schema:
        type: integer
        default: 1
    - name: size
      in: query
      schema:
        type: integer
        default: 20
  responses:
    '200':
      description: List of client applications
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ApplicationListResponse'

post:
  summary: Create new OAuth2 client application
  tags: [Applications]
  requestBody:
    required: true
    content:
      application/json:
        schema:
          $ref: '#/components/schemas/ApplicationCreateRequest'
  responses:
    '201':
      description: Application created successfully
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ApplicationResponse'
```

### Schema Definitions
```yaml
components:
  schemas:
    LoginResponse:
      type: object
      properties:
        access_token:
          type: string
          description: JWT access token
        refresh_token:
          type: string
          description: Refresh token for obtaining new access tokens
        token_type:
          type: string
          enum: [Bearer]
          default: Bearer
        expires_in:
          type: integer
          description: Token expiration time in seconds
        scope:
          type: string
          description: Granted scopes
        user:
          $ref: '#/components/schemas/UserResponse'

    UserResponse:
      type: object
      properties:
        id:
          type: string
          format: uuid
          description: Unique user identifier
        email:
          type: string
          format: email
          description: User email address
        username:
          type: string
          description: Unique username
        full_name:
          type: string
          description: User's full name
        email_verified:
          type: boolean
          description: Whether email is verified
        is_active:
          type: boolean
          description: Whether user account is active
        roles:
          type: array
          items:
            $ref: '#/components/schemas/RoleResponse'
        permissions:
          type: array
          items:
            type: string
          description: User permissions
        created_at:
          type: string
          format: date-time
        last_login:
          type: string
          format: date-time

    ApplicationResponse:
      type: object
      properties:
        id:
          type: string
          format: uuid
        client_id:
          type: string
          description: Public client identifier
        client_name:
          type: string
          description: Application name
        client_type:
          type: string
          enum: [confidential, public]
        redirect_uris:
          type: array
          items:
            type: string
            format: uri
        allowed_grant_types:
          type: array
          items:
            type: string
        allowed_scopes:
          type: array
          items:
            type: string
        is_active:
          type: boolean
        created_at:
          type: string
          format: date-time

    ErrorResponse:
      type: object
      properties:
        error:
          type: object
          properties:
            code:
              type: string
              description: Error code
            message:
              type: string
              description: Human-readable error message
            details:
              type: array
              items:
                type: object
                properties:
                  field:
                    type: string
                    description: Field that caused the error
                  message:
                    type: string
                    description: Field-specific error message
            request_id:
              type: string
              description: Unique request identifier for troubleshooting

    RateLimitErrorResponse:
      type: object
      properties:
        error:
          type: object
          properties:
            code:
              type: string
              enum: [RATE_LIMIT_EXCEEDED]
            message:
              type: string
              description: Rate limit exceeded message
            retry_after:
              type: integer
              description: Seconds to wait before retrying
```

## SDK Documentation

### JavaScript/TypeScript SDK

#### Installation and Setup
```bash
# npm
npm install @sigma/iam-js

# yarn
yarn add @sigma/iam-js

# pnpm
pnpm add @sigma/iam-js
```

#### Basic Usage
```typescript
import { SigmaIAM } from '@sigma/iam-js';

// Initialize the client
const iam = new SigmaIAM({
  baseURL: 'https://your-iam-instance.com',
  clientId: 'your-client-id',
  clientSecret: 'your-client-secret',
  redirectUri: 'https://your-app.com/callback'
});

// Authentication
const { user, accessToken } = await iam.login('user@example.com', 'password');
console.log('Logged in as:', user.full_name);

// Social login
const { user: googleUser } = await iam.loginWithGoogle();

// User management
const profile = await iam.getProfile();
await iam.updateProfile({ fullName: 'John Doe' });

// Role management
const roles = await iam.getUserRoles();
await iam.assignRole(userId, 'admin');

// Client application management
const app = await iam.createApplication({
  client_name: 'My Application',
  client_type: 'confidential',
  redirect_uris: ['https://myapp.com/callback'],
  allowed_grant_types: ['authorization_code', 'refresh_token'],
  allowed_scopes: ['read', 'write']
});

// Get OAuth2 authorization URL
const authUrl = iam.getAuthorizationUrl({
  scope: 'read write',
  state: 'random_state_value',
  codeChallenge: codeChallenge,
  codeChallengeMethod: 'S256'
});
```

#### React Integration
```tsx
import { useSigmaAuth } from '@sigma/iam-react';

function App() {
  const {
    user,
    login,
    logout,
    isLoading,
    isAuthenticated
  } = useSigmaAuth();

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (!isAuthenticated) {
    return (
      <LoginForm onLogin={login} />
    );
  }

  return (
    <div>
      <h1>Welcome, {user?.fullName}</h1>
      <button onClick={logout}>Logout</button>
      
      {/* Protected content */}
      <ProtectedComponent />
    </div>
  );
}

function ProtectedComponent() {
  const { user, hasPermission } = useSigmaAuth();

  // Check specific permissions
  if (!hasPermission('users:read')) {
    return <div>Access denied</div>;
  }

  return <UserManagement />;
}
```

#### Next.js Integration
```typescript
// pages/api/auth/login.ts
import { SigmaIAM } from '@sigma/iam-js';
import type { NextApiRequest, NextApiResponse } from 'next';

const iam = new SigmaIAM({
  baseURL: process.env.SIGMA_IAM_BASE_URL!,
  clientId: process.env.SIGMA_IAM_CLIENT_ID!,
  clientSecret: process.env.SIGMA_IAM_CLIENT_SECRET!,
});

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { email, password } = req.body;

  try {
    const { user, accessToken } = await iam.login(email, password);
    
    // Set HTTP-only cookie
    res.setHeader('Set-Cookie', [
      `access_token=${accessToken}; HttpOnly; Secure; SameSite=Strict; Path=/`
    ]);

    res.status(200).json({ user });
  } catch (error) {
    res.status(401).json({ error: 'Invalid credentials' });
  }
}

// middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const accessToken = request.cookies.get('access_token');

  // Protect routes that require authentication
  if (request.nextUrl.pathname.startsWith('/admin') && !accessToken) {
    return NextResponse.redirect(new URL('/login', request.url));
  }

  return NextResponse.next();
}
```

### Python SDK

#### Installation and Setup
```bash
pip install sigma-iam-python
```

#### Basic Usage
```python
from sigma_iam import SigmaIAM

# Initialize the client
iam = SigmaIAM(
    base_url='https://your-iam-instance.com',
    client_id='your-client-id',
    client_secret='your-client-secret'
)

# Authentication
user = iam.login('user@example.com', 'password')
print(f'Logged in as: {user.full_name}')

# User management
profile = iam.get_profile()
iam.update_profile(full_name='John Doe')

# Role management
roles = iam.get_user_roles()
iam.assign_role(user_id='user-uuid', role='admin')

# OAuth2 client management
app = iam.create_application(
    client_name='My Application',
    client_type='confidential',
    redirect_uris=['https://myapp.com/callback'],
    allowed_grant_types=['authorization_code', 'refresh_token'],
    allowed_scopes=['read', 'write']
)

# Get authorization URL
auth_url = iam.get_authorization_url(
    scope='read write',
    state='random_state_value'
)
```

#### FastAPI Integration
```python
from fastapi import FastAPI, Depends, HTTPException
from sigma_iam import SigmaIAM
from sigma_iam.fastapi import SigmaIAMMiddleware

app = FastAPI()

# Add Sigma IAM middleware
iam = SigmaIAMMiddleware(
    app,
    base_url='https://your-iam-instance.com',
    client_id='your-client-id',
    client_secret='your-client-secret'
)

@app.get("/protected")
async def protected_endpoint(user: dict = Depends(iam.get_current_user)):
    """Endpoint that requires authentication"""
    return {"message": f"Hello, {user['full_name']}"}

@app.get("/admin")
async def admin_endpoint(user: dict = Depends(iam.require_permission('admin:read'))):
    """Endpoint that requires admin permission"""
    return {"message": "Admin access granted"}
```

### Node.js/Express Integration

#### Basic Setup
```javascript
const express = require('express');
const SigmaIAM = require('@sigma/iam-node');
const app = express();

const iam = new SigmaIAM({
  baseURL: 'https://your-iam-instance.com',
  clientId: 'your-client-id',
  clientSecret: 'your-client-secret'
});

// Middleware to protect routes
const requireAuth = async (req, res, next) => {
  try {
    const token = req.headers.authorization?.replace('Bearer ', '');
    if (!token) {
      return res.status(401).json({ error: 'Missing access token' });
    }

    const user = await iam.verifyToken(token);
    req.user = user;
    next();
  } catch (error) {
    res.status(401).json({ error: 'Invalid access token' });
  }
};

// Protected route
app.get('/api/protected', requireAuth, (req, res) => {
  res.json({ 
    message: `Hello, ${req.user.full_name}`,
    user: req.user 
  });
});

// OAuth2 callback handler
app.get('/auth/callback', async (req, res) => {
  const { code } = req.query;
  
  try {
    const tokens = await iam.exchangeCodeForTokens(code);
    
    // Store tokens securely (session, database, etc.)
    req.session.tokens = tokens;
    
    res.redirect('/dashboard');
  } catch (error) {
    res.status(400).json({ error: 'Authentication failed' });
  }
});
```

## Integration Examples

### React Application Integration

#### Complete Example
```tsx
import React, { useState, useEffect } from 'react';
import { SigmaIAM } from '@sigma/iam-js';

const iam = new SigmaIAM({
  baseURL: process.env.REACT_APP_IAM_URL!,
  clientId: process.env.REACT_APP_CLIENT_ID!,
  redirectUri: `${window.location.origin}/callback`
});

function App() {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check if user is authenticated
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      const profile = await iam.getProfile();
      setUser(profile);
    } catch (error) {
      console.log('Not authenticated');
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogin = async (email: string, password: string) => {
    try {
      const { user } = await iam.login(email, password);
      setUser(user);
    } catch (error) {
      console.error('Login failed:', error);
    }
  };

  const handleSocialLogin = async (provider: string) => {
    try {
      const authUrl = iam.getAuthorizationUrl({
        scope: 'read write profile',
        provider: provider
      });
      
      // Redirect to social provider
      window.location.href = authUrl;
    } catch (error) {
      console.error('Social login failed:', error);
    }
  };

  const handleLogout = async () => {
    await iam.logout();
    setUser(null);
  };

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (!user) {
    return <LoginForm onLogin={handleLogin} onSocialLogin={handleSocialLogin} />;
  }

  return (
    <div className="app">
      <header>
        <h1>My Application</h1>
        <div>
          <span>Welcome, {user.full_name}</span>
          <button onClick={handleLogout}>Logout</button>
        </div>
      </header>
      
      <main>
        <Dashboard user={user} />
      </main>
    </div>
  );
}

export default App;
```

### Mobile App Integration

#### React Native Example
```typescript
import React, { useState, useEffect } from 'react';
import { View, Text, TextInput, Button, Alert } from 'react-native';
import { SigmaIAMMobile } from '@sigma/iam-react-native';

const iam = new SigmaIAMMobile({
  baseURL: 'https://your-iam-instance.com',
  clientId: 'your-client-id',
  redirectUri: 'yourapp://auth/callback'
});

function LoginScreen() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleLogin = async () => {
    setIsLoading(true);
    try {
      const { user } = await iam.login(email, password);
      Alert.alert('Success', `Welcome, ${user.full_name}!`);
      // Navigate to main app
    } catch (error) {
      Alert.alert('Error', 'Login failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleLogin = async () => {
    try {
      const authUrl = await iam.getAuthorizationUrl({
        provider: 'google',
        scope: 'profile email'
      });
      
      // Open WebView or external browser
      // Handle the callback in your app
    } catch (error) {
      Alert.alert('Error', 'Google login failed');
    }
  };

  return (
    <View style={styles.container}>
      <TextInput
        style={styles.input}
        placeholder="Email"
        value={email}
        onChangeText={setEmail}
        keyboardType="email-address"
      />
      
      <TextInput
        style={styles.input}
        placeholder="Password"
        value={password}
        onChangeText={setPassword}
        secureTextEntry
      />
      
      <Button
        title={isLoading ? 'Logging in...' : 'Login'}
        onPress={handleLogin}
        disabled={isLoading}
      />
      
      <Button
        title="Login with Google"
        onPress={handleGoogleLogin}
      />
    </View>
  );
}
```

## Error Handling Guidelines

### Standard Error Format
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request contains invalid data",
    "details": [
      {
        "field": "email",
        "message": "Invalid email format"
      },
      {
        "field": "password",
        "message": "Password must be at least 8 characters long"
      }
    ],
    "request_id": "req_1234567890",
    "timestamp": "2025-11-30T08:04:56Z"
  }
}
```

### Error Code Reference
| Code | HTTP Status | Description |
|------|-------------|-------------|
| `AUTHENTICATION_REQUIRED` | 401 | Authentication token is missing or invalid |
| `INSUFFICIENT_PERMISSIONS` | 403 | User doesn't have required permissions |
| `RESOURCE_NOT_FOUND` | 404 | Requested resource doesn't exist |
| `VALIDATION_ERROR` | 422 | Request data validation failed |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests in time window |
| `CONFLICT` | 409 | Resource conflict (e.g., duplicate email) |
| `SERVER_ERROR` | 500 | Internal server error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |

### Client-Side Error Handling
```typescript
class IAMError extends Error {
  constructor(
    public code: string,
    public message: string,
    public status: number,
    public details?: Array<{ field: string; message: string }>
  ) {
    super(message);
  }
}

const handleAPIError = (error: any): IAMError => {
  if (error.response?.data?.error) {
    const { code, message, details } = error.response.data.error;
    return new IAMError(code, message, error.response.status, details);
  }
  
  return new IAMError('NETWORK_ERROR', 'Network request failed', 0);
};

// Usage
try {
  await iam.login(email, password);
} catch (error) {
  const iamError = handleAPIError(error);
  
  switch (iamError.code) {
    case 'VALIDATION_ERROR':
      // Handle validation errors
      iamError.details?.forEach(detail => {
        console.log(`${detail.field}: ${detail.message}`);
      });
      break;
      
    case 'RATE_LIMIT_EXCEEDED':
      // Handle rate limiting
      alert('Too many requests. Please wait and try again.');
      break;
      
    case 'AUTHENTICATION_REQUIRED':
      // Redirect to login
      window.location.href = '/login';
      break;
      
    default:
      // Generic error handling
      alert(iamError.message);
  }
}
```

## Security Best Practices

### Token Management
```typescript
// Secure token storage
class TokenManager {
  private static TOKEN_KEY = 'sigma_iam_tokens';
  
  static storeTokens(tokens: { accessToken: string; refreshToken: string }) {
    // Store in secure storage (not localStorage for production)
    localStorage.setItem(this.TOKEN_KEY, JSON.stringify(tokens));
  }
  
  static getTokens() {
    const stored = localStorage.getItem(this.TOKEN_KEY);
    return stored ? JSON.parse(stored) : null;
  }
  
  static clearTokens() {
    localStorage.removeItem(this.TOKEN_KEY);
  }
  
  static async refreshAccessToken() {
    const tokens = this.getTokens();
    if (!tokens?.refreshToken) {
      throw new Error('No refresh token available');
    }
    
    try {
      const response = await fetch(`${baseURL}/api/v1/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: new URLSearchParams({
          refresh_token: tokens.refreshToken
        })
      });
      
      if (!response.ok) {
        throw new Error('Token refresh failed');
      }
      
      const data = await response.json();
      this.storeTokens({
        accessToken: data.access_token,
        refreshToken: data.refresh_token
      });
      
      return data.access_token;
    } catch (error) {
      this.clearTokens();
      throw error;
    }
  }
}
```

### Request Interceptor
```typescript
class APIInterceptor {
  private static instance: APIInterceptor;
  
  static getInstance(): APIInterceptor {
    if (!this.instance) {
      this.instance = new APIInterceptor();
    }
    return this.instance;
  }
  
  interceptRequest(config: any) {
    const tokens = TokenManager.getTokens();
    
    if (tokens?.accessToken) {
      config.headers['Authorization'] = `Bearer ${tokens.accessToken}`;
    }
    
    return config;
  }
  
  async interceptResponse(response: any) {
    if (response.status === 401) {
      // Try to refresh token
      try {
        const newAccessToken = await TokenManager.refreshAccessToken();
        
        // Retry original request with new token
        const originalRequest = response.config;
        originalRequest.headers['Authorization'] = `Bearer ${newAccessToken}`;
        
        return await fetch(originalRequest);
      } catch (error) {
        // Refresh failed, redirect to login
        TokenManager.clearTokens();
        window.location.href = '/login';
        throw error;
      }
    }
    
    return response;
  }
}
```

This comprehensive API specification and integration guide provides developers with everything they need to successfully integrate Sigma IAM into their applications, maintaining security best practices while ensuring a smooth integration experience.