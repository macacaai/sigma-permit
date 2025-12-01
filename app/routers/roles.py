from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app import models, schemas
from app.auth import get_current_active_superuser, check_permission

router = APIRouter()

# Role Management Endpoints
@router.get("/", response_model=List[schemas.Role])
async def get_roles(
    skip: int = 0,
    limit: int = 100,
    tenant_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_superuser)
):
    """Get all roles with optional tenant filtering"""
    query = db.query(models.Role)
    if tenant_id:
        query = query.filter(models.Role.tenant_id == tenant_id)
    roles = query.offset(skip).limit(limit).all()
    return roles

@router.post("/", response_model=schemas.Role)
async def create_role(
    role: schemas.RoleCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_superuser)
):
    """Create a new role"""
    # Check if role name already exists for this tenant
    existing_role = db.query(models.Role).filter(
        models.Role.name == role.name,
        models.Role.tenant_id == role.tenant_id
    ).first()
    if existing_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role name already exists for this tenant"
        )

    db_role = models.Role(
        name=role.name,
        description=role.description,
        tenant_id=role.tenant_id,
        is_system=False
    )
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role

@router.get("/{role_id}", response_model=schemas.Role)
async def get_role(
    role_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_superuser)
):
    """Get a specific role by ID"""
    role = db.query(models.Role).filter(models.Role.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    return role

@router.put("/{role_id}", response_model=schemas.Role)
async def update_role(
    role_id: str,
    role_update: schemas.RoleUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_superuser)
):
    """Update a role"""
    role = db.query(models.Role).filter(models.Role.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )

    # Prevent updating system roles
    if role.is_system:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify system roles"
        )

    # Check name uniqueness if name is being updated
    if role_update.name and role_update.name != role.name:
        existing_role = db.query(models.Role).filter(
            models.Role.name == role_update.name,
            models.Role.tenant_id == role.tenant_id
        ).first()
        if existing_role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role name already exists for this tenant"
            )

    for field, value in role_update.dict(exclude_unset=True).items():
        setattr(role, field, value)

    db.commit()
    db.refresh(role)
    return role

@router.delete("/{role_id}")
async def delete_role(
    role_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_superuser)
):
    """Delete a role"""
    role = db.query(models.Role).filter(models.Role.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )

    # Prevent deleting system roles
    if role.is_system:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete system roles"
        )

    db.delete(role)
    db.commit()
    return {"message": "Role deleted successfully"}

# Permission Management Endpoints
@router.get("/permissions/", response_model=List[schemas.Permission])
async def get_permissions(
    skip: int = 0,
    limit: int = 100,
    resource: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(check_permission("roles.read"))
):
    """Get all permissions with optional resource filtering"""
    query = db.query(models.Permission)
    if resource:
        query = query.filter(models.Permission.resource == resource)
    permissions = query.offset(skip).limit(limit).all()
    return permissions

@router.post("/permissions/", response_model=schemas.Permission)
async def create_permission(
    permission: schemas.PermissionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_superuser)
):
    """Create a new permission"""
    # Check if permission already exists
    existing_permission = db.query(models.Permission).filter(
        models.Permission.resource == permission.resource,
        models.Permission.action == permission.action
    ).first()
    if existing_permission:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Permission already exists"
        )

    db_permission = models.Permission(
        name=permission.name,
        resource=permission.resource,
        action=permission.action,
        description=permission.description,
        is_system=False
    )
    db.add(db_permission)
    db.commit()
    db.refresh(db_permission)
    return db_permission

# Role-Permission Assignment Endpoints
@router.post("/{role_id}/permissions/{permission_id}")
async def assign_permission_to_role(
    role_id: str,
    permission_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_superuser)
):
    """Assign a permission to a role"""
    role = db.query(models.Role).filter(models.Role.id == role_id).first()
    permission = db.query(models.Permission).filter(models.Permission.id == permission_id).first()

    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found"
        )

    # Check if already assigned
    if permission in role.permissions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Permission already assigned to role"
        )

    role.permissions.append(permission)
    db.commit()
    return {"message": "Permission assigned to role successfully"}

@router.delete("/{role_id}/permissions/{permission_id}")
async def remove_permission_from_role(
    role_id: str,
    permission_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_superuser)
):
    """Remove a permission from a role"""
    role = db.query(models.Role).filter(models.Role.id == role_id).first()
    permission = db.query(models.Permission).filter(models.Permission.id == permission_id).first()

    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found"
        )

    if permission not in role.permissions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Permission not assigned to role"
        )

    role.permissions.remove(permission)
    db.commit()
    return {"message": "Permission removed from role successfully"}

# User-Role Assignment Endpoints
@router.post("/users/{user_id}/roles/{role_id}")
async def assign_role_to_user(
    user_id: str,
    role_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_superuser)
):
    """Assign a role to a user"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    role = db.query(models.Role).filter(models.Role.id == role_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )

    # Check if already assigned
    if role in user.roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role already assigned to user"
        )

    user.roles.append(role)
    db.commit()
    return {"message": "Role assigned to user successfully"}

@router.delete("/users/{user_id}/roles/{role_id}")
async def remove_role_from_user(
    user_id: str,
    role_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_superuser)
):
    """Remove a role from a user"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    role = db.query(models.Role).filter(models.Role.id == role_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )

    if role not in user.roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role not assigned to user"
        )

    user.roles.remove(role)
    db.commit()
    return {"message": "Role removed from user successfully"}

@router.get("/users/{user_id}/permissions")
async def get_user_permissions(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_superuser)
):
    """Get effective permissions for a user"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Collect all permissions from user's roles
    permissions = set()
    for role in user.roles:
        for permission in role.permissions:
            permissions.add(permission.name)

    return {"permissions": list(permissions)}