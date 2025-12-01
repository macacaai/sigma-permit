const fs = require('fs');
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
    let decrypted = decipher.update(ciphertext, 'buffer');
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
            const url = `https://your-api-domain.com/api/licenses/issue?encoded_license_key=${encodeURIComponent(encodedKey)}`;

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
                console.error(`Download failed: ${err.message}`);
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
});