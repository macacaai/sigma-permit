package main

import (
	"crypto"
	"crypto/rsa"
	"crypto/sha256"
	"crypto/x509"
	"encoding/hex"
	"encoding/json"
	"encoding/pem"
	"fmt"
	"io/ioutil"
	"os"
	"time"
)

type LicenseData struct {
	EncryptedPayload string `json:"encrypted_payload"`
	Signature        string `json:"signature"`
}

type LicensePayload struct {
	ExpiresAt string `json:"expires_at"`
}

func validateLicense(licensePath string, trustedPublicKey string) bool {
	// Read license file
	data, err := ioutil.ReadFile(licensePath)
	if err != nil {
		fmt.Printf("Error reading license file: %v\n", err)
		return false
	}

	var license LicenseData
	if err := json.Unmarshal(data, &license); err != nil {
		fmt.Printf("Error parsing license JSON: %v\n", err)
		return false
	}

	if license.EncryptedPayload == "" || license.Signature == "" {
		fmt.Println("Invalid license format")
		return false
	}

	// Parse public key
	block, _ := pem.Decode([]byte(trustedPublicKey))
	if block == nil {
		fmt.Println("Failed to parse PEM block containing public key")
		return false
	}

	pub, err := x509.ParsePKIXPublicKey(block.Bytes)
	if err != nil {
		fmt.Printf("Failed to parse public key: %v\n", err)
		return false
	}

	rsaPub, ok := pub.(*rsa.PublicKey)
	if !ok {
		fmt.Println("Not an RSA public key")
		return false
	}

	// Verify signature
	hashed := sha256.Sum256([]byte(license.EncryptedPayload))
	sig, err := hex.DecodeString(license.Signature)
	if err != nil {
		fmt.Printf("Error decoding signature: %v\n", err)
		return false
	}

	err = rsa.VerifyPSS(rsaPub, crypto.SHA256, hashed[:], sig, nil)
	if err != nil {
		fmt.Printf("Signature verification failed: %v\n", err)
		return false
	}

	// Decrypt payload (placeholder - implement your decryption logic)
	// decrypted := decrypt(license.EncryptedPayload, privateKey)
	// var payload LicensePayload
	// if err := json.Unmarshal([]byte(decrypted), &payload); err != nil { ... }
	payload := LicensePayload{ExpiresAt: "2025-12-31T23:59:59Z"} // Example

	// Check expiration
	if payload.ExpiresAt == "" {
		fmt.Println("Missing expiration date")
		return false
	}

	expirationTime, err := time.Parse(time.RFC3339, payload.ExpiresAt)
	if err != nil {
		fmt.Printf("Error parsing expiration date: %v\n", err)
		return false
	}

	if time.Now().UTC().After(expirationTime) {
		fmt.Println("License has expired")
		return false
	}

	return true
}

// Example usage:
// func main() {
//     trustedPublicKey := `-----BEGIN PUBLIC KEY-----...`
//     if validateLicense("license.json", trustedPublicKey) {
//         fmt.Println("Valid license")
//     } else {
//         fmt.Println("Invalid license")
//     }
// }
