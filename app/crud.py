from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from uuid import UUID, uuid4
from app import models, schemas
from app.crypto_utils import generate_license_keypair, der_to_pem_public_key

# Tenant CRUD
def get_tenant(db: Session, tenant_id: UUID) -> Optional[models.Tenant]:
    return db.query(models.Tenant).filter(models.Tenant.id == str(tenant_id)).first()

def get_tenant_by_slug(db: Session, slug: str) -> Optional[models.Tenant]:
    return db.query(models.Tenant).filter(models.Tenant.slug == slug).first()

def get_tenants(db: Session, skip: int = 0, limit: int = 100) -> List[models.Tenant]:
    return db.query(models.Tenant).offset(skip).limit(limit).all()

def create_tenant(db: Session, tenant: schemas.TenantCreate) -> models.Tenant:
    db_tenant = models.Tenant(**tenant.model_dump())
    db.add(db_tenant)
    db.commit()
    db.refresh(db_tenant)
    return db_tenant

def update_tenant(db: Session, tenant_id: UUID, tenant_update: schemas.TenantUpdate) -> Optional[models.Tenant]:
    db_tenant = db.query(models.Tenant).filter(models.Tenant.id == str(tenant_id)).first()
    if db_tenant:
        update_data = tenant_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_tenant, field, value)
        db.commit()
        db.refresh(db_tenant)
    return db_tenant

def delete_tenant(db: Session, tenant_id: UUID) -> bool:
    db_tenant = db.query(models.Tenant).filter(models.Tenant.id == str(tenant_id)).first()
    if db_tenant:
        db.delete(db_tenant)
        db.commit()
        return True
    return False

# Template CRUD
def get_template(db: Session, template_id: UUID) -> Optional[models.Template]:
    return db.query(models.Template).filter(models.Template.id == str(template_id)).first()

def get_templates(db: Session, skip: int = 0, limit: int = 100) -> List[models.Template]:
    return db.query(models.Template).offset(skip).limit(limit).all()

def create_template(db: Session, template: schemas.TemplateCreate) -> models.Template:
    db_template = models.Template(**template.model_dump())
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template

def update_template(db: Session, template_id: UUID, template_update: schemas.TemplateUpdate) -> Optional[models.Template]:
    db_template = db.query(models.Template).filter(models.Template.id == str(template_id)).first()
    if db_template:
        update_data = template_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_template, field, value)
        db.commit()
        db.refresh(db_template)
    return db_template

def delete_template(db: Session, template_id: UUID) -> bool:
    db_template = db.query(models.Template).filter(models.Template.id == str(template_id)).first()
    if db_template:
        db.delete(db_template)
        db.commit()
        return True
    return False

# License CRUD
def get_license(db: Session, license_id: UUID) -> Optional[models.License]:
    return db.query(models.License).filter(models.License.id == str(license_id)).first()

def get_licenses(db: Session, skip: int = 0, limit: int = 100, tenant_id: Optional[UUID] = None) -> List[models.License]:
    query = db.query(models.License)
    if tenant_id:
        query = query.filter(models.License.tenant_id == str(tenant_id))
    return query.offset(skip).limit(limit).all()

def create_license(db: Session, license: schemas.LicenseCreate) -> models.License:
    # Generate cryptographic key pair
    license_key, license_secret = generate_license_keypair()

    # Create license with generated keys
    license_data = license.model_dump()
    # Convert UUID objects to strings for database compatibility
    if 'tenant_id' in license_data and isinstance(license_data['tenant_id'], UUID):
        license_data['tenant_id'] = str(license_data['tenant_id'])
    if 'template_id' in license_data and license_data['template_id'] is not None and isinstance(license_data['template_id'], UUID):
        license_data['template_id'] = str(license_data['template_id'])
    if 'linked_subscription' in license_data and license_data['linked_subscription'] is not None and isinstance(license_data['linked_subscription'], UUID):
        license_data['linked_subscription'] = str(license_data['linked_subscription'])

    # If linked to subscription, use subscription's dates
    if license_data.get('linked_subscription'):
        subscription = get_subscription(db, license_data['linked_subscription'])
        if not subscription:
            raise ValueError("Linked subscription not found")

        # Use subscription's issue_date as license issued_at
        license_data['issued_at'] = subscription.issue_date

        # Calculate validity_days from subscription end_date - issue_date
        if subscription.end_date:
            from datetime import timedelta
            validity_period = subscription.end_date - subscription.issue_date
            license_data['validity_days'] = validity_period.days
        else:
            # If no end_date, calculate based on plan's billing interval and issue_date
            plan = get_plan_definition(db, subscription.plan_id)
            if plan and subscription.issue_date:
                if plan.billing_interval == 'monthly':
                    # Use actual number of days in the month of issue_date
                    import calendar
                    year = subscription.issue_date.year
                    month = subscription.issue_date.month
                    license_data['validity_days'] = calendar.monthrange(year, month)[1]
                elif plan.billing_interval == 'yearly':
                    # Calculate days from issue_date to same date next year
                    from datetime import timedelta
                    next_year_date = subscription.issue_date.replace(year=subscription.issue_date.year + 1)
                    license_data['validity_days'] = (next_year_date - subscription.issue_date).days
                else:
                    license_data['validity_days'] = 30  # Default to monthly
            else:
                license_data['validity_days'] = 30  # Default fallback

    license_data.update({
        'license_key': license_key,
        'license_secret': license_secret
    })

    db_license = models.License(**license_data)
    db.add(db_license)
    db.commit()
    db.refresh(db_license)
    return db_license

