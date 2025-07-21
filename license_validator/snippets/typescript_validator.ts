import * as crypto from 'crypto';
import * as fs from 'fs';

interface LicenseData {
    encrypted_payload: string;
    signature: string;
}

interface LicensePayload {
    expires_at: string;
}

function validateLicense(licensePath: string, trustedPublicKey: string): boolean {
    try {
        // Read license file
        const data: LicenseData = JSON.parse(fs.readFileSync(licensePath, 'utf8'));
        
        const encryptedPayload = data.encrypted_payload;
        const signature = data.signature;
        
        if (!encryptedPayload || !signature) {
            console.error("Invalid license format");
            return false;
        }
        
        // Verify signature
        const verify = crypto.createVerify('SHA256');
        verify.update(encryptedPayload);
        const isValid = verify.verify(
            trustedPublicKey,
            Buffer.from(signature, 'hex')
        );
        
        if (!isValid) {
            console.error("Signature verification failed");
            return false;
        }
        
        // Decrypt payload (placeholder - implement your decryption logic)
        // const decrypted = decrypt(encryptedPayload, privateKey);
        // const payload: LicensePayload = JSON.parse(decrypted);
        const payload: LicensePayload = { expires_at: "2025-12-31T23:59:59Z" }; // Example
        
        // Check expiration
        const expiresAt = payload.expires_at;
        if (!expiresAt) {
            console.error("Missing expiration date");
            return false;
        }
        
        const expirationTime = new Date(expiresAt);
        if (new Date() > expirationTime) {
            console.error("License has expired");
            return false;
        }
        
        return true;
        
    } catch (err) {
        console.error(`License validation error: ${(err as Error).message}`);
        return false;
    }
}

// Example usage:
// const trustedPublicKey = `-----BEGIN PUBLIC KEY-----...`;
// if (validateLicense('license.json', trustedPublicKey)) {
//     console.log('Valid license');
// } else {
//     console.log('Invalid license');
// }
