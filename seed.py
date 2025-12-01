#!/usr/bin/env python3
"""
Database seeding script for Sigma Permit
Seeds initial data: tenants and pre-built license templates
"""

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app import models
from app.crud import create_tenant, create_template, create_default_admin, create_product, create_feature_definition, create_plan_definition, create_subscription
from app.schemas import TenantCreate, TemplateCreate, ProductCreate, FeatureDefinitionCreate, PlanDefinitionCreate, SubscriptionCreate
from datetime import datetime, timedelta
from uuid import UUID

def seed_database():
    """Seed the database with initial data"""

    # Create database tables
    models.Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        print("Seeding database...")

        # Seed tenants
        tenants_data = [
            {
                "name": "Macaca Cloud",
                "slug": "macaca-cloud",
                "max_licenses": 1000,
                "is_active": True
            },
            {
                "name": "Engagenest",
                "slug": "engagenest",
                "max_licenses": 500,
                "is_active": True
            }
        ]

        for tenant_data in tenants_data:
            existing_tenant = db.query(models.Tenant).filter(models.Tenant.slug == tenant_data["slug"]).first()
            if not existing_tenant:
                tenant = create_tenant(db=db, tenant=TenantCreate(**tenant_data))
                print(f"Created tenant: {tenant.name} (ID: {tenant.id})")
            else:
                print(f"Tenant already exists: {existing_tenant.name}")

        # Seed pre-built license templates
        templates_data = [
            {
                "name": "Basic",
                "description": "Basic license with essential features for small teams",
                "payload_schema": {
                    "features": ["user_management", "basic_reporting", "email_support"],
                    "user_limit": 5,
                    "api_access": False,
                    "support_level": "basic",
                    "license_type": "basic"
                },
                "validation_rules": {
                    "max_features": 5,
                    "min_validity": 30,
                    "max_validity": 365,
                    "max_users": 10
                },
                "is_active": True
            },
            {
                "name": "Business",
                "description": "Business license with advanced features for growing companies",
                "payload_schema": {
                    "features": ["user_management", "advanced_reporting", "api_access", "custom_dashboards", "priority_support"],
                    "user_limit": 50,
                    "api_access": True,
                    "support_level": "premium",
                    "custom_integrations": False,
                    "license_type": "business",
                    "department": "IT"
                },
                "validation_rules": {
                    "max_features": 20,
                    "min_validity": 90,
                    "max_validity": 1095,
                    "max_users": 100
                },
                "is_active": True
            },
            {
                "name": "Enterprise",
                "description": "Enterprise license with unlimited features for large organizations",
                "payload_schema": {
                    "features": ["user_management", "advanced_reporting", "api_access", "custom_integrations", "white_label", "multi_tenant", "sso", "audit_logs"],
                    "user_limit": 500,
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

        # Seed products
        products_data = [
            {
                "name": "Auditchimp",
                "description": "Analytics solution for contact center voice conversations",
                "version": 1
            },
            {
                "name": "Banana Bot",
                "description": "Voice agent for enterprise contact centers",
                "version": 1
            }
        ]

        products = []
        for product_data in products_data:
            existing_product = db.query(models.Product).filter(models.Product.name == product_data["name"]).first()
            if not existing_product:
                product = create_product(db=db, product=ProductCreate(**product_data))
                products.append(product)
                print(f"Created product: {product.name} (ID: {product.id})")
            else:
                products.append(existing_product)
                print(f"Product already exists: {existing_product.name}")

        # Get products from db
        auditchimp_product = db.query(models.Product).filter(models.Product.name == "Auditchimp").first()
        banana_bot_product = db.query(models.Product).filter(models.Product.name == "Banana Bot").first()

        # Seed features for products
        features_data = [
            # Auditchimp features
            {
                "product_id": auditchimp_product.id,
                "key": "feedback",
                "type": "boolean",
                "default_value": False,
                "validation_rules": {}
            },
            {
                "product_id": auditchimp_product.id,
                "key": "sentiment_emotions",
                "type": "boolean",
                "default_value": False,
                "validation_rules": {}
            },
            {
                "product_id": auditchimp_product.id,
                "key": "macaca_login",
                "type": "boolean",
                "default_value": False,
                "validation_rules": {}
            },
            {
                "product_id": auditchimp_product.id,
                "key": "compliance",
                "type": "boolean",
                "default_value": False,
                "validation_rules": {}
            },
            {
                "product_id": auditchimp_product.id,
                "key": "aps_calculation",
                "type": "boolean",
                "default_value": False,
                "validation_rules": {}
            },
            {
                "product_id": auditchimp_product.id,
                "key": "csat_calculations",
                "type": "boolean",
                "default_value": False,
                "validation_rules": {}
            },
            {
                "product_id": auditchimp_product.id,
                "key": "dashboards",
                "type": "boolean",
                "default_value": False,
                "validation_rules": {}
            },
            {
                "product_id": auditchimp_product.id,
                "key": "agent_reports",
                "type": "boolean",
                "default_value": False,
                "validation_rules": {}
            },
            {
                "product_id": auditchimp_product.id,
                "key": "customer_reports",
                "type": "boolean",
                "default_value": False,
                "validation_rules": {}
            },
            {
                "product_id": auditchimp_product.id,
                "key": "sso",
                "type": "boolean",
                "default_value": False,
                "validation_rules": {}
            },
            {
                "product_id": auditchimp_product.id,
                "key": "social_logins",
                "type": "boolean",
                "default_value": False,
                "validation_rules": {}
            },
            {
                "product_id": auditchimp_product.id,
                "key": "rbac",
                "type": "boolean",
                "default_value": False,
                "validation_rules": {}
            },
            # Banana Bot features
            {
                "product_id": banana_bot_product.id,
                "key": "voice_recognition",
                "type": "boolean",
                "default_value": False,
                "validation_rules": {}
            },
            {
                "product_id": banana_bot_product.id,
                "key": "natural_language_processing",
                "type": "boolean",
                "default_value": False,
                "validation_rules": {}
            },
            {
                "product_id": banana_bot_product.id,
                "key": "call_routing",
                "type": "boolean",
                "default_value": False,
                "validation_rules": {}
            },
            {
                "product_id": banana_bot_product.id,
                "key": "ivr_system",
                "type": "boolean",
                "default_value": False,
                "validation_rules": {}
            },
            {
                "product_id": banana_bot_product.id,
                "key": "call_recording",
                "type": "boolean",
                "default_value": False,
                "validation_rules": {}
            },
            {
                "product_id": banana_bot_product.id,
                "key": "real_time_transcription",
                "type": "boolean",
                "default_value": False,
                "validation_rules": {}
            },
            {
                "product_id": banana_bot_product.id,
                "key": "sentiment_analysis",
                "type": "boolean",
                "default_value": False,
                "validation_rules": {}
            },
            {
                "product_id": banana_bot_product.id,
                "key": "multi_language_support",
                "type": "boolean",
                "default_value": False,
                "validation_rules": {}
            },
            {
                "product_id": banana_bot_product.id,
                "key": "integration_apis",
                "type": "boolean",
                "default_value": False,
                "validation_rules": {}
            },
            {
                "product_id": banana_bot_product.id,
                "key": "custom_voice_personalities",
                "type": "boolean",
                "default_value": False,
                "validation_rules": {}
            },
            {
                "product_id": banana_bot_product.id,
                "key": "analytics_dashboard",
                "type": "boolean",
                "default_value": False,
                "validation_rules": {}
            },
            {
                "product_id": banana_bot_product.id,
                "key": "enterprise_security",
                "type": "boolean",
                "default_value": False,
                "validation_rules": {}
            }
        ]

        features = []
        for feature_data in features_data:
            # Convert UUID to string for database compatibility
            feature_data_copy = feature_data.copy()
            if isinstance(feature_data_copy["product_id"], UUID):
                feature_data_copy["product_id"] = str(feature_data_copy["product_id"])

            existing_feature = db.query(models.FeatureDefinition).filter(
                models.FeatureDefinition.product_id == feature_data_copy["product_id"],
                models.FeatureDefinition.key == feature_data_copy["key"]
            ).first()
            if not existing_feature:
                feature = create_feature_definition(db=db, feature=FeatureDefinitionCreate(**feature_data_copy))
                features.append(feature)
                print(f"Created feature: {feature.key} for {feature.product.name}")
            else:
                features.append(existing_feature)
                print(f"Feature already exists: {existing_feature.key}")

        # Seed plans
        plans_data = [
            # Auditchimp plans
            {
                "product_id": auditchimp_product.id,
                "name": "Pro",
                "price": 49.99,
                "billing_interval": "monthly",
                "is_active": True,
                "plan_metadata": {"description": "Pro plan with feedback, sentiment & emotions, macaca login"}
            },
            {
                "product_id": auditchimp_product.id,
                "name": "Premium Pro",
                "price": 99.99,
                "billing_interval": "monthly",
                "is_active": True,
                "plan_metadata": {"description": "Premium Pro with Pro features plus compliance"}
            },
            {
                "product_id": auditchimp_product.id,
                "name": "Ultimate",
                "price": 199.99,
                "billing_interval": "monthly",
                "is_active": True,
                "plan_metadata": {"description": "Ultimate plan with all features including APS calculation, CSAT calculations, dashboards, reports, SSO, social logins, RBAC"}
            },
            # Banana Bot plans
            {
                "product_id": banana_bot_product.id,
                "name": "Starter",
                "price": 29.99,
                "billing_interval": "monthly",
                "is_active": True,
                "plan_metadata": {"description": "Starter plan with voice recognition, natural language processing, and call routing"}
            },
            {
                "product_id": banana_bot_product.id,
                "name": "Professional",
                "price": 79.99,
                "billing_interval": "monthly",
                "is_active": True,
                "plan_metadata": {"description": "Professional plan with IVR system, call recording, and real-time transcription"}
            },
            {
                "product_id": banana_bot_product.id,
                "name": "Enterprise",
                "price": 149.99,
                "billing_interval": "monthly",
                "is_active": True,
                "plan_metadata": {"description": "Enterprise plan with all features including multi-language support, custom voice personalities, analytics dashboard, and enterprise security"}
            }
        ]

        plans = []
        for plan_data in plans_data:
            # Convert UUID to string for database compatibility
            plan_data_copy = plan_data.copy()
            if isinstance(plan_data_copy["product_id"], UUID):
                plan_data_copy["product_id"] = str(plan_data_copy["product_id"])

            existing_plan = db.query(models.PlanDefinition).filter(
                models.PlanDefinition.product_id == plan_data_copy["product_id"],
                models.PlanDefinition.name == plan_data_copy["name"]
            ).first()
            if not existing_plan:
                plan = create_plan_definition(db=db, plan=PlanDefinitionCreate(**plan_data_copy))
                plans.append(plan)
                print(f"Created plan: {plan.name} (ID: {plan.id})")
            else:
                plans.append(existing_plan)
                print(f"Plan already exists: {existing_plan.name}")

        # Create plan features (link plans to features with overrides)
        plan_features_data = [
            # Pro plan
            {"plan_id": plans[0].id, "feature_id": features[0].id, "override_value": True},  # feedback = true
            {"plan_id": plans[0].id, "feature_id": features[1].id, "override_value": True},  # sentiment_emotions = true
            {"plan_id": plans[0].id, "feature_id": features[2].id, "override_value": True},  # macaca_login = true
            # Premium Pro plan
            {"plan_id": plans[1].id, "feature_id": features[0].id, "override_value": True},  # feedback = true
            {"plan_id": plans[1].id, "feature_id": features[1].id, "override_value": True},  # sentiment_emotions = true
            {"plan_id": plans[1].id, "feature_id": features[2].id, "override_value": True},  # macaca_login = true
            {"plan_id": plans[1].id, "feature_id": features[3].id, "override_value": True},  # compliance = true
            # Ultimate plan
            {"plan_id": plans[2].id, "feature_id": features[0].id, "override_value": True},  # feedback = true
            {"plan_id": plans[2].id, "feature_id": features[1].id, "override_value": True},  # sentiment_emotions = true
            {"plan_id": plans[2].id, "feature_id": features[2].id, "override_value": True},  # macaca_login = true
            {"plan_id": plans[2].id, "feature_id": features[3].id, "override_value": True},  # compliance = true
            {"plan_id": plans[2].id, "feature_id": features[4].id, "override_value": True},  # aps_calculation = true
            {"plan_id": plans[2].id, "feature_id": features[5].id, "override_value": True},  # csat_calculations = true
            {"plan_id": plans[2].id, "feature_id": features[6].id, "override_value": True},  # dashboards = true
            {"plan_id": plans[2].id, "feature_id": features[7].id, "override_value": True},  # agent_reports = true
            {"plan_id": plans[2].id, "feature_id": features[8].id, "override_value": True},  # customer_reports = true
            {"plan_id": plans[2].id, "feature_id": features[9].id, "override_value": True},  # sso = true
            {"plan_id": plans[2].id, "feature_id": features[10].id, "override_value": True},  # social_logins = true
            {"plan_id": plans[2].id, "feature_id": features[11].id, "override_value": True},  # rbac = true
        ]

        for pf_data in plan_features_data:
            # Convert UUIDs to strings
            pf_data_copy = pf_data.copy()
            if isinstance(pf_data_copy["plan_id"], UUID):
                pf_data_copy["plan_id"] = str(pf_data_copy["plan_id"])
            if isinstance(pf_data_copy["feature_id"], UUID):
                pf_data_copy["feature_id"] = str(pf_data_copy["feature_id"])

            existing_pf = db.query(models.PlanFeature).filter(
                models.PlanFeature.plan_id == pf_data_copy["plan_id"],
                models.PlanFeature.feature_id == pf_data_copy["feature_id"]
            ).first()
            if not existing_pf:
                from app.crud import create_plan_feature
                from app.schemas import PlanFeatureCreate
                pf = create_plan_feature(db=db, plan_feature=PlanFeatureCreate(**pf_data_copy))
                print(f"Created plan feature link: Plan {pf.plan.name} - Feature {pf.feature.key}")

        # Seed subscriptions
        tenants = db.query(models.Tenant).all()
        if tenants:
            subscriptions_data = [
                {
                    "tenant_id": tenants[0].id,
                    "plan_id": plans[0].id,
                    "status": "active",
                    "start_date": datetime.utcnow(),
                    "auto_renew": True,
                    "payment_provider_id": "stripe_sub_macaca_12345"
                },
                {
                    "tenant_id": tenants[1].id,
                    "plan_id": plans[2].id,
                    "status": "trialing",
                    "start_date": datetime.utcnow(),
                    "end_date": datetime.utcnow() + timedelta(days=14),
                    "auto_renew": True,
                    "payment_provider_id": "stripe_sub_engagenest_67890"
                }
            ]

            for sub_data in subscriptions_data:
                # Convert UUIDs to strings
                sub_data_copy = sub_data.copy()
                if isinstance(sub_data_copy["tenant_id"], UUID):
                    sub_data_copy["tenant_id"] = str(sub_data_copy["tenant_id"])
                if isinstance(sub_data_copy["plan_id"], UUID):
                    sub_data_copy["plan_id"] = str(sub_data_copy["plan_id"])

                existing_sub = db.query(models.Subscription).filter(
                    models.Subscription.tenant_id == sub_data_copy["tenant_id"],
                    models.Subscription.plan_id == sub_data_copy["plan_id"]
                ).first()
                if not existing_sub:
                    sub = create_subscription(db=db, subscription=SubscriptionCreate(**sub_data_copy))
                    print(f"Created subscription: Tenant {sub.tenant.name} - Plan {sub.plan.name}")
                else:
                    print(f"Subscription already exists for tenant {existing_sub.tenant.name}")

        # Create default admin user
        admin_user = create_default_admin(db=db)
        print(f"Default admin user: {admin_user.username} (Email: {admin_user.email})")
        print("Default password: admin123 (change this in production!)")

        print("Database seeding completed successfully!")

    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