def update_license(db: Session, license_id: UUID, license_update: schemas.LicenseUpdate) -> Optional[models.License]:
    db_license = db.query(models.License).filter(models.License.id == str(license_id)).first()
    if db_license:
        update_data = license_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_license, field, value)
        db.commit()
        db.refresh(db_license)
    return db_license

def delete_license(db: Session, license_id: UUID) -> bool:
    db_license = db.query(models.License).filter(models.License.id == str(license_id)).first()
    if db_license:
        db.delete(db_license)
        db.commit()
        return True
    return False

def get_tenant_license_count(db: Session, tenant_id: UUID) -> int:
    return db.query(models.License).filter(models.License.tenant_id == str(tenant_id)).count()

def get_licenses_with_tenant(db: Session, skip: int = 0, limit: int = 100, tenant_id: Optional[UUID] = None) -> List[schemas.LicenseResponse]:
    """Get licenses with tenant names included."""
    from sqlalchemy.orm import joinedload

    query = db.query(models.License).options(joinedload(models.License.tenant))
    if tenant_id:
        query = query.filter(models.License.tenant_id == str(tenant_id))

    licenses = query.offset(skip).limit(limit).all()

    # Convert to LicenseResponse with tenant names (keys are base64-encoded DER)
    result = []
    for license in licenses:
        # Calculate validity_days dynamically for licenses linked to subscriptions
        validity_days = license.validity_days
        if license.linked_subscription:
            subscription = get_subscription(db, license.linked_subscription)
            if subscription:
                # Use same logic as create_license
                if subscription.end_date:
                    from datetime import timedelta
                    validity_period = subscription.end_date - subscription.issue_date
                    validity_days = validity_period.days
                elif subscription.plan and subscription.issue_date:
                    plan = get_plan_definition(db, subscription.plan_id)
                    if plan:
                        if plan.billing_interval == 'monthly':
                            # Use actual number of days in the month of issue_date
                            import calendar
                            year = subscription.issue_date.year
                            month = subscription.issue_date.month
                            validity_days = calendar.monthrange(year, month)[1]
                        elif plan.billing_interval == 'yearly':
                            # Calculate days from issue_date to same date next year
                            from datetime import timedelta
                            next_year_date = subscription.issue_date.replace(year=subscription.issue_date.year + 1)
                            validity_days = (next_year_date - subscription.issue_date).days

        license_dict = {
            "id": license.id,
            "license_key": license.license_key,  # Base64-encoded DER as-is
            "tenant_id": license.tenant_id,
            "tenant_name": license.tenant.name if license.tenant else "Unknown Tenant",
            "template_id": license.template_id,
            "linked_subscription": license.linked_subscription,
            "issued_at": license.issued_at,
            "validity_days": validity_days,
            "payload": license.payload
        }
        result.append(schemas.LicenseResponse(**license_dict))

    return result

