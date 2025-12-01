// Client-side cryptographic utilities using Web Crypto API
// These functions mirror the backend crypto_utils.py functions

// Hybrid decrypt function - decrypts data encrypted with RSA+AES-GCM
export async function hybridDecrypt(encryptedData: string, rsaPrivateKeyB64: string): Promise<string> {
  try {
    console.log('Starting hybrid decryption...');
    console.log('Encrypted data length:', encryptedData.length);
    console.log('RSA private key length:', rsaPrivateKeyB64?.length);

    // Split the encrypted data (format: "encrypted_aes_key:encrypted_data")
    const parts = encryptedData.split(':', 2);
    if (parts.length !== 2) {
      throw new Error('Invalid hybrid encrypted data format');
    }

    const [encryptedAesKeyB64, aesEncryptedB64] = parts;
    console.log('AES key part length:', encryptedAesKeyB64.length);
    console.log('Data part length:', aesEncryptedB64.length);

    // Decode base64 strings
    const encryptedAesKey = Uint8Array.from(atob(encryptedAesKeyB64), c => c.charCodeAt(0));
    const aesEncrypted = Uint8Array.from(atob(aesEncryptedB64), c => c.charCodeAt(0));
    console.log('Decoded AES key length:', encryptedAesKey.length);
    console.log('Decoded data length:', aesEncrypted.length);

    // Import RSA private key
    const rsaPrivateKeyDer = Uint8Array.from(atob(rsaPrivateKeyB64), c => c.charCodeAt(0));
    const privateKey = await crypto.subtle.importKey(
      'pkcs8',
      rsaPrivateKeyDer,
      {
        name: 'RSA-OAEP',
        hash: 'SHA-256',
      },
      false,
      ['decrypt']
    );

    // Decrypt AES key with RSA
    const aesKeyBytes = await crypto.subtle.decrypt(
      {
        name: 'RSA-OAEP',
      },
      privateKey,
      encryptedAesKey
    );

    // Extract IV, tag, and ciphertext from AES encrypted data
    // Format: IV (12 bytes) + Tag (16 bytes) + Ciphertext
    const iv = aesEncrypted.slice(0, 12);
    const tag = aesEncrypted.slice(12, 28);
    const ciphertext = aesEncrypted.slice(28);

    // Import AES key
    const aesKey = await crypto.subtle.importKey(
      'raw',
      aesKeyBytes,
      {
        name: 'AES-GCM',
        length: 256,
      },
      false,
      ['decrypt']
    );

    // Combine ciphertext and tag for GCM decryption
    const combinedCiphertext = new Uint8Array(ciphertext.length + tag.length);
    combinedCiphertext.set(ciphertext);
    combinedCiphertext.set(tag, ciphertext.length);

    // Decrypt with AES-GCM
    const plaintext = await crypto.subtle.decrypt(
      {
        name: 'AES-GCM',
        iv: iv,
      },
      aesKey,
      combinedCiphertext
    );

    // Convert to string
    return new TextDecoder().decode(plaintext);
  } catch (error) {
    console.error('Hybrid decryption failed:', error);
    throw new Error(`Hybrid decryption failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}

// Verify signature function
export async function verifySignature(data: string, signature: string, publicKeyB64: string): Promise<boolean> {
  try {
    console.log('Starting signature verification...');
    console.log('Data length:', data.length);
    console.log('Signature length:', signature.length);
    console.log('Public key length:', publicKeyB64?.length);

    // Import RSA public key
    const publicKeyDer = Uint8Array.from(atob(publicKeyB64), c => c.charCodeAt(0));
    const publicKey = await crypto.subtle.importKey(
      'spki',
      publicKeyDer,
      {
        name: 'RSASSA-PSS',
        hash: 'SHA-256',
      },
      false,
      ['verify']
    );

    // Decode signature
    const signatureBytes = Uint8Array.from(atob(signature), c => c.charCodeAt(0));

    // Hash the data
    const dataBytes = new TextEncoder().encode(data);
    const hashBuffer = await crypto.subtle.digest('SHA-256', dataBytes);

    // Verify signature
    const isValid = await crypto.subtle.verify(
      {
        name: 'RSASSA-PSS',
        saltLength: 32, // PSS salt length (matches backend)
      },
      publicKey,
      signatureBytes,
      hashBuffer
    );

    return isValid;
  } catch (error) {
    console.error('Signature verification failed:', error);
    return false;
  }
}

// Utility function to check if Web Crypto API is available
export function isWebCryptoAvailable(): boolean {
  return typeof crypto !== 'undefined' && typeof crypto.subtle !== 'undefined';
}

// Fallback for environments without Web Crypto API
export function hybridDecryptFallback(encryptedData: string, rsaPrivateKeyB64: string): string {
  // This is a simplified fallback that won't work with real encrypted data
  // In production, you might want to use a library like node-forge
  throw new Error('Web Crypto API not available. Please use a modern browser.');
}