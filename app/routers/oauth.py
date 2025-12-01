from fastapi import APIRouter, Depends, HTTPException, status, Query, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional
import secrets
import hashlib
import base64
import os
import requests
from datetime import datetime, timedelta
from app.database import get_db
from app import models, schemas, crud
from app.auth import create_access_token, create_refresh_token, verify_token

router = APIRouter()

# Social Provider Configurations
SOCIAL_PROVIDERS = {
    "google": {
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
        "authorize_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "userinfo_url": "https://www.googleapis.com/oauth2/v2/userinfo",
        "scope": "openid email profile",
        "redirect_uri": os.getenv("BASE_URL", "http://localhost:8000") + "/oauth/v1/social/google/callback"
    },
    "github": {
        "client_id": os.getenv("GITHUB_CLIENT_ID"),
        "client_secret": os.getenv("GITHUB_CLIENT_SECRET"),
        "authorize_url": "https://github.com/login/oauth/authorize",
        "token_url": "https://github.com/login/oauth/access_token",
        "userinfo_url": "https://api.github.com/user",
        "scope": "user:email",
        "redirect_uri": os.getenv("BASE_URL", "http://localhost:8000") + "/oauth/v1/social/github/callback"
    },
    "microsoft": {
        "client_id": os.getenv("MICROSOFT_CLIENT_ID"),
        "client_secret": os.getenv("MICROSOFT_CLIENT_SECRET"),
        "authorize_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
        "token_url": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
        "userinfo_url": "https://graph.microsoft.com/v1.0/me",
        "scope": "openid email profile",
        "redirect_uri": os.getenv("BASE_URL", "http://localhost:8000") + "/oauth/v1/social/microsoft/callback"
    },
    "facebook": {
        "client_id": os.getenv("FACEBOOK_CLIENT_ID"),
        "client_secret": os.getenv("FACEBOOK_CLIENT_SECRET"),
        "authorize_url": "https://www.facebook.com/v18.0/dialog/oauth",
        "token_url": "https://graph.facebook.com/v18.0/oauth/access_token",
        "userinfo_url": "https://graph.facebook.com/me?fields=id,name,email",
        "scope": "email,public_profile",
        "redirect_uri": os.getenv("BASE_URL", "http://localhost:8000") + "/oauth/v1/social/facebook/callback"
    }
}

# Helper functions
def generate_client_id() -> str:
    """Generate a unique client ID"""
    return secrets.token_urlsafe(32)

def generate_client_secret() -> str:
    """Generate a client secret"""
    return secrets.token_urlsafe(64)

def verify_pkce(code_challenge: str, code_verifier: str, method: str = "S256") -> bool:
    """Verify PKCE code challenge"""
    if method == "S256":
        code_challenge_computed = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode('ascii')).digest()
        ).decode('ascii').rstrip('=')
        return secrets.compare_digest(code_challenge, code_challenge_computed)
    elif method == "plain":
        return secrets.compare_digest(code_challenge, code_verifier)
    return False

def get_social_provider_config(provider: str) -> dict:
    """Get social provider configuration"""
    config = SOCIAL_PROVIDERS.get(provider.lower())
    if not config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported social provider: {provider}"
        )
    if not config.get("client_id") or not config.get("client_secret"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Social provider {provider} not configured"
        )
    return config

def exchange_code_for_token(provider_config: dict, code: str) -> dict:
    """Exchange authorization code for access token"""
    data = {
        "client_id": provider_config["client_id"],
        "client_secret": provider_config["client_secret"],
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": provider_config["redirect_uri"]
    }

    headers = {"Accept": "application/json"}
    if "github" in provider_config["token_url"]:
        headers["Accept"] = "application/json"

    response = requests.post(provider_config["token_url"], data=data, headers=headers)
    response.raise_for_status()
    return response.json()