def get_license_with_tenant(db: Session, license_id: UUID) -> Optional[schemas.LicenseResponse]:
    """Get a single license with tenant name included."""
    from sqlalchemy.orm import joinedload

    license = db.query(models.License).options(joinedload(models.License.tenant)).filter(
        models.License.id == str(license_id)
    ).first()

    if not license:
        return None

    # Calculate validity_days dynamically for licenses linked to subscriptions
    validity_days = license.validity_days
    if license.linked_subscription:
        subscription = get_subscription(db, license.linked_subscription)
        if subscription:
            # Use same logic as create_license
            if subscription.end_date:
                from datetime import timedelta
                validity_period = subscription.end_date - subscription.issue_date
                validity_days = validity_period.days
            elif subscription.plan and subscription.issue_date:
                plan = get_plan_definition(db, subscription.plan_id)
                if plan:
                    if plan.billing_interval == 'monthly':
                        # Use actual number of days in the month of issue_date
                        import calendar
                        year = subscription.issue_date.year
                        month = subscription.issue_date.month
                        validity_days = calendar.monthrange(year, month)[1]
                    elif plan.billing_interval == 'yearly':
                        # Calculate days from issue_date to same date next year
                        from datetime import timedelta
                        next_year_date = subscription.issue_date.replace(year=subscription.issue_date.year + 1)
                        validity_days = (next_year_date - subscription.issue_date).days

    # Keys are base64-encoded DER as-is
    license_dict = {
        "id": license.id,
        "license_key": license.license_key,  # Base64-encoded DER as-is
        "tenant_id": license.tenant_id,
        "tenant_name": license.tenant.name if license.tenant else "Unknown Tenant",
        "template_id": license.template_id,
        "linked_subscription": license.linked_subscription,
        "issued_at": license.issued_at,
        "validity_days": validity_days,
        "payload": license.payload
    }

    return schemas.LicenseResponse(**license_dict)

# Helper function to create license from form data
def create_license_from_form(db: Session, tenant_id: UUID, issued_at, validity_days: int, custom_payload: dict) -> models.License:
    # Generate cryptographic key pair
    license_key, license_secret = generate_license_keypair()

    # Create license data with string UUIDs
    license_data = {
        'id': str(uuid.uuid4()),
        'license_key': license_key,
        'license_secret': license_secret,
        'tenant_id': str(tenant_id),
        'template_id': None,
        'issued_at': issued_at,
        'validity_days': validity_days,
        'payload': custom_payload
    }

    db_license = models.License(**license_data)
    db.add(db_license)
    db.commit()
    db.refresh(db_license)
    return db_license

# Helper function to update license from form data
def update_license_from_form(db: Session, license_id: UUID, tenant_id: UUID, issued_at, validity_days: int, custom_payload: dict) -> Optional[models.License]:
    license_update = schemas.LicenseUpdate(
        tenant_id=tenant_id,
        issued_at=issued_at,
        validity_days=validity_days,
        payload=custom_payload
    )
    return update_license(db, license_id, license_update)

# User CRUD
def get_user(db: Session, user_id: UUID) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.id == str(user_id)).first()

def get_user_by_email(db: Session, email: str, tenant_id: Optional[str] = None) -> Optional[models.User]:
    query = db.query(models.User).filter(models.User.email == email)
    if tenant_id:
        query = query.filter(models.User.tenant_id == tenant_id)
    return query.first()

def get_user_by_username(db: Session, username: str, tenant_id: Optional[str] = None) -> Optional[models.User]:
    query = db.query(models.User).filter(models.User.username == username)
    if tenant_id:
        query = query.filter(models.User.tenant_id == tenant_id)
    return query.first()

def get_user_by_username_or_email(db: Session, username_or_email: str, tenant_id: Optional[str] = None) -> Optional[models.User]:
    """Get user by username or email (for login)"""
    query = db.query(models.User).filter(
        (models.User.username == username_or_email) | (models.User.email == username_or_email)
    )
    if tenant_id:
        query = query.filter(models.User.tenant_id == tenant_id)
    return query.first()

def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[models.User]:
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    db_user = models.User(
        tenant_id=user.tenant_id,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        is_verified=user.is_verified,
        oauth_provider=user.oauth_provider,
        oauth_id=user.oauth_id,
        sso_provider=user.sso_provider,
        sso_id=user.sso_id,
        avatar_url=user.avatar_url,
        bio=user.bio,
        phone_number=user.phone_number
    )
    db_user.set_password(user.password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user_id: UUID, user_update: schemas.UserUpdate) -> Optional[models.User]:
    db_user = db.query(models.User).filter(models.User.id == str(user_id)).first()
    if db_user:
        update_data = user_update.model_dump(exclude_unset=True)
        if 'password' in update_data:
            db_user.set_password(update_data.pop('password'))

        for field, value in update_data.items():
            setattr(db_user, field, value)

        db.commit()
        db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: UUID) -> bool:
    db_user = db.query(models.User).filter(models.User.id == str(user_id)).first()
    if db_user:
        db.delete(db_user)
        db.commit()
        return True
    return False

