#!/usr/bin/env python3
"""
Simplified database seeding for application startup
Automatically creates essential data when the application starts
Designed for Docker compose deployment
"""

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import models
from app.crud import create_tenant, create_template, create_default_admin
from app.schemas import TenantCreate, TemplateCreate

def seed_startup_data():
    """Seed essential data during application startup"""
    
    db = SessionLocal()
    try:
        print("Starting application database initialization...")
        
        # Create Sigma Permit Default tenant
        default_tenant_data = {
            "name": "Sigma Permit Default",
            "slug": "sigma-permit-default",
            "max_licenses": 10000,  # Large limit for default tenant
            "is_active": True
        }
        
        existing_tenant = db.query(models.Tenant).filter(models.Tenant.slug == default_tenant_data["slug"]).first()
        if not existing_tenant:
            tenant = create_tenant(db=db, tenant=TenantCreate(**default_tenant_data))
            print(f"Created default tenant: {tenant.name} (ID: {tenant.id})")
        else:
            print(f"Default tenant already exists: {existing_tenant.name}")
        
        # Create essential license templates
        templates_data = [
            {
                "name": "Basic License",
                "description": "Basic license template for essential features",
                "payload_schema": {
                    "features": ["user_management", "basic_reporting"],
                    "user_limit": 10,
                    "api_access": False,
                    "support_level": "basic",
                    "license_type": "basic"
                },
                "validation_rules": {
                    "max_features": 5,
                    "min_validity": 30,
                    "max_validity": 365,
                    "max_users": 20
                },
                "is_active": True
            },
            {
                "name": "Standard License",
                "description": "Standard license template with enhanced features",
                "payload_schema": {
                    "features": ["user_management", "advanced_reporting", "api_access", "custom_dashboards"],
                    "user_limit": 100,
                    "api_access": True,
                    "support_level": "standard",
                    "license_type": "standard",
                    "department": "IT"
                },
                "validation_rules": {
                    "max_features": 15,
                    "min_validity": 90,
                    "max_validity": 1095,
                    "max_users": 200
                },
                "is_active": True
            },
            {
                "name": "Enterprise License",
                "description": "Enterprise license template with full feature access",
                "payload_schema": {
                    "features": ["user_management", "advanced_reporting", "api_access", "custom_integrations", "white_label", "multi_tenant", "sso", "audit_logs"],
                    "user_limit": 1000,
                    "api_access": True,
                    "custom_integrations": True,
                    "support_level": "enterprise",
                    "sla_guarantee": "99.9% uptime",
                    "white_label": True,
                    "license_type": "enterprise",
                    "contract_value": 50000
                },
                "validation_rules": {
                    "min_validity": 365,
                    "min_users": 50,
                    "allowed_support_levels": ["enterprise", "white-glove"]
                },
                "is_active": True
            }
        ]
        
        for template_data in templates_data:
            existing_template = db.query(models.Template).filter(models.Template.name == template_data["name"]).first()
            if not existing_template:
                template = create_template(db=db, template=TemplateCreate(**template_data))
                print(f"Created template: {template.name} (ID: {template.id})")
            else:
                print(f"Template already exists: {existing_template.name}")
        
        # Create default admin user
        admin_user = create_default_admin(db=db)
        print(f"Default admin user: {admin_user.username} (Email: {admin_user.email})")
        print("Default password: admin123 (change this in production!)")
        
        print("Application database initialization completed successfully!")
        
    except Exception as e:
        print(f"Error during application startup seeding: {e}")
        db.rollback()
        raise  # Re-raise the exception to ensure startup fails if seeding fails
    finally:
        db.close()

if __name__ == "__main__":
    seed_startup_data()