def get_user_info(provider: str, access_token: str) -> dict:
    """Get user information from social provider"""
    config = get_social_provider_config(provider)
    headers = {"Authorization": f"Bearer {access_token}"}

    if provider.lower() == "github":
        # GitHub requires token in header
        headers = {"Authorization": f"token {access_token}"}

    response = requests.get(config["userinfo_url"], headers=headers)
    response.raise_for_status()
    user_data = response.json()

    # Normalize user data across providers
    normalized_data = {
        "provider": provider.lower(),
        "provider_user_id": str(user_data.get("id")),
        "email": user_data.get("email"),
        "name": user_data.get("name") or user_data.get("login"),
        "username": user_data.get("login") or user_data.get("preferred_username"),
        "avatar_url": user_data.get("picture") or user_data.get("avatar_url"),
        "profile_data": user_data
    }

    # For GitHub, get email separately if not provided
    if provider.lower() == "github" and not normalized_data["email"]:
        email_response = requests.get("https://api.github.com/user/emails", headers=headers)
        if email_response.status_code == 200:
            emails = email_response.json()
            primary_email = next((email for email in emails if email.get("primary")), None)
            if primary_email:
                normalized_data["email"] = primary_email["email"]

    return normalized_data

# Social Login Endpoints
@router.get("/social/{provider}")
async def social_login_initiate(
    provider: str,
    tenant_id: str = Query(...),
    state: Optional[str] = Query(None),
    scope: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Initiate social login flow"""
    config = get_social_provider_config(provider)

    # Generate state if not provided
    if not state:
        state = secrets.token_urlsafe(32)

    # Use provider default scope if not specified
    if not scope:
        scope = config["scope"]

    # Build authorization URL
    params = {
        "client_id": config["client_id"],
        "redirect_uri": config["redirect_uri"],
        "scope": scope,
        "response_type": "code",
        "state": state
    }

    # Provider-specific parameters
    if provider.lower() == "google":
        params["access_type"] = "offline"
        params["prompt"] = "consent"

    auth_url = config["authorize_url"] + "?" + "&".join([f"{k}={requests.utils.quote(str(v))}" for k, v in params.items()])

    return RedirectResponse(url=auth_url)

@router.get("/social/{provider}/callback")
async def social_login_callback(
    provider: str,
    tenant_id: str = Query(...),
    code: str = Query(...),
    state: str = Query(...),
    error: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Handle social login callback"""
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Social login error: {error}"
        )

    try:
        # Get provider config
        config = get_social_provider_config(provider)

        # Exchange code for token
        token_data = exchange_code_for_token(config, code)

        # Get user info
        user_info = get_user_info(provider, token_data["access_token"])

        # Check if social connection exists
        social_connection = db.query(models.SocialConnection).filter(
            models.SocialConnection.provider == user_info["provider"],
            models.SocialConnection.provider_user_id == user_info["provider_user_id"]
        ).first()

        if social_connection:
            # Existing user - log them in
            user = social_connection.user
        else:
            # New user - check if email exists
            existing_user = None
            if user_info["email"]:
                existing_user = db.query(models.User).filter(
                    models.User.email == user_info["email"]
                ).first()

            if existing_user:
                # Link social account to existing user
                social_connection = models.SocialConnection(
                    user_id=existing_user.id,
                    provider=user_info["provider"],
                    provider_user_id=user_info["provider_user_id"],
                    provider_username=user_info["username"],
                    provider_email=user_info["email"],
                    provider_name=user_info["name"],
                    provider_avatar_url=user_info["avatar_url"],
                    access_token=token_data.get("access_token"),
                    refresh_token=token_data.get("refresh_token"),
                    expires_at=datetime.utcnow() + timedelta(seconds=token_data.get("expires_in", 3600)),
                    profile_data=user_info["profile_data"]
                )
                db.add(social_connection)
                user = existing_user
            else:
                # Create new user
                username = user_info["username"] or user_info["email"].split("@")[0] if user_info["email"] else f"{provider}_{user_info['provider_user_id']}"
                # For social login users, set a dummy password since they authenticate via social providers
                dummy_password = secrets.token_urlsafe(64)
                user = models.User(
                    tenant_id=tenant_id,
                    username=username,
                    email=user_info["email"],
                    full_name=user_info["name"],
                    hashed_password=dummy_password,  # Dummy password for social users
                    is_active=True,
                    email_verified=bool(user_info["email"])
                )
                db.add(user)
                db.flush()  # Get user ID

                # Create social connection
                social_connection = models.SocialConnection(
                    user_id=user.id,
                    provider=user_info["provider"],
                    provider_user_id=user_info["provider_user_id"],
                    provider_username=user_info["username"],
                    provider_email=user_info["email"],
                    provider_name=user_info["name"],
                    provider_avatar_url=user_info["avatar_url"],
                    access_token=token_data.get("access_token"),
                    refresh_token=token_data.get("refresh_token"),
                    expires_at=datetime.utcnow() + timedelta(seconds=token_data.get("expires_in", 3600)),
                    profile_data=user_info["profile_data"],
                    is_primary=True
                )
                db.add(social_connection)

        db.commit()

        # Create access token for our system
        access_token = create_access_token(data={"sub": str(user.id), "tenant_id": user.tenant_id, "type": "access"})
        refresh_token = create_refresh_token(data={"sub": str(user.id), "tenant_id": user.tenant_id, "type": "refresh"})

        # Redirect to frontend with tokens
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        redirect_url = f"{frontend_url}/auth/callback?access_token={access_token}&refresh_token={refresh_token}&state={state}"

        return RedirectResponse(url=redirect_url)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Social login failed: {str(e)}"
        )

