# Sigma Permit 2.0

A comprehensive, enterprise-grade license management system built with modern web technologies. Features multi-tenant architecture, cryptographic license keys, subscription management, and multiple frontend implementations.

## Features

### Core License Management
- **Multi-tenant architecture** with tenant-specific license limits and isolation
- **Flexible license templates** with JSON schema validation and custom payload structures
- **Cryptographic license keys** using RSA+AES hybrid encryption for security
- **License validation** with offline capability and API-based verification
- **License lifecycle management** with issuance, validation, and revocation

### User Management & Authentication
- **JWT-based authentication** with refresh token support
- **Role-based access control** with admin and regular user permissions
- **User profile management** with password change and account settings
- **Secure password hashing** using bcrypt

### Subscription & Billing
- **Product management** for organizing software offerings
- **Flexible subscription plans** with monthly/yearly billing cycles
- **Feature definitions** with type validation (boolean, integer, string, JSON)
- **Plan-feature mapping** with override values and constraints
- **Subscription management** with status tracking (active, trialing, past_due, canceled)
- **Entitlement calculation** based on active subscriptions

### Web Interfaces
- **Modern admin interface** built with Bootstrap and HTMX for full CRUD operations
- **SvelteKit frontend** with responsive design and client-side routing
- **React/Next.js frontend** as an alternative implementation
- **SPA architecture** with API-driven data management
- **Real-time validation** and form handling

### API & Integration
- **RESTful API** with automatic OpenAPI/Swagger documentation
- **Pagination support** on all list endpoints
- **Health checks** and Prometheus metrics endpoints
- **CORS configuration** for cross-origin requests
- **Multi-language validators** (Python, JavaScript, TypeScript)

### Infrastructure
- **Database flexibility** (SQLite for development, PostgreSQL/MySQL for production)
- **Docker containerization** with docker-compose support
- **Environment-based configuration** for different deployment scenarios
- **Master key management** for cryptographic operations
- **Seed data support** for development and testing

## Quick Start

### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd sigma-permit-2.0

# Build and run with Docker Compose (includes PostgreSQL)
docker-compose up --build

