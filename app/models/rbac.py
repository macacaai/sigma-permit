# RBAC Models for Sigma IAM
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, JSON, Table, Enum, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.database import Base

# Association tables
role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', String(36), ForeignKey('roles.id'), primary_key=True),
    Column('permission_id', String(36), ForeignKey('permissions.id'), primary_key=True),
    Column('granted_at', DateTime(timezone=True), server_default=func.now()),
    Column('granted_by', String(36), ForeignKey('users.id')),
    extend_existing=True
)

user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', String(36), ForeignKey('users.id'), primary_key=True),
    Column('role_id', String(36), ForeignKey('roles.id'), primary_key=True),
    Column('assigned_by', String(36), ForeignKey('users.id')),
    Column('expires_at', DateTime(timezone=True)),
    Column('created_at', DateTime(timezone=True), server_default=func.now()),
    extend_existing=True
)

class Role(Base):
    __tablename__ = "roles"
    __table_args__ = {'extend_existing': True}

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    is_system = Column(Boolean, default=False)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")
    users = relationship("User", secondary=user_roles, back_populates="roles",
                        primaryjoin="Role.id == user_roles.c.role_id",
                        secondaryjoin="User.id == user_roles.c.user_id")

    __table_args__ = (UniqueConstraint('name', 'tenant_id', name='uq_role_name_tenant'),)

class Permission(Base):
    __tablename__ = "permissions"
    __table_args__ = {'extend_existing': True}

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    name = Column(String(100), nullable=False)
    resource = Column(String(100), nullable=False)
    action = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    is_system = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")

    __table_args__ = (UniqueConstraint('resource', 'action', name='uq_permission_resource_action'),)

class UserSession(Base):
    __tablename__ = "user_sessions"
    __table_args__ = {'extend_existing': True}

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    session_id = Column(String(100), unique=True, nullable=False, index=True)
    device_info = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(Text, nullable=True)
    location = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)

    # Relationships
    user = relationship("User", back_populates="sessions")

class AuditLog(Base):
    __tablename__ = "audit_log"
    __table_args__ = {'extend_existing': True}

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    session_id = Column(String(36), ForeignKey("user_sessions.id"), nullable=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=True)
    event_type = Column(String(50), nullable=False)
    event_category = Column(String(50), nullable=False)
    resource = Column(String(100), nullable=True)
    resource_id = Column(String(36), nullable=True)
    action = Column(String(50), nullable=True)
    success = Column(Boolean, nullable=False)
    error_message = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    request_id = Column(String(100), nullable=True)
    event_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class IdentityProvider(Base):
    __tablename__ = "identity_providers"
    __table_args__ = {'extend_existing': True}

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    name = Column(String(100), nullable=False)
    type = Column(Enum('saml', 'oidc', 'ldap', 'active_directory', name='identity_provider_type_enum'), nullable=False)
    configuration = Column(JSON, nullable=False)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    external_identities = relationship("ExternalIdentity", back_populates="identity_provider")

    __table_args__ = (UniqueConstraint('name', 'tenant_id', name='uq_identity_provider_name_tenant'),)

class ExternalIdentity(Base):
    __tablename__ = "external_identities"
    __table_args__ = {'extend_existing': True}

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    identity_provider_id = Column(String(36), ForeignKey("identity_providers.id"), nullable=False)
    external_user_id = Column(String(255), nullable=False)
    external_username = Column(String(255), nullable=True)
    external_email = Column(String(255), nullable=True)
    external_groups = Column(JSON, nullable=True)
    attributes = Column(JSON, nullable=True)
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="external_identities")
    identity_provider = relationship("IdentityProvider", back_populates="external_identities")

    __table_args__ = (
        UniqueConstraint('identity_provider_id', 'external_user_id', name='uq_external_identity_provider_user'),
    )