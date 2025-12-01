# OAuth2 Models for Sigma IAM
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, JSON, Enum, Integer, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.database import Base

# Association table for OAuth client users
oauth_client_users = Table(
    'oauth_client_users',
    Base.metadata,
    Column('user_id', String(36), ForeignKey('users.id'), primary_key=True),
    Column('client_id', String(36), ForeignKey('oauth_clients.id'), primary_key=True),
    Column('granted_at', DateTime(timezone=True), server_default=func.now()),
    Column('scope', Text),
    Column('expires_at', DateTime(timezone=True)),
    extend_existing=True
)

class OAuthClient(Base):
    __tablename__ = "oauth_clients"
    __table_args__ = {'extend_existing': True}

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    client_id = Column(String(100), unique=True, nullable=False, index=True)
    client_secret_hash = Column(String(255), nullable=True)
    client_name = Column(String(255), nullable=False)
    client_type = Column(Enum('confidential', 'public', name='client_type_enum'), nullable=False)
    redirect_uris = Column(JSON, nullable=True)
    allowed_grant_types = Column(JSON, nullable=False)
    allowed_scopes = Column(JSON, nullable=True)
    logo_uri = Column(String(500), nullable=True)
    website_uri = Column(String(500), nullable=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    authorization_codes = relationship("OAuthAuthorizationCode", back_populates="client", cascade="all, delete-orphan")
    access_tokens = relationship("OAuthAccessToken", back_populates="client", cascade="all, delete-orphan")
    refresh_tokens = relationship("OAuthRefreshToken", back_populates="client", cascade="all, delete-orphan")
    authorized_users = relationship("User", secondary=oauth_client_users, back_populates="oauth_authorized_clients")

class OAuthAuthorizationCode(Base):
    __tablename__ = "oauth_authorization_codes"
    __table_args__ = {'extend_existing': True}

    code = Column(String(100), primary_key=True, index=True)
    client_id = Column(String(36), ForeignKey("oauth_clients.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    redirect_uri = Column(String(500), nullable=True)
    scope = Column(Text, nullable=True)
    code_challenge = Column(String(128), nullable=True)
    code_challenge_method = Column(String(10), nullable=True)
    nonce = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    client = relationship("OAuthClient", back_populates="authorization_codes")
    user = relationship("User")

class OAuthAccessToken(Base):
    __tablename__ = "oauth_access_tokens"
    __table_args__ = {'extend_existing': True}

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    token = Column(String(100), unique=True, nullable=False, index=True)
    client_id = Column(String(36), ForeignKey("oauth_clients.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    scope = Column(Text, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    client = relationship("OAuthClient", back_populates="access_tokens")
    user = relationship("User")
    refresh_tokens = relationship("OAuthRefreshToken", back_populates="access_token")

class OAuthRefreshToken(Base):
    __tablename__ = "oauth_refresh_tokens"
    __table_args__ = {'extend_existing': True}

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    token = Column(String(100), unique=True, nullable=False, index=True)
    client_id = Column(String(36), ForeignKey("oauth_clients.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    access_token_id = Column(String(36), ForeignKey("oauth_access_tokens.id"), nullable=True)
    scope = Column(Text, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    revoked_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    client = relationship("OAuthClient", back_populates="refresh_tokens")
    user = relationship("User")
    access_token = relationship("OAuthAccessToken", back_populates="refresh_tokens")

class SocialConnection(Base):
    __tablename__ = "social_connections"
    __table_args__ = {'extend_existing': True}

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    provider = Column(String(50), nullable=False)  # google, github, facebook, etc.
    provider_user_id = Column(String(255), nullable=False)
    provider_username = Column(String(255), nullable=True)
    provider_email = Column(String(255), nullable=True)
    provider_name = Column(String(255), nullable=True)
    provider_avatar_url = Column(String(500), nullable=True)
    access_token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    profile_data = Column(JSON, nullable=True)
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="social_connections")

    __table_args__ = (
        # Ensure uniqueness per provider per external user
        {'extend_existing': True}
    )

class UserExtension(Base):
    __tablename__ = "user_extensions"
    __table_args__ = {'extend_existing': True}

    user_id = Column(String(36), ForeignKey("users.id"), primary_key=True)
    email_verified = Column(Boolean, default=False)
    phone_verified = Column(Boolean, default=False)
    
    # Account security
    require_password_change = Column(Boolean, default=False)
    password_expires_at = Column(DateTime(timezone=True), nullable=True)
    account_locked_until = Column(DateTime(timezone=True), nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    
    # Privacy and preferences
    profile_visibility = Column(Enum('public', 'private', 'organization', name='profile_visibility_enum'), default='organization')
    preferred_language = Column(String(10), default='en')
    timezone = Column(String(50), default='UTC')
    
    # Timestamps
    email_verified_at = Column(DateTime(timezone=True), nullable=True)
    phone_verified_at = Column(DateTime(timezone=True), nullable=True)
    last_password_change = Column(DateTime(timezone=True), nullable=True)
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="user_extension")