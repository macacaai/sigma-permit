<script lang="ts">
   import { toast } from 'svelte-french-toast';
   import {
     Shield,
     Upload,
     FileText,
     CheckCircle,
     XCircle,
     AlertTriangle,
     Download,
     Eye,
     Key,
     Code
   } from 'lucide-svelte';

   import { licenseApi } from '$lib/api';

   let activeTab = 'validate';

   let licenseKey = '';
   let selectedFile: File | null = null;
   let validationResult: any = null;
   let isValidating = false;
   let showLicenseKeyPreview = false;

   let selectedLanguage = 'js';
   let validatorCode = '';
   let masterKeys: any[] = [];
   let isDownloading = false;

   const languages = [
     { value: 'js', label: 'JavaScript' },
     { value: 'ts', label: 'TypeScript' },
     { value: 'py', label: 'Python' },
     { value: 'java', label: 'Java' },
     { value: 'rust', label: 'Rust' },
     { value: 'dart', label: 'Dart' },
     { value: 'go', label: 'Go' }
   ];

   const baseUrl = 'https://your-api-domain.com'; // TODO: Make this configurable

   const codeTemplates = {
     js: `const fs = require('fs');
const crypto = require('crypto');
const https = require('https');

const MASTER_PRIVATE_KEY = "MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC37s7Bu4HCpJZ9Ghppfe9vad9eUUcjF72sd8aRLGZOLIbeF4tkl8On79DKFVi35ySMyphDRDBteBBXEMgmrjA+SNbw7v6gDWcN0EJll+pQVUAfyimCQmhVcqsN+RE/IKVQtSOGcJxa5JbG/MsBZQR4f5aZY6YpNfX51TbY/iaQMIh9C7LurM6HXZpllwqjpTdGXS3sdgCnVwFAO1UYMKUL1c6qQ9XmSAVgeNjM0mM82L6aYHxJt2q82gu5GX0AT+pIOSHf9TjqMu9a/MyKoDkRmznqBHRV2PJJKnSy+/d6A9bGnseqDgRg/CvdjiBNM1P3D4WTFDvUN6zREtLRnHydAgMBAAECggEAAMGCfVlVQdowpCL5/iT+WZQzJCLBYBY2OVc6Aa66XOfh8K0NbZm8vBvy3QxpaO1nlmHew6gBavHAtMWPjQPPlEdIWtp17BfMrJ8xJqm71Mivksc0lHchZqMqAMyyksfXkMADKAeecjaDnXMR19efxRRWfMWOu+yfg39U0l95A8QC1uDTwDDDBvrIO4EzKo2sDG1dM3W7fg89ZaUtK/WDcnuOHh8KorUZQHKIFVZ1zOfJiW3VblcPU86RxTa9ZJywCUX6I2+rU0h3/CH+Wo4BOEYm7cGcxUPw2XqYKyt7uTPOuwkurHVA4lyxcTp3j52zpwyfZ+08881eizA1a8nxIQKBgQDq+fz3N5ud84iuo+sDeMw0Yo7IyUUKSWJ7a4+gdaaePedLBMKBeynx/9l7/XlbUjCH7YF6LtSdssDDJocCIMYDprKvd/9V1lF+wexfGfVISV3SUfI3JC+enIbA2ZV4SmBIn4XIesKrnh4Pi1yBYkQ5oYv8SCqeQwHkTOihN2whDwKBgQDIY7D8phrN+MPtYodFgDqoLoDOz0tOAqUynP800q4TezyElnZ4xp4dUFpsJGAvzoi+Y/bnU3L1Z1hq/xPN3Y+fEGdSpZvREEZBIpbvdCEEKSdZvZOjpZROheGAvx4LNSdrxFQ0HuNq3oRQ/V5+hZ1r/xLx9WO17MkZGFxOwNBvkwKBgQDMcIyDm0It/wFg0QVck/E3crjAQT1sYcTplP/1n+dDrqBaSN3iQgKQpwXWNwcrSSsoWKBaafxa6HeGUzMLyu/9pT+6IzFowXtOSfMaGz+pkQusPdf72eQEoDMt/yFo820qQoDnmMdfAcctxxbJC3JIoiFlcnSCFdLDi5arDclqSQKBgQCE0w+NZ8x8mlfEEXr4ZnZ649gdPOn9W2OEmOvQZ5Va9GS4vcLpaz2C0LAe3j2jcpLRIBGYY4ffghDpWwoVeraoCId0ELGncdIfen3xWlhIGb8rjK0/25DiO3utiwCvDRyEIi5uHctAGx45ULhBxO8Dlp9IIg9llv301GDbEpMWYQKBgHjlBB071edG7a9xLpuL3tf7/QP2AA05Ugdw92Jp920sd5Kb7G3OwCEu5otr4yJwpEvw3ZnnZW2NPp/oPPqQrH+GSmhNiStRX5anvHpbxsP4XcqvZzd6Zx5quM42ZIX4BK4bTocRpgylAj6lapaxkBA7vujqnZ/uRndLMAWOFsmE";

function hybridDecrypt(encryptedData, privateKeyB64) {
   const parts = encryptedData.split(':', 2);
   if (parts.length !== 2) {
       throw new Error('Invalid hybrid encrypted data format');
   }

   const [encryptedAesKeyB64, aesEncryptedB64] = parts;

   // Decrypt AES key with RSA
   const privateKey = crypto.createPrivateKey({
       key: Buffer.from(privateKeyB64, 'base64'),
       format: 'der',
       type: 'pkcs8'
   });
   const encryptedAesKey = Buffer.from(encryptedAesKeyB64, 'base64');
   const aesKey = crypto.privateDecrypt({
       key: privateKey,
       padding: crypto.constants.RSA_PKCS1_OAEP_PADDING,
       oaepHash: 'sha256'
   }, encryptedAesKey);

   // Decrypt data with AES
   const aesEncrypted = Buffer.from(aesEncryptedB64, 'base64');
   const iv = aesEncrypted.subarray(0, 12);
   const tag = aesEncrypted.subarray(12, 28);
   const ciphertext = aesEncrypted.subarray(28);

   const decipher = crypto.createDecipherGCM('aes-256-gcm', aesKey);
   decipher.setAuthTag(tag);
   decipher.setIV(iv);
   let decrypted = decipher.update(ciphertext);
   decrypted = Buffer.concat([decrypted, decipher.final()]);

   return decrypted.toString('utf8');
}

async function validateLicense() {
   const licenseKey = process.env.LICENSE_KEY;
   if (!licenseKey) {
       console.error("LICENSE_KEY environment variable not set");
       return false;
   }

   const licenseFile = './license.lic';
   let downloaded = false;

   async function validateFile() {
       if (!fs.existsSync(licenseFile)) {
           if (downloaded) {
               console.error("License file not found after download");
               return false;
           }
           console.log("License file not found, downloading...");
           const downloadSuccess = await downloadLicense();
           if (!downloadSuccess) {
               console.error("Failed to download license");
               return false;
           }
           downloaded = true;
       }

       try {
           const encryptedContent = fs.readFileSync(licenseFile, 'utf8').trim();
           const decryptedContent = hybridDecrypt(encryptedContent, MASTER_PRIVATE_KEY);
           const data = JSON.parse(decryptedContent);
           const licenseJson = JSON.stringify(data.license);

           // Verify signature
           const publicKey = crypto.createPublicKey({
               key: Buffer.from(licenseKey, 'base64'),
               format: 'der',
               type: 'spki'
           });

           const signature = data.signature;
           const isValid = crypto.verify('sha256', Buffer.from(licenseJson), publicKey, Buffer.from(signature, 'base64'));

           if (!isValid) {
               if (!downloaded) {
                   console.log("Signature verification failed, downloading new license...");
                   const downloadSuccess = await downloadLicense();
                   if (!downloadSuccess) {
                       console.error("Failed to download new license");
                       return false;
                   }
                   downloaded = true;
                   return await validateFile();
               } else {
                   console.error("Signature verification failed after download");
                   return false;
               }
           }

           // Check expiry
           const issuedAt = new Date(data.license.issued_at);
           const validityDays = data.license.validity_days;
           const expiryDate = new Date(issuedAt);
           expiryDate.setDate(expiryDate.getDate() + validityDays);

           if (new Date() > expiryDate) {
               if (!downloaded) {
                   console.log("License expired, downloading new license...");
                   const downloadSuccess = await downloadLicense();
                   if (!downloadSuccess) {
                       console.error("Failed to download new license");
                       return false;
                   }
                   downloaded = true;
                   return await validateFile();
               } else {
                   console.error("License expired after download");
                   return false;
               }
           }

           console.log("License is valid");
           return true;

       } catch (error) {
           console.error("Error validating license:", error.message);
           if (!downloaded) {
               console.log("Downloading new license...");
               const downloadSuccess = await downloadLicense();
               if (!downloadSuccess) {
                   console.error("Failed to download new license");
                   return false;
               }
               downloaded = true;
               return await validateFile();
           } else {
               console.error("Error validating license after download");
               return false;
           }
       }
   }

   async function downloadLicense() {
       return new Promise((resolve) => {
           const encodedKey = Buffer.from(licenseKey).toString('base64');
           const url = \`\${baseUrl}/api/licenses/issue?encoded_license_key=\${encodeURIComponent(encodedKey)}\`;

           https.get(url, (res) => {
               if (res.statusCode !== 200) {
                   resolve(false);
                   return;
               }

               const fileStream = fs.createWriteStream(licenseFile);
               res.pipe(fileStream);

               fileStream.on('finish', () => {
                   fileStream.close();
                   console.log("License downloaded successfully");
                   resolve(true);
               });
           }).on('error', (err) => {
               console.error(\`Download failed: \${err.message}\`);
               resolve(false);
           });
       });
   }

   return await validateFile();
}

// Usage
validateLicense().then(success => {
   if (success) {
       console.log("Validation successful");
   } else {
       console.error("Validation failed");
       process.exit(1);
   }
}).catch(error => {
   console.error("Validation error:", error.message);
   process.exit(1);
});`,
     ts: `import * as fs from 'fs';
import * as crypto from 'crypto';
import * as https from 'https';

const MASTER_PRIVATE_KEY = "MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC37s7Bu4HCpJZ9Ghppfe9vad9eUUcjF72sd8aRLGZOLIbeF4tkl8On79DKFVi35ySMyphDRDBteBBXEMgmrjA+SNbw7v6gDWcN0EJll+pQVUAfyimCQmhVcqsN+RE/IKVQtSOGcJxa5JbG/MsBZQR4f5aZY6YpNfX51TbY/iaQMIh9C7LurM6HXZpllwqjpTdGXS3sdgCnVwFAO1UYMKUL1c6qQ9XmSAVgeNjM0mM82L6aYHxJt2q82gu5GX0AT+pIOSHf9TjqMu9a/MyKoDkRmznqBHRV2PJJKnSy+/d6A9bGnseqDgRg/CvdjiBNM1P3D4WTFDvUN6zREtLRnHydAgMBAAECggEAAMGCfVlVQdowpCL5/iT+WZQzJCLBYBY2OVc6Aa66XOfh8K0NbZm8vBvy3QxpaO1nlmHew6gBavHAtMWPjQPPlEdIWtp17BfMrJ8xJqm71Mivksc0lHchZqMqAMyyksfXkMADKAeecjaDnXMR19efxRRWfMWOu+yfg39U0l95A8QC1uDTwDDDBvrIO4EzKo2sDG1dM3W7fg89ZaUtK/WDcnuOHh8KorUZQHKIFVZ1zOfJiW3VblcPU86RxTa9ZJywCUX6I2+rU0h3/CH+Wo4BOEYm7cGcxUPw2XqYKyt7uTPOuwkurHVA4lyxcTp3j52zpwyfZ+08881eizA1a8nxIQKBgQDq+fz3N5ud84iuo+sDeMw0Yo7IyUUKSWJ7a4+gdaaePedLBMKBeynx/9l7/XlbUjCH7YF6LtSdssDDJocCIMYDprKvd/9V1lF+wexfGfVISV3SUfI3JC+enIbA2ZV4SmBIn4XIesKrnh4Pi1yBYkQ5oYv8SCqeQwHkTOihN2whDwKBgQDIY7D8phrN+MPtYodFgDqoLoDOz0tOAqUynP800q4TezyElnZ4xp4dUFpsJGAvzoi+Y/bnU3L1Z1hq/xPN3Y+fEGdSpZvREEZBIpbvdCEEKSdZvZOjpZROheGAvx4LNSdrxFQ0HuNq3oRQ/V5+hZ1r/xLx9WO17MkZGFxOwNBvkwKBgQDMcIyDm0It/wFg0QVck/E3crjAQT1sYcTplP/1n+dDrqBaSN3iQgKQpwXWNwcrSSsoWKBaafxa6HeGUzMLyu/9pT+6IzFowXtOSfMaGz+pkQusPdf72eQEoDMt/yFo820qQoDnmMdfAcctxxbJC3JIoiFlcnSCFdLDi5arDclqSQKBgQCE0w+NZ8x8mlfEEXr4ZnZ649gdPOn9W2OEmOvQZ5Va9GS4vcLpaz2C0LAe3j2jcpLRIBGYY4ffghDpWwoVeraoCId0ELGncdIfen3xWlhIGb8rjK0/25DiO3utiwCvDRyEIi5uHctAGx45ULhBxO8Dlp9IIg9llv301GDbEpMWYQKBgHjlBB071edG7a9xLpuL3tf7/QP2AA05Ugdw92Jp920sd5Kb7G3OwCEu5otr4yJwpEvw3ZnnZW2NPp/oPPqQrH+GSmhNiStRX5anvHpbxsP4XcqvZzd6Zx5quM42ZIX4BK4bTocRpgylAj6lapaxkBA7vujqnZ/uRndLMAWOFsmE";

function hybridDecrypt(encryptedData: string, privateKeyB64: string): string {
   const parts = encryptedData.split(':', 2);
   if (parts.length !== 2) {
       throw new Error('Invalid hybrid encrypted data format');
   }

   const [encryptedAesKeyB64, aesEncryptedB64] = parts;

   // Decrypt AES key with RSA
   const privateKey = crypto.createPrivateKey({
       key: Buffer.from(privateKeyB64, 'base64'),
       format: 'der',
       type: 'pkcs8'
   });
   const encryptedAesKey = Buffer.from(encryptedAesKeyB64, 'base64');
   const aesKey = crypto.privateDecrypt({
       key: privateKey,
       padding: crypto.constants.RSA_PKCS1_OAEP_PADDING,
       oaepHash: 'sha256'
   }, encryptedAesKey);

   // Decrypt data with AES
   const aesEncrypted = Buffer.from(aesEncryptedB64, 'base64');
   const iv = aesEncrypted.subarray(0, 12);
   const tag = aesEncrypted.subarray(12, 28);
   const ciphertext = aesEncrypted.subarray(28);

   const decipher = crypto.createDecipherGCM('aes-256-gcm', aesKey);
   decipher.setAuthTag(tag);
   decipher.setIV(iv);
   let decrypted = decipher.update(ciphertext);
   decrypted = Buffer.concat([decrypted, decipher.final()]);

   return decrypted.toString('utf8');
}

interface LicenseData {
   license: {
       id: string;
       tenant_id: string;
       issued_at: string;
       validity_days: number;
       payload: any;
   };
   signature: string;
}

async function validateLicense(): Promise<boolean> {
   const licenseKey = process.env.LICENSE_KEY;
   if (!licenseKey) {
       console.error("LICENSE_KEY environment variable not set");
       return false;
   }

   const licenseFile = './license.lic';
   let downloaded = false;

   async function validateFile(): Promise<boolean> {
       if (!fs.existsSync(licenseFile)) {
           if (downloaded) {
               console.error("License file not found after download");
               return false;
           }
           console.log("License file not found, downloading...");
           const downloadSuccess = await downloadLicense();
           if (!downloadSuccess) {
               console.error("Failed to download license");
               return false;
           }
           downloaded = true;
       }

       try {
           const encryptedContent = fs.readFileSync(licenseFile, 'utf8').trim();
           const decryptedContent = hybridDecrypt(encryptedContent, MASTER_PRIVATE_KEY);
           const data: LicenseData = JSON.parse(decryptedContent);
           const licenseJson = JSON.stringify(data.license);

           // Verify signature
           const publicKey = crypto.createPublicKey({
               key: Buffer.from(licenseKey, 'base64'),
               format: 'der',
               type: 'spki'
           });

           const signature = data.signature;
           const isValid = crypto.verify('sha256', Buffer.from(licenseJson), publicKey, Buffer.from(signature, 'base64'));

           if (!isValid) {
               if (!downloaded) {
                   console.log("Signature verification failed, downloading new license...");
                   const downloadSuccess = await downloadLicense();
                   if (!downloadSuccess) {
                       console.error("Failed to download new license");
                       return false;
                   }
                   downloaded = true;
                   return await validateFile();
               } else {
                   console.error("Signature verification failed after download");
                   return false;
               }
           }

           // Check expiry
           const issuedAt = new Date(data.license.issued_at);
           const validityDays = data.license.validity_days;
           const expiryDate = new Date(issuedAt);
           expiryDate.setDate(expiryDate.getDate() + validityDays);

           if (new Date() > expiryDate) {
               if (!downloaded) {
                   console.log("License expired, downloading new license...");
                   const downloadSuccess = await downloadLicense();
                   if (!downloadSuccess) {
                       console.error("Failed to download new license");
                       return false;
                   }
                   downloaded = true;
                   return await validateFile();
               } else {
                   console.error("License expired after download");
                   return false;
               }
           }

           console.log("License is valid");
           return true;

       } catch (error) {
           console.error("Error validating license:", (error as Error).message);
           if (!downloaded) {
               console.log("Downloading new license...");
               const downloadSuccess = await downloadLicense();
               if (!downloadSuccess) {
                   console.error("Failed to download new license");
                   return false;
               }
               downloaded = true;
               return await validateFile();
           } else {
               console.error("Error validating license after download");
               return false;
           }
       }
   }

   async function downloadLicense(): Promise<boolean> {
       return new Promise((resolve) => {
           const encodedKey = Buffer.from(licenseKey).toString('base64');
           const url = \`\${baseUrl}/api/licenses/issue?encoded_license_key=\${encodeURIComponent(encodedKey)}\`;

           https.get(url, (res) => {
               if (res.statusCode !== 200) {
                   resolve(false);
                   return;
               }

               const fileStream = fs.createWriteStream(licenseFile);
               res.pipe(fileStream);

               fileStream.on('finish', () => {
                   fileStream.close();
                   console.log("License downloaded successfully");
                   resolve(true);
               });
           }).on('error', (err) => {
               console.error(\`Download failed: \${err.message}\`);
               resolve(false);
           });
       });
   }

   return await validateFile();
}

// Usage
validateLicense().then(success => {
   if (success) {
       console.log("Validation successful");
   } else {
       console.error("Validation failed");
       process.exit(1);
   }
}).catch(error => {
   console.error("Validation error:", error.message);
   process.exit(1);
});`,
     py: `import os
import json
import base64
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
               padding.PSS(
                   mgf=padding.MGF1(hashes.SHA256()),
                   salt_length=padding.PSS.MAX_LENGTH
               ),
               hashes.SHA256()
           )

           # Check expiry
           issued_at = datetime.fromisoformat(data['license']['issued_at'].replace('Z', '+00:00'))
           validity_days = data['license']['validity_days']
           expiry_date = issued_at + datetime.timedelta(days=validity_days)

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
           url = f"{baseUrl}/api/licenses/issue"
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
       sys.exit(1)`,
     java: `import java.io.*;
import java.net.*;
import java.nio.file.*;
import java.security.*;
import java.security.spec.*;
import java.util.Base64;
import java.util.Date;
import java.util.Calendar;
import javax.crypto.Cipher;
import org.json.JSONObject;

public class LicenseValidator {
   private static final String BASE_URL = "{baseUrl}";
   private static boolean downloaded = false;

   public static void main(String[] args) {
       boolean valid = validateLicense();
       if (valid) {
           System.out.println("Validation successful");
           System.exit(0);
       } else {
           System.err.println("Validation failed");
           System.exit(1);
       }
   }

   public static boolean validateLicense() {
       String licenseKey = System.getenv("LICENSE_KEY");
       if (licenseKey == null || licenseKey.isEmpty()) {
           System.err.println("LICENSE_KEY environment variable not set");
           return false;
       }

       Path licenseFile = Paths.get("./license.lic");

       return validateFile(licenseFile);
   }

   private static boolean validateFile(Path filePath) {
       if (!Files.exists(filePath)) {
           if (downloaded) {
               System.err.println("License file not found after download");
               return false;
           }
           System.out.println("License file not found, downloading...");
           boolean downloadSuccess = downloadLicense();
           if (!downloadSuccess) {
               System.err.println("Failed to download license");
               return false;
           }
           downloaded = true;
       }

       try {
           String content = new String(Files.readAllBytes(filePath));
           JSONObject data = new JSONObject(content);
           JSONObject license = data.getJSONObject("license");

           String licenseJson = license.toString();

           // Load public key
           byte[] publicKeyDer = Base64.getDecoder().decode(System.getenv("LICENSE_KEY"));
           KeyFactory keyFactory = KeyFactory.getInstance("RSA");
           X509EncodedKeySpec keySpec = new X509EncodedKeySpec(publicKeyDer);
           PublicKey publicKey = keyFactory.generatePublic(keySpec);

           // Verify signature
           Signature signature = Signature.getInstance("SHA256withRSA");
           signature.initVerify(publicKey);
           signature.update(licenseJson.getBytes("UTF-8"));

           String signatureStr = data.getString("signature");
           byte[] signatureBytes = Base64.getDecoder().decode(signatureStr);

           if (!signature.verify(signatureBytes)) {
               if (!downloaded) {
                   System.out.println("Signature verification failed, downloading new license...");
                   boolean downloadSuccess = downloadLicense();
                   if (!downloadSuccess) {
                       System.err.println("Failed to download new license");
                       return false;
                   }
                   downloaded = true;
                   return validateFile(filePath);
               } else {
                   System.err.println("Signature verification failed after download");
                   return false;
               }
           }

           // Check expiry
           String issuedAtStr = license.getString("issued_at");
           int validityDays = license.getInt("validity_days");

           // Simple date parsing (you might want to use a proper date library)
           Date issuedAt = new Date(); // Parse properly in production
           Calendar cal = Calendar.getInstance();
           cal.setTime(issuedAt);
           cal.add(Calendar.DAY_OF_MONTH, validityDays);

           if (new Date().after(cal.getTime())) {
               if (!downloaded) {
                   System.out.println("License expired, downloading new license...");
                   boolean downloadSuccess = downloadLicense();
                   if (!downloadSuccess) {
                       System.err.println("Failed to download new license");
                       return false;
                   }
                   downloaded = true;
                   return validateFile(filePath);
               } else {
                   System.err.println("License expired after download");
                   return false;
               }
           }

           System.out.println("License is valid");
           return true;

       } catch (Exception e) {
           System.err.println("Error validating license: " + e.getMessage());
           if (!downloaded) {
               System.out.println("Downloading new license...");
               boolean downloadSuccess = downloadLicense();
               if (!downloadSuccess) {
                   System.err.println("Failed to download new license");
                   return false;
               }
               downloaded = true;
               return validateFile(filePath);
           } else {
               System.err.println("Error validating license after download");
               return false;
           }
       }
   }

   private static boolean downloadLicense() {
       try {
           String encodedKey = Base64.getEncoder().encodeToString(System.getenv("LICENSE_KEY").getBytes("UTF-8"));
           String urlStr = BASE_URL + "/api/licenses/issue?encoded_license_key=" + URLEncoder.encode(encodedKey, "UTF-8");

           URL url = new URL(urlStr);
           HttpURLConnection conn = (HttpURLConnection) url.openConnection();
           conn.setRequestMethod("GET");

           if (conn.getResponseCode() != 200) {
               return false;
           }

           try (InputStream in = conn.getInputStream();
                FileOutputStream out = new FileOutputStream("./license.lic")) {
               byte[] buffer = new byte[4096];
               int bytesRead;
               while ((bytesRead = in.read(buffer)) != -1) {
                   out.write(buffer, 0, bytesRead);
               }
           }

           System.out.println("License downloaded successfully");
           return true;

       } catch (Exception e) {
           System.err.println("Download failed: " + e.getMessage());
           return false;
       }
   }
}`,
     rust: `use std::env;
use std::fs;
use std::io::{{self, Write}};
use std::path::Path;
use reqwest::blocking;
use serde::{{Deserialize, Serialize}};
use base64::{{Engine as _, engine::general_purpose}};

#[derive(Serialize, Deserialize)]
struct LicenseData {
   license: License,
   signature: String,
}

#[derive(Serialize, Deserialize)]
struct License {
   id: String,
   tenant_id: String,
   issued_at: String,
   validity_days: u32,
   payload: serde_json::Value,
}

fn main() {
   if validate_license() {
       println!("Validation successful");
       std::process::exit(0);
   } else {
       eprintln!("Validation failed");
       std::process::exit(1);
   }
}

fn validate_license() -> bool {
   let license_key = match env::var("LICENSE_KEY") {
       Ok(key) => key,
       Err(_) => {
           eprintln!("LICENSE_KEY environment variable not set");
           return false;
       }
   };

   let license_file = "./license.lic";
   let mut downloaded = false;
   validate_file(license_file, &license_key, &mut downloaded)
}

fn validate_file(file_path: &str, license_key: &str, downloaded: &mut bool) -> bool {
   if !Path::new(file_path).exists() {
       if *downloaded {
           eprintln!("License file not found after download");
           return false;
       }
       println!("License file not found, downloading...");
       let download_success = download_license(license_key);
       if !download_success {
           eprintln!("Failed to download license");
           return false;
       }
       *downloaded = true;
   }

   match fs::read_to_string(file_path) {
       Ok(content) => {
           match serde_json::from_str::<LicenseData>(&content) {
               Ok(data) => {
                   let license_json = serde_json::to_string(&data.license).unwrap();

                   // Verify signature (placeholder - implement proper RSA verification)
                   if !verify_signature(&license_json, &data.signature, license_key) {
                       if !*downloaded {
                           println!("Signature verification failed, downloading new license...");
                           let download_success = download_license(license_key);
                           if !download_success {
                               eprintln!("Failed to download new license");
                               return false;
                           }
                           *downloaded = true;
                           return validate_file(file_path, license_key, downloaded);
                       } else {
                           eprintln!("Signature verification failed after download");
                           return false;
                       }
                   }

                   // Check expiry (placeholder - implement proper date checking)
                   if !check_expiry(&data.license) {
                       if !*downloaded {
                           println!("License expired, downloading new license...");
                           let download_success = download_license(license_key);
                           if !download_success {
                               eprintln!("Failed to download new license");
                               return false;
                           }
                           *downloaded = true;
                           return validate_file(file_path, license_key, downloaded);
                       } else {
                           eprintln!("License expired after download");
                           return false;
                       }
                   }

                   println!("License is valid");
                   true
               }
               Err(e) => {
                   eprintln!("Error parsing license: {}", e);
                   if !*downloaded {
                       println!("Downloading new license...");
                       let download_success = download_license(license_key);
                       if !download_success {
                           eprintln!("Failed to download new license");
                           return false;
                       }
                       *downloaded = true;
                       return validate_file(file_path, license_key, downloaded);
                   } else {
                       eprintln!("Error parsing license after download");
                       return false;
                   }
               }
           }
       }
       Err(e) => {
           eprintln!("Error reading license file: {}", e);
           if !*downloaded {
               println!("Downloading new license...");
               let download_success = download_license(license_key);
               if !download_success {
                   eprintln!("Failed to download new license");
                   return false;
               }
               *downloaded = true;
               return validate_file(file_path, license_key, downloaded);
           } else {
               eprintln!("Error reading license file after download");
               return false;
           }
       }
   }
}

fn verify_signature(data: &str, signature: &str, public_key_der: &str) -> bool {
   // Placeholder - implement proper RSA signature verification
   true // TODO: Implement actual verification
}

fn check_expiry(license: &License) -> bool {
   // Placeholder - implement proper date checking
   true // TODO: Implement actual expiry check
}

fn download_license(license_key: &str) -> bool {
   let encoded_key = general_purpose::STANDARD.encode(license_key.as_bytes());
   let url = format!("{}/api/licenses/issue?encoded_license_key={}", "{baseUrl}", urlencoding::encode(&encoded_key));

   match blocking::get(&url) {
       Ok(response) => {
           if response.status().is_success() {
               match response.bytes() {
                   Ok(bytes) => {
                       match fs::write("./license.lic", &bytes) {
                           Ok(_) => {
                               println!("License downloaded successfully");
                               true
                           }
                           Err(e) => {
                               eprintln!("Error writing license file: {}", e);
                               false
                           }
                       }
                   }
                   Err(e) => {
                       eprintln!("Error reading response: {}", e);
                       false
                   }
               }
           } else {
               eprintln!("Failed to download license: {}", response.status());
               false
           }
       }
       Err(e) => {
           eprintln!("Download failed: {}", e);
           false
       }
   }
}`,
     dart: `import 'dart:io';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:crypto/crypto.dart';
import 'package:pointycastle/pointycastle.dart';

void main() async {
 bool valid = await validateLicense();
 if (valid) {
   print('Validation successful');
   exit(0);
 } else {
   stderr.writeln('Validation failed');
   exit(1);
 }
}

Future<bool> validateLicense() async {
 String? licenseKey = Platform.environment['LICENSE_KEY'];
 if (licenseKey == null || licenseKey.isEmpty) {
   stderr.writeln('LICENSE_KEY environment variable not set');
   return false;
 }

 File licenseFile = File('./license.lic');
 bool downloaded = false;
 return validateFile(licenseFile, downloaded);
}

Future<bool> validateFile(File file, bool downloaded) async {
 if (!await file.exists()) {
   if (downloaded) {
     stderr.writeln('License file not found after download');
     return false;
   }
   print('License file not found, downloading...');
   bool downloadSuccess = await downloadLicense();
   if (!downloadSuccess) {
     stderr.writeln('Failed to download license');
     return false;
   }
   downloaded = true;
 }

 try {
   String content = await file.readAsString();
   Map<String, dynamic> data = json.decode(content);
   Map<String, dynamic> license = data['license'];

   String licenseJson = json.encode(license);

   // Verify signature (placeholder - implement proper RSA verification)
   String signature = data['signature'];
   String? licenseKey = Platform.environment['LICENSE_KEY'];
   if (!verifySignature(licenseJson, signature, licenseKey!)) {
     if (!downloaded) {
       print('Signature verification failed, downloading new license...');
       bool downloadSuccess = await downloadLicense();
       if (!downloadSuccess) {
         stderr.writeln('Failed to download new license');
         return false;
       }
       downloaded = true;
       return validateFile(file, downloaded);
     } else {
       stderr.writeln('Signature verification failed after download');
       return false;
     }
   }

   // Check expiry (simplified)
   String issuedAtStr = license['issued_at'];
   int validityDays = license['validity_days'];

   DateTime issuedAt = DateTime.parse(issuedAtStr);
   DateTime expiryDate = issuedAt.add(Duration(days: validityDays));

   if (DateTime.now().isAfter(expiryDate)) {
     if (!downloaded) {
       print('License expired, downloading new license...');
       bool downloadSuccess = await downloadLicense();
       if (!downloadSuccess) {
         stderr.writeln('Failed to download new license');
         return false;
       }
       downloaded = true;
       return validateFile(file, downloaded);
     } else {
       stderr.writeln('License expired after download');
       return false;
     }
   }

   print('License is valid');
   return true;

 } catch (e) {
   stderr.writeln('Error validating license: $e');
   if (!downloaded) {
     print('Downloading new license...');
     bool downloadSuccess = await downloadLicense();
     if (!downloadSuccess) {
       stderr.writeln('Failed to download new license');
       return false;
     }
     downloaded = true;
     return validateFile(file, downloaded);
   } else {
     stderr.writeln('Error validating license after download');
     return false;
   }
 }
}

bool verifySignature(String data, String signature, String publicKeyDer) {
 // Placeholder - implement proper RSA signature verification
 return true; // TODO: Implement actual verification
}

Future<bool> downloadLicense() async {
 try {
   String licenseKey = Platform.environment['LICENSE_KEY']!;
   String encodedKey = base64.encode(utf8.encode(licenseKey));
   String url = '{baseUrl}/api/licenses/issue?encoded_license_key=\${Uri.encodeComponent(encodedKey)}';

   http.Response response = await http.get(Uri.parse(url));
   if (response.statusCode != 200) {
     return false;
   }

   File licenseFile = File('./license.lic');
   await licenseFile.writeAsBytes(response.bodyBytes);

   print('License downloaded successfully');
   return true;

 } catch (e) {
   stderr.writeln('Download failed: $e');
   return false;
 }
}`,
     go: `package main

import (
   "crypto/rsa"
   "crypto/sha256"
   "crypto/x509"
   "encoding/base64"
   "encoding/json"
   "fmt"
   "io"
   "net/http"
   "net/url"
   "os"
   "time"
)

type LicenseData struct {
   License   License \`json:"license"\`
   Signature string  \`json:"signature"\`
}

type License struct {
   ID           string      \`json:"id"\`
   TenantID     string      \`json:"tenant_id"\`
   IssuedAt     string      \`json:"issued_at"\`
   ValidityDays int         \`json:"validity_days"\`
   Payload      interface{} \`json:"payload"\`
}

const baseURL = "{baseUrl}"

func main() {
   if validateLicense() {
       fmt.Println("Validation successful")
       os.Exit(0)
   } else {
       fmt.Fprintln(os.Stderr, "Validation failed")
       os.Exit(1)
   }
}

func validateLicense() bool {
   licenseKey := os.Getenv("LICENSE_KEY")
   if licenseKey == "" {
       fmt.Fprintln(os.Stderr, "LICENSE_KEY environment variable not set")
       return false
   }

   licenseFile := "./license.lic"
   downloaded := false
   return validateFile(licenseFile, &downloaded)
}

func validateFile(filePath string, downloaded *bool) bool {
   if _, err := os.Stat(filePath); os.IsNotExist(err) {
       if *downloaded {
           fmt.Fprintln(os.Stderr, "License file not found after download")
           return false
       }
       fmt.Println("License file not found, downloading...")
       downloadSuccess := downloadLicense()
       if !downloadSuccess {
           fmt.Fprintln(os.Stderr, "Failed to download license")
           return false
       }
       *downloaded = true
   }

   content, err := os.ReadFile(filePath)
   if err != nil {
       fmt.Fprintf(os.Stderr, "Error reading license file: %v\\n", err)
       if !*downloaded {
           fmt.Println("Downloading new license...")
           downloadSuccess := downloadLicense()
           if !downloadSuccess {
               fmt.Fprintln(os.Stderr, "Failed to download new license")
               return false
           }
           *downloaded = true
           return validateFile(filePath, downloaded)
       } else {
           fmt.Fprintln(os.Stderr, "Error reading license file after download")
           return false
       }
   }

   var data LicenseData
   if err := json.Unmarshal(content, &data); err != nil {
       fmt.Fprintf(os.Stderr, "Error parsing license: %v\\n", err)
       if !*downloaded {
           fmt.Println("Downloading new license...")
           downloadSuccess := downloadLicense()
           if !downloadSuccess {
               fmt.Fprintln(os.Stderr, "Failed to download new license")
               return false
           }
           *downloaded = true
           return validateFile(filePath, downloaded)
       } else {
           fmt.Fprintln(os.Stderr, "Error parsing license after download")
           return false
       }
   }

   licenseJson, _ := json.Marshal(data.License)

   // Verify signature
   publicKeyDer, _ := base64.StdEncoding.DecodeString(os.Getenv("LICENSE_KEY"))
   publicKey, err := x509.ParsePKIXPublicKey(publicKeyDer)
   if err != nil {
       fmt.Fprintf(os.Stderr, "Error parsing public key: %v\\n", err)
       return false
   }

   rsaPublicKey, ok := publicKey.(*rsa.PublicKey)
   if !ok {
       fmt.Fprintln(os.Stderr, "Not an RSA public key")
       return false
   }

   signature, _ := base64.StdEncoding.DecodeString(data.Signature)
   hashed := sha256.Sum256(licenseJson)

   if err := rsa.VerifyPKCS1v15(rsaPublicKey, crypto.SHA256, hashed[:], signature); err != nil {
       if !*downloaded {
           fmt.Println("Signature verification failed, downloading new license...")
           downloadSuccess := downloadLicense()
           if !downloadSuccess {
               fmt.Fprintln(os.Stderr, "Failed to download new license")
               return false
           }
           *downloaded = true
           return validateFile(filePath, downloaded)
       } else {
           fmt.Fprintln(os.Stderr, "Signature verification failed after download")
           return false
       }
   }

   // Check expiry
   issuedAt, err := time.Parse(time.RFC3339, data.License.IssuedAt)
   if err != nil {
       fmt.Fprintf(os.Stderr, "Error parsing issued_at: %v\\n", err)
       return false
   }

   expiryDate := issuedAt.AddDate(0, 0, data.License.ValidityDays)
   if time.Now().After(expiryDate) {
       if !*downloaded {
           fmt.Println("License expired, downloading new license...")
           downloadSuccess := downloadLicense()
           if !downloadSuccess {
               fmt.Fprintln(os.Stderr, "Failed to download new license")
               return false
           }
           *downloaded = true
           return validateFile(filePath, downloaded)
       } else {
           fmt.Fprintln(os.Stderr, "License expired after download")
           return false
       }
   }

   fmt.Println("License is valid")
   return true
}

func downloadLicense() bool {
   licenseKey := os.Getenv("LICENSE_KEY")
   encodedKey := base64.StdEncoding.EncodeToString([]byte(licenseKey))

   fullURL := fmt.Sprintf("%s/api/licenses/issue?encoded_license_key=%s", baseURL, url.QueryEscape(encodedKey))

   resp, err := http.Get(fullURL)
   if err != nil {
       fmt.Fprintf(os.Stderr, "Download failed: %v\\n", err)
       return false
   }
   defer resp.Body.Close()

   if resp.StatusCode != 200 {
       return false
   }

   out, err := os.Create("./license.lic")
   if err != nil {
       fmt.Fprintf(os.Stderr, "Error creating license file: %v\\n", err)
       return false
   }
   defer out.Close()

   _, err = io.Copy(out, resp.Body)
   if err != nil {
       fmt.Fprintf(os.Stderr, "Error writing license file: %v\\n", err)
       return false
   }

   fmt.Println("License downloaded successfully")
   return true
}`
   };

   // Reactive statement to update validatorCode when selectedLanguage changes
   $: validatorCode = codeTemplates[selectedLanguage as keyof typeof codeTemplates].replace(/{baseUrl}/g, baseUrl);

   // Reactive statement for current usage example
   $: currentUsageExample = usageExamples[selectedLanguage as keyof typeof usageExamples];

   // Usage examples for different languages
   const usageExamples = {
     js: `// JavaScript
validateLicense().then(success => {
 if (success) console.log("Valid");
 else process.exit(1);
});`,
     ts: `// TypeScript
validateLicense().then(success => {
 if (success) console.log("Valid");
 else process.exit(1);
});`,
     py: `# Python
if __name__ == "__main__":
   if validate_license():
       print("Validation successful")
       sys.exit(0)
   else:
       print("Validation failed", file=sys.stderr)
       sys.exit(1)`,
     java: `// Java
public class Main {
   public static void main(String[] args) {
       boolean valid = LicenseValidator.validateLicense();
       if (valid) {
           System.out.println("Validation successful");
           System.exit(0);
       } else {
           System.err.println("Validation failed");
           System.exit(1);
       }
   }
}`,
     rust: `// Rust
fn main() {
   if validate_license() {
       println!("Validation successful");
       std::process::exit(0);
   } else {
       eprintln!("Validation failed");
       std::process::exit(1);
   }
}`,
     dart: `// Dart
void main() async {
 bool valid = await validateLicense();
 if (valid) {
   print('Validation successful');
   exit(0);
 } else {
   stderr.writeln('Validation failed');
   exit(1);
 }
}`,
     go: `// Go
func main() {
   if validateLicense() {
       fmt.Println("Validation successful")
       os.Exit(0)
   } else {
       fmt.Fprintln(os.Stderr, "Validation failed")
       os.Exit(1)
   }
}`
   };

  function handleFileChange(event: Event) {
    const target = event.target as HTMLInputElement;
    const file = target.files?.[0];
    if (file) {
      selectedFile = file;
      console.log('Selected file:', file.name, file.size, file.type);
    }
  }

  function handleDrop(event: DragEvent) {
    event.preventDefault();
    const files = event.dataTransfer?.files;
    if (files && files.length > 0) {
      selectedFile = files[0];
      console.log('Dropped file:', selectedFile.name);
    }
  }

  function handleDragOver(event: DragEvent) {
    event.preventDefault();
  }

  function formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  async function handleValidation() {
    if (!licenseKey.trim()) {
      toast.error('Please enter a license key');
      return;
    }

    if (!selectedFile) {
      toast.error('Please select a license file to validate');
      return;
    }

    isValidating = true;
    validationResult = null;

    try {
      console.log('Validating license file...');
      console.log('License key:', licenseKey);
      console.log('File:', selectedFile.name);
      
      const result = await licenseApi.validateFile(licenseKey, selectedFile);
      
      console.log('Validation result:', result);
      validationResult = result;
      
      if (result.decryption === 'success' && result.validity === 'valid' && result.signature === 'verified') {
        toast.success('License Validation Successful\nThe license file has been successfully validated and is ready for use.', {
          duration: 3000,
        });
      } else {
        toast.error('License Validation Failed\nThe license file validation completed with issues. Please check the details above.', {
          duration: 3000,
        });
      }
    } catch (error) {
      console.error('Validation error:', error);
      toast.error('Failed to validate license file');
    } finally {
      isValidating = false;
    }
  }

  function clearForm() {
    licenseKey = '';
    selectedFile = null;
    validationResult = null;
    
    // Reset file input
    const fileInput = document.getElementById('license-file') as HTMLInputElement;
    if (fileInput) {
      fileInput.value = '';
    }
  }

  function getStatusIcon(status: string) {
    switch (status) {
      case 'success':
      case 'verified':
      case 'valid':
        return CheckCircle;
      case 'failed':
      case 'verification_failed':
      case 'invalid':
        return XCircle;
      case 'error':
        return AlertTriangle;
      default:
        return FileText;
    }
  }

  function getStatusColor(status: string): string {
    switch (status) {
      case 'success':
      case 'verified':
      case 'valid':
        return 'text-green-600 dark:text-green-400';
      case 'failed':
      case 'verification_failed':
      case 'invalid':
        return 'text-red-600 dark:text-red-400';
      case 'error':
        return 'text-yellow-600 dark:text-yellow-400';
      default:
        return 'text-gray-600 dark:text-gray-400';
    }
  }

  function toggleLicenseKeyPreview() {
    showLicenseKeyPreview = !showLicenseKeyPreview;
  }

  async function downloadValidator() {
    try {
      isDownloading = true;

      // Call backend endpoint to generate validator code with real master keys
      const response = await fetch(`/api/licenses/generate-validator?language=${selectedLanguage}`, {
        headers: {
          'Authorization': `Bearer ${sessionStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to generate validator code');
      }

      const data = await response.json();
      const code = data.code;

      // Create and download the file
      const blob = new Blob([code], { type: 'text/plain' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `license_validator.${getFileExtension(selectedLanguage)}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      toast.success('Validator Download Complete\nThe validator code has been downloaded with integrated master keys.');
    } catch (error) {
      console.error('Download error:', error);
      toast.error('Validator Download Failed\nUnable to generate validator code. Please try again.');
    } finally {
      isDownloading = false;
    }
  }

  function getFileExtension(language: string): string {
    const extensions: { [key: string]: string } = {
      js: 'js',
      ts: 'ts',
      py: 'py',
      java: 'java',
      rust: 'rs',
      dart: 'dart',
      go: 'go'
    };
    return extensions[language] || 'txt';
  }

</script>

<svelte:head>
  <title>Validate License - Sigma Permit</title>
</svelte:head>

<div class="space-y-6">
  <!-- Header -->
  <div class="text-center">
    <div class="flex items-center justify-center mb-4">
      <div class="bg-blue-100 dark:bg-blue-900/20 p-3 rounded-full">
        <Shield class="text-blue-600 dark:text-blue-400" size={32} />
      </div>
    </div>
    <h1 class="text-3xl font-bold text-gray-900 dark:text-gray-50">Validation</h1>
    <p class="text-gray-600 dark:text-gray-400 mt-2 max-w-2xl mx-auto">
      Validate license files or generate validator code for different programming languages to automate license checking in your applications.
    </p>
  </div>

  <!-- Tabs -->
  <div class="max-w-4xl mx-auto mb-6">
    <div class="border-b border-gray-200 dark:border-gray-700">
      <nav class="-mb-px flex space-x-8">
        <button
          class="py-2 px-1 border-b-2 font-medium text-sm {activeTab === 'validate'
            ? 'border-blue-500 text-blue-600 dark:text-blue-400'
            : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'}"
          on:click={() => activeTab = 'validate'}
        >
          <Shield size={18} class="inline mr-2" />
          Validate
        </button>
        <button
          class="py-2 px-1 border-b-2 font-medium text-sm {activeTab === 'validator'
            ? 'border-blue-500 text-blue-600 dark:text-blue-400'
            : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'}"
          on:click={() => activeTab = 'validator'}
        >
          <Code size={18} class="inline mr-2" />
          Validator
        </button>
      </nav>
    </div>
  </div>

  {#if activeTab === 'validate'}
  <!-- Validation Form -->
  <div class="max-w-2xl mx-auto">
    <div class="card p-6 space-y-6">
      <!-- License Key Input -->
      <div>
        <label for="license-key" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          License Key
        </label>
        <div class="relative">
          {#if showLicenseKeyPreview}
            <input
              id="license-key"
              type="text"
              placeholder="Enter the license key that corresponds to your license file"
              class="form-input pr-12"
              bind:value={licenseKey}
              on:keydown={(e) => e.key === 'Enter' && handleValidation()}
            />
          {:else}
            <input
              id="license-key"
              type="password"
              placeholder="Enter the license key that corresponds to your license file"
              class="form-input pr-12"
              bind:value={licenseKey}
              on:keydown={(e) => e.key === 'Enter' && handleValidation()}
            />
          {/if}
          <button
            type="button"
            class="absolute inset-y-0 right-0 pr-3 flex items-center"
            on:click={toggleLicenseKeyPreview}
            title={showLicenseKeyPreview ? 'Hide license key' : 'Show license key'}
          >
            <Eye size={18} class="text-gray-400 hover:text-gray-600" />
          </button>
        </div>
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
          The license key should match the one used to generate the license file.
        </p>
      </div>

      <!-- File Upload -->
      <div>
        <label for="license-file" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          License File
        </label>
        <div
          class="relative border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-6 text-center hover:border-gray-400 dark:hover:border-gray-500 transition-colors"
          on:drop={handleDrop}
          on:dragover={handleDragOver}
        >
          <input
            id="license-file"
            type="file"
            accept=".lic,.license,license.*"
            class="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            on:change={handleFileChange}
          />
          
          {#if selectedFile}
            <div class="space-y-2">
              <CheckCircle class="mx-auto text-green-500" size={32} />
              <div class="text-sm font-medium text-gray-900 dark:text-gray-50">
                {selectedFile.name}
              </div>
              <div class="text-xs text-gray-500 dark:text-gray-400">
                {formatFileSize(selectedFile.size)}
                {#if selectedFile.type}
                  • {selectedFile.type}
                {/if}
              </div>
            </div>
          {:else}
            <div class="space-y-2">
              <Upload class="mx-auto text-gray-400" size={32} />
              <div class="text-sm text-gray-600 dark:text-gray-400">
                Drag and drop your license file here, or click to browse
              </div>
              <div class="text-xs text-gray-500 dark:text-gray-500">
                Supports .lic, .license files
              </div>
            </div>
          {/if}
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="flex flex-col sm:flex-row gap-3">
        <button
          class="btn btn-primary flex-1 flex items-center justify-center space-x-2"
          on:click={handleValidation}
          disabled={isValidating || !licenseKey.trim() || !selectedFile}
        >
          {#if isValidating}
            <div class="spinner"></div>
            <span>Validating...</span>
          {:else}
            <Shield size={18} />
            <span>Validate License</span>
          {/if}
        </button>
        
        <button
          class="btn btn-secondary"
          on:click={clearForm}
          disabled={isValidating}
        >
          Clear
        </button>
      </div>
    </div>
  </div>

  <!-- Validation Results -->
  {#if validationResult}
    <div class="max-w-4xl mx-auto">
      <div class="card p-6">
        <h2 class="text-xl font-semibold text-gray-900 dark:text-gray-50 mb-6 flex items-center space-x-2">
          <Shield size={20} class="text-blue-600" />
          <span>License Validation Results</span>
        </h2>

        <!-- Signature Verification: Parsing and Validity -->
        <div class="mb-6">
          <h3 class="text-lg font-medium text-gray-900 dark:text-gray-50 mb-4 flex items-center space-x-2">
            <Key size={18} class="text-purple-600" />
            <span>Signature Verification: Parsing and Validity</span>
          </h3>
          
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <!-- Parsing Status -->
            <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
              <div class="flex items-center space-x-2 mb-2">
                {#if validationResult.parsing === 'success'}
                  <CheckCircle size={18} class="text-green-500" />
                  <span class="font-medium text-green-700 dark:text-green-400">Parsing</span>
                  <span class="px-2 py-1 text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400 rounded-full">SUCCESS</span>
                {:else if validationResult.parsing === 'failed'}
                  <XCircle size={18} class="text-red-500" />
                  <span class="font-medium text-red-700 dark:text-red-400">Parsing</span>
                  <span class="px-2 py-1 text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400 rounded-full">FAILED</span>
                {:else}
                  <AlertTriangle size={18} class="text-yellow-500" />
                  <span class="font-medium text-yellow-700 dark:text-yellow-400">Parsing</span>
                  <span class="px-2 py-1 text-xs font-medium bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400 rounded-full">UNKNOWN</span>
                {/if}
              </div>
              {#if validationResult.error && validationResult.parsing === 'failed'}
                <p class="text-xs text-red-600 dark:text-red-400 mt-1">
                  {validationResult.error}
                </p>
              {/if}
            </div>

            <!-- Validity Status -->
            <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
              <div class="flex items-center space-x-2 mb-2">
                {#if validationResult.validity === 'valid'}
                  <CheckCircle size={18} class="text-green-500" />
                  <span class="font-medium text-green-700 dark:text-green-400">Validity</span>
                  <span class="px-2 py-1 text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400 rounded-full">VALID</span>
                {:else if validationResult.validity === 'invalid'}
                  <XCircle size={18} class="text-red-500" />
                  <span class="font-medium text-red-700 dark:text-red-400">Validity</span>
                  <span class="px-2 py-1 text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400 rounded-full">INVALID</span>
                {:else}
                  <AlertTriangle size={18} class="text-yellow-500" />
                  <span class="font-medium text-yellow-700 dark:text-yellow-400">Validity</span>
                  <span class="px-2 py-1 text-xs font-medium bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400 rounded-full">UNKNOWN</span>
                {/if}
              </div>
              {#if validationResult.license_info && validationResult.license_info.expires_at}
                <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Expires: {new Date(validationResult.license_info.expires_at).toLocaleDateString()}
                </p>
              {/if}
            </div>

            <!-- Signature Status -->
            <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
              <div class="flex items-center space-x-2 mb-2">
                {#if validationResult.signature === 'verified'}
                  <CheckCircle size={18} class="text-green-500" />
                  <span class="font-medium text-green-700 dark:text-green-400">Signature</span>
                  <span class="px-2 py-1 text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400 rounded-full">VERIFIED</span>
                {:else if validationResult.signature === 'verification_failed'}
                  <XCircle size={18} class="text-red-500" />
                  <span class="font-medium text-red-700 dark:text-red-400">Signature</span>
                  <span class="px-2 py-1 text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400 rounded-full">FAILED</span>
                {:else}
                  <AlertTriangle size={18} class="text-yellow-500" />
                  <span class="font-medium text-yellow-700 dark:text-yellow-400">Signature</span>
                  <span class="px-2 py-1 text-xs font-medium bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400 rounded-full">UNKNOWN</span>
                {/if}
              </div>
            </div>
          </div>
        </div>

        <!-- License Payload -->
        {#if validationResult.license_info && validationResult.license_info.payload}
          <div>
            <h3 class="text-lg font-medium text-gray-900 dark:text-gray-50 mb-4 flex items-center space-x-2">
              <FileText size={18} class="text-indigo-600" />
              <span>License Payload</span>
            </h3>
            
            <div class="bg-gradient-to-br from-indigo-50 to-purple-50 dark:from-indigo-900/20 dark:to-purple-900/20 border border-indigo-200 dark:border-indigo-800 rounded-lg p-6">
              <!-- License ID -->
              <div class="mb-4">
                <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-indigo-100 text-indigo-800 dark:bg-indigo-900/30 dark:text-indigo-300">
                  License ID: {validationResult.license_info.id}
                </span>
              </div>

              <!-- Features as Tags -->
              {#if validationResult.license_info.payload.features}
                <div class="mb-4">
                  <span class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">Features:</span>
                  <div class="flex flex-wrap gap-2">
                    {#each validationResult.license_info.payload.features as feature}
                      <span class="px-3 py-1 text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300 rounded-full border border-blue-200 dark:border-blue-700">
                        {feature}
                      </span>
                    {/each}
                  </div>
                </div>
              {/if}

              <!-- Other License Properties -->
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <!-- User Limit -->
                {#if validationResult.license_info.payload.user_limit}
                  <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-3">
                    <span class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">User Limit</span>
                    <p class="text-lg font-semibold text-gray-900 dark:text-gray-100">{validationResult.license_info.payload.user_limit}</p>
                  </div>
                {/if}

                <!-- Support Level -->
                {#if validationResult.license_info.payload.support_level}
                  <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-3">
                    <span class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">Support Level</span>
                    <p class="text-lg font-semibold text-gray-900 dark:text-gray-100 capitalize">{validationResult.license_info.payload.support_level}</p>
                  </div>
                {/if}

                <!-- API Access -->
                {#if validationResult.license_info.payload.api_access !== undefined}
                  <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-3">
                    <span class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">API Access</span>
                    <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium {validationResult.license_info.payload.api_access ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300' : 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-300'}">
                      {validationResult.license_info.payload.api_access ? 'Enabled' : 'Disabled'}
                    </span>
                  </div>
                {/if}

                <!-- License Type -->
                {#if validationResult.license_info.payload.license_type}
                  <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-3">
                    <span class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">License Type</span>
                    <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300 capitalize">
                      {validationResult.license_info.payload.license_type}
                    </span>
                  </div>
                {/if}
              </div>

              <!-- License Metadata -->
              <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">License Metadata</h4>
                <div class="text-xs text-gray-600 dark:text-gray-400 space-y-1">
                  <p><strong>Issued:</strong> {new Date(validationResult.license_info.issued_at).toLocaleDateString()}</p>
                  <p><strong>Validity Days:</strong> {validationResult.license_info.validity_days}</p>
                  <p><strong>Tenant ID:</strong> <span class="font-mono text-xs">{validationResult.license_info.tenant_id}</span></p>
                </div>
              </div>
            </div>
          </div>
        {/if}

        <!-- Error Message for Failed Validation -->
        {#if validationResult.error && (validationResult.parsing === 'failed' || validationResult.validity === 'invalid' || validationResult.signature === 'verification_failed')}
          <div class="mt-6 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
            <div class="flex items-center space-x-2">
              <XCircle size={20} class="text-red-600" />
              <h4 class="text-sm font-medium text-red-800 dark:text-red-200">Validation Failed</h4>
            </div>
            <p class="text-sm text-red-700 dark:text-red-300 mt-2">{validationResult.error}</p>
          </div>
        {/if}

        <!-- Not Found Message -->
        {#if !validationResult.license_info && validationResult.signature === 'verification_failed'}
          <div class="mt-6 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
            <div class="flex items-center space-x-2">
              <AlertTriangle size={20} class="text-yellow-600" />
              <h4 class="text-sm font-medium text-yellow-800 dark:text-yellow-200">License Not Found</h4>
            </div>
            <p class="text-sm text-yellow-700 dark:text-yellow-300 mt-2">
              The provided license key could not be found in our database. Please check your license key and try again.
            </p>
          </div>
        {/if}
      </div>
    </div>
  {/if}
  {/if}

  {#if activeTab === 'validator'}
  <!-- Validator Code Generator -->
  <div class="max-w-4xl mx-auto">
    <div class="card p-6 space-y-6">
      <div class="text-center">
        <div class="flex items-center justify-center mb-4">
          <div class="bg-green-100 dark:bg-green-900/20 p-3 rounded-full">
            <Code class="text-green-600 dark:text-green-400" size={32} />
          </div>
        </div>
        <h2 class="text-2xl font-bold text-gray-900 dark:text-gray-50">License Validator Setup</h2>
        <p class="text-gray-600 dark:text-gray-400 mt-2">
          Download pre-configured validator code for your applications with integrated master key decryption.
        </p>
      </div>

      <!-- Language Selection and Download -->
      <div class="flex items-end space-x-4">
        <div class="flex-1">
          <label for="language-select" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Select Programming Language
          </label>
          <select
            id="language-select"
            bind:value={selectedLanguage}
            class="form-input"
          >
            {#each languages as lang}
              <option value={lang.value}>{lang.label}</option>
            {/each}
          </select>
        </div>
        <button
          class="btn btn-primary flex items-center space-x-2"
          on:click={downloadValidator}
          disabled={isDownloading}
        >
          {#if isDownloading}
            <div class="spinner"></div>
            <span>Downloading...</span>
          {:else}
            <Download size={18} />
            <span>Download Validator</span>
          {/if}
        </button>
      </div>

      <!-- Instructions -->
      <div class="bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-6">
        <h3 class="text-lg font-semibold text-blue-900 dark:text-blue-100 mb-4 flex items-center space-x-2">
          <Shield size={20} class="text-blue-600" />
          <span>Integration Instructions</span>
        </h3>

        <div class="space-y-4">
          <div class="bg-white dark:bg-gray-800 border border-blue-200 dark:border-blue-700 rounded-lg p-4">
            <h4 class="text-sm font-medium text-blue-800 dark:text-blue-200 mb-2">1. Environment Setup</h4>
            <p class="text-sm text-blue-700 dark:text-blue-300 mb-2">
              Set the LICENSE_KEY environment variable with your license key:
            </p>
            <div class="bg-gray-100 dark:bg-gray-700 rounded p-2">
              <code class="text-xs text-gray-800 dark:text-gray-200">
                export LICENSE_KEY="your-license-key-here"
              </code>
            </div>
          </div>

          <div class="bg-white dark:bg-gray-800 border border-blue-200 dark:border-blue-700 rounded-lg p-4">
            <h4 class="text-sm font-medium text-blue-800 dark:text-blue-200 mb-2">2. Download & Integrate</h4>
            <p class="text-sm text-blue-700 dark:text-blue-300 mb-2">
              Download the validator code above and add it to your project. The code includes:
            </p>
            <ul class="text-sm text-blue-700 dark:text-blue-300 space-y-1 ml-4 list-disc">
              <li>Automatic license file download and caching</li>
              <li>Hybrid encryption decryption using master keys</li>
              <li>Signature verification and expiry checking</li>
              <li>Error handling and retry logic</li>
            </ul>
          </div>

          <div class="bg-white dark:bg-gray-800 border border-blue-200 dark:border-blue-700 rounded-lg p-4">
            <h4 class="text-sm font-medium text-blue-800 dark:text-blue-200 mb-2">3. Usage</h4>
            <p class="text-sm text-blue-700 dark:text-blue-300 mb-2">
              Call the validation function in your application:
            </p>
            <div class="bg-gray-100 dark:bg-gray-700 rounded p-2">
              <pre class="text-xs text-gray-800 dark:text-gray-200"><code>{currentUsageExample}</code></pre>
            </div>
          </div>

          <div class="bg-white dark:bg-gray-800 border border-blue-200 dark:border-blue-700 rounded-lg p-4">
            <h4 class="text-sm font-medium text-blue-800 dark:text-blue-200 mb-2">4. Configuration</h4>
            <p class="text-sm text-blue-700 dark:text-blue-300 mb-2">
              Update the baseUrl variable to point to your API endpoint:
            </p>
            <div class="bg-gray-100 dark:bg-gray-700 rounded p-2">
              <code class="text-xs text-gray-800 dark:text-gray-200">
                const baseUrl = "https://your-api-domain.com";
              </code>
            </div>
          </div>
        </div>

        <div class="mt-6 p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
          <div class="flex items-start space-x-2">
            <AlertTriangle size={18} class="text-yellow-600 mt-0.5" />
            <div>
              <h4 class="text-sm font-medium text-yellow-800 dark:text-yellow-200">Security Note</h4>
              <p class="text-sm text-yellow-700 dark:text-yellow-300 mt-1">
                The downloaded validator code contains sensitive master key information. Store it securely and never commit it to version control.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
  {/if}
</div>

