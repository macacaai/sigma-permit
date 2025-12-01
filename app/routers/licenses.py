from fastapi import APIRouter, Depends, HTTPException, Query, Request, Form, Body, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from math import ceil
from datetime import datetime, timedelta
import json
import base64
from uuid import UUID
from app import crud, models, schemas
from app.database import get_db
from app.auth import get_current_user
from app.crypto_utils import sign_payload, verify_signature, rsa_encrypt, rsa_decrypt, hybrid_encrypt, hybrid_decrypt, generate_rsa_keypair
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/templates")

router = APIRouter()

def get_master_key(db: Session) -> str:
    """Get or create master AES key."""
    master_key = db.query(models.MasterKey).first()
    if not master_key:
        aes_key = generate_aes_key()
        master_key = models.MasterKey(aes_key=aes_key)
        db.add(master_key)
        db.commit()
        db.refresh(master_key)
    return master_key.aes_key

def paginate_response(items: List, total: int, page: int, size: int) -> schemas.PaginatedResponse:
    return schemas.PaginatedResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=ceil(total / size) if size > 0 else 0
    )

@router.post("", response_model=schemas.LicenseResponse)
def create_license(
    license: schemas.LicenseCreate = Body(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check if tenant exists
    tenant = crud.get_tenant(db, license.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Check license limit
    current_count = crud.get_tenant_license_count(db, license.tenant_id)
    if current_count >= tenant.max_licenses:
        raise HTTPException(status_code=400, detail="Maximum licenses reached for this tenant")

    # Create the license
    db_license = crud.create_license(db=db, license=license)

    # Return LicenseResponse with tenant name (keys are base64-encoded DER)
    return schemas.LicenseResponse(
        id=db_license.id,
        license_key=db_license.license_key,  # Base64-encoded DER as-is
        tenant_id=db_license.tenant_id,
        tenant_name=tenant.name,
        template_id=db_license.template_id,
        issued_at=db_license.issued_at,
        validity_days=db_license.validity_days,
        payload=db_license.payload
    )

@router.get("/master-keys")
def get_master_keys(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Get master keys (admin only)."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Superuser access required")

    # Get private key from database
    private_key_masked = "Not generated"
    master_key_record = db.query(models.MasterKey).first()
    if master_key_record and master_key_record.private_key:
        private_key = master_key_record.private_key
        # Mask the private key (show first 20 and last 20 chars)
        if len(private_key) > 40:
            private_key_masked = private_key[:20] + "..." + private_key[-20:]
        else:
            private_key_masked = private_key

    master_keys = db.query(models.MasterKey).all()
    return [{
        "id": mk.id,
        "public_key": mk.public_key,
        "private_key_masked": private_key_masked,
        "is_active": mk.is_active,
        "created_at": mk.created_at,
        "updated_at": mk.updated_at
    } for mk in master_keys]

@router.post("/master-keys/rotate")
def rotate_master_key(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Rotate master key - generate new key pair and mark existing as inactive (admin only)."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Superuser access required")

    # Mark all existing active keys as inactive
    db.query(models.MasterKey).filter(models.MasterKey.is_active == True).update({"is_active": False})

    # Generate new RSA key pair
    public_key, private_key = generate_rsa_keypair()

    # Create new master key record
    new_master_key = models.MasterKey(
        public_key=public_key,
        private_key=private_key,
        is_active=True
    )

    db.add(new_master_key)
    db.commit()
    db.refresh(new_master_key)

    return {
        "message": "Master key rotated successfully",
        "new_master_key": {
            "id": new_master_key.id,
            "public_key": new_master_key.public_key,
            "is_active": new_master_key.is_active,
            "created_at": new_master_key.created_at
        }
    }

@router.post("/master-keys/override")
def override_master_key(
    public_key: str = Body(..., embed=True),
    private_key: str = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Override master key - mark current active as inactive and insert provided key pair (admin only)."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Superuser access required")

    if not public_key or not private_key:
        raise HTTPException(status_code=400, detail="Both public_key and private_key are required")

    # Mark all existing active keys as inactive
    db.query(models.MasterKey).filter(models.MasterKey.is_active == True).update({"is_active": False})

    # Create new master key record with provided keys
    new_master_key = models.MasterKey(
        public_key=public_key,
        private_key=private_key,
        is_active=True
    )

    db.add(new_master_key)
    db.commit()
    db.refresh(new_master_key)

    return {
        "message": "Master key overridden successfully",
        "new_master_key": {
            "id": new_master_key.id,
            "public_key": new_master_key.public_key,
            "is_active": new_master_key.is_active,
            "created_at": new_master_key.created_at
        }
    }

@router.get("/master-keys/current-private")
def get_current_master_private_key(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Get current active master private key for client-side validation (admin only)."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Superuser access required")

    master_key_record = db.query(models.MasterKey).filter(models.MasterKey.is_active == True).first()
    if not master_key_record:
        raise HTTPException(status_code=404, detail="No active master key found")

    return {
        "private_key": master_key_record.private_key
    }


@router.get("/issue")
def issue_license_file(encoded_license_key: str, db: Session = Depends(get_db)):
    """
    Issue a license file for download.
    Input: base64 encoded license key
    Output: Encrypted license file (license.lic)
    """
    try:
        # Decode the base64 encoded license key
        license_key_b64 = encoded_license_key
        license_key = base64.b64decode(license_key_b64).decode('utf-8')
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid base64 encoded license key")

    # Find the license in database by license_key
    db_license = db.query(models.License).filter(models.License.license_key == license_key).first()
    if not db_license:
        raise HTTPException(status_code=404, detail="License not found")

    # Calculate validity_days dynamically for licenses linked to subscriptions
    validity_days = db_license.validity_days
    expires_at = None
    if db_license.linked_subscription:
        subscription = crud.get_subscription(db, db_license.linked_subscription)
        if subscription:
            # Use same logic as create_license
            if subscription.end_date:
                from datetime import timedelta
                validity_period = subscription.end_date - subscription.issue_date
                validity_days = validity_period.days
                expires_at = subscription.end_date.isoformat()
            elif subscription.plan and subscription.issue_date:
                plan = crud.get_plan_definition(db, subscription.plan_id)
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

                    # Calculate expires_at
                    from datetime import timedelta
                    expiry_date = subscription.issue_date + timedelta(days=validity_days - 1)
                    expires_at = expiry_date.isoformat()

    # Create the license file structure
    license_data = {
        "license": {
            "id": str(db_license.id),
            "tenant_id": str(db_license.tenant_id),
            "linked_subscription": db_license.linked_subscription,
            "issued_at": db_license.issued_at.isoformat() if db_license.issued_at else None,
            "validity_days": validity_days,
            "payload": db_license.payload
        },
        "signature": ""
    }

    # Include expires_at if available
    if expires_at:
        license_data["license"]["expires_at"] = expires_at

    # Convert to JSON string for signing
    license_json = json.dumps(license_data["license"], separators=(',', ':'))

    # Sign the license data
    signature = sign_payload(license_json, db_license.license_secret)

    # Add signature to the data
    license_data["signature"] = signature

    # Get master public key and encrypt the complete data using hybrid encryption
    master_key_record = db.query(models.MasterKey).first()
    if not master_key_record:
        raise HTTPException(status_code=500, detail="Master key not configured")
    complete_json = json.dumps(license_data, separators=(',', ':'))
    encrypted_json = hybrid_encrypt(complete_json, master_key_record.public_key)

    # Create a temporary file
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(mode='w', suffix='.lic', delete=False) as temp_file:
        temp_file.write(encrypted_json)
        temp_file_path = temp_file.name

    # Return the file for download
    return FileResponse(
        path=temp_file_path,
        filename="license.lic",
        media_type="application/octet-stream",
        background=None  # Don't delete immediately, let FastAPI handle it
    )

@router.get("/generate-validator")
def generate_validator_code(language: str = Query(..., description="Programming language (js, ts, py, java, rust, dart, go)"), db: Session = Depends(get_db)):
    """
    Generate and download validator code for the specified programming language.
    """
    if language not in ["js", "ts", "py", "java", "rust", "dart", "go"]:
        raise HTTPException(status_code=400, detail="Unsupported language")

    # Base URL for the API (this would be configurable in production)
    base_url = "https://your-api-domain.com"  # TODO: Make this configurable

    # Get current active master private key for validators
    master_key_record = db.query(models.MasterKey).filter(models.MasterKey.is_active == True).first()
    if not master_key_record:
        raise HTTPException(status_code=500, detail="No active master key found")
    master_private_key = master_key_record.private_key

    # Read the template file
    template_path = f"app/validator_templates/{language}.template"
    try:
        with open(template_path, 'r') as f:
            code = f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail=f"Template file not found for language: {language}")

    # Replace placeholders in the template
    code = code.replace("{master_private_key}", master_private_key).replace("{base_url}", base_url)

    # File extensions for different languages
    extensions = {
        "js": "js",
        "ts": "ts",
        "py": "py",
        "java": "java",
        "rust": "rs",
        "dart": "dart",
        "go": "go"
    }

    # Generate filename
    filename = f"license-validator.{extensions[language]}"

    # Create a temporary file with the validator code
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(mode='w', suffix=f'.{extensions[language]}', delete=False) as temp_file:
        temp_file.write(code)
        temp_file_path = temp_file.name

    # Return the file for download
    return FileResponse(
        path=temp_file_path,
        filename=filename,
        media_type="text/plain",
        background=None  # Don't delete immediately, let FastAPI handle it
    )

@router.get("", response_model=schemas.PaginatedResponse)
def read_licenses(
    request: Request,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=200),
    tenant_id: Optional[UUID] = Query(None),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check if this is an HTMX request
    if request.headers.get("HX-Request"):
        # Return HTML for HTMX
        skip = (page - 1) * size
        licenses_list = crud.get_licenses(db, skip=skip, limit=size, tenant_id=tenant_id)
        query = db.query(models.License)
        if tenant_id:
            query = query.filter(models.License.tenant_id == tenant_id)
        total = query.count()
        pages = ceil(total / size) if size > 0 else 0
        return templates.TemplateResponse("licenses_list.html", {
            "request": request,
            "licenses": licenses_list,
            "page": page,
            "size": size,
            "total": total,
            "pages": pages
        })

    # Return JSON for API requests
    skip = (page - 1) * size
    licenses_list = crud.get_licenses_with_tenant(db, skip=skip, limit=size, tenant_id=tenant_id)
    query = db.query(models.License)
    if tenant_id:
        query = query.filter(models.License.tenant_id == tenant_id)
    total = query.count()
    return paginate_response(
        items=licenses_list,
        total=total,
        page=page,
        size=size
    )

@router.get("/{license_id}", response_model=schemas.LicenseResponse)
def read_license(
    license_id: UUID,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    license_with_tenant = crud.get_license_with_tenant(db, license_id=license_id)
    if license_with_tenant is None:
        raise HTTPException(status_code=404, detail="License not found")
    return license_with_tenant

@router.put("/{license_id}", response_model=schemas.LicenseResponse)
def update_license(
    license_id: UUID,
    license: schemas.LicenseUpdate = Body(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_license = crud.update_license(db, license_id=license_id, license_update=license)
    if db_license is None:
        raise HTTPException(status_code=404, detail="License not found")
    return crud.get_license_with_tenant(db, license_id=license_id)

@router.delete("/{license_id}")
def delete_license(
    license_id: UUID,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    success = crud.delete_license(db, license_id=license_id)
    if not success:
        raise HTTPException(status_code=404, detail="License not found")
    return {"message": "License deleted successfully"}

@router.get("/validate/{license_key}")
def validate_license(license_key: str, db: Session = Depends(get_db)):
    """
    Validate a license key.
    Returns validation status and license details if valid.
    """
    try:
        # Find the license in database by license_key
        db_license = db.query(models.License).filter(models.License.license_key == license_key).first()
        if not db_license:
            raise HTTPException(status_code=404, detail="License not found")

        # Check if license is active (tenant is active)
        tenant = crud.get_tenant(db, db_license.tenant_id)
        if not tenant or not tenant.is_active:
            return {
                "valid": False,
                "error": "License is inactive",
                "details": "Associated tenant is inactive or not found"
            }

        # Check validity period
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)

        # Calculate validity_days dynamically for licenses linked to subscriptions
        validity_days = db_license.validity_days
        if db_license.linked_subscription:
            subscription = crud.get_subscription(db, db_license.linked_subscription)
            if not subscription:
                return {
                    "valid": False,
                    "error": "License validation failed",
                    "details": "Linked subscription not found"
                }

            # Check if subscription is active
            if subscription.status != "active":
                return {
                    "valid": False,
                    "error": "License is inactive",
                    "details": f"Linked subscription is {subscription.status}"
                }

            issued_at = subscription.issue_date
            if issued_at.tzinfo is None:
                issued_at = issued_at.replace(tzinfo=timezone.utc)

            # Calculate validity_days based on current subscription (same logic as create_license)
            if subscription.end_date:
                from datetime import timedelta
                validity_period = subscription.end_date - subscription.issue_date
                validity_days = validity_period.days
            elif subscription.plan:
                plan = crud.get_plan_definition(db, subscription.plan_id)
                if plan and subscription.issue_date:
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
                    else:
                        validity_days = 30

            # Use subscription's end_date as expiry, or calculate from validity_days
            if subscription.end_date:
                expiry_date = subscription.end_date
                if expiry_date.tzinfo is None:
                    expiry_date = expiry_date.replace(tzinfo=timezone.utc)
            else:
                # Calculate expiry from validity_days (issued_at + validity_days - 1)
                expiry_date = issued_at + datetime.timedelta(days=validity_days - 1)
        else:
            # Use license's own dates
            issued_at = db_license.issued_at
            if issued_at.tzinfo is None:
                issued_at = issued_at.replace(tzinfo=timezone.utc)

            expiry_date = issued_at + datetime.timedelta(days=db_license.validity_days)

        # Check expiry if there is an expiry date
        if expiry_date and now > expiry_date:
            return {
                "valid": False,
                "error": "License has expired",
                "details": f"Expired on {expiry_date.strftime('%Y-%m-%d')}"
            }

        # License is valid
        return {
            "valid": True,
            "license": {
                "id": str(db_license.id),
                "license_key": db_license.license_key[:50] + "..." if len(db_license.license_key) > 50 else db_license.license_key,
                "tenant_id": str(db_license.tenant_id),
                "template_id": str(db_license.template_id) if db_license.template_id else None,
                "linked_subscription": db_license.linked_subscription,
                "issued_at": issued_at.isoformat(),
                "validity_days": validity_days,
                "expires_at": expiry_date.isoformat() if expiry_date else None,
                "payload": db_license.payload
            },
            "message": "License is valid and active"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation error: {str(e)}")

@router.post("/validate-file")
def validate_license_file(
    license_key: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Validate an uploaded license file.
    Takes license key and license file, returns validation results.
    """
    try:
        # Step 1: The license key from the form is base64-encoded, decode it to get the actual license key
        print(f"DEBUG: validate-file - Encoded license key: {license_key[:100]}...")
        try:
            search_key = base64.b64decode(license_key).decode('utf-8')
        except Exception as e:
            print(f"DEBUG: validate-file - Failed to decode license key: {e}")
            return {
                "parsing": "failed",
                "validity": "invalid",
                "signature": "verification_failed",
                "error": f"Invalid base64 license key: {e}"
            }
        print(f"DEBUG: validate-file - Decoded license key: {search_key[:100]}...")

        db_license = db.query(models.License).filter(models.License.license_key == search_key).first()
        if not db_license:
            # Debug: Show all available license keys
            all_keys = db.query(models.License.license_key).all()
            print(f"DEBUG: validate-file - License key not found. Available keys (first 50 chars each):")
            for i, (key,) in enumerate(all_keys[:5]):
                print(f"  {i+1}: {key[:50]}")
            return {
                "parsing": "failed",
                "validity": "invalid",
                "signature": "verification_failed",
                "error": "License key not found in database"
            }
        print(f"DEBUG: validate-file - License found! ID: {db_license.id}")

        # Step 2: Read the uploaded file content (license files are hybrid encrypted)
        encrypted_content = file.file.read().decode('utf-8').strip()

        # Get master private key and decrypt using hybrid decryption
        try:
            master_key_record = db.query(models.MasterKey).first()
            if not master_key_record:
                return {
                    "parsing": "failed",
                    "validity": "invalid",
                    "signature": "verification_failed",
                    "error": "Master key not configured"
                }
            decrypted_content = hybrid_decrypt(encrypted_content, master_key_record.private_key)
            license_data = json.loads(decrypted_content)
            parsing_status = "success"  # File parsed successfully
        except Exception as e:
            return {
                "parsing": "failed",
                "validity": "invalid",
                "signature": "verification_failed",
                "error": f"Failed to decrypt or parse license file: {str(e)}"
            }

        # Step 5: Verify signature using the public key (license_key)
        if "license" in license_data and "signature" in license_data:
            license_json = json.dumps(license_data["license"], separators=(',', ':'))
            signature_verified = verify_signature(license_json, license_data["signature"], db_license.license_key)
            signature_status = "verified" if signature_verified else "verification_failed"
        else:
            signature_status = "verification_failed"

        # Step 6: Check validity (expiry)
        validity_status = "invalid"
        if "license" in license_data:
            license_info = license_data["license"]
            try:
                from datetime import datetime, timezone

                # Check if license is linked to subscription
                linked_subscription = license_info.get("linked_subscription")
                if linked_subscription:
                    # For subscription-linked licenses, validate against current subscription data
                    try:
                        subscription = crud.get_subscription(db, linked_subscription)
                        if subscription and subscription.status == "active":
                            # Calculate validity based on current subscription (same logic as create_license)
                            issued_at = subscription.issue_date
                            if issued_at.tzinfo is None:
                                issued_at = issued_at.replace(tzinfo=timezone.utc)

                            if subscription.end_date:
                                from datetime import timedelta
                                validity_period = subscription.end_date - subscription.issue_date
                                validity_days = validity_period.days
                                expiry_date = subscription.end_date
                                if expiry_date.tzinfo is None:
                                    expiry_date = expiry_date.replace(tzinfo=timezone.utc)
                            elif subscription.plan:
                                plan = crud.get_plan_definition(db, subscription.plan_id)
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
                                    else:
                                        validity_days = 30

                                    expiry_date = issued_at + timedelta(days=validity_days - 1)

                                    # Check if current time is before expiry
                                    now = datetime.now(timezone.utc)
                                    if now <= expiry_date:
                                        validity_status = "valid"
                                    else:
                                        validity_status = "invalid"
                                else:
                                    validity_status = "invalid"
                            else:
                                validity_status = "invalid"
                        else:
                            validity_status = "invalid"
                    except Exception as e:
                        print(f"Error validating subscription-linked license: {e}")
                        validity_status = "invalid"
                else:
                    # Standard license validation
                    if "issued_at" in license_info and "validity_days" in license_info:
                        issued_at_str = license_info["issued_at"]
                        validity_days = license_info["validity_days"]

                        # Parse issued_at (handle different formats)
                        if isinstance(issued_at_str, str):
                            try:
                                issued_at = datetime.fromisoformat(issued_at_str.replace('Z', '+00:00'))
                            except ValueError:
                                issued_at = datetime.fromisoformat(issued_at_str)
                        else:
                            issued_at = datetime.fromisoformat(str(issued_at_str))

                        # Ensure timezone awareness
                        if issued_at.tzinfo is None:
                            issued_at = issued_at.replace(tzinfo=timezone.utc)

                        # Calculate expiry date (add validity_days - 1 to issued_at)
                        expiry_date = issued_at + timedelta(days=validity_days - 1)

                        # Check if current time is before expiry
                        now = datetime.now(timezone.utc)
                        if now <= expiry_date:
                            validity_status = "valid"
                        else:
                            validity_status = "invalid"
                    else:
                        validity_status = "invalid"

            except Exception as e:
                validity_status = "invalid"
                print(f"Error checking validity: {e}")

        # Step 7: Return validation results
        return {
            "parsing": parsing_status,
            "validity": validity_status,
            "signature": signature_status,
            "license_info": license_data.get("license", {}) if parsing_status == "success" else None
        }

    except Exception as e:
        return {
            "parsing": "failed",
            "validity": "invalid",
            "signature": "verification_failed",
            "error": f"Unexpected error: {str(e)}"
        }

@router.get("/issue")
def issue_license_file(encoded_license_key: str, db: Session = Depends(get_db)):
    """
    Issue a license file for download.
    Input: base64 encoded license key
    Output: Encrypted license file (license.lic)
    """
    try:
        # Decode the base64 encoded license key
        license_key_b64 = encoded_license_key
        license_key = base64.b64decode(license_key_b64).decode('utf-8')
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid base64 encoded license key")

    # Find the license in database by license_key
    db_license = db.query(models.License).filter(models.License.license_key == license_key).first()
    if not db_license:
        raise HTTPException(status_code=404, detail="License not found")

    # Calculate validity_days dynamically for licenses linked to subscriptions
    validity_days = db_license.validity_days
    expires_at = None
    if db_license.linked_subscription:
        subscription = crud.get_subscription(db, db_license.linked_subscription)
        if subscription:
            # Use same logic as create_license
            if subscription.end_date:
                from datetime import timedelta
                validity_period = subscription.end_date - subscription.issue_date
                validity_days = validity_period.days
                expires_at = subscription.end_date.isoformat()
            elif subscription.plan and subscription.issue_date:
                plan = crud.get_plan_definition(db, subscription.plan_id)
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

                    # Calculate expires_at
                    from datetime import timedelta
                    expiry_date = subscription.issue_date + timedelta(days=validity_days - 1)
                    expires_at = expiry_date.isoformat()

    # Create the license file structure
    license_data = {
        "license": {
            "id": str(db_license.id),
            "tenant_id": str(db_license.tenant_id),
            "linked_subscription": db_license.linked_subscription,
            "issued_at": db_license.issued_at.isoformat() if db_license.issued_at else None,
            "validity_days": validity_days,
            "payload": db_license.payload
        },
        "signature": ""
    }

    # Include expires_at if available
    if expires_at:
        license_data["license"]["expires_at"] = expires_at

    # Convert to JSON string for signing
    license_json = json.dumps(license_data["license"], separators=(',', ':'))

    # Sign the license data
    signature = sign_payload(license_json, db_license.license_secret)

    # Add signature to the data
    license_data["signature"] = signature

    # Get master public key and encrypt the complete data using hybrid encryption
    master_key_record = db.query(models.MasterKey).first()
    if not master_key_record:
        raise HTTPException(status_code=500, detail="Master key not configured")
    complete_json = json.dumps(license_data, separators=(',', ':'))
    encrypted_json = hybrid_encrypt(complete_json, master_key_record.public_key)

    # Create a temporary file
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(mode='w', suffix='.lic', delete=False) as temp_file:
        temp_file.write(encrypted_json)
        temp_file_path = temp_file.name

    # Return the file for download
    return FileResponse(
        path=temp_file_path,
        filename="license.lic",
        media_type="application/octet-stream",
        background=None  # Don't delete immediately, let FastAPI handle it
    )