@router.get("/authorize")
async def authorize(
    response_type: str = Query(..., regex=r"^(code|token|id_token)$"),
    client_id: str = Query(...),
    redirect_uri: Optional[str] = Query(None),
    scope: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    nonce: Optional[str] = Query(None),
    code_challenge: Optional[str] = Query(None),
    code_challenge_method: Optional[str] = Query("S256", regex=r"^(S256|plain)$"),
    db: Session = Depends(get_db)
):
    """OAuth2 authorization endpoint"""
    # Validate client
    client = db.query(models.OAuthClient).filter(
        models.OAuthClient.client_id == client_id,
        models.OAuthClient.is_active == True
    ).first()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid client"
        )

    # Validate redirect URI
    if redirect_uri and redirect_uri not in (client.redirect_uris or []):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid redirect URI"
        )

    # For now, redirect to login page (this would be a full implementation)
    # In a real implementation, this would show a consent screen
    login_url = f"/admin/login?client_id={client_id}&response_type={response_type}&redirect_uri={redirect_uri or ''}&scope={scope or ''}&state={state or ''}"
    return RedirectResponse(url=login_url)

@router.post("/token")
async def token(
    grant_type: str = Form(...),
    code: Optional[str] = Form(None),
    redirect_uri: Optional[str] = Form(None),
    code_verifier: Optional[str] = Form(None),
    refresh_token: Optional[str] = Form(None),
    scope: Optional[str] = Form(None),
    client_id: Optional[str] = Form(None),
    client_secret: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """OAuth2 token endpoint"""
    if grant_type == "authorization_code":
        # Handle authorization code grant
        if not code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Authorization code required"
            )

        # Find authorization code
        auth_code = db.query(models.OAuthAuthorizationCode).filter(
            models.OAuthAuthorizationCode.code == code
        ).first()

        if not auth_code or auth_code.expires_at < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid authorization code"
            )

        # Verify PKCE if present
        if auth_code.code_challenge:
            if not code_verifier:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Code verifier required"
                )
            if not verify_pkce(auth_code.code_challenge, code_verifier, auth_code.code_challenge_method):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid code verifier"
                )

        # Create access token
        access_token = models.OAuthAccessToken(
            client_id=auth_code.client_id,
            user_id=auth_code.user_id,
            scope=auth_code.scope
        )
        db.add(access_token)
        db.flush()

        # Create refresh token
        refresh_token_obj = models.OAuthRefreshToken(
            client_id=auth_code.client_id,
            user_id=auth_code.user_id,
            access_token_id=access_token.id,
            scope=auth_code.scope
        )
        db.add(refresh_token_obj)
        db.commit()

        return schemas.TokenResponse(
            access_token=str(access_token.id),  # In real implementation, this would be JWT
            refresh_token=str(refresh_token_obj.id),
            token_type="Bearer",
            expires_in=3600,
            scope=auth_code.scope
        )

    elif grant_type == "refresh_token":
        # Handle refresh token grant
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Refresh token required"
            )

        # Find refresh token
        refresh_token_obj = db.query(models.OAuthRefreshToken).filter(
            models.OAuthRefreshToken.token == refresh_token
        ).first()

        if not refresh_token_obj or refresh_token_obj.expires_at < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid refresh token"
            )

        # Create new access token
        access_token = models.OAuthAccessToken(
            client_id=refresh_token_obj.client_id,
            user_id=refresh_token_obj.user_id,
            scope=refresh_token_obj.scope
        )
        db.add(access_token)
        db.flush()

        # Update refresh token's access token reference
        refresh_token_obj.access_token_id = access_token.id
        db.commit()

        return schemas.TokenResponse(
            access_token=str(access_token.id),
            refresh_token=refresh_token,
            token_type="Bearer",
            expires_in=3600,
            scope=refresh_token_obj.scope
        )

    elif grant_type == "client_credentials":
        # Handle client credentials grant (simplified)
        # In real implementation, validate client credentials
        access_token = models.OAuthAccessToken(
            client_id=client_id,
            user_id=None,  # No user for client credentials
            scope=scope
        )
        db.add(access_token)
        db.commit()

        return schemas.TokenResponse(
            access_token=str(access_token.id),
            token_type="Bearer",
            expires_in=3600,
            scope=scope
        )

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported grant type"
        )

