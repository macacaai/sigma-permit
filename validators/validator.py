import os
import json
import base64
import hashlib
import requests
from cryptography.hazmat.primitives import hashes, ciphers, algorithms, modes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization
from datetime import datetime, timezone
import sys

MASTER_PRIVATE_KEY = "MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC37s7Bu4HCpJZ9Ghppfe9vad9eUUcjF72sd8aRLGZOLIbeF4tkl8On79DKFVi35ySMyphDRDBteBBXEMgmrjA+SNbw7v6gDWcN0EJll+pQVUAfyimCQmhVcqsN+RE/IKVQtSOGcJxa5JbG/MsBZQR4f5aZY6YpNfX51TbY/iaQMIh9C7LurM6HXZpllwqjpTdGXS3sdgCnVwFAO1UYMKUL1c6qQ9XmSAVgeNjM0mM82L6aYHxJt2q82gu5GX0AT+pIOSHf9TjqMu9a/MyKoDkRmznqBHRV2PJJKnSy+/d6A9bGnseqDgRg/CvdjiBNM1P3D4WTFDvUN6zREtLRnHydAgMBAAECggEAAMGCfVlVQdowpCL5/iT+WZQzJCLBYBY2OVc6Aa66XOfh8K0NbZm8vBvy3QxpaO1nlmHew6gBavHAtMWPjQPPlEdIWtp17BfMrJ8xJqm71Mivksc0lHchZqMqAMyyksfXkMADKAeecjaDnXMR19efxRRWfMWOu+yfg39U0l95A8QC1uDTwDDDBvrIO4EzKo2sDG1dM3W7fg89ZaUtK/WDcnuOHh8KorUZQHKIFVZ1zOfJiW3VblcPU86RxTa9ZJywCUX6I2+rU0h3/CH+Wo4BOEYm7cGcxUPw2XqYKyt7uTPOuwkurHVA4lyxcTp3j52zpwyfZ+08881eizA1a8nxIQKBgQDq+fz3N5ud84iuo+sDeMw0Yo7IyUUKSWJ7a4+gdaaePedLBMKBeynx/9l7/XlbUjCH7YF6LtSdssDDJocCIMYDprKvd/9V1lF+wexfGfVISV3SUfI3JC+enIbA2ZV4SmBIn4XIesKrnh4Pi1yBYkQ5oYv8SCqeQwHkTOihN2whDwKBgQDIY7D8phrN+MPtYodFgDqoLoDOz0tOAqUynP800q4TezyElnZ4xp4dUFpsJGAvzoi+Y/bnU3L1Z1hq/xPN3Y+fEGdSpZvREEZBIpbvdCEEKSdZvZOjpZROheGAvx4LNSdrxFQ0HuNq3oRQ/V5+hZ1r/xLx9WO17MkZGFxOwNBvkwKBgQDMcIyDm0It/wFg0QVck/E3crjAQT1sYcTplP/1n+dDrqBaSN3iQgKQpwXWNwcrSSsoWKBaafxa6HeGUzMLyu/9pT+6IzFowXtOSfMaGz+pkQusPdf72eQEoDMt/yFo820qQoDnmMdfAcctxxbJC3JIoiFlcnSCFdLDi5arDclqSQKBgQCE0w+NZ8x8mlfEEXr4ZnZ649gdPOn9W2OEmOvQZ5Va9GS4vcLpaz2C0LAe3j2jcpLRIBGYY4ffghDpWwoVeraoCId0ELGncdIfen3xWlhIGb8rjK0/25DiO3utiwCvDRyEIi5uHctAGx45ULhBxO8Dlp9IIg9llv301GDbEpMWYQKBgHjlBB071edG7a9xLpuL3tf7/QP2AA05Ugdw92Jp920sd5Kb7G3OwCEu5otr4yJwpEvw3ZnnZW2NPp/oPPqQrH+GSmhNiStRX5anvHpbxsP4XcqvZzd6Zx5quM42ZIX4BK4bTocRpgylAj6lapaxkBA7vujqnZ/uRndLMAWOFsmE"

