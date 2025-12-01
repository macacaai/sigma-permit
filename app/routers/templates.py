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

router = APIRouter()

def paginate_response(items: List, total: int, page: int, size: int) -> schemas.PaginatedResponse:
    return schemas.PaginatedResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=ceil(total / size) if size > 0 else 0
    )

@router.post("", response_model=schemas.Template)
def create_template(
    template: schemas.TemplateCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return crud.create_template(db=db, template=template)

@router.get("", response_model=schemas.PaginatedResponse)
def read_templates(
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
        templates_list = crud.get_templates(db, skip=skip, limit=size)
        total = db.query(models.Template).count()
        pages = ceil(total / size) if size > 0 else 0
        return templates.TemplateResponse("templates_list.html", {
            "request": request,
            "templates": templates_list,
            "page": page,
            "size": size,
            "total": total,
            "pages": pages
        })

    # Return JSON for API requests
    skip = (page - 1) * size
    templates_list = crud.get_templates(db, skip=skip, limit=size)
    total = db.query(models.Template).count()
    return paginate_response(
        items=[schemas.Template.model_validate(template) for template in templates_list],
        total=total,
        page=page,
        size=size
    )

@router.get("/{template_id}", response_model=schemas.Template)
def read_template(
    template_id: UUID,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_template = crud.get_template(db, template_id=template_id)
    if db_template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    return db_template

@router.put("/{template_id}", response_model=schemas.Template)
def update_template(
    template_id: UUID,
    template: schemas.TemplateUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_template = crud.update_template(db, template_id=template_id, template_update=template)
    if db_template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    return db_template

@router.delete("/{template_id}")
def delete_template(
    template_id: UUID,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    success = crud.delete_template(db, template_id=template_id)
    if not success:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"message": "Template deleted successfully"}
