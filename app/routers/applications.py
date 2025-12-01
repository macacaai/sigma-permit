from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.database import get_db
from app import models, schemas, crud
from app.auth import get_current_user
import secrets

router = APIRouter()

def generate_client_id() -> str:
    """Generate a unique client ID"""
    return secrets.token_urlsafe(32)

def generate_client_secret() -> str:
    """Generate a client secret"""
    return secrets.token_urlsafe(64)

def validate_redirect_uris(uris: list[str]) -> list[str]:
    """Validate redirect URIs format"""
    from urllib.parse import urlparse

    validated = []
    for uri in uris:
        try:
            parsed = urlparse(uri)
            if parsed.scheme in ['http', 'https'] and parsed.netloc:
                validated.append(uri)
            else:
                raise ValueError(f"Invalid redirect URI: {uri}")
        except:
            raise ValueError(f"Invalid redirect URI format: {uri}")
    return validated

@router.get("/", response_model=List[schemas.OAuthClient])
async def list_applications(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    tenant_id: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List OAuth2 client applications with filtering and pagination"""
    # Check permissions - admin or tenant admin can list applications
    if not current_user.is_superuser:
        # For non-admin users, only show applications they have access to
        query = db.query(models.OAuthClient).join(
            models.oauth_client_users
        ).filter(
            models.oauth_client_users.c.user_id == str(current_user.id)
        )
    else:
        query = db.query(models.OAuthClient)

    # Apply filters
    if tenant_id:
        query = query.filter(models.OAuthClient.tenant_id == tenant_id)
    if is_active is not None:
        query = query.filter(models.OAuthClient.is_active == is_active)

    applications = query.offset(skip).limit(limit).all()
    return applications

@router.post("/", response_model=schemas.OAuthClient, status_code=status.HTTP_201_CREATED)
async def create_application(
    application: schemas.OAuthClientCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create a new OAuth2 client application"""
    # Validate permissions
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create applications"
        )

    # Validate redirect URIs
    if application.redirect_uris:
        try:
            application.redirect_uris = validate_redirect_uris(application.redirect_uris)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

    # Generate client credentials
    client_id = generate_client_id()
    client_secret = generate_client_secret() if application.client_type == "confidential" else None

    # Create application
    db_application = models.OAuthClient(
        client_id=client_id,
        client_secret_hash=client_secret,  # Store as-is for now (should hash in production)
        client_name=application.client_name,
        client_type=application.client_type,
        redirect_uris=application.redirect_uris,
        allowed_grant_types=application.allowed_grant_types,
        allowed_scopes=application.allowed_scopes,
        logo_uri=application.logo_uri,
        website_uri=application.website_uri,
        tenant_id=application.tenant_id,
        is_active=application.is_active
    )

    db.add(db_application)
    db.commit()
    db.refresh(db_application)

    # Return with client secret (only shown on creation)
    response = schemas.OAuthClient.from_orm(db_application)
    # Add client_secret to response for initial setup
    response.__dict__['client_secret'] = client_secret
    return response

@router.get("/{client_id}", response_model=schemas.OAuthClient)
async def get_application(
    client_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get OAuth2 client application by client_id"""
    application = db.query(models.OAuthClient).filter(
        models.OAuthClient.client_id == client_id
    ).first()

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )

    # Check permissions
    if not current_user.is_superuser:
        # Check if user has access to this application
        has_access = db.query(models.oauth_client_users).filter(
            models.oauth_client_users.c.user_id == str(current_user.id),
            models.oauth_client_users.c.client_id == str(application.id)
        ).first()
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this application"
            )

    return application

@router.put("/{client_id}", response_model=schemas.OAuthClient)
async def update_application(
    client_id: str,
    application_update: schemas.OAuthClientUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Update OAuth2 client application"""
    application = db.query(models.OAuthClient).filter(
        models.OAuthClient.client_id == client_id
    ).first()

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )

    # Check permissions
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update applications"
        )

    # Validate redirect URIs if provided
    if application_update.redirect_uris:
        try:
            application_update.redirect_uris = validate_redirect_uris(application_update.redirect_uris)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

    # Update fields
    update_data = application_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(application, field, value)

    db.commit()
    db.refresh(application)
    return application