def hybrid_decrypt(encrypted_data, private_key_b64):
    from cryptography.hazmat.primitives import ciphers, algorithms, modes
    parts = encrypted_data.split(':', 1)
    if len(parts) != 2:
        raise ValueError('Invalid hybrid encrypted data format')

    encrypted_aes_key_b64, aes_encrypted_b64 = parts

    # Decrypt AES key with RSA
    private_der = base64.b64decode(private_key_b64)
    private_key = serialization.load_der_private_key(private_der, password=None)
    encrypted_aes_key = base64.b64decode(encrypted_aes_key_b64)
    aes_key = private_key.decrypt(
        encrypted_aes_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    # Decrypt data with AES
    aes_encrypted = base64.b64decode(aes_encrypted_b64)
    iv = aes_encrypted[:12]
    tag = aes_encrypted[12:28]
    ciphertext = aes_encrypted[28:]

    cipher = ciphers.Cipher(algorithms.AES(aes_key), modes.GCM(iv, tag))
    decryptor = cipher.decryptor()
    plaintext = decryptor.update(ciphertext) + decryptor.finalize()

    return plaintext.decode('utf-8')

def validate_license():
    license_key = os.getenv('LICENSE_KEY')
    if not license_key:
        print("LICENSE_KEY environment variable not set", file=sys.stderr)
        return False

    license_file = './license.lic'
    downloaded = False

    def validate_file():
        nonlocal downloaded
        if not os.path.exists(license_file):
            if downloaded:
                print("License file not found after download", file=sys.stderr)
                return False
            print("License file not found, downloading...")
            download_success = download_license()
            if not download_success:
                print("Failed to download license", file=sys.stderr)
                return False
            downloaded = True

        try:
            with open(license_file, 'r') as f:
                encrypted_content = f.read().strip()
            decrypted_content = hybrid_decrypt(encrypted_content, MASTER_PRIVATE_KEY)
            data = json.loads(decrypted_content)

            license_json = json.dumps(data['license'], separators=(',', ':'))

            # Load public key
            public_key_der = base64.b64decode(license_key)
            public_key = serialization.load_der_public_key(public_key_der)

            # Verify signature
            signature = base64.b64decode(data['signature'])
            public_key.verify(
                signature,
                license_json.encode('utf-8'),
                padding.PKCS1v15(),
                hashes.SHA256()
            )

            # Check expiry
            issued_at = datetime.fromisoformat(data['license']['issued_at'].replace('Z', '+00:00'))
            validity_days = data['license']['validity_days']
            expiry_date = issued_at.replace(hour=23, minute=59, second=59)
            expiry_date = expiry_date.replace(day=min(expiry_date.day + validity_days - 1,
                                                      28 if expiry_date.month == 2 else 30 if expiry_date.month in [4, 6, 9, 11] else 31))

            if datetime.now(timezone.utc) > expiry_date:
                if not downloaded:
                    print("License expired, downloading new license...")
                    download_success = download_license()
                    if not download_success:
                        print("Failed to download new license", file=sys.stderr)
                        return False
                    downloaded = True
                    return validate_file()
                else:
                    print("License expired after download", file=sys.stderr)
                    return False

            print("License is valid")
            return True

        except Exception as e:
            print(f"Error validating license: {e}", file=sys.stderr)
            if not downloaded:
                print("Downloading new license...")
                download_success = download_license()
                if not download_success:
                    print("Failed to download new license", file=sys.stderr)
                    return False
                downloaded = True
                return validate_file()
            else:
                print("Error validating license after download", file=sys.stderr)
                return False

    def download_license():
        try:
            encoded_key = base64.b64encode(license_key.encode('utf-8')).decode('utf-8')
            url = "https://your-api-domain.com/api/licenses/issue"
            params = {"encoded_license_key": encoded_key}

            response = requests.get(url, params=params)
            response.raise_for_status()

            with open(license_file, 'wb') as f:
                f.write(response.content)

            print("License downloaded successfully")
            return True

        except Exception as e:
            print(f"Download failed: {e}", file=sys.stderr)
            return False

    return validate_file()

if __name__ == "__main__":
    if validate_license():
        print("Validation successful")
        sys.exit(0)
    else:
        print("Validation failed", file=sys.stderr)
        sys.exit(1)