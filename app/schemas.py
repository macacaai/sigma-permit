from pydantic import BaseModel, Field, field_validator
from typing import Optional, Any, Dict, Union, Literal
from datetime import datetime, timezone
from enum import Enum

# Tenant schemas
class TenantBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., min_length=1, max_length=50, pattern=r'^[a-z0-9-]+$')
    is_active: bool = True
    max_licenses: int = Field(..., gt=0)

class TenantCreate(TenantBase):
    pass

class TenantUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    slug: Optional[str] = Field(None, min_length=1, max_length=50, pattern=r'^[a-z0-9-]+$')
    is_active: Optional[bool] = None
    max_licenses: Optional[int] = Field(None, gt=0)

class Tenant(TenantBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True

# Template schemas
class TemplateBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    payload_schema: Optional[Dict[str, Any]] = None
    validation_rules: Optional[Dict[str, Any]] = None
    is_active: bool = True

class TemplateCreate(TemplateBase):
    pass

class TemplateUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    payload_schema: Optional[Dict[str, Any]] = None
    validation_rules: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class Template(TemplateBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True

# License schemas
class LicenseBase(BaseModel):
    license_key: str = Field(..., description="Public license key for customer")
    license_secret: str = Field(..., description="Private cryptographic key for server")
    tenant_id: str
    template_id: Optional[str] = None
    linked_subscription: Optional[str] = None  # Optional link to subscription
    issued_at: Optional[datetime] = None
    validity_days: Optional[int] = Field(None, gt=0, description="Number of days the license is valid")
    payload: Dict[str, Any]  # Contains custom license data

class LicenseCreate(BaseModel):
    tenant_id: str
    template_id: Optional[str] = None
    linked_subscription: Optional[str] = None  # Optional link to subscription
    issued_at: Optional[datetime] = None
    validity_days: Optional[int] = Field(None, gt=0, description="Number of days the license is valid")
    payload: Dict[str, Any]  # Contains custom license data

    @field_validator('issued_at', mode='before')
    @classmethod
    def parse_datetime(cls, v):
        if v is None:
            return v
        if isinstance(v, str):
            # Handle various datetime formats
            try:
                # Try standard ISO format first
                dt = datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                # Try alternative parsing
                if v.endswith('Z'):
                    v = v[:-1] + '+00:00'
                dt = datetime.fromisoformat(v)

            # Ensure the datetime has UTC timezone
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        return v

    @field_validator('linked_subscription', mode='after')
    @classmethod
    def validate_subscription_fields(cls, v, values):
        linked_subscription = v
        issued_at = values.data.get('issued_at')
        validity_days = values.data.get('validity_days')

        if linked_subscription:
            # If linked to subscription, issued_at and validity_days should be None
            if issued_at is not None or validity_days is not None:
                raise ValueError("When linked_subscription is provided, issued_at and validity_days must be None")
        else:
            # If not linked to subscription, issued_at and validity_days are required
            if issued_at is None or validity_days is None:
                raise ValueError("When linked_subscription is not provided, issued_at and validity_days are required")

        return v

class LicenseUpdate(BaseModel):
    tenant_id: Optional[str] = None
    template_id: Optional[str] = None
    linked_subscription: Optional[str] = None
    issued_at: Optional[datetime] = None
    validity_days: Optional[int] = Field(None, gt=0)
    payload: Optional[Dict[str, Any]] = None

    @field_validator('issued_at', mode='before')
    @classmethod
    def parse_datetime(cls, v):
        if v is None:
            return v
        if isinstance(v, str):
            # Handle various datetime formats
            try:
                # Try standard ISO format first
                dt = datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                # Try alternative parsing
                if v.endswith('Z'):
                    v = v[:-1] + '+00:00'
                dt = datetime.fromisoformat(v)

            # Ensure the datetime has UTC timezone
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        return v

    @field_validator('linked_subscription', mode='after')
    @classmethod
    def validate_subscription_fields(cls, v, values):
        linked_subscription = v
        issued_at = values.data.get('issued_at')
        validity_days = values.data.get('validity_days')

        if linked_subscription is not None:
            # If linked to subscription, issued_at and validity_days should be None
            if issued_at is not None or validity_days is not None:
                raise ValueError("When linked_subscription is provided, issued_at and validity_days must be None")
        # Note: For updates, we allow None values even without subscription link for partial updates

        return v

class License(LicenseBase):
    id: str

    class Config:
        from_attributes = True

# License response schema (excludes sensitive license_secret)
class LicenseResponse(BaseModel):
    id: str
    license_key: str = Field(..., description="Public license key for customer")
    tenant_id: str
    tenant_name: str = Field(..., description="Name of the associated tenant")
    template_id: Optional[str] = None
    linked_subscription: Optional[str] = None
    issued_at: Optional[datetime] = None
    validity_days: Optional[int] = Field(None, gt=0, description="Number of days the license is valid")
    payload: Dict[str, Any]  # Contains custom license data

    class Config:
        from_attributes = True

# Form schemas for UI
class LicenseForm(BaseModel):
    tenant_id: str
    template_id: Optional[str] = None
    linked_subscription: Optional[str] = None
    issued_at: Optional[datetime] = None  # Changed from issue_date to issued_at
    validity_days: Optional[int] = Field(None, gt=0, description="Number of days the license is valid")
    payload: Dict[str, Any]  # Custom license data

# User schemas
class UserBase(BaseModel):
    tenant_id: str = Field(..., description="Tenant ID the user belongs to")
    email: str = Field(..., description="User's email address")
    username: str = Field(..., min_length=3, max_length=50, pattern=r'^[a-zA-Z0-9_-]+$', description="Unique username within tenant")
    full_name: Optional[str] = Field(None, max_length=100, description="User's full name")
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = False

    # OAuth/Social login fields (for future use)
    oauth_provider: Optional[str] = Field(None, description="OAuth provider (google, github, etc.)")
    oauth_id: Optional[str] = Field(None, description="Provider's user ID")

    # SSO/SAML fields (for future use)
    sso_provider: Optional[str] = Field(None, description="SSO provider (okta, auth0, etc.)")
    sso_id: Optional[str] = Field(None, description="SSO user ID")

    # Profile fields
    avatar_url: Optional[str] = Field(None, description="User's avatar URL")
    bio: Optional[str] = Field(None, description="User biography")
    phone_number: Optional[str] = Field(None, description="User's phone number")

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="User's password")

class UserUpdate(BaseModel):
    tenant_id: Optional[str] = Field(None, description="Tenant ID the user belongs to")
    email: Optional[str] = Field(None, description="User's email address")
    username: Optional[str] = Field(None, min_length=3, max_length=50, pattern=r'^[a-zA-Z0-9_-]+$', description="Unique username within tenant")
    full_name: Optional[str] = Field(None, max_length=100, description="User's full name")
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    is_verified: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=8, description="New password")
    avatar_url: Optional[str] = Field(None, description="User's avatar URL")
    bio: Optional[str] = Field(None, description="User biography")
    phone_number: Optional[str] = Field(None, description="User's phone number")