# Access the application at http://localhost:8000
# PostgreSQL is available at localhost:5432
```

### Option 2: Local Development

#### Prerequisites

- Python 3.13+
- Node.js 18+
- uv package manager (optional, can use pip instead)

#### Installation

1. **Clone and setup:**
    ```bash
    git clone <repository-url>
    cd sigma-permit-2.0
    uv sync  # or pip install -r requirements.txt
    ```

2. **Build the frontend (choose one):**
    ```bash
    # Option A: SvelteKit frontend
    cd frontend
    npm install
    npm run build
    cd ..

    # Option B: React frontend
    cd react-frontend
    npm install
    npm run build
    cd ..
    ```

3. **Run the application:**
    ```bash
    uv run python main.py  # or python main.py
    ```

4. **Seed the database (optional):**
    ```bash
    uv run python seed.py  # or python seed.py
    ```

#### Testing License Validation

After starting the application, test the license validation:

```bash
# Validate a license using the Python validator
python validator.py YOUR_LICENSE_KEY_HERE
```

### Access Points

- **Main Web Interface:** http://localhost:8000
- **Admin Interface:** http://localhost:8000/admin
- **API Documentation:** http://localhost:8000/docs
- **API Redoc:** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/api/health
- **Metrics:** http://localhost:8000/metrics

## Environment Variables

### Database Configuration

The application uses SQLite by default. To use PostgreSQL or MySQL, set the `DATABASE_URL` environment variable:

```bash
export DATABASE_URL="postgresql://user:password@localhost/dbname"
# or
export DATABASE_URL="mysql://user:password@localhost/dbname"
```

### JWT Configuration

Set the `JWT_SECRET_KEY` environment variable for JWT token signing (required for production):

```bash
export JWT_SECRET_KEY="your-secure-random-secret-key-here"
```

If not set, a default development key will be used (not recommended for production).

## API Endpoints

### Authentication
- `POST /api/auth/login` - User login with base64 encoded credentials
- `POST /api/auth/refresh` - Refresh access token
- `POST /api/auth/logout` - User logout
- `GET /api/auth/me` - Get current user information
- `POST /api/auth/change-password` - Change user password
- `GET /api/auth/users` - List users (admin only)
- `POST /api/auth/users` - Create user (admin only)
- `GET /api/auth/users/{id}` - Get user by ID
- `PUT /api/auth/users/{id}` - Update user
- `DELETE /api/auth/users/{id}` - Delete user (admin only)

### Tenants
- `GET /api/tenants` - List tenants (paginated)
- `POST /api/tenants` - Create tenant
- `GET /api/tenants/{id}` - Get tenant by ID
- `PUT /api/tenants/{id}` - Update tenant
- `DELETE /api/tenants/{id}` - Delete tenant

### Templates
- `GET /api/templates` - List templates (paginated)
- `POST /api/templates` - Create template
- `GET /api/templates/{id}` - Get template by ID
- `PUT /api/templates/{id}` - Update template
- `DELETE /api/templates/{id}` - Delete template

### Licenses
- `GET /api/licenses` - List licenses (paginated, optional tenant filter)
- `POST /api/licenses` - Create license
- `GET /api/licenses/{id}` - Get license by ID
- `PUT /api/licenses/{id}` - Update license
- `DELETE /api/licenses/{id}` - Delete license
- `GET /api/licenses/validate/{key}` - Validate license key
- `GET /api/licenses/issue` - Download license file

### Products
- `GET /api/products` - List products (paginated)
- `POST /api/products` - Create product
- `GET /api/products/{id}` - Get product by ID
- `PUT /api/products/{id}` - Update product
- `DELETE /api/products/{id}` - Delete product

### Plans
- `GET /api/plans` - List plans (paginated)
- `POST /api/plans` - Create plan
- `GET /api/plans/{id}` - Get plan by ID
- `PUT /api/plans/{id}` - Update plan
- `DELETE /api/plans/{id}` - Delete plan

### Features
- `GET /api/features` - List features (paginated)
- `POST /api/features` - Create feature
- `GET /api/features/{id}` - Get feature by ID
- `PUT /api/features/{id}` - Update feature
- `DELETE /api/features/{id}` - Delete feature

### Subscriptions
- `GET /api/subscriptions` - List subscriptions (paginated)
- `POST /api/subscriptions` - Create subscription
- `GET /api/subscriptions/{id}` - Get subscription by ID
- `PUT /api/subscriptions/{id}` - Update subscription
- `DELETE /api/subscriptions/{id}` - Delete subscription

### System
- `GET /api/health` - Health check endpoint
- `GET /metrics` - Prometheus metrics

## Web Interfaces

The application provides multiple web interfaces for different use cases:

### Admin Interface (`/admin`)
Built with Bootstrap and HTMX for server-side rendering and real-time updates:
- **Tenants:** Manage organizations and their license limits
- **Templates:** Create license templates with JSON schema validation
- **Licenses:** Issue and manage licenses with cryptographic keys
- **Users:** User management with role-based permissions

### SvelteKit Frontend (`/`)
Modern single-page application with responsive design:
- Full CRUD operations for all entities
- Real-time form validation and error handling
- Client-side routing and state management
- API integration with automatic error handling

### React/Next.js Frontend
Alternative frontend implementation with similar functionality:
- Component-based architecture
- Server-side rendering capabilities
- TypeScript support for type safety

## License Validation

The system includes multi-language license validators for integration with client applications:

### Python Validator
```bash
python validator.py YOUR_LICENSE_KEY --api-url http://your-api.com/api
```

**Features:**
- Downloads encrypted license files from API
- Local file caching for offline validation
- Cryptographic verification using RSA+AES hybrid encryption
- Command-line interface with configurable API endpoints

### JavaScript/TypeScript Validators
Client-side validation libraries for web applications with similar functionality to the Python validator.

## Deployment

For detailed deployment instructions including Docker setup, environment configuration, and production deployment options, see [README_DEPLOYMENT.md](README_DEPLOYMENT.md).

## Sample Data

The seeding script (`python seed.py`) creates comprehensive sample data:

### Users
- **Admin User** (username: `admin`, password: `admin123`)
- **Regular User** (username: `user`, password: `user123`)

### Tenant
- **Demo Company** (slug: `demo-company`, 100 max licenses)

### Products
- **Sigma Software Suite** - Complete software licensing solution

### Plans
1. **Basic Plan** - $9.99/month - Essential features
2. **Business Plan** - $29.99/month - Advanced features
3. **Enterprise Plan** - $99.99/month - Unlimited features

### Features
- **User Limit** (integer) - Maximum number of users
- **API Access** (boolean) - API access permission
- **Support Level** (string) - Support tier (basic/premium/enterprise)
- **Custom Branding** (boolean) - White-labeling capability

### Templates
1. **Basic License** - Essential features, 30-365 days validity
2. **Business License** - Advanced features, up to 100 users
3. **Enterprise License** - Unlimited features, SLA guarantees

### Subscriptions
Sample subscriptions linking tenants to plans with calculated entitlements

## Project Structure

```
sigma-permit-2.0/
├── app/                          # FastAPI backend
│   ├── main.py                   # FastAPI application setup
│   ├── database.py               # Database configuration
│   ├── models.py                 # SQLAlchemy models
│   ├── schemas.py                # Pydantic schemas
│   ├── crud.py                   # CRUD operations
│   ├── crypto_utils.py           # Cryptographic utilities
│   ├── auth.py                   # Authentication utilities
│   ├── routers/                  # API endpoint modules
│   │   ├── auth.py              # User authentication
│   │   ├── tenants.py           # Tenant management
│   │   ├── templates.py         # License templates
│   │   ├── licenses.py          # License management
│   │   ├── products.py          # Product management
│   │   ├── plans.py             # Subscription plans
│   │   ├── features.py          # Feature definitions
│   │   └── subscriptions.py     # Subscription management
│   ├── templates/               # Jinja2 admin templates
│   └── static/                  # Static assets
├── frontend/                     # SvelteKit frontend
│   ├── src/
│   │   ├── routes/              # Page routes
│   │   ├── components/          # Reusable components
│   │   └── lib/                 # Utilities and API client
│   ├── build/                   # Built static files
│   └── package.json
├── react-frontend/               # React/Next.js frontend
│   ├── src/
│   │   ├── app/                 # Next.js app router
│   │   ├── components/          # React components
│   │   └── lib/                 # Utilities
│   └── package.json
├── validator.py                  # Python license validator
├── validator.js                  # JavaScript license validator
├── validator.ts                  # TypeScript license validator
├── main.py                       # Application entry point
├── seed.py                       # Database seeding script
├── pyproject.toml                # Python project configuration
├── docker-compose.yml            # Docker composition
├── Dockerfile                    # Container definition
└── README_DEPLOYMENT.md          # Deployment guide
```

## Development

### Running Tests
```bash
uv run pytest
```

### Code Formatting
```bash
uv run black .
uv run isort .
```

## License

This project is licensed under the MIT License.
