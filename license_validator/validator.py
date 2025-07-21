import json, logging
from datetime import datetime  # Added for expiration check
from common.crypto import verify_signature, decrypt_payload
from common.models import SignedLicense

logger = logging.getLogger(__name__)

import os

# Validator's hardcoded private key for decryption
VALIDATOR_PRIVATE_KEY = """-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDH9uW8dTdLm8Oc
... [full key would be here in real implementation] ...
-----END PRIVATE KEY-----"""

from license_validator.config import settings

def validate(license_path: str = None) -> bool:
    # Use configured path if not specified
    license_path = license_path or settings.LICENSE_FILE_PATH
    trusted_public_key = os.getenv("TRUSTED_PUBLIC_KEY")
    if not trusted_public_key:
        logger.error("TRUSTED_PUBLIC_KEY environment variable not set")
        return False
        
    try:
        with open(license_path, "r") as f:
            data = json.load(f)
        lic = SignedLicense(**data)
        
        # Verify the signature of the encrypted payload
        if not verify_signature({"encrypted_payload": lic.encrypted_payload}, 
                               lic.signature, 
                               trusted_public_key):
            logger.error("Signature verification failed")
            return False
            
        # Decrypt the payload using validator's private key
        try:
            decrypted_payload = decrypt_payload(lic.encrypted_payload, VALIDATOR_PRIVATE_KEY)
        except Exception as e:
            logger.error(f"Decryption failed: {str(e)}")
            return False
            
        # Verify the issuer's public key matches trusted key
        if decrypted_payload.get("issuer_public_key") != trusted_public_key:
            logger.error("Issuer public key does not match trusted key")
            return False
            
        # Verify expiration
        expires_at = decrypted_payload.get("expires_at")
        if not expires_at:
            logger.error("Missing expiration date")
            return False
            
        # Convert to datetime and check expiration
        expiration_time = datetime.fromisoformat(expires_at.replace('Z', ''))
        if datetime.utcnow() > expiration_time:
            logger.error("License has expired")
            return False
            
        return True
        
    except Exception as ex:
        logger.error("License validation error: %s", ex)
        return False