@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_application(
    client_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Delete OAuth2 client application"""
    application = db.query(models.OAuthClient).filter(
        models.OAuthClient.client_id == client_id
    ).first()

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )

    # Check permissions
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete applications"
        )

    db.delete(application)
    db.commit()
    return

@router.patch("/{client_id}/activate", response_model=schemas.OAuthClient)
async def activate_application(
    client_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Activate OAuth2 client application"""
    application = db.query(models.OAuthClient).filter(
        models.OAuthClient.client_id == client_id
    ).first()

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )

    # Check permissions
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can manage application status"
        )

    application.is_active = True
    db.commit()
    db.refresh(application)
    return application

@router.patch("/{client_id}/deactivate", response_model=schemas.OAuthClient)
async def deactivate_application(
    client_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Deactivate OAuth2 client application"""
    application = db.query(models.OAuthClient).filter(
        models.OAuthClient.client_id == client_id
    ).first()

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )

    # Check permissions
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can manage application status"
        )

    application.is_active = False
    db.commit()
    db.refresh(application)
    return application

@router.post("/{client_id}/secret", response_model=dict)
async def rotate_client_secret(
    client_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Rotate client secret for confidential applications"""
    application = db.query(models.OAuthClient).filter(
        models.OAuthClient.client_id == client_id
    ).first()

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )

    # Check permissions
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can rotate client secrets"
        )

    if application.client_type != "confidential":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only confidential clients have secrets"
        )

    # Generate new secret
    new_secret = generate_client_secret()
    application.client_secret_hash = new_secret

    db.commit()

    return {
        "message": "Client secret rotated successfully",
        "client_secret": new_secret,
        "client_id": client_id
    }

@router.get("/{client_id}/authorized-users", response_model=List[schemas.User])
async def get_authorized_users(
    client_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get users authorized for this application"""
    application = db.query(models.OAuthClient).filter(
        models.OAuthClient.client_id == client_id
    ).first()

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )

    # Check permissions
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can view authorized users"
        )

    users = db.query(models.User).join(
        models.oauth_client_users
    ).filter(
        models.oauth_client_users.c.client_id == str(application.id)
    ).all()

    return users

@router.post("/{client_id}/authorized-users", status_code=status.HTTP_201_CREATED)
async def grant_user_access(
    client_id: str,
    user_id: str,
    scope: Optional[List[str]] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Grant user access to this application"""
    application = db.query(models.OAuthClient).filter(
        models.OAuthClient.client_id == client_id
    ).first()

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check permissions
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can manage user access"
        )

    # Check if access already exists
    existing = db.query(models.oauth_client_users).filter(
        models.oauth_client_users.c.user_id == user_id,
        models.oauth_client_users.c.client_id == str(application.id)
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already has access to this application"
        )

    # Grant access
    db.execute(
        models.oauth_client_users.insert().values(
            user_id=user_id,
            client_id=str(application.id),
            scope=scope,
            granted_at=db.func.now()
        )
    )
    db.commit()

    return {"message": "User access granted successfully"}

@router.delete("/{client_id}/authorized-users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_user_access(
    client_id: str,
    user_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Revoke user access from this application"""
    application = db.query(models.OAuthClient).filter(
        models.OAuthClient.client_id == client_id
    ).first()

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )

    # Check permissions
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can manage user access"
        )

    # Revoke access
    result = db.execute(
        models.oauth_client_users.delete().where(
            models.oauth_client_users.c.user_id == user_id,
            models.oauth_client_users.c.client_id == str(application.id)
        )
    )

    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User does not have access to this application"
        )

    db.commit()
    return