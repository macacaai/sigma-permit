from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from prometheus_client import make_asgi_app
from app.routers import tenants, templates, licenses, auth, products, plans, features, subscriptions, oauth, applications, sessions, roles
from fastapi import Request
from fastapi.responses import HTMLResponse
from app.database import engine, get_db
from app import models
from app.rate_limiter import rate_limit_middleware
from app.security import security_headers_middleware, request_validation_middleware
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
from datetime import datetime

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables on startup, seed master key and application data"""
    models.Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

    # Seed master RSA key pair if not exists
    from app.database import SessionLocal
    from app.crypto_utils import generate_rsa_keypair
    db = SessionLocal()
    try:
        master_key = db.query(models.MasterKey).first()
        if not master_key:
            public_key_b64, private_key_b64 = generate_rsa_keypair()
            master_key = models.MasterKey(public_key=public_key_b64, private_key=private_key_b64, is_active=True)
            db.add(master_key)
            db.commit()
            print("Master RSA key pair generated and seeded on startup")
    finally:
        db.close()

    # Seed essential application data for Docker compose deployment
    from startup_seeding import seed_startup_data
    seed_startup_data()

    yield

app = FastAPI(
    title="Sigma Permit API",
    description="API for managing tenants, templates, and licenses",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React development server
        "http://127.0.0.1:3000",  # Alternative localhost
        "http://localhost:5173",  # Vite development server (if used)
        "*",  # Allow all origins for development - restrict in production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting middleware
app.middleware("http")(rate_limit_middleware)

# Add security middleware
app.middleware("http")(security_headers_middleware)
app.middleware("http")(request_validation_middleware)

# Include routers FIRST (before static mounts)
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(oauth.router, prefix="/oauth/v1", tags=["oauth2"])
app.include_router(applications.router, prefix="/api/v1/applications", tags=["applications"])
app.include_router(sessions.router, prefix="/api/v1/sessions", tags=["sessions"])
app.include_router(roles.router, prefix="/api/v1/roles", tags=["roles"])

# Add OIDC discovery endpoint without prefix
@app.get("/.well-known/openid-configuration")
async def openid_configuration():
    """OpenID Connect discovery endpoint"""
    from app.routers.oauth import openid_configuration as oauth_discovery
    return await oauth_discovery()
app.include_router(tenants.router, prefix="/api/tenants", tags=["tenants"])
app.include_router(templates.router, prefix="/api/templates", tags=["templates"])
app.include_router(licenses.router, prefix="/api/licenses", tags=["licenses"])
app.include_router(products.router, prefix="/api/products", tags=["products"])
app.include_router(plans.router, prefix="/api/plans", tags=["plans"])
app.include_router(features.router, prefix="/api/features", tags=["features"])
app.include_router(subscriptions.router, prefix="/api/subscriptions", tags=["subscriptions"])

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

# Add metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/")
async def serve_root():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/docs", status_code=302)

# Jinja2 templates (keeping for potential admin routes)
jinja_templates = Jinja2Templates(directory="app/templates")

# Add custom filters and globals
import json
jinja_templates.env.filters["tojson"] = lambda x: json.dumps(x, indent=2)
jinja_templates.env.globals.update(min=min, max=max)

# Admin UI routes (moved to /admin to avoid conflicts with frontend)
@app.get("/admin", response_class=HTMLResponse)
async def admin_home(request: Request):
    return jinja_templates.TemplateResponse("index.html", {"request": request})

@app.get("/admin/tenants", response_class=HTMLResponse)
async def admin_tenants_page(request: Request):
    return jinja_templates.TemplateResponse("tenants.html", {"request": request})

@app.get("/admin/tenants/list", response_class=HTMLResponse)
async def admin_tenants_list(request: Request, page: int = 1, size: int = 10, db: Session = Depends(get_db)):
    from app.crud import get_tenants
    from app.models import Tenant
    skip = (page - 1) * size
    tenants = get_tenants(db, skip=skip, limit=size)
    total = db.query(Tenant).count()
    pages = (total + size - 1) // size if size > 0 else 0
    return jinja_templates.TemplateResponse("tenants_list.html", {
        "request": request,
        "tenants": tenants,
        "page": page,
        "size": size,
        "total": total,
        "pages": pages
    })

@app.get("/admin/templates", response_class=HTMLResponse)
async def admin_templates_page(request: Request):
    return jinja_templates.TemplateResponse("templates.html", {"request": request})

@app.get("/admin/templates/list", response_class=HTMLResponse)
async def admin_templates_list(request: Request, page: int = 1, size: int = 10, db: Session = Depends(get_db)):
    from app.crud import get_templates
    from app.models import Template
    skip = (page - 1) * size
    templates_list = get_templates(db, skip=skip, limit=size)
    total = db.query(Template).count()
    pages = (total + size - 1) // size if size > 0 else 0
    return jinja_templates.TemplateResponse("templates_list.html", {
        "request": request,
        "templates": templates_list,
        "page": page,
        "size": size,
        "total": total,
        "pages": pages
    })

@app.get("/admin/licenses", response_class=HTMLResponse)
async def admin_licenses_page(request: Request):
    return jinja_templates.TemplateResponse("licenses.html", {"request": request})

@app.get("/admin/licenses/list", response_class=HTMLResponse)
async def admin_licenses_list(request: Request, page: int = 1, size: int = 10, tenant_id: int = None, db: Session = Depends(get_db)):
    from app.crud import get_licenses
    from app.models import License
    skip = (page - 1) * size
    licenses_list = get_licenses(db, skip=skip, limit=size, tenant_id=tenant_id)
    query = db.query(License)
    if tenant_id:
        query = query.filter(License.tenant_id == tenant_id)
    total = query.count()
    pages = (total + size - 1) // size if size > 0 else 0
    return jinja_templates.TemplateResponse("licenses_list.html", {
        "request": request,
        "licenses": licenses_list,
        "page": page,
        "size": size,
        "total": total,
        "pages": pages
    })

# Admin HTMX endpoints for forms (moved to /admin to avoid conflicts)
@app.post("/admin/tenants", response_class=HTMLResponse)
async def create_tenant_web(request: Request, db: Session = Depends(get_db)):
    from app.crud import create_tenant, get_tenant_by_slug
    from app.schemas import TenantCreate
    try:
        form_data = await request.form()
        tenant_data = TenantCreate(**form_data)
        if get_tenant_by_slug(db, tenant_data.slug):
            return HTMLResponse('<div class="alert alert-danger">Tenant slug already exists</div>', status_code=400)
        create_tenant(db=db, tenant=tenant_data)
        return HTMLResponse('<div class="alert alert-success">Tenant created successfully!</div>', status_code=201)
    except Exception as e:
        return HTMLResponse(f'<div class="alert alert-danger">Error: {str(e)}</div>', status_code=400)

@app.put("/admin/tenants/{tenant_id}", response_class=HTMLResponse)
async def update_tenant_web(tenant_id: int, request: Request, db: Session = Depends(get_db)):
    from app.crud import update_tenant
    from app.schemas import TenantUpdate
    try:
        form_data = await request.form()
        tenant_data = TenantUpdate(**form_data)
        tenant = update_tenant(db=db, tenant_id=tenant_id, tenant_update=tenant_data)
        if not tenant:
            return HTMLResponse('<div class="alert alert-danger">Tenant not found</div>', status_code=404)
        return HTMLResponse('<div class="alert alert-success">Tenant updated successfully!</div>', status_code=200)
    except Exception as e:
        return HTMLResponse(f'<div class="alert alert-danger">Error: {str(e)}</div>', status_code=400)

@app.delete("/admin/tenants/{tenant_id}", response_class=HTMLResponse)
async def delete_tenant_web(tenant_id: int, db: Session = Depends(get_db)):
    from app.crud import delete_tenant
    try:
        success = delete_tenant(db=db, tenant_id=tenant_id)
        if not success:
            return HTMLResponse('<div class="alert alert-danger">Tenant not found</div>', status_code=404)
        return HTMLResponse('<div class="alert alert-success">Tenant deleted successfully!</div>', status_code=200)
    except Exception as e:
        return HTMLResponse(f'<div class="alert alert-danger">Error: {str(e)}</div>', status_code=400)

@app.post("/admin/templates", response_class=HTMLResponse)
async def create_template_web(request: Request, db: Session = Depends(get_db)):
    from app.crud import create_template
    from app.schemas import TemplateCreate
    try:
        form_data = await request.form()
        template_data = {
            "name": form_data.get("name"),
            "description": form_data.get("description"),
            "payload_schema": form_data.get("payload_schema") if form_data.get("payload_schema") else None,
            "validation_rules": form_data.get("validation_rules") if form_data.get("validation_rules") else None,
            "is_active": form_data.get("is_active") == "on"
        }
        # Parse JSON if provided
        if template_data["payload_schema"]:
            import json
            template_data["payload_schema"] = json.loads(template_data["payload_schema"])
        if template_data["validation_rules"]:
            import json
            template_data["validation_rules"] = json.loads(template_data["validation_rules"])

        template = TemplateCreate(**template_data)
        create_template(db=db, template=template)
        return HTMLResponse('<div class="alert alert-success">Template created successfully!</div>', status_code=201)
    except Exception as e:
        return HTMLResponse(f'<div class="alert alert-danger">Error: {str(e)}</div>', status_code=400)

@app.put("/admin/templates/{template_id}", response_class=HTMLResponse)
async def update_template_web(template_id: int, request: Request, db: Session = Depends(get_db)):
    from app.crud import update_template
    from app.schemas import TemplateUpdate
    try:
        form_data = await request.form()
        template_data = {
            "name": form_data.get("name"),
            "description": form_data.get("description"),
            "payload_schema": form_data.get("payload_schema") if form_data.get("payload_schema") else None,
            "validation_rules": form_data.get("validation_rules") if form_data.get("validation_rules") else None,
            "is_active": form_data.get("is_active") == "on"
        }
        # Parse JSON if provided
        if template_data["payload_schema"]:
            import json
            template_data["payload_schema"] = json.loads(template_data["payload_schema"])
        if template_data["validation_rules"]:
            import json
            template_data["validation_rules"] = json.loads(template_data["validation_rules"])

        template = TemplateUpdate(**template_data)
        template = update_template(db=db, template_id=template_id, template_update=template)
        if not template:
            return HTMLResponse('<div class="alert alert-danger">Template not found</div>', status_code=404)
        return HTMLResponse('<div class="alert alert-success">Template updated successfully!</div>', status_code=200)
    except Exception as e:
        return HTMLResponse(f'<div class="alert alert-danger">Error: {str(e)}</div>', status_code=400)

@app.delete("/admin/templates/{template_id}", response_class=HTMLResponse)
async def delete_template_web(template_id: int, request: Request, db: Session = Depends(get_db)):
    from app.crud import delete_template
    try:
        success = delete_template(db=db, template_id=template_id)
        if not success:
            return HTMLResponse('<div class="alert alert-danger">Template not found</div>', status_code=404)
        return HTMLResponse('<div class="alert alert-success">Template deleted successfully!</div>', status_code=200)
    except Exception as e:
        return HTMLResponse(f'<div class="alert alert-danger">Error: {str(e)}</div>', status_code=400)

@app.post("/admin/licenses", response_class=HTMLResponse)
async def create_license_web(request: Request, db: Session = Depends(get_db)):
    from app.crud import create_license, get_tenant
    from app.schemas import LicenseCreate
    try:
        form_data = await request.form()
        license_data = {
            "tenant_id": int(form_data.get("tenant_id")),
            "payload": form_data.get("payload")
        }
        # Parse JSON payload
        if license_data["payload"]:
            import json
            license_data["payload"] = json.loads(license_data["payload"])

        # Check tenant exists and license limit
        tenant = get_tenant(db, license_data["tenant_id"])
        if not tenant:
            return HTMLResponse('<div class="alert alert-danger">Tenant not found</div>', status_code=400)

        from app.crud import get_tenant_license_count
        current_count = get_tenant_license_count(db, tenant.id)
        if current_count >= tenant.max_licenses:
            return HTMLResponse('<div class="alert alert-danger">Maximum licenses reached for this tenant</div>', status_code=400)

        license = LicenseCreate(**license_data)
        create_license(db=db, license=license)
        return HTMLResponse('<div class="alert alert-success">License issued successfully!</div>', status_code=201)
    except Exception as e:
        return HTMLResponse(f'<div class="alert alert-danger">Error: {str(e)}</div>', status_code=400)

@app.delete("/admin/licenses/{license_id}", response_class=HTMLResponse)
async def delete_license_web(license_id: int, db: Session = Depends(get_db)):
    from app.crud import delete_license
    try:
        success = delete_license(db=db, license_id=license_id)
        if not success:
            return HTMLResponse('<div class="alert alert-danger">License not found</div>', status_code=404)
        return HTMLResponse('<div class="alert alert-success">License revoked successfully!</div>', status_code=200)
    except Exception as e:
        return HTMLResponse(f'<div class="alert alert-danger">Error: {str(e)}</div>', status_code=400)

# IAM Identity Management Routes
@app.get("/admin/identity/users", response_class=HTMLResponse)
async def admin_identity_users_page(request: Request):
    return jinja_templates.TemplateResponse("identity_users.html", {"request": request})

@app.get("/admin/identity/users/list", response_class=HTMLResponse)
async def admin_identity_users_list(
    request: Request,
    page: int = 1,
    size: int = 10,
    filter_role: str = None,
    filter_status: str = None,
    search: str = None,
    db: Session = Depends(get_db)
):
    from app.auth import get_current_user
    from app.models import User
    from sqlalchemy.orm import joinedload

    # Get current user for tenant filtering
    try:
        current_user = await get_current_user(token=request.headers.get("authorization", "").replace("Bearer ", ""), db=db)
        is_superuser = current_user.is_superuser
        user_tenant_id = str(current_user.tenant_id) if current_user.tenant_id else None
    except:
        # Fallback for unauthenticated access (shouldn't happen in admin)
        is_superuser = False
        user_tenant_id = None

    # Build query
    query = db.query(User)

    # Apply tenant isolation for non-superusers
    if not is_superuser and user_tenant_id:
        query = query.filter(User.tenant_id == user_tenant_id)

    # Apply filters
    if filter_role:
        query = query.join(User.roles).join(models.UserRole.role).filter(models.Role.name == filter_role)

    if filter_status:
        if filter_status == "active":
            query = query.filter(User.is_active == True)
        elif filter_status == "inactive":
            query = query.filter(User.is_active == False)
        elif filter_status == "pending_verification":
            query = query.filter(User.email_verified == False)

    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            db.or_(
                User.username.ilike(search_filter),
                User.email.ilike(search_filter),
                User.full_name.ilike(search_filter)
            )
        )

    # Get total count
    total = query.count()
    skip = (page - 1) * size
    users = query.offset(skip).limit(size).all()
    pages = (total + size - 1) // size if size > 0 else 0

    return jinja_templates.TemplateResponse("identity_users_list.html", {
        "request": request,
        "users": users,
        "page": page,
        "size": size,
        "total": total,
        "pages": pages,
        "filter_role": filter_role,
        "filter_status": filter_status,
        "search": search,
        "is_superuser": is_superuser
    })

@app.get("/admin/identity/applications", response_class=HTMLResponse)
async def admin_identity_applications_page(request: Request):
    return jinja_templates.TemplateResponse("identity_applications.html", {"request": request})

@app.get("/admin/identity/applications/list", response_class=HTMLResponse)
async def admin_identity_applications_list(
    request: Request,
    page: int = 1,
    size: int = 10,
    tenant_id: str = None,
    is_active: bool = None,
    db: Session = Depends(get_db)
):
    from app.auth import get_current_user
    from app.models import OAuthClient

    # Get current user for tenant filtering
    try:
        current_user = await get_current_user(token=request.headers.get("authorization", "").replace("Bearer ", ""), db=db)
        is_superuser = current_user.is_superuser
        user_tenant_id = str(current_user.tenant_id) if current_user.tenant_id else None
    except:
        is_superuser = False
        user_tenant_id = None

    # Build query
    query = db.query(OAuthClient)

    # Apply tenant isolation for non-superusers
    if not is_superuser and user_tenant_id:
        query = query.filter(OAuthClient.tenant_id == user_tenant_id)

    # Apply filters
    if tenant_id and is_superuser:  # Only superusers can filter by other tenants
        query = query.filter(OAuthClient.tenant_id == tenant_id)
    if is_active is not None:
        query = query.filter(OAuthClient.is_active == is_active)

    # Get total count
    total = query.count()
    skip = (page - 1) * size
    applications = query.offset(skip).limit(size).all()
    pages = (total + size - 1) // size if size > 0 else 0

    return jinja_templates.TemplateResponse("identity_applications_list.html", {
        "request": request,
        "applications": applications,
        "page": page,
        "size": size,
        "total": total,
        "pages": pages,
        "tenant_id": tenant_id,
        "is_active": is_active,
        "is_superuser": is_superuser
    })

@app.get("/admin/identity/sessions", response_class=HTMLResponse)
async def admin_identity_sessions_page(request: Request):
    return jinja_templates.TemplateResponse("identity_sessions.html", {"request": request})

@app.get("/admin/identity/sessions/list", response_class=HTMLResponse)
async def admin_identity_sessions_list(
    request: Request,
    page: int = 1,
    size: int = 10,
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    from app.auth import get_current_user
    from app.models import UserSession

    # Get current user for tenant filtering
    try:
        current_user = await get_current_user(token=request.headers.get("authorization", "").replace("Bearer ", ""), db=db)
        is_superuser = current_user.is_superuser
        user_id = str(current_user.id)
    except:
        is_superuser = False
        user_id = None

    # Build query
    query = db.query(UserSession)

    # Apply user isolation for non-superusers
    if not is_superuser and user_id:
        query = query.filter(UserSession.user_id == user_id)

    if active_only:
        query = query.filter(
            UserSession.is_active == True,
            UserSession.expires_at > datetime.utcnow()
        )

    # Get total count
    total = query.count()
    skip = (page - 1) * size
    sessions = query.offset(skip).limit(size).all()
    pages = (total + size - 1) // size if size > 0 else 0

    return jinja_templates.TemplateResponse("identity_sessions_list.html", {
        "request": request,
        "sessions": sessions,
        "page": page,
        "size": size,
        "total": total,
        "pages": pages,
        "active_only": active_only,
        "is_superuser": is_superuser
    })