def authenticate_user(db: Session, username_or_email: str, password: str, tenant_id: Optional[str] = None) -> Optional[models.User]:
    """Authenticate a user with username/email and password"""
    user = get_user_by_username_or_email(db, username_or_email, tenant_id)
    if user and user.verify_password(password) and user.is_active:
        # Update last login
        user.last_login = models.func.now()
        db.commit()
        return user
    return None

def create_default_admin(db: Session) -> models.User:
    """Create a default admin user if no admin exists"""
    # Check if any admin user exists
    admin_exists = db.query(models.User).filter(models.User.is_superuser == True).first()
    if admin_exists:
        return admin_exists

    # Create default admin user
    admin_user = models.User(
        email="admin@sigma-permit.com",
        username="admin",
        full_name="System Administrator",
        is_active=True,
        is_superuser=True,
        is_verified=True
    )
    admin_user.set_password("admin123")  # Default password

    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    return admin_user

# Product CRUD
def get_product(db: Session, product_id: UUID) -> Optional[models.Product]:
    return db.query(models.Product).filter(models.Product.id == str(product_id)).first()

def get_products(db: Session, skip: int = 0, limit: int = 100) -> List[models.Product]:
    return db.query(models.Product).offset(skip).limit(limit).all()

def create_product(db: Session, product: schemas.ProductCreate) -> models.Product:
    db_product = models.Product(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

def update_product(db: Session, product_id: UUID, product_update: schemas.ProductUpdate) -> Optional[models.Product]:
    db_product = db.query(models.Product).filter(models.Product.id == str(product_id)).first()
    if db_product:
        update_data = product_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_product, field, value)
        db.commit()
        db.refresh(db_product)
    return db_product

def delete_product(db: Session, product_id: UUID) -> bool:
    db_product = db.query(models.Product).filter(models.Product.id == str(product_id)).first()
    if db_product:
        db.delete(db_product)
        db.commit()
        return True
    return False

# PlanDefinition CRUD
def get_plan_definition(db: Session, plan_id: UUID) -> Optional[models.PlanDefinition]:
    return db.query(models.PlanDefinition).filter(models.PlanDefinition.id == str(plan_id)).first()

def get_plan_definitions(db: Session, product_id: Optional[UUID] = None, skip: int = 0, limit: int = 100) -> List[models.PlanDefinition]:
    query = db.query(models.PlanDefinition)
    if product_id:
        query = query.filter(models.PlanDefinition.product_id == str(product_id))
    return query.offset(skip).limit(limit).all()

def get_plan_definitions_with_product(db: Session, product_id: Optional[UUID] = None, skip: int = 0, limit: int = 100) -> List[dict]:
    """Get plan definitions with product names included."""
    from sqlalchemy.orm import joinedload

    query = db.query(models.PlanDefinition).options(
        joinedload(models.PlanDefinition.product)
    )
    if product_id:
        query = query.filter(models.PlanDefinition.product_id == str(product_id))

    plans = query.offset(skip).limit(limit).all()

    # Convert to dict with additional fields
    result = []
    for plan in plans:
        plan_dict = {
            "id": plan.id,
            "product_id": plan.product_id,
            "product_name": plan.product.name if plan.product else "Unknown Product",
            "name": plan.name,
            "price": plan.price,
            "billing_interval": plan.billing_interval,
            "is_active": plan.is_active,
            "plan_metadata": plan.plan_metadata,
        }
        result.append(plan_dict)

    return result

def create_plan_definition(db: Session, plan: schemas.PlanDefinitionCreate) -> models.PlanDefinition:
    db_plan = models.PlanDefinition(**plan.model_dump())
    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)
    return db_plan

def update_plan_definition(db: Session, plan_id: UUID, plan_update: schemas.PlanDefinitionUpdate) -> Optional[models.PlanDefinition]:
    db_plan = db.query(models.PlanDefinition).filter(models.PlanDefinition.id == str(plan_id)).first()
    if db_plan:
        update_data = plan_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_plan, field, value)
        db.commit()
        db.refresh(db_plan)
    return db_plan

