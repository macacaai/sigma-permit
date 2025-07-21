import json
from typing import Dict
from nacl import signing, exceptions as nacl_exc
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
import os

# Existing Ed25519 functions for signing
def canonical_json(data: Dict) -> bytes:
    return json.dumps(data, separators=(',', ':'), sort_keys=True).encode()

def generate_keypair() -> tuple[str, str]:
    sk = signing.SigningKey.generate()
    return sk.encode().hex(), sk.verify_key.encode().hex()

def sign_payload(payload: Dict, private_key_hex: str) -> str:
    sk = signing.SigningKey(bytes.fromhex(private_key_hex))
    signed = sk.sign(canonical_json(payload))
    return signed.signature.hex()

def verify_signature(payload: Dict, signature_hex: str, public_key_hex: str) -> bool:
    try:
        vk = signing.VerifyKey(bytes.fromhex(public_key_hex))
        vk.verify(canonical_json(payload), bytes.fromhex(signature_hex))
        return True
    except nacl_exc.BadSignatureError:
        return False
    except:
        return False

# New RSA encryption/decryption functions
def generate_rsa_keypair() -> tuple[str, str]:
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    priv_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode()
    
    public_key = private_key.public_key()
    pub_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode()
    
    return priv_pem, pub_pem

def encrypt_payload(payload: Dict, public_key_pem: str) -> str:
    public_key = serialization.load_pem_public_key(
        public_key_pem.encode(),
        backend=default_backend()
    )
    payload_bytes = canonical_json(payload)
    encrypted = public_key.encrypt(
        payload_bytes,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return encrypted.hex()

def decrypt_payload(encrypted_hex: str, private_key_pem: str) -> Dict:
    private_key = serialization.load_pem_private_key(
        private_key_pem.encode(),
        password=None,
        backend=default_backend()
    )
    decrypted = private_key.decrypt(
        bytes.fromhex(encrypted_hex),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return json.loads(decrypted.decode())
