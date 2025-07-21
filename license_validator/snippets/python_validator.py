import json
import os
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
from datetime import datetime

def validate_license(license_path: str, trusted_public_key: str) -> bool:
    """Validates a license file for Python applications"""
    try:
        # Read license file
        with open(license_path, 'r') as f:
            data = json.load(f)
        
        encrypted_payload = data.get('encrypted_payload')
        signature = data.get('signature')
        
        if not encrypted_payload or not signature:
            print("Invalid license format")
            return False
        
        # Verify signature
        public_key = serialization.load_pem_public_key(
            trusted_public_key.encode(),
            backend=default_backend()
        )
        public_key.verify(
            bytes.fromhex(signature),
            encrypted_payload.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        # Decrypt payload (using your private key - should be kept secure!)
        # This is just a placeholder - implement your decryption logic
        # decrypted = decrypt(encrypted_payload, PRIVATE_KEY)
        # payload = json.loads(decrypted)
        payload = {"expires_at": "2025-12-31T23:59:59Z"}  # Example
        
        # Check expiration
        expires_at = payload.get("expires_at")
        if not expires_at:
            print("Missing expiration date")
            return False
            
        expiration_time = datetime.fromisoformat(expires_at.replace('Z', ''))
        if datetime.utcnow() > expiration_time:
            print("License has expired")
            return False
            
        return True
        
    except Exception as e:
        print(f"License validation error: {str(e)}")
        return False

# Example usage:
# if validate_license("license.json", "-----BEGIN PUBLIC KEY-----..."):
#     print("Valid license")
# else:
#     print("Invalid license")
