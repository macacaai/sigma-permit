import base64
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Form, Query, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import or_ as sql_or
from typing import List, Optional, Dict, Any
from app.database import get_db
from app import crud, models, schemas
from app.auth import create_access_token, create_refresh_token, verify_refresh_token, get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES
from app.routers.sessions import generate_session_id, extract_device_info, create_session_fingerprint

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

@router.post("/login", response_model=schemas.TokenResponse)
async def login(
    request: Request,
    credentials: str = Form(...),
    tenant_id: str = Form(...),
    db: Session = Depends(get_db)
):
    """Login endpoint for base64 encoded username/password authentication"""
    try:
        # Decode base64 credentials (format: username:password)
        decoded = credentials.encode('ascii').decode('ascii')  # Validate base64
        decoded_bytes = base64.b64decode(decoded)
        decoded_str = decoded_bytes.decode('ascii')

        # Split username:password
        if ':' not in decoded_str:
            raise ValueError("Invalid credentials format")

        username, password = decoded_str.split(':', 1)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid credentials format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Authenticate user
    user = crud.authenticate_user(db, username, password, tenant_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "user_id": str(user.id), "tenant_id": user.tenant_id},
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        data={"sub": user.username, "user_id": str(user.id), "tenant_id": user.tenant_id}
    )

    # Store refresh token in database
    user.refresh_token = refresh_token

    # Create user session for tracking
    device_info = extract_device_info(request)
    fingerprint = create_session_fingerprint(device_info)

    session_id = generate_session_id()
    expires_at = datetime.utcnow() + timedelta(hours=8)  # 8 hours default

    session = models.UserSession(
        user_id=str(user.id),
        session_id=session_id,
        device_info=device_info,
        ip_address=device_info.get("ip_address"),
        user_agent=device_info.get("user_agent"),
        is_active=True,
        expires_at=expires_at
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    return schemas.TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=schemas.User.from_orm(user)
    )