def delete_plan_definition(db: Session, plan_id: UUID) -> bool:
    db_plan = db.query(models.PlanDefinition).filter(models.PlanDefinition.id == str(plan_id)).first()
    if db_plan:
        db.delete(db_plan)
        db.commit()
        return True
    return False

# FeatureDefinition CRUD
def get_feature_definition(db: Session, feature_id: UUID) -> Optional[models.FeatureDefinition]:
    return db.query(models.FeatureDefinition).filter(models.FeatureDefinition.id == str(feature_id)).first()

def get_feature_definitions(db: Session, product_id: Optional[UUID] = None, skip: int = 0, limit: int = 100) -> List[models.FeatureDefinition]:
    query = db.query(models.FeatureDefinition)
    if product_id:
        query = query.filter(models.FeatureDefinition.product_id == str(product_id))
    return query.offset(skip).limit(limit).all()

def get_feature_definitions_with_product(db: Session, product_id: Optional[UUID] = None, skip: int = 0, limit: int = 100) -> List[dict]:
    """Get feature definitions with product names included."""
    from sqlalchemy.orm import joinedload

    query = db.query(models.FeatureDefinition).options(
        joinedload(models.FeatureDefinition.product)
    )
    if product_id:
        query = query.filter(models.FeatureDefinition.product_id == str(product_id))

    features = query.offset(skip).limit(limit).all()

    # Convert to dict with additional fields
    result = []
    for feature in features:
        feature_dict = {
            "id": feature.id,
            "product_id": feature.product_id,
            "product_name": feature.product.name if feature.product else "Unknown Product",
            "key": feature.key,
            "type": feature.type,
            "default_value": feature.default_value,
            "validation_rules": feature.validation_rules,
        }
        result.append(feature_dict)

    return result

def create_feature_definition(db: Session, feature: schemas.FeatureDefinitionCreate) -> models.FeatureDefinition:
    db_feature = models.FeatureDefinition(**feature.model_dump())
    db.add(db_feature)
    db.commit()
    db.refresh(db_feature)
    return db_feature

def update_feature_definition(db: Session, feature_id: UUID, feature_update: schemas.FeatureDefinitionUpdate) -> Optional[models.FeatureDefinition]:
    db_feature = db.query(models.FeatureDefinition).filter(models.FeatureDefinition.id == str(feature_id)).first()
    if db_feature:
        update_data = feature_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_feature, field, value)
        db.commit()
        db.refresh(db_feature)
    return db_feature

def delete_feature_definition(db: Session, feature_id: UUID) -> bool:
    db_feature = db.query(models.FeatureDefinition).filter(models.FeatureDefinition.id == str(feature_id)).first()
    if db_feature:
        db.delete(db_feature)
        db.commit()
        return True
    return False

# PlanFeature CRUD
def get_plan_feature(db: Session, plan_id: UUID, feature_id: UUID) -> Optional[models.PlanFeature]:
    return db.query(models.PlanFeature).filter(
        and_(models.PlanFeature.plan_id == str(plan_id), models.PlanFeature.feature_id == str(feature_id))
    ).first()

def get_plan_features(db: Session, plan_id: Optional[UUID] = None, skip: int = 0, limit: int = 100) -> List[models.PlanFeature]:
    query = db.query(models.PlanFeature)
    if plan_id:
        query = query.filter(models.PlanFeature.plan_id == str(plan_id))
    return query.offset(skip).limit(limit).all()

def create_plan_feature(db: Session, plan_feature: schemas.PlanFeatureCreate) -> models.PlanFeature:
    db_plan_feature = models.PlanFeature(**plan_feature.model_dump())
    db.add(db_plan_feature)
    db.commit()
    db.refresh(db_plan_feature)
    return db_plan_feature

def update_plan_feature(db: Session, plan_id: UUID, feature_id: UUID, plan_feature_update: schemas.PlanFeatureUpdate) -> Optional[models.PlanFeature]:
    db_plan_feature = db.query(models.PlanFeature).filter(
        and_(models.PlanFeature.plan_id == str(plan_id), models.PlanFeature.feature_id == str(feature_id))
    ).first()
    if db_plan_feature:
        update_data = plan_feature_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_plan_feature, field, value)
        db.commit()
        db.refresh(db_plan_feature)
    return db_plan_feature

