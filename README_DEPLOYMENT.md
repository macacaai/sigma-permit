# Sigma Permit - Deployment Guide

## Overview

Sigma Permit 2.0 combines a FastAPI backend with multiple frontend implementations (SvelteKit and React/Next.js), served from a single server. The application provides comprehensive license management with multi-tenant architecture, subscription billing, and cryptographic license validation.

## Architecture

- **Backend**: FastAPI (Python) serving REST API at `/api/*`
  - User authentication with JWT tokens
  - Multi-tenant license management
  - Subscription and billing system
  - Cryptographic license key generation
  - Admin interface with HTMX
- **Frontend Options**:
  - **SvelteKit**: Modern SPA served from `/` (default)
  - **React/Next.js**: Alternative implementation with SSR capabilities
- **Database**: PostgreSQL (production) or SQLite (development)
- **Admin UI**: Bootstrap + HTMX interface at `/admin/*`
- **Validators**: Multi-language license validation clients

## Route Structure

```
/                     # Main frontend (SvelteKit or React SPA)
/admin/*             # Admin interface (Jinja2 + HTMX)
/api/*               # REST API endpoints
  /api/auth/*        # Authentication endpoints
  /api/tenants/*     # Tenant management
  /api/templates/*   # License templates
  /api/licenses/*    # License management
  /api/products/*    # Product catalog
  /api/plans/*       # Subscription plans
  /api/features/*    # Feature definitions
  /api/subscriptions/* # Subscription management
  /api/health        # Health check
/docs                # API documentation (Swagger UI)
/redoc               # API documentation (ReDoc)
/metrics             # Prometheus metrics
/static/*            # Static assets
```

## Building and Running

### Option 1: Docker (Recommended)

```bash
# Build and run with Docker Compose (includes PostgreSQL)
docker-compose up --build

# Or build and run separately
docker build -t sigma-permit .
docker run -p 8000:8000 --env DATABASE_URL=postgresql://user:password@host:5432/dbname sigma-permit
```

### Option 2: Local Development

#### Prerequisites

- Python 3.13+ with uv package manager or pip
- Node.js 18+ for frontend builds
- PostgreSQL (optional, SQLite used by default)

#### 1. Install Python Dependencies

```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -r requirements.txt
```

#### 2. Build the Frontend

Choose one frontend implementation:

```bash
# Option A: SvelteKit Frontend
cd frontend
npm install
npm run build
cd ..

# Option B: React/Next.js Frontend
cd react-frontend
npm install
npm run build
cd ..

# Option C: Use the build script (builds SvelteKit)
chmod +x build.sh
./build.sh
```

#### 3. Configure Environment (Optional)

Create a `.env` file for custom configuration:

```bash
# Database (optional, defaults to SQLite)
DATABASE_URL=postgresql://user:password@localhost/sigma_permit

# JWT Secret (optional, generates random for development)
JWT_SECRET_KEY=your-secure-secret-key-here

# CORS Origins (optional)
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

#### 4. Run the Application

```bash
# Using uv
uv run python main.py

# Or directly with Python
python main.py

# Or with uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 5. Seed Sample Data (Optional)

```bash
# Seed the database with sample data
uv run python seed.py
```

### 3. Access the Application

- **Main Web Interface**: http://localhost:8000
- **Admin Interface**: http://localhost:8000/admin
- **API Documentation**: http://localhost:8000/docs
- **API Reference**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/api/health
- **Metrics**: http://localhost:8000/metrics

#### Default Credentials (after seeding)

- **Admin User**: username: `admin`, password: `admin123`
- **Regular User**: username: `user`, password: `user123`

## Development vs Production

### Development Mode

#### Frontend Development
```bash
# SvelteKit development server (with HMR)
cd frontend
npm run dev  # Runs on http://localhost:5173

# React development server
cd react-frontend
npm run dev  # Runs on http://localhost:3000
```

#### Backend Development
```bash
# Run backend with auto-reload
uv run python main.py  # or python -m uvicorn app.main:app --reload
```

#### Development Features
- **Hot Module Replacement** for frontend development
- **Auto-reload** for backend changes
- **CORS enabled** for cross-origin development
- **SQLite database** for easy development setup
- **Debug logging** and development error pages

### Production Mode

#### Single Server Architecture
- **Unified server** on port 8000 serving both frontend and API
- **Static file serving** for built frontend assets
- **API endpoints** under `/api/*` prefix
- **Admin interface** under `/admin/*` prefix
- **No CORS issues** (same origin for all resources)

#### Production Configuration
- **PostgreSQL database** recommended for production
- **Environment variables** for sensitive configuration
- **JWT secret key** required for security
- **Optimized static assets** from build process

## Route Conflict Resolution

The following measures prevent route conflicts:

1. **API routes** use `/api/` prefix
2. **Frontend routes** use `/` (SPA fallback)
3. **Admin routes** use `/admin/` prefix
4. **Static mounting order** ensures API routes take precedence

## Deployment Checklist

### Pre-deployment
- [ ] Choose frontend implementation (SvelteKit or React)
- [ ] Configure environment variables (DATABASE_URL, JWT_SECRET_KEY)
- [ ] Set up database (PostgreSQL for production, SQLite for development)
- [ ] Install Python dependencies (`uv sync` or `pip install`)

### Build Process
- [ ] Build selected frontend:
  - [ ] For SvelteKit: `cd frontend && npm install && npm run build`
  - [ ] For React: `cd react-frontend && npm install && npm run build`
- [ ] Verify build output directory exists (`frontend/build/` or `react-frontend/build/`)
- [ ] Test frontend build locally if needed

### Database Setup
- [ ] Run database migrations (handled automatically on startup)
- [ ] Seed initial data if required (`python seed.py`)
- [ ] Verify database connectivity

### Application Startup
- [ ] Start application server (`python main.py`)
- [ ] Verify server starts without errors
- [ ] Check application logs for any issues

### Testing
- [ ] Test main web interface at `http://localhost:8000`
- [ ] Test admin interface at `http://localhost:8000/admin`
- [ ] Test API health at `http://localhost:8000/api/health`
- [ ] Test API documentation at `http://localhost:8000/docs`
- [ ] Verify user authentication flow
- [ ] Test license validation with sample data

### Production Considerations
- [ ] Configure reverse proxy (nginx/Caddy) for production
- [ ] Set up SSL/TLS certificates
- [ ] Configure proper CORS settings
- [ ] Set up monitoring and logging
- [ ] Configure backup strategy for database
- [ ] Review security settings (JWT secrets, database credentials)

## Troubleshooting

### Application Won't Start
- **Check Python version**: Ensure Python 3.13+ is installed
- **Dependencies**: Run `uv sync` or `pip install -r requirements.txt`
- **Database connection**: Verify DATABASE_URL if using PostgreSQL
- **Port conflicts**: Ensure port 8000 is available

### Frontend Not Loading
- **Build verification**: Ensure correct build directory exists
  - SvelteKit: `frontend/build/` with `index.html`
  - React: `react-frontend/build/` or `react-frontend/.next/`
- **Build process**: Re-run build if files are missing
- **Static file serving**: Check server logs for static file errors
- **Browser cache**: Hard refresh (Ctrl+F5) after rebuilds

### API Issues
- **Health check**: Test `/api/health` endpoint first
- **CORS errors**: Check CORS_ORIGINS environment variable
- **Authentication**: Verify JWT_SECRET_KEY is set
- **Database**: Ensure database is accessible and migrations ran

### Admin Interface Problems
- **HTMX loading**: Check browser console for JavaScript errors
- **Template errors**: Verify `app/templates/` directory exists
- **Database permissions**: Ensure user has admin privileges

### License Validation Issues
- **Master key**: Check that RSA key pair was generated on startup
- **File permissions**: Ensure write access for license file downloads
- **API connectivity**: Verify validator can reach API endpoints

### Database Issues
- **Connection string**: Validate DATABASE_URL format
- **Migrations**: Database tables are created automatically on startup
- **SQLite file**: Ensure write permissions for `sigma_permit.db`
- **PostgreSQL**: Check connection credentials and database existence

### Route Conflicts
- **API precedence**: API routes (`/api/*`) take precedence over static files
- **Admin separation**: Admin routes (`/admin/*`) are isolated
- **SPA fallback**: Client-side routes handled by `index.html` fallback
- **Static mounting**: Order matters - API routes before static files

### Performance Issues
- **Database queries**: Check for N+1 query problems in logs
- **Static files**: Ensure proper caching headers
- **Frontend bundles**: Minimize bundle size for production
- **Memory usage**: Monitor for memory leaks in long-running processes

### Development Environment
- **Hot reload**: Use `--reload` flag with uvicorn for backend
- **Frontend dev servers**: Run `npm run dev` in frontend directories
- **CORS**: Ensure proper CORS configuration for development
- **Environment variables**: Use `.env` file for local configuration