class User(UserBase):
    id: str
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True

# Authentication schemas
class LoginRequest(BaseModel):
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="User password")

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: User

class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)

# Enhanced authentication schemas
class ForgotPasswordRequest(BaseModel):
    email: str = Field(..., description="User's email address")

class ResetPasswordRequest(BaseModel):
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, description="New password")

class VerifyEmailRequest(BaseModel):
    token: str = Field(..., description="Email verification token")

class ResendVerificationRequest(BaseModel):
    email: str = Field(..., description="User's email address")

class EnhancedTokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "Bearer"
    expires_in: Optional[int] = None
    scope: Optional[str] = None
    id_token: Optional[str] = None
    user: User  # Enhanced user info

# Pagination schemas
class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    size: int
    pages: int

# Enums for subscription models
class BillingInterval(str, Enum):
    monthly = "monthly"
    yearly = "yearly"

class SubscriptionStatus(str, Enum):
    active = "active"
    trialing = "trialing"
    past_due = "past_due"
    canceled = "canceled"

class FeatureType(str, Enum):
    boolean = "boolean"
    integer = "integer"
    string = "string"
    json = "json"

# Product schemas
class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    version: int = Field(1, ge=1)

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    version: Optional[int] = Field(None, ge=1)

class Product(ProductBase):
    id: str

    class Config:
        from_attributes = True

# PlanDefinition schemas
class PlanDefinitionBase(BaseModel):
    product_id: str
    name: str = Field(..., min_length=1, max_length=100)
    price: float = Field(..., ge=0)
    billing_interval: BillingInterval
    is_active: bool = True
    plan_metadata: Optional[Dict[str, Any]] = None

class PlanDefinitionCreate(PlanDefinitionBase):
    pass

class PlanDefinitionUpdate(BaseModel):
    product_id: Optional[str] = None
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    price: Optional[float] = Field(None, ge=0)
    billing_interval: Optional[BillingInterval] = None
    is_active: Optional[bool] = None
    plan_metadata: Optional[Dict[str, Any]] = None

class PlanDefinition(PlanDefinitionBase):
    id: str

    class Config:
        from_attributes = True

# FeatureDefinition schemas
class FeatureDefinitionBase(BaseModel):
    product_id: str
    key: str = Field(..., min_length=1, max_length=50)
    type: FeatureType
    default_value: Optional[Any] = None
    validation_rules: Optional[Dict[str, Any]] = None

class FeatureDefinitionCreate(FeatureDefinitionBase):
    pass

class FeatureDefinitionUpdate(BaseModel):
    product_id: Optional[str] = None
    key: Optional[str] = Field(None, min_length=1, max_length=50)
    type: Optional[FeatureType] = None
    default_value: Optional[Any] = None
    validation_rules: Optional[Dict[str, Any]] = None

class FeatureDefinition(FeatureDefinitionBase):
    id: str

    class Config:
        from_attributes = True

# PlanFeature schemas
class PlanFeatureBase(BaseModel):
    plan_id: str
    feature_id: str
    override_value: Optional[Any] = None
    constraints: Optional[Dict[str, Any]] = None

class PlanFeatureCreate(PlanFeatureBase):
    pass

class PlanFeatureUpdate(BaseModel):
    override_value: Optional[Any] = None
    constraints: Optional[Dict[str, Any]] = None

class PlanFeature(PlanFeatureBase):
    class Config:
        from_attributes = True

# Subscription schemas
class SubscriptionBase(BaseModel):
    tenant_id: str
    plan_id: str
    status: SubscriptionStatus
    start_date: datetime
    issue_date: datetime  # Date when subscription was issued
    end_date: Optional[datetime] = None
    validity_days: Optional[int] = None  # Calculated based on plan's billing interval
    auto_renew: bool = True
    payment_provider_id: Optional[str] = None

class SubscriptionCreate(BaseModel):
    tenant_id: str
    plan_id: str
    start_date: datetime
    auto_renew: bool = True
    payment_provider_id: Optional[str] = None
    # issue_date is set automatically to created_at

class SubscriptionUpdate(BaseModel):
    plan_id: Optional[str] = None
    status: Optional[SubscriptionStatus] = None
    start_date: Optional[datetime] = None
    issue_date: Optional[datetime] = None  # Allow editing issue_date
    end_date: Optional[datetime] = None
    auto_renew: Optional[bool] = None
    payment_provider_id: Optional[str] = None

class Subscription(SubscriptionBase):
    id: str

    class Config:
        from_attributes = True

# SubscriptionEntitlement schemas
class SubscriptionEntitlementBase(BaseModel):
    subscription_id: str
    feature_id: str
    effective_value: Any
    overridden: bool = False
    billing_interval: Optional[str] = None
    validity_days: Optional[int] = None

class SubscriptionEntitlementCreate(SubscriptionEntitlementBase):
    pass

class SubscriptionEntitlementUpdate(BaseModel):
    effective_value: Optional[Any] = None
    overridden: Optional[bool] = None

class SubscriptionEntitlement(SubscriptionEntitlementBase):
    class Config:
        from_attributes = True

# OAuth2/OIDC schemas
class OAuthClientBase(BaseModel):
    client_name: str = Field(..., min_length=1, max_length=255)
    client_type: str = Field(..., pattern=r'^(confidential|public)$')
    redirect_uris: Optional[list[str]] = None
    allowed_grant_types: list[str]
    allowed_scopes: Optional[list[str]] = None
    logo_uri: Optional[str] = None
    website_uri: Optional[str] = None
    tenant_id: Optional[str] = None
    is_active: bool = True

class OAuthClientCreate(OAuthClientBase):
    pass

class OAuthClientUpdate(BaseModel):
    client_name: Optional[str] = Field(None, min_length=1, max_length=255)
    client_type: Optional[str] = Field(None, pattern=r'^(confidential|public)$')
    redirect_uris: Optional[list[str]] = None
    allowed_grant_types: Optional[list[str]] = None
    allowed_scopes: Optional[list[str]] = None
    logo_uri: Optional[str] = None
    website_uri: Optional[str] = None
    tenant_id: Optional[str] = None
    is_active: Optional[bool] = None

class OAuthClient(OAuthClientBase):
    id: str
    client_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# OAuth2 Token schemas
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "Bearer"
    expires_in: Optional[int] = None
    scope: Optional[str] = None
    id_token: Optional[str] = None

class TokenIntrospectionResponse(BaseModel):
    active: bool
    client_id: Optional[str] = None
    sub: Optional[str] = None
    exp: Optional[int] = None
    iat: Optional[int] = None
    scope: Optional[str] = None
    token_type: Optional[str] = None
    tenant_id: Optional[str] = None

# OAuth2 Authorization Request
class AuthorizationRequest(BaseModel):
    response_type: str = Field(..., pattern=r'^(code|token|id_token)$')
    client_id: str
    redirect_uri: Optional[str] = None
    scope: Optional[str] = None
    state: Optional[str] = None
    nonce: Optional[str] = None
    code_challenge: Optional[str] = None
    code_challenge_method: Optional[str] = Field(None, pattern=r'^(S256|plain)$')

# OAuth2 Token Request
class AuthorizationCodeGrant(BaseModel):
    grant_type: Literal["authorization_code"]
    code: str
    redirect_uri: Optional[str] = None
    code_verifier: Optional[str] = None

class ClientCredentialsGrant(BaseModel):
    grant_type: Literal["client_credentials"]
    scope: Optional[str] = None

class RefreshTokenGrant(BaseModel):
    grant_type: Literal["refresh_token"]
    refresh_token: str
    scope: Optional[str] = None

# OIDC Discovery Document
class OIDCDiscoveryDocument(BaseModel):
    issuer: str
    authorization_endpoint: str
    token_endpoint: str
    userinfo_endpoint: Optional[str] = None
    jwks_uri: str
    response_types_supported: list[str]
    subject_types_supported: list[str]
    id_token_signing_alg_values_supported: list[str]
    scopes_supported: list[str]
    token_endpoint_auth_methods_supported: list[str]
    claims_supported: list[str]

# JWK Set
class JWK(BaseModel):
    kty: str
    use: str
    kid: str
    n: Optional[str] = None
    e: Optional[str] = None
    x5c: Optional[list[str]] = None

class JWKSet(BaseModel):
    keys: list[JWK]

# Session Management Schemas
class SessionBase(BaseModel):
    device_info: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    location: Optional[Dict[str, Any]] = None
    is_active: bool = True

class SessionCreate(SessionBase):
    pass

class SessionUpdate(BaseModel):
    is_active: Optional[bool] = None
    device_info: Optional[Dict[str, Any]] = None

class Session(SessionBase):
    id: str
    user_id: str
    session_id: str
    created_at: datetime
    last_activity: datetime
    expires_at: datetime

    class Config:
        from_attributes = True

class DeviceInfo(BaseModel):
    device_id: Optional[str] = None
    device_name: Optional[str] = None
    device_type: Optional[str] = None  # desktop, mobile, tablet
    os: Optional[str] = None
    browser: Optional[str] = None
    is_trusted: bool = False

class SessionSecurityConfig(BaseModel):
    max_concurrent_sessions: int = 5
    session_timeout_minutes: int = 480  # 8 hours
    require_device_trust: bool = False
    allow_session_sharing: bool = False

# RBAC Schemas
class PermissionBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    resource: str = Field(..., min_length=1, max_length=100)
    action: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None

class PermissionCreate(PermissionBase):
    pass

class PermissionUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    resource: Optional[str] = Field(None, min_length=1, max_length=100)
    action: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = None

class Permission(PermissionBase):
    id: str
    is_system: bool
    created_at: datetime

    class Config:
        from_attributes = True

class RoleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    tenant_id: Optional[str] = None

class RoleCreate(RoleBase):
    pass

class RoleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    tenant_id: Optional[str] = None

class Role(RoleBase):
    id: str
    is_system: bool
    created_at: datetime
    updated_at: datetime
    permissions: list[Permission] = []

    class Config:
        from_attributes = True
