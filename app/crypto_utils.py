import uuid
import base64
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend


def generate_license_keypair() -> tuple[str, str]:
    """Generate a license key pair (public key, private key) as base64-encoded DER."""
    # Generate RSA private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )

    # Serialize private key to DER format
    private_der = private_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    # Get public key and serialize to DER format
    public_key = private_key.public_key()
    public_der = public_key.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    # Return as base64-encoded DER strings
    return base64.b64encode(public_der).decode('utf-8'), base64.b64encode(private_der).decode('utf-8')





def get_public_key_from_secret(license_secret: str) -> str:
    """Extract public key from base64-encoded private key DER."""
    # Decode base64 to get DER bytes
    private_der = base64.b64decode(license_secret)

    private_key = serialization.load_der_private_key(
        private_der,
        password=None,
        backend=default_backend()
    )

    public_key = private_key.public_key()
    public_der = public_key.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    # Return as base64-encoded DER (consistent with new format)
    return base64.b64encode(public_der).decode('utf-8')


def sign_payload(payload: str, license_secret: str) -> str:
    """Sign a payload using the base64-encoded private key DER."""
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding

    # Decode base64 to get DER bytes
    private_der = base64.b64decode(license_secret)

    private_key = serialization.load_der_private_key(
        private_der,
        password=None,
        backend=default_backend()
    )

    signature = private_key.sign(
        payload.encode('utf-8'),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )

    return base64.b64encode(signature).decode('utf-8')


def verify_signature(payload: str, signature: str, license_key: str) -> bool:
    """Verify a signature using the base64-encoded public key DER."""
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding

    # Decode base64 to get DER bytes
    public_der = base64.b64decode(license_key)

    public_key = serialization.load_der_public_key(
        public_der,
        backend=default_backend()
    )

    try:
        public_key.verify(
            base64.b64decode(signature),
            payload.encode('utf-8'),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True
    except:
        return False


def encrypt_payload(payload: str, public_key_pem: str) -> str:
    """Encrypt a payload using the public key."""
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding

    public_key = serialization.load_pem_public_key(
        public_key_pem.encode('utf-8'),
        backend=default_backend()
    )

    encrypted = public_key.encrypt(
        payload.encode('utf-8'),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    return base64.b64encode(encrypted).decode('utf-8')


def decrypt_payload(encrypted_payload: str, license_secret: str) -> str:
    """Decrypt a payload using the private key."""
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding

    private_key = serialization.load_pem_private_key(
        license_secret.encode('utf-8'),
        password=None,
        backend=default_backend()
    )

    decrypted = private_key.decrypt(
        base64.b64decode(encrypted_payload),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    return decrypted.decode('utf-8')


def der_to_pem_public_key(der_b64: str) -> str:
    """Convert base64-encoded DER public key to PEM format."""
    der_bytes = base64.b64decode(der_b64)
    public_key = serialization.load_der_public_key(der_bytes, backend=default_backend())

    pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    return pem.decode('utf-8')


def der_to_pem_private_key(der_b64: str) -> str:
    """Convert base64-encoded DER private key to PEM format."""
    der_bytes = base64.b64decode(der_b64)
    private_key = serialization.load_der_private_key(der_bytes, password=None, backend=default_backend())

    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    return pem.decode('utf-8')

def generate_rsa_keypair() -> tuple[str, str]:
    """Generate RSA key pair and return (public_key_b64, private_key_b64)."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )

    public_key = private_key.public_key()
    public_der = public_key.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    private_der = private_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    return base64.b64encode(public_der).decode('utf-8'), base64.b64encode(private_der).decode('utf-8')

def rsa_encrypt(data: str, public_key_b64: str) -> str:
    """Encrypt data with RSA public key."""
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.primitives import hashes

    public_der = base64.b64decode(public_key_b64)
    public_key = serialization.load_der_public_key(public_der, backend=default_backend())

    encrypted = public_key.encrypt(
        data.encode('utf-8'),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return base64.b64encode(encrypted).decode('utf-8')

def rsa_decrypt(encrypted_b64: str, private_key_b64: str) -> str:
    """Decrypt data with RSA private key."""
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.primitives import hashes

    private_der = base64.b64decode(private_key_b64)
    private_key = serialization.load_der_private_key(private_der, password=None, backend=default_backend())

    encrypted = base64.b64decode(encrypted_b64)
    decrypted = private_key.decrypt(
        encrypted,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return decrypted.decode('utf-8')

def hybrid_encrypt(data: str, rsa_public_key_b64: str) -> str:
    """Encrypt data using hybrid encryption (AES + RSA)."""
    from cryptography.hazmat.primitives.ciphers import algorithms, modes
    from cryptography.hazmat.primitives import ciphers
    from cryptography.hazmat.primitives.asymmetric import padding
    import os

    # Generate a random AES key and IV
    aes_key = os.urandom(32)  # 256-bit AES key
    iv = os.urandom(12)  # 96-bit IV for GCM

    # Encrypt data with AES-GCM
    cipher = ciphers.Cipher(algorithms.AES(aes_key), modes.GCM(iv))
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(data.encode('utf-8')) + encryptor.finalize()
    tag = encryptor.tag

    # Combine IV + tag + ciphertext
    aes_encrypted = iv + tag + ciphertext

    # Encrypt AES key with RSA
    rsa_public_der = base64.b64decode(rsa_public_key_b64)
    rsa_public_key = serialization.load_der_public_key(rsa_public_der, backend=default_backend())

    encrypted_aes_key = rsa_public_key.encrypt(
        aes_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    # Return format: base64(encrypted_aes_key) + ":" + base64(aes_encrypted_data)
    return base64.b64encode(encrypted_aes_key).decode('utf-8') + ":" + base64.b64encode(aes_encrypted).decode('utf-8')

def hybrid_decrypt(encrypted_data: str, rsa_private_key_b64: str) -> str:
    """Decrypt data using hybrid decryption (AES + RSA)."""
    from cryptography.hazmat.primitives.ciphers import algorithms, modes
    from cryptography.hazmat.primitives import ciphers
    from cryptography.hazmat.primitives.asymmetric import padding

    # Split the encrypted data
    parts = encrypted_data.split(":", 1)
    if len(parts) != 2:
        raise ValueError("Invalid hybrid encrypted data format")

    encrypted_aes_key_b64, aes_encrypted_b64 = parts

    # Decrypt AES key with RSA
    rsa_private_der = base64.b64decode(rsa_private_key_b64)
    rsa_private_key = serialization.load_der_private_key(rsa_private_der, password=None, backend=default_backend())

    encrypted_aes_key = base64.b64decode(encrypted_aes_key_b64)
    aes_key = rsa_private_key.decrypt(
        encrypted_aes_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    # Decrypt data with AES
    aes_encrypted = base64.b64decode(aes_encrypted_b64)
    iv = aes_encrypted[:12]  # First 12 bytes are IV
    tag = aes_encrypted[12:28]  # Next 16 bytes are tag
    ciphertext = aes_encrypted[28:]  # Rest is ciphertext

    cipher = ciphers.Cipher(algorithms.AES(aes_key), modes.GCM(iv, tag))
    decryptor = cipher.decryptor()
    plaintext = decryptor.update(ciphertext) + decryptor.finalize()

    return plaintext.decode('utf-8')
