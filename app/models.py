from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON, Numeric, Enum, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.sqlite import TEXT
import uuid
import bcrypt
from app.database import Base

# Import the user_roles table from rbac models
from app.models.rbac import user_roles

class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    max_licenses = Column(Integer, nullable=False)

    # Relationships
    licenses = relationship("License", back_populates="tenant", cascade="all, delete-orphan")
    subscriptions = relationship("Subscription", back_populates="tenant", cascade="all, delete-orphan")
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")

class Template(Base):
    __tablename__ = "templates"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    payload_schema = Column(JSON)
    validation_rules = Column(JSON)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class License(Base):
    __tablename__ = "licenses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    license_key = Column(String, unique=True, nullable=False)  # Public license key for customer
    license_secret = Column(Text, nullable=False)  # Private cryptographic key for server
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    template_id = Column(String(36), ForeignKey("templates.id"), nullable=True)
    linked_subscription = Column(String(36), ForeignKey("subscriptions.id"), nullable=True)  # Optional link to subscription
    issued_at = Column(DateTime(timezone=True), nullable=True)
    validity_days = Column(Integer, nullable=True)  # Number of days the license is valid
    payload = Column(JSON, nullable=False)  # Contains custom license data

    # Relationships
    tenant = relationship("Tenant", back_populates="licenses")
    template = relationship("Template", cascade="all")
    subscription = relationship("Subscription", back_populates="licenses")