@router.post("/refresh", response_model=schemas.TokenResponse)
async def refresh_token(
    refresh_token: str = Form(...),
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token"""
    username = verify_refresh_token(refresh_token)
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = crud.get_user_by_username(db, username=username)
    if user is None or user.refresh_token != refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )

    # Generate new tokens
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token = create_access_token(
        data={"sub": user.username, "user_id": str(user.id)},
        expires_delta=access_token_expires
    )
    new_refresh_token = create_refresh_token(
        data={"sub": user.username, "user_id": str(user.id)}
    )

    # Update refresh token in database
    user.refresh_token = new_refresh_token
    db.commit()

    return schemas.TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        user=schemas.User.from_orm(user)
    )

@router.post("/logout")
async def logout(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Logout endpoint - clear refresh token from database"""
    current_user.refresh_token = None
    db.commit()
    return {"message": "Successfully logged out"}

@router.get("/me", response_model=schemas.User)
async def read_users_me(current_user: models.User = Depends(get_current_user)):
    """Get current user information"""
    return schemas.User.from_orm(current_user)

@router.post("/change-password")
async def change_password(
    password_change: schemas.PasswordChange,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change current user's password"""
    # Verify current password
    if not current_user.verify_password(password_change.current_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    # Update password
    crud.update_user(db, current_user.id, schemas.UserUpdate(password=password_change.new_password))

    return {"message": "Password changed successfully"}

# User management endpoints (admin only)
@router.get("/users", response_model=list[schemas.User])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all users (admin only)"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    users = crud.get_users(db, skip=skip, limit=limit)
    return [schemas.User.from_orm(user) for user in users]

@router.post("/users", response_model=schemas.User)
async def create_user(
    user: schemas.UserCreate,
    tenant_id: str = Form(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new user (admin only)"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    # Check if user already exists
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    return schemas.User.from_orm(crud.create_user(db=db, user=user))

@router.get("/users/{user_id}", response_model=schemas.User)
async def read_user(
    user_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user by ID (admin only or own profile)"""
    if not current_user.is_superuser and str(current_user.id) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    db_user = crud.get_user(db, user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return schemas.User.from_orm(db_user)

@router.put("/users/{user_id}", response_model=schemas.User)
async def update_user(
    user_id: str,
    user_update: schemas.UserUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user (admin only or own profile)"""
    if not current_user.is_superuser and str(current_user.id) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    # Non-admin users can't change their own admin status or activate/deactivate themselves
    if not current_user.is_superuser:
        user_update.is_superuser = None
        user_update.is_active = None

    db_user = crud.update_user(db, user_id, user_update)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return schemas.User.from_orm(db_user)

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete user (admin only)"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    if str(current_user.id) == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )

    success = crud.delete_user(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": "User deleted successfully"}

# Enhanced Authentication Endpoints (v1)

@router.post("/v1/forgot-password")
async def forgot_password(
    request: schemas.ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    """Initiate password reset process"""
    user = crud.get_user_by_email(db, email=request.email)
    if not user:
        # Don't reveal if email exists or not for security
        return {"message": "If the email exists, a password reset link has been sent"}

    # In a real implementation, send email with reset token
    # For now, just return success message
    return {"message": "If the email exists, a password reset link has been sent"}

@router.post("/v1/reset-password")
async def reset_password(
    request: schemas.ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """Reset password using reset token"""
    # In a real implementation, verify the token
    # For now, just accept any token and update password
    # This is a simplified implementation

    # Find user by token (simplified - in real app, decode JWT token)
    # For demo purposes, assume token contains user_id
    try:
        # This is a placeholder - real implementation would verify JWT token
        user_id = "placeholder_user_id"  # Extract from token
        user = crud.get_user(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid reset token"
            )

        # Update password
        crud.update_user(db, user.id, schemas.UserUpdate(password=request.new_password))
        return {"message": "Password reset successfully"}

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token"
        )

@router.post("/v1/verify-email")
async def verify_email(
    request: schemas.VerifyEmailRequest,
    db: Session = Depends(get_db)
):
    """Verify user's email address"""
    # In a real implementation, verify the token and mark email as verified
    # For now, just return success
    try:
        # This is a placeholder - real implementation would verify JWT token
        user_id = "placeholder_user_id"  # Extract from token
        user = crud.get_user(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification token"
            )

        # Mark email as verified
        user.email_verified = True
        user.email_verified_at = datetime.utcnow()
        db.commit()

        return {"message": "Email verified successfully"}

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token"
        )

@router.post("/v1/resend-verification")
async def resend_verification(
    request: schemas.ResendVerificationRequest,
    db: Session = Depends(get_db)
):
    """Resend email verification"""
    user = crud.get_user_by_email(db, email=request.email)
    if not user:
        # Don't reveal if email exists or not
        return {"message": "If the email exists, a verification link has been sent"}

    if user.email_verified:
        return {"message": "Email is already verified"}

    # In a real implementation, send verification email
    # For now, just return success message
    return {"message": "If the email exists, a verification link has been sent"}

# Enhanced login endpoint with additional user information
@router.post("/v1/login", response_model=schemas.EnhancedTokenResponse)
async def enhanced_login(
    credentials: str = Form(...),
    tenant_id: str = Form(...),
    db: Session = Depends(get_db)
):
    """Enhanced login endpoint with additional user information and roles"""
    try:
        # Decode base64 credentials (format: username:password)
        decoded = credentials.encode('ascii').decode('ascii')  # Validate base64
        decoded_bytes = base64.b64decode(decoded)
        decoded_str = decoded_bytes.decode('ascii')

        # Split username:password
        if ':' not in decoded_str:
            raise ValueError("Invalid credentials format")

        username, password = decoded_str.split(':', 1)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid credentials format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Authenticate user
    user = crud.authenticate_user(db, username, password, tenant_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user roles and permissions
    user_roles = []
    user_permissions = []

    # Query user roles with role names
    from sqlalchemy.orm import joinedload
    user_with_roles = db.query(models.User).options(
        joinedload(models.User.roles).joinedload(models.UserRole.role)
    ).filter(models.User.id == user.id).first()

    if user_with_roles and user_with_roles.roles:
        for user_role in user_with_roles.roles:
            user_roles.append(user_role.role.name)
            # Get permissions for this role
            role_permissions = db.query(models.Permission).join(
                models.role_permissions
            ).filter(
                models.role_permissions.c.role_id == user_role.role.id
            ).all()
            for perm in role_permissions:
                user_permissions.append(f"{perm.resource}:{perm.action}")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "user_id": str(user.id), "tenant_id": user.tenant_id, "roles": user_roles, "permissions": user_permissions},
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        data={"sub": user.username, "user_id": str(user.id), "tenant_id": user.tenant_id}
    )

    # Store refresh token in database
    user.refresh_token = refresh_token
    db.commit()

    # Create enhanced user response
    enhanced_user = schemas.User.from_orm(user)
    enhanced_user.__dict__.update({
        'roles': user_roles,
        'permissions': list(set(user_permissions)),  # Remove duplicates
        'last_login': user.last_login
    })

    return schemas.EnhancedTokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="Bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        scope="read write",  # Default scope
        user=enhanced_user
    )

# Enhanced User Management Endpoints (v1)

@router.get("/v1/users", response_model=schemas.PaginatedResponse)
async def list_users_v1(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    sort: str = Query("created_at:desc", pattern=r"^[a-zA-Z_]+:(asc|desc)$"),
    filter_role: Optional[str] = None,
    filter_status: Optional[str] = Query(None, pattern=r"^(active|inactive|pending_verification)$"),
    filter_verified: Optional[bool] = None,
    filter_tenant: Optional[str] = None,
    search: Optional[str] = Query(None, min_length=2, max_length=100),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Enhanced user listing with filtering, pagination, and sorting"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can list users"
        )

    # Build query
    query = db.query(models.User)

    # Apply filters
    if filter_role:
        query = query.join(models.User.roles).join(models.UserRole.role).filter(
            models.Role.name == filter_role
        )

    if filter_status:
        if filter_status == "active":
            query = query.filter(models.User.is_active == True)
        elif filter_status == "inactive":
            query = query.filter(models.User.is_active == False)
        elif filter_status == "pending_verification":
            query = query.filter(models.User.email_verified == False)

    if filter_verified is not None:
        query = query.filter(models.User.email_verified == filter_verified)

    if filter_tenant:
        query = query.filter(models.User.tenant_id == filter_tenant)

    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            sql_or(
                models.User.username.ilike(search_filter),
                models.User.email.ilike(search_filter),
                models.User.full_name.ilike(search_filter)
            )
        )

    # Apply sorting
    sort_field, sort_order = sort.split(":")
    if sort_order == "desc":
        query = query.order_by(getattr(models.User, sort_field).desc())
    else:
        query = query.order_by(getattr(models.User, sort_field).asc())

    # Get total count
    total = query.count()

    # Apply pagination
    skip = (page - 1) * size
    users = query.offset(skip).limit(size).all()

    # Calculate pagination info
    total_pages = (total + size - 1) // size if size > 0 else 0

    return schemas.PaginatedResponse(
        items=[schemas.User.from_orm(user) for user in users],
        total=total,
        page=page,
        size=size,
        pages=total_pages
    )

@router.get("/v1/users/me/profile", response_model=schemas.User)
async def get_my_profile(
    current_user: models.User = Depends(get_current_user)
):
    """Get current user's profile"""
    return schemas.User.from_orm(current_user)

@router.put("/v1/users/me/profile", response_model=schemas.User)
async def update_my_profile(
    profile_update: schemas.UserUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's profile"""
    # Non-admin users can't change sensitive fields
    profile_update.is_superuser = None
    profile_update.is_active = None
    profile_update.is_verified = None

    updated_user = crud.update_user(db, str(current_user.id), profile_update)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")

    return schemas.User.from_orm(updated_user)

@router.post("/v1/users/bulk-create", response_model=dict)
async def bulk_create_users(
    users_data: list[schemas.UserCreate],
    tenant_id: str = Form(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Bulk create users"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can bulk create users"
        )

    created_users = []
    errors = []

    for i, user_data in enumerate(users_data):
        try:
            # Set tenant_id for the user
            user_data.tenant_id = tenant_id

            # Check for duplicates within tenant
            if crud.get_user_by_email(db, email=user_data.email, tenant_id=tenant_id):
                errors.append({"index": i, "error": "Email already registered in this tenant", "email": user_data.email})
                continue
            if crud.get_user_by_username(db, username=user_data.username, tenant_id=tenant_id):
                errors.append({"index": i, "error": "Username already registered in this tenant", "username": user_data.username})
                continue

            user = crud.create_user(db=db, user=user_data)
            created_users.append(schemas.User.from_orm(user))
        except Exception as e:
            errors.append({"index": i, "error": str(e), "data": user_data.model_dump()})

    return {
        "created": len(created_users),
        "errors": len(errors),
        "users": created_users,
        "error_details": errors
    }

@router.put("/v1/users/bulk-update", response_model=dict)
async def bulk_update_users(
    updates: list[dict],  # [{"user_id": "id", "updates": {...}}]
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Bulk update users"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can bulk update users"
        )

    updated_users = []
    errors = []

    for i, update_data in enumerate(updates):
        try:
            user_id = update_data["user_id"]
            updates_dict = update_data["updates"]

            update_schema = schemas.UserUpdate(**updates_dict)
            user = crud.update_user(db, user_id, update_schema)

            if user:
                updated_users.append(schemas.User.from_orm(user))
            else:
                errors.append({"index": i, "error": "User not found", "user_id": user_id})
        except Exception as e:
            errors.append({"index": i, "error": str(e), "data": update_data})

    return {
        "updated": len(updated_users),
        "errors": len(errors),
        "users": updated_users,
        "error_details": errors
    }

@router.delete("/v1/users/bulk-delete", response_model=dict)
async def bulk_delete_users(
    user_ids: list[str],
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Bulk delete users"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can bulk delete users"
        )

    deleted_count = 0
    errors = []

    for i, user_id in enumerate(user_ids):
        try:
            if user_id == str(current_user.id):
                errors.append({"index": i, "error": "Cannot delete your own account", "user_id": user_id})
                continue

            success = crud.delete_user(db, user_id)
            if success:
                deleted_count += 1
            else:
                errors.append({"index": i, "error": "User not found", "user_id": user_id})
        except Exception as e:
            errors.append({"index": i, "error": str(e), "user_id": user_id})

    return {
        "deleted": deleted_count,
        "errors": len(errors),
        "error_details": errors
    }

@router.get("/v1/users/export", response_model=dict)
async def export_users(
    format: str = Query("json", pattern=r"^(json|csv)$"),
    filter_role: Optional[str] = None,
    filter_status: Optional[str] = Query(None, pattern=r"^(active|inactive|pending_verification)$"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Export users data"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can export users"
        )

    # Build query similar to list_users_v1
    query = db.query(models.User)

    if filter_role:
        query = query.join(models.User.roles).join(models.UserRole.role).filter(
            models.Role.name == filter_role
        )

    if filter_status:
        if filter_status == "active":
            query = query.filter(models.User.is_active == True)
        elif filter_status == "inactive":
            query = query.filter(models.User.is_active == False)
        elif filter_status == "pending_verification":
            query = query.filter(models.User.email_verified == False)

    users = query.all()

    if format == "json":
        return {
            "users": [schemas.User.from_orm(user).model_dump() for user in users],
            "total": len(users),
            "exported_at": datetime.utcnow().isoformat()
        }
    else:  # CSV format
        # Simple CSV implementation
        csv_data = "id,email,username,full_name,is_active,email_verified,created_at\n"
        for user in users:
            csv_data += f"{user.id},{user.email},{user.username},{user.full_name or ''},{user.is_active},{user.email_verified},{user.created_at.isoformat()}\n"

        return {
            "format": "csv",
            "data": csv_data,
            "total": len(users),
            "exported_at": datetime.utcnow().isoformat()
        }

@router.patch("/v1/users/{user_id}/verify-email", response_model=schemas.User)
async def verify_user_email(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Manually verify user's email (admin only)"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can verify emails"
        )

    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.email_verified = True
    user.email_verified_at = datetime.utcnow()
    db.commit()
    db.refresh(user)

    return schemas.User.from_orm(user)

@router.patch("/v1/users/{user_id}/activate", response_model=schemas.User)
async def activate_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Activate user account"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can manage user status"
        )

    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = True
    db.commit()
    db.refresh(user)

    return schemas.User.from_orm(user)

@router.patch("/v1/users/{user_id}/deactivate", response_model=schemas.User)
async def deactivate_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Deactivate user account"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can manage user status"
        )

    if user_id == str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )

    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = False
    db.commit()
    db.refresh(user)

    return schemas.User.from_orm(user)
