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

@router.post("", response_model=schemas.PlanDefinition)
def create_plan(
    plan: schemas.PlanDefinitionCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify product exists
    product = crud.get_product(db, plan.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return crud.create_plan_definition(db=db, plan=plan)

@router.get("", response_model=schemas.PaginatedResponse)
def read_plans(
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
        plans = crud.get_plan_definitions(db, product_id=product_id, skip=skip, limit=size)
        total = db.query(models.PlanDefinition).count()
        pages = ceil(total / size) if size > 0 else 0
        return templates.TemplateResponse("plans_list.html", {
            "request": request,
            "plans": plans,
            "page": page,
            "size": size,
            "total": total,
            "pages": pages
        })

    # Return JSON for API requests
    skip = (page - 1) * size
    plans = crud.get_plan_definitions_with_product(db, product_id=product_id, skip=skip, limit=size)
    total = db.query(models.PlanDefinition).count()
    return paginate_response(
        items=plans,
        total=total,
        page=page,
        size=size
    )

@router.get("/{plan_id}", response_model=schemas.PlanDefinition)
def read_plan(
    plan_id: UUID,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_plan = crud.get_plan_definition(db, plan_id=plan_id)
    if db_plan is None:
        raise HTTPException(status_code=404, detail="Plan not found")
    return db_plan

@router.put("/{plan_id}", response_model=schemas.PlanDefinition)
def update_plan(
    plan_id: UUID,
    plan: schemas.PlanDefinitionUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_plan = crud.update_plan_definition(db, plan_id=plan_id, plan_update=plan)
    if db_plan is None:
        raise HTTPException(status_code=404, detail="Plan not found")
    return db_plan

@router.delete("/{plan_id}")
def delete_plan(
    plan_id: UUID,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    success = crud.delete_plan_definition(db, plan_id=plan_id)
    if not success:
        raise HTTPException(status_code=404, detail="Plan not found")
    return {"message": "Plan deleted successfully"}