class MasterKey(Base):
    __tablename__ = "master_keys"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    public_key = Column(Text, nullable=False)  # Base64-encoded RSA public key
    private_key = Column(Text, nullable=False)  # Base64-encoded RSA private key
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    email = Column(String, nullable=False, index=True)
    username = Column(String, nullable=False, index=True)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)

    # OAuth/Social login fields (for future use)
    oauth_provider = Column(String, nullable=True)  # google, github, etc.
    oauth_id = Column(String, nullable=True)  # Provider's user ID
    oauth_access_token = Column(Text, nullable=True)
    oauth_refresh_token = Column(Text, nullable=True)

    # Refresh token for JWT authentication
    refresh_token = Column(Text, nullable=True)

    # SSO/SAML fields (for future use)
    sso_provider = Column(String, nullable=True)  # okta, auth0, etc.
    sso_id = Column(String, nullable=True)
    sso_metadata = Column(JSON, nullable=True)  # Additional SSO data
    
    # IAM Extension fields (placeholder for future use)
    email_verified = Column(Boolean, default=False)
    phone_verified = Column(Boolean, default=False)
    require_password_change = Column(Boolean, default=False)
    password_expires_at = Column(DateTime(timezone=True), nullable=True)
    account_locked_until = Column(DateTime(timezone=True), nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    profile_visibility = Column(Enum('public', 'private', 'organization', name='profile_visibility_enum'), default='organization')
    preferred_language = Column(String(10), default='en')
    timezone = Column(String(50), default='UTC')
    email_verified_at = Column(DateTime(timezone=True), nullable=True)
    phone_verified_at = Column(DateTime(timezone=True), nullable=True)
    last_password_change = Column(DateTime(timezone=True), nullable=True)
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    # Profile fields
    avatar_url = Column(String, nullable=True)
    bio = Column(Text, nullable=True)
    phone_number = Column(String, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

    # IAM Relationships
    social_connections = relationship("SocialConnection", back_populates="user", cascade="all, delete-orphan")
    roles = relationship("Role", secondary=user_roles, back_populates="users",
                        primaryjoin="User.id == user_roles.c.user_id",
                        secondaryjoin="Role.id == user_roles.c.role_id")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    user_extension = relationship("UserExtension", back_populates="user", uselist=False, cascade="all, delete-orphan")
    external_identities = relationship("ExternalIdentity", back_populates="user", cascade="all, delete-orphan")
    oauth_authorized_clients = relationship("OAuthClient", secondary="oauth_client_users", back_populates="authorized_users")

    # Relationships
    tenant = relationship("Tenant", back_populates="users")

    __table_args__ = (
        UniqueConstraint('tenant_id', 'username', name='uq_user_tenant_username'),
        UniqueConstraint('tenant_id', 'email', name='uq_user_tenant_email'),
    )

    def set_password(self, password: str):
        """Hash and set the user's password"""
        self.hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def verify_password(self, password: str) -> bool:
        """Verify a password against the hashed password"""
        return bcrypt.checkpw(password.encode('utf-8'), self.hashed_password.encode('utf-8'))

class Product(Base):
    __tablename__ = "products"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    version = Column(Integer, nullable=False, default=1)

    # Relationships
    plans = relationship("PlanDefinition", back_populates="product", cascade="all, delete-orphan")
    features = relationship("FeatureDefinition", back_populates="product", cascade="all, delete-orphan")

class PlanDefinition(Base):
    __tablename__ = "plan_definitions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    product_id = Column(String(36), ForeignKey("products.id"), nullable=False)
    name = Column(String, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    billing_interval = Column(Enum('monthly', 'yearly', name='billing_interval_enum'), nullable=False)
    is_active = Column(Boolean, default=True)
    plan_metadata = Column(JSON)

    # Relationships
    product = relationship("Product", back_populates="plans")
    plan_features = relationship("PlanFeature", back_populates="plan", cascade="all, delete-orphan")
    subscriptions = relationship("Subscription", back_populates="plan", cascade="all, delete-orphan")

class FeatureDefinition(Base):
    __tablename__ = "feature_definitions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    product_id = Column(String(36), ForeignKey("products.id"), nullable=False)
    key = Column(String, nullable=False)
    type = Column(Enum('boolean', 'integer', 'string', 'json', name='feature_type_enum'), nullable=False)
    default_value = Column(JSON)
    validation_rules = Column(JSON)

    # Relationships
    product = relationship("Product", back_populates="features")
    plan_features = relationship("PlanFeature", back_populates="feature", cascade="all, delete-orphan")
    subscription_entitlements = relationship("SubscriptionEntitlement", back_populates="feature", cascade="all, delete-orphan")

class PlanFeature(Base):
    __tablename__ = "plan_features"

    plan_id = Column(String(36), ForeignKey("plan_definitions.id"), primary_key=True)
    feature_id = Column(String(36), ForeignKey("feature_definitions.id"), primary_key=True)
    override_value = Column(JSON)
    constraints = Column(JSON)

    # Relationships
    plan = relationship("PlanDefinition", back_populates="plan_features")
    feature = relationship("FeatureDefinition", back_populates="plan_features")

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    plan_id = Column(String(36), ForeignKey("plan_definitions.id"), nullable=False)
    status = Column(Enum('active', 'trialing', 'past_due', 'canceled', name='subscription_status_enum'), nullable=False)
    start_date = Column(DateTime(timezone=True), nullable=False)
    issue_date = Column(DateTime(timezone=True), server_default=func.now())  # Date when subscription was issued
    end_date = Column(DateTime(timezone=True), nullable=True)
    auto_renew = Column(Boolean, default=True)
    payment_provider_id = Column(String)

    # Relationships
    tenant = relationship("Tenant", back_populates="subscriptions")
    plan = relationship("PlanDefinition", back_populates="subscriptions")
    entitlements = relationship("SubscriptionEntitlement", back_populates="subscription", cascade="all, delete-orphan")
    licenses = relationship("License", back_populates="subscription", cascade="all, delete-orphan")

class SubscriptionEntitlement(Base):
    __tablename__ = "subscription_entitlements"

    subscription_id = Column(String(36), ForeignKey("subscriptions.id"), primary_key=True)
    feature_id = Column(String(36), ForeignKey("feature_definitions.id"), primary_key=True)
    effective_value = Column(JSON, nullable=False)
    overridden = Column(Boolean, default=False)

    # Relationships
    subscription = relationship("Subscription", back_populates="entitlements")
    feature = relationship("FeatureDefinition", back_populates="subscription_entitlements")
