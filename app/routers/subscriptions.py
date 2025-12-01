from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import List, Optional
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

@router.post("", response_model=schemas.Subscription)
def create_subscription(
    subscription: schemas.SubscriptionCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify tenant exists
    tenant = crud.get_tenant(db, subscription.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Verify plan exists
    plan = crud.get_plan_definition(db, subscription.plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    return crud.create_subscription(db=db, subscription=subscription)

@router.get("", response_model=schemas.PaginatedResponse)
def read_subscriptions(
    request: Request,
    tenant_id: Optional[UUID] = None,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=200),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check if this is an HTMX request
    if request.headers.get("HX-Request"):
        # Return HTML for HTMX
        skip = (page - 1) * size
        subscriptions = crud.get_subscriptions(db, tenant_id=tenant_id, skip=skip, limit=size)
        total = db.query(models.Subscription).count()
        pages = ceil(total / size) if size > 0 else 0
        return templates.TemplateResponse("subscriptions_list.html", {
            "request": request,
            "subscriptions": subscriptions,
            "page": page,
            "size": size,
            "total": total,
            "pages": pages
        })

    # Return JSON for API requests
    skip = (page - 1) * size
    subscriptions = crud.get_subscriptions_with_details(db, tenant_id=tenant_id, skip=skip, limit=size)
    total = db.query(models.Subscription).count()
    return paginate_response(
        items=subscriptions,
        total=total,
        page=page,
        size=size
    )

@router.get("/{subscription_id}", response_model=schemas.Subscription)
def read_subscription(
    subscription_id: UUID,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_subscription = crud.get_subscription(db, subscription_id=subscription_id)
    if db_subscription is None:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return db_subscription

@router.put("/{subscription_id}", response_model=schemas.Subscription)
def update_subscription(
    subscription_id: UUID,
    subscription: schemas.SubscriptionUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_subscription = crud.update_subscription(db, subscription_id=subscription_id, subscription_update=subscription)
    if db_subscription is None:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return db_subscription

@router.delete("/{subscription_id}")
def delete_subscription(
    subscription_id: UUID,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    success = crud.delete_subscription(db, subscription_id=subscription_id)
    if not success:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return {"message": "Subscription deleted successfully"}

@router.post("/{subscription_id}/entitlements", response_model=schemas.SubscriptionEntitlement)
def create_subscription_entitlement(
    subscription_id: UUID,
    entitlement: schemas.SubscriptionEntitlementCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify subscription exists
    subscription = crud.get_subscription(db, subscription_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    # Verify feature exists
    feature = crud.get_feature_definition(db, entitlement.feature_id)
    if not feature:
        raise HTTPException(status_code=404, detail="Feature not found")

    # Ensure the entitlement is for this subscription
    if str(entitlement.subscription_id) != str(subscription_id):
        raise HTTPException(status_code=400, detail="Subscription ID mismatch")

    return crud.create_subscription_entitlement(db=db, entitlement=entitlement)

@router.get("/{subscription_id}/entitlements", response_model=schemas.PaginatedResponse)
def read_subscription_entitlements(
    subscription_id: UUID,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=200),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify subscription exists
    subscription = crud.get_subscription(db, subscription_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    skip = (page - 1) * size
    entitlements = crud.get_subscription_entitlements_with_details(db, subscription_id=subscription_id, skip=skip, limit=size)
    total = db.query(models.SubscriptionEntitlement).filter(models.SubscriptionEntitlement.subscription_id == str(subscription_id)).count()
    return paginate_response(
        items=entitlements,
        total=total,
        page=page,
        size=size
    )

@router.put("/{subscription_id}/entitlements/{feature_id}", response_model=schemas.SubscriptionEntitlement)
def update_subscription_entitlement(
    subscription_id: UUID,
    feature_id: UUID,
    entitlement: schemas.SubscriptionEntitlementUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify subscription exists
    subscription = crud.get_subscription(db, subscription_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    db_entitlement = crud.update_subscription_entitlement(db, subscription_id=subscription_id, feature_id=feature_id, entitlement_update=entitlement)
    if db_entitlement is None:
        raise HTTPException(status_code=404, detail="Entitlement not found")
    return db_entitlement

@router.delete("/{subscription_id}/entitlements/{feature_id}")
def delete_subscription_entitlement(
    subscription_id: UUID,
    feature_id: UUID,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify subscription exists
    subscription = crud.get_subscription(db, subscription_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    success = crud.delete_subscription_entitlement(db, subscription_id=subscription_id, feature_id=feature_id)
    if not success:
        raise HTTPException(status_code=404, detail="Entitlement not found")
    return {"message": "Entitlement deleted successfully"}