def delete_plan_feature(db: Session, plan_id: UUID, feature_id: UUID) -> bool:
    db_plan_feature = db.query(models.PlanFeature).filter(
        and_(models.PlanFeature.plan_id == str(plan_id), models.PlanFeature.feature_id == str(feature_id))
    ).first()
    if db_plan_feature:
        db.delete(db_plan_feature)
        db.commit()
        return True
    return False

# Subscription CRUD
def get_subscription(db: Session, subscription_id: UUID) -> Optional[models.Subscription]:
    return db.query(models.Subscription).filter(models.Subscription.id == str(subscription_id)).first()

def get_subscriptions(db: Session, tenant_id: Optional[UUID] = None, skip: int = 0, limit: int = 100) -> List[models.Subscription]:
    query = db.query(models.Subscription)
    if tenant_id:
        query = query.filter(models.Subscription.tenant_id == str(tenant_id))
    return query.offset(skip).limit(limit).all()

def get_subscriptions_with_details(db: Session, tenant_id: Optional[UUID] = None, skip: int = 0, limit: int = 100) -> List[dict]:
    """Get subscriptions with tenant and plan names included."""
    from sqlalchemy.orm import joinedload

    query = db.query(models.Subscription).options(
        joinedload(models.Subscription.tenant),
        joinedload(models.Subscription.plan)
    )
    if tenant_id:
        query = query.filter(models.Subscription.tenant_id == str(tenant_id))

    subscriptions = query.offset(skip).limit(limit).all()

    # Convert to dict with additional fields
    result = []
    for subscription in subscriptions:
        # Calculate validity_days based on plan's billing interval and issue_date
        validity_days = None
        if subscription.plan and subscription.issue_date:
            if subscription.plan.billing_interval == "monthly":
                # Use actual number of days in the month of issue_date
                import calendar
                year = subscription.issue_date.year
                month = subscription.issue_date.month
                validity_days = calendar.monthrange(year, month)[1]
            elif subscription.plan.billing_interval == "yearly":
                # Calculate days from issue_date to same date next year minus 1 day
                from datetime import timedelta
                next_year_date = subscription.issue_date.replace(year=subscription.issue_date.year + 1)
                validity_days = (next_year_date - subscription.issue_date).days

        subscription_dict = {
            "id": subscription.id,
            "tenant_id": subscription.tenant_id,
            "tenant_name": subscription.tenant.name if subscription.tenant else "Unknown Tenant",
            "plan_id": subscription.plan_id,
            "plan_name": subscription.plan.name if subscription.plan else "Unknown Plan",
            "billing_interval": subscription.plan.billing_interval if subscription.plan else None,
            "status": subscription.status,
            "start_date": subscription.start_date,
            "issue_date": subscription.issue_date,
            "end_date": subscription.end_date,
            "validity_days": validity_days,
            "auto_renew": subscription.auto_renew,
            "payment_provider_id": subscription.payment_provider_id,
        }
        result.append(subscription_dict)

    return result

def create_subscription(db: Session, subscription: schemas.SubscriptionCreate) -> models.Subscription:
    # Set default status to active if not provided
    subscription_data = subscription.model_dump()
    if 'status' not in subscription_data:
        subscription_data['status'] = schemas.SubscriptionStatus.active

    # Set issue_date to current timestamp
    subscription_data['issue_date'] = models.func.now()

    db_subscription = models.Subscription(**subscription_data)
    db.add(db_subscription)
    db.commit()
    db.refresh(db_subscription)

    # Create entitlements based on plan features
    plan = get_plan_definition(db, subscription.plan_id)
    if plan:
        for plan_feature in plan.plan_features:
            feature = plan_feature.feature
            effective_value = plan_feature.override_value if plan_feature.override_value is not None else feature.default_value
            entitlement = models.SubscriptionEntitlement(
                subscription_id=db_subscription.id,
                feature_id=feature.id,
                effective_value=effective_value,
                overridden=plan_feature.override_value is not None
            )
            db.add(entitlement)
        db.commit()

    return db_subscription

def update_subscription(db: Session, subscription_id: UUID, subscription_update: schemas.SubscriptionUpdate) -> Optional[models.Subscription]:
    db_subscription = db.query(models.Subscription).filter(models.Subscription.id == str(subscription_id)).first()
    if db_subscription:
        update_data = subscription_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_subscription, field, value)
        db.commit()
        db.refresh(db_subscription)

        # If the plan was changed, we don't need to update licenses since they now calculate validity_days dynamically
        # The licenses will automatically reflect the new plan's billing interval when retrieved

    return db_subscription

def delete_subscription(db: Session, subscription_id: UUID) -> bool:
    db_subscription = db.query(models.Subscription).filter(models.Subscription.id == str(subscription_id)).first()
    if db_subscription:
        db.delete(db_subscription)
        db.commit()
        return True
    return False

# SubscriptionEntitlement CRUD
def get_subscription_entitlement(db: Session, subscription_id: UUID, feature_id: UUID) -> Optional[models.SubscriptionEntitlement]:
    return db.query(models.SubscriptionEntitlement).filter(
        and_(models.SubscriptionEntitlement.subscription_id == str(subscription_id), models.SubscriptionEntitlement.feature_id == str(feature_id))
    ).first()

def get_subscription_entitlements(db: Session, subscription_id: Optional[UUID] = None, skip: int = 0, limit: int = 100) -> List[models.SubscriptionEntitlement]:
    query = db.query(models.SubscriptionEntitlement)
    if subscription_id:
        query = query.filter(models.SubscriptionEntitlement.subscription_id == str(subscription_id))
    return query.offset(skip).limit(limit).all()

def get_subscription_entitlements_with_details(db: Session, subscription_id: Optional[UUID] = None, skip: int = 0, limit: int = 100) -> List[dict]:
    """Get subscription entitlements with feature keys and billing information included."""
    from sqlalchemy.orm import joinedload

    query = db.query(models.SubscriptionEntitlement).options(
        joinedload(models.SubscriptionEntitlement.feature),
        joinedload(models.SubscriptionEntitlement.subscription).joinedload(models.Subscription.plan)
    )
    if subscription_id:
        query = query.filter(models.SubscriptionEntitlement.subscription_id == str(subscription_id))

    entitlements = query.offset(skip).limit(limit).all()

    # Convert to dict with additional fields
    result = []
    for entitlement in entitlements:
        # Calculate validity_days based on subscription's plan billing interval and issue_date
        validity_days = None
        billing_interval = None
        if entitlement.subscription and entitlement.subscription.plan:
            billing_interval = entitlement.subscription.plan.billing_interval
            issue_date = entitlement.subscription.issue_date
            if issue_date:
                if billing_interval == "monthly":
                    # Use actual number of days in the month of issue_date
                    import calendar
                    year = issue_date.year
                    month = issue_date.month
                    validity_days = calendar.monthrange(year, month)[1]
                elif billing_interval == "yearly":
                    # Calculate days from issue_date to same date next year minus 1 day
                    from datetime import timedelta
                    next_year_date = issue_date.replace(year=issue_date.year + 1)
                    validity_days = (next_year_date - issue_date).days

        entitlement_dict = {
            "subscription_id": entitlement.subscription_id,
            "feature_id": entitlement.feature_id,
            "feature_key": entitlement.feature.key if entitlement.feature else "Unknown Feature",
            "effective_value": entitlement.effective_value,
            "overridden": entitlement.overridden,
            "billing_interval": billing_interval,
            "validity_days": validity_days,
        }
        result.append(entitlement_dict)

    return result

def create_subscription_entitlement(db: Session, entitlement: schemas.SubscriptionEntitlementCreate) -> models.SubscriptionEntitlement:
    db_entitlement = models.SubscriptionEntitlement(**entitlement.model_dump())
    db.add(db_entitlement)
    db.commit()
    db.refresh(db_entitlement)
    return db_entitlement

def update_subscription_entitlement(db: Session, subscription_id: UUID, feature_id: UUID, entitlement_update: schemas.SubscriptionEntitlementUpdate) -> Optional[models.SubscriptionEntitlement]:
    db_entitlement = db.query(models.SubscriptionEntitlement).filter(
        and_(models.SubscriptionEntitlement.subscription_id == str(subscription_id), models.SubscriptionEntitlement.feature_id == str(feature_id))
    ).first()
    if db_entitlement:
        update_data = entitlement_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_entitlement, field, value)
        db.commit()
        db.refresh(db_entitlement)
    return db_entitlement

def delete_subscription_entitlement(db: Session, subscription_id: UUID, feature_id: UUID) -> bool:
    db_entitlement = db.query(models.SubscriptionEntitlement).filter(
        and_(models.SubscriptionEntitlement.subscription_id == str(subscription_id), models.SubscriptionEntitlement.feature_id == str(feature_id))
    ).first()
    if db_entitlement:
        db.delete(db_entitlement)
        db.commit()
        return True
    return False