@router.post("/introspect")
async def introspect(
    token: str = Form(...),
    token_type_hint: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Token introspection endpoint"""
    # Find access token
    access_token = db.query(models.OAuthAccessToken).filter(
        models.OAuthAccessToken.token == token
    ).first()

    if not access_token or access_token.expires_at < datetime.utcnow():
        return schemas.TokenIntrospectionResponse(active=False)

    return schemas.TokenIntrospectionResponse(
        active=True,
        client_id=access_token.client.client_id if access_token.client else None,
        sub=str(access_token.user_id) if access_token.user_id else None,
        exp=int(access_token.expires_at.timestamp()),
        iat=int(access_token.created_at.timestamp()),
        scope=access_token.scope,
        token_type="Bearer",
        tenant_id=access_token.client.tenant_id if access_token.client else None
    )

@router.post("/revoke")
async def revoke(
    token: str = Form(...),
    token_type_hint: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Token revocation endpoint"""
    # Find and revoke access token
    access_token = db.query(models.OAuthAccessToken).filter(
        models.OAuthAccessToken.token == token
    ).first()

    if access_token:
        # Mark as expired (in real implementation, might delete or mark revoked)
        access_token.expires_at = datetime.utcnow()
        db.commit()

    # Find and revoke refresh token
    refresh_token = db.query(models.OAuthRefreshToken).filter(
        models.OAuthRefreshToken.token == token
    ).first()

    if refresh_token:
        refresh_token.revoked_at = datetime.utcnow()
        db.commit()

    return {"message": "Token revoked"}

@router.get("/.well-known/openid-configuration")
async def openid_configuration():
    """OpenID Connect discovery endpoint"""
    base_url = "http://localhost:8000"  # In real implementation, get from config

    return schemas.OIDCDiscoveryDocument(
        issuer=f"{base_url}",
        authorization_endpoint=f"{base_url}/oauth/v1/authorize",
        token_endpoint=f"{base_url}/oauth/v1/token",
        userinfo_endpoint=f"{base_url}/oauth/v1/userinfo",
        jwks_uri=f"{base_url}/oauth/v1/jwks",
        response_types_supported=["code", "token", "id_token"],
        subject_types_supported=["public"],
        id_token_signing_alg_values_supported=["RS256"],
        scopes_supported=["openid", "profile", "email", "read", "write"],
        token_endpoint_auth_methods_supported=["client_secret_basic", "client_secret_post"],
        claims_supported=["sub", "name", "email", "email_verified", "preferred_username"]
    )

@router.get("/jwks")
async def jwks():
    """JSON Web Key Set endpoint"""
    # In real implementation, return actual JWKS
    # For now, return empty set
    return schemas.JWKSet(keys=[])