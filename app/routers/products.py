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

@router.post("", response_model=schemas.Product)
def create_product(
    product: schemas.ProductCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return crud.create_product(db=db, product=product)

@router.get("", response_model=schemas.PaginatedResponse)
def read_products(
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
        products = crud.get_products(db, skip=skip, limit=size)
        total = db.query(models.Product).count()
        pages = ceil(total / size) if size > 0 else 0
        return templates.TemplateResponse("products_list.html", {
            "request": request,
            "products": products,
            "page": page,
            "size": size,
            "total": total,
            "pages": pages
        })

    # Return JSON for API requests
    skip = (page - 1) * size
    products = crud.get_products(db, skip=skip, limit=size)
    total = db.query(models.Product).count()
    return paginate_response(
        items=[schemas.Product.model_validate(product) for product in products],
        total=total,
        page=page,
        size=size
    )

@router.get("/{product_id}", response_model=schemas.Product)
def read_product(
    product_id: UUID,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_product = crud.get_product(db, product_id=product_id)
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return db_product

@router.put("/{product_id}", response_model=schemas.Product)
def update_product(
    product_id: UUID,
    product: schemas.ProductUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_product = crud.update_product(db, product_id=product_id, product_update=product)
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return db_product

@router.delete("/{product_id}")
def delete_product(
    product_id: UUID,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    success = crud.delete_product(db, product_id=product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product deleted successfully"}