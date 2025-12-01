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

@router.post("", response_model=schemas.FeatureDefinition)
def create_feature(
    feature: schemas.FeatureDefinitionCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify product exists
    product = crud.get_product(db, feature.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return crud.create_feature_definition(db=db, feature=feature)

@router.get("", response_model=schemas.PaginatedResponse)
def read_features(
    request: Request,
    product_id: Optional[UUID] = None,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=200),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check if this is an HTMX request
    if request.headers.get("HX-Request"):
        # Return HTML for HTMX
        skip = (page - 1) * size
        features = crud.get_feature_definitions(db, product_id=product_id, skip=skip, limit=size)
        total = db.query(models.FeatureDefinition).count()
        pages = ceil(total / size) if size > 0 else 0
        return templates.TemplateResponse("features_list.html", {
            "request": request,
            "features": features,
            "page": page,
            "size": size,
            "total": total,
            "pages": pages
        })

    # Return JSON for API requests
    skip = (page - 1) * size
    features = crud.get_feature_definitions_with_product(db, product_id=product_id, skip=skip, limit=size)
    total = db.query(models.FeatureDefinition).count()
    return paginate_response(
        items=features,
        total=total,
        page=page,
        size=size
    )

@router.get("/{feature_id}", response_model=schemas.FeatureDefinition)
def read_feature(
    feature_id: UUID,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_feature = crud.get_feature_definition(db, feature_id=feature_id)
    if db_feature is None:
        raise HTTPException(status_code=404, detail="Feature not found")
    return db_feature

@router.put("/{feature_id}", response_model=schemas.FeatureDefinition)
def update_feature(
    feature_id: UUID,
    feature: schemas.FeatureDefinitionUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_feature = crud.update_feature_definition(db, feature_id=feature_id, feature_update=feature)
    if db_feature is None:
        raise HTTPException(status_code=404, detail="Feature not found")
    return db_feature

@router.delete("/{feature_id}")
def delete_feature(
    feature_id: UUID,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    success = crud.delete_feature_definition(db, feature_id=feature_id)
    if not success:
        raise HTTPException(status_code=404, detail="Feature not found")
    return {"message": "Feature deleted successfully"}