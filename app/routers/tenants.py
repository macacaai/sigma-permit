from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import List
from math import ceil
from uuid import UUID
from app import crud, models, schemas
from app.database import get_db
from app.auth import get_current_user
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/templates")
templates.env.globals.update(min=min, max=max)

router = APIRouter()

def paginate_response(items: List, total: int, page: int, size: int) -> schemas.PaginatedResponse:
    return schemas.PaginatedResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=ceil(total / size) if size > 0 else 0
    )

@router.post("", response_model=schemas.Tenant)
def create_tenant(
    tenant: schemas.TenantCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_tenant = crud.get_tenant_by_slug(db, tenant.slug)
    if db_tenant:
        raise HTTPException(status_code=400, detail="Tenant slug already exists")
    return crud.create_tenant(db=db, tenant=tenant)

@router.get("", response_model=schemas.PaginatedResponse)
def read_tenants(
    request: Request,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=200),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check if this is an HTMX request
    if request.headers.get("HX-Request"):
        # Return HTML for HTMX
        skip = (page - 1) * size
        tenants = crud.get_tenants(db, skip=skip, limit=size)
        total = db.query(models.Tenant).count()
        pages = ceil(total / size) if size > 0 else 0
        return templates.TemplateResponse("tenants_list.html", {
            "request": request,
            "tenants": tenants,
            "page": page,
            "size": size,
            "total": total,
            "pages": pages
        })

    # Return JSON for API requests
    skip = (page - 1) * size
    tenants = crud.get_tenants(db, skip=skip, limit=size)
    total = db.query(models.Tenant).count()
    return paginate_response(
        items=[schemas.Tenant.model_validate(tenant) for tenant in tenants],
        total=total,
        page=page,
        size=size
    )

@router.get("/{tenant_id}", response_model=schemas.Tenant)
def read_tenant(
    tenant_id: UUID,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_tenant = crud.get_tenant(db, tenant_id=tenant_id)
    if db_tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return db_tenant

@router.put("/{tenant_id}", response_model=schemas.Tenant)
def update_tenant(
    tenant_id: UUID,
    tenant: schemas.TenantUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_tenant = crud.update_tenant(db, tenant_id=tenant_id, tenant_update=tenant)
    if db_tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return db_tenant

@router.delete("/{tenant_id}")
def delete_tenant(
    tenant_id: UUID,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    success = crud.delete_tenant(db, tenant_id=tenant_id)
    if not success:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return {"message": "Tenant deleted successfully"}

@router.get("/{tenant_id}/licenses", response_model=schemas.PaginatedResponse)
def get_tenant_licenses(
    tenant_id: UUID,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=200),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all licenses for a specific tenant."""
    # Verify tenant exists
    tenant = crud.get_tenant(db, tenant_id=tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    skip = (page - 1) * size
    licenses = crud.get_licenses_with_tenant(db, skip=skip, limit=size, tenant_id=tenant_id)
    total = db.query(models.License).filter(models.License.tenant_id == str(tenant_id)).count()
    return paginate_response(
        items=licenses,
        total=total,
        page=page,
        size=size
    )

@router.get("/{tenant_id}/subscriptions", response_model=schemas.PaginatedResponse)
def get_tenant_subscriptions(
    tenant_id: UUID,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=200),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all subscriptions for a specific tenant."""
    # Verify tenant exists
    tenant = crud.get_tenant(db, tenant_id=tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    skip = (page - 1) * size
    subscriptions = crud.get_subscriptions_with_details(db, tenant_id=tenant_id, skip=skip, limit=size)
    total = db.query(models.Subscription).filter(models.Subscription.tenant_id == str(tenant_id)).count()
    return paginate_response(
        items=subscriptions,
        total=total,
        page=page,
        size=size
    )

@router.get("/{tenant_id}/products", response_model=schemas.PaginatedResponse)
def get_tenant_products(
    tenant_id: UUID,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=200),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all products that have plans with subscriptions for a specific tenant."""
    # Verify tenant exists
    tenant = crud.get_tenant(db, tenant_id=tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Get distinct product IDs from tenant's subscriptions
    from sqlalchemy import distinct
    product_ids = db.query(distinct(models.Subscription.plan_id)).filter(
        models.Subscription.tenant_id == str(tenant_id)
    ).subquery()

    plan_ids = db.query(distinct(models.PlanDefinition.product_id)).filter(
        models.PlanDefinition.id.in_(product_ids)
    ).subquery()

    skip = (page - 1) * size
    products = db.query(models.Product).filter(
        models.Product.id.in_(plan_ids)
    ).offset(skip).limit(size).all()

    total = db.query(models.Product).filter(
        models.Product.id.in_(plan_ids)
    ).count()

    # Convert to dict format
    product_dicts = []
    for product in products:
        product_dicts.append({
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "version": product.version
        })

    return paginate_response(
        items=product_dicts,
        total=total,
        page=page,
        size=size
    )

@router.get("/{tenant_id}/plans", response_model=schemas.PaginatedResponse)
def get_tenant_plans(
    tenant_id: UUID,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=200),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all plans that have subscriptions for a specific tenant."""
    # Verify tenant exists
    tenant = crud.get_tenant(db, tenant_id=tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Get plan IDs from tenant's subscriptions
    plan_ids_query = db.query(models.Subscription.plan_id).filter(
        models.Subscription.tenant_id == str(tenant_id)
    ).distinct()

    plan_ids = [str(pid) for pid, in plan_ids_query.all()]

    skip = (page - 1) * size
    # Get all plans with product info, then filter
    all_plans = crud.get_plan_definitions_with_product(db, skip=0, limit=1000)  # Get more to filter
    filtered_plans = [plan for plan in all_plans if plan["id"] in plan_ids]

    # Apply pagination to filtered results
    total = len(filtered_plans)
    start_idx = skip
    end_idx = min(start_idx + size, total)
    paginated_plans = filtered_plans[start_idx:end_idx]

    return paginate_response(
        items=paginated_plans,
        total=total,
        page=page,
        size=size
    )

@router.get("/{tenant_id}/features", response_model=schemas.PaginatedResponse)
def get_tenant_features(
    tenant_id: UUID,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=200),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all features that are in plans with subscriptions for a specific tenant."""
    # Verify tenant exists
    tenant = crud.get_tenant(db, tenant_id=tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Get plan IDs from tenant's subscriptions
    plan_ids_query = db.query(models.Subscription.plan_id).filter(
        models.Subscription.tenant_id == str(tenant_id)
    ).distinct()
    plan_ids = [str(pid) for pid, in plan_ids_query.all()]

    # Get product IDs from those plans
    product_ids_query = db.query(models.PlanDefinition.product_id).filter(
        models.PlanDefinition.id.in_(plan_ids)
    ).distinct()
    product_ids = [str(pid) for pid, in product_ids_query.all()]

    skip = (page - 1) * size
    # Get all features with product info, then filter
    all_features = crud.get_feature_definitions_with_product(db, skip=0, limit=1000)  # Get more to filter
    filtered_features = [feature for feature in all_features if feature["product_id"] in product_ids]

    # Apply pagination to filtered results
    total = len(filtered_features)
    start_idx = skip
    end_idx = min(start_idx + size, total)
    paginated_features = filtered_features[start_idx:end_idx]

    return paginate_response(
        items=paginated_features,
        total=total,
        page=page,
        size=size
    )
