'use client';

import { useState } from 'react';
import ProtectedRoute from '@/components/ProtectedRoute';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Shield, Upload, CheckCircle, XCircle, AlertCircle, Loader2, Download, Code, ChevronDown } from 'lucide-react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { toast } from '@/lib/toast';
import { licenseApi } from '@/lib/api';

interface ValidationResult {
  parsing: 'success' | 'failed';
  validity: 'valid' | 'invalid';
  signature: 'verified' | 'verification_failed';
  licenseInfo?: any;
  error?: string;
}

export default function ValidatePage() {
  const [licenseKey, setLicenseKey] = useState('');
  const [licenseFile, setLicenseFile] = useState<File | null>(null);
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);
  const [isValidating, setIsValidating] = useState(false);
  const [downloadDialogOpen, setDownloadDialogOpen] = useState(false);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setLicenseFile(file);
    }
  };

  const validateLicense = async () => {
    if (!licenseKey.trim()) {
      toast.error('Please enter a license key');
      return;
    }

    if (!licenseFile) {
      toast.error('Please select a license file');
      return;
    }

    setIsValidating(true);
    setValidationResult(null);

    try {
      const result = await performValidation(licenseKey.trim(), licenseFile);
      setValidationResult(result);

      if (result.parsing === 'success' && result.validity === 'valid' && result.signature === 'verified') {
        toast.success('License validation successful!');
      } else if (result.error) {
        toast.error(`Validation failed: ${result.error}`);
      } else {
        toast.error('License validation failed');
      }
    } catch (error) {
      console.error('Validation error:', error);
      setValidationResult({
        parsing: 'failed',
        validity: 'invalid',
        signature: 'verification_failed',
        error: error instanceof Error ? error.message : 'Unknown error occurred'
      });
      toast.error('Validation failed');
    } finally {
      setIsValidating(false);
    }
  };

  const performValidation = async (key: string, file: File): Promise<ValidationResult> => {
    try {
      // Use server-side validation API
      const result = await licenseApi.validateFile(key, file);

      // Map server response to our ValidationResult format
      return {
        parsing: result.parsing,
        validity: result.validity,
        signature: result.signature,
        licenseInfo: result.license_info,
        error: result.error
      };
    } catch (error) {
      return {
        parsing: 'failed',
        validity: 'invalid',
        signature: 'verification_failed',
        error: error instanceof Error ? error.message : 'Validation failed'
      };
    }
  };


  const resetValidation = () => {
    setLicenseKey('');
    setLicenseFile(null);
    setValidationResult(null);
  };

  const downloadValidator = (language: string) => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';
    window.open(`${apiUrl}/licenses/generate-validator?language=${language}`, '_blank');
    setDownloadDialogOpen(false);
  };

  return (
    <ProtectedRoute>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-50">License Validation</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">Validate license files offline using embedded master key</p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="w-5 h-5" />
              License Validator
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* License Key Input */}
              <div className="space-y-2">
                <Label htmlFor="license-key">License Key (Base64-encoded)</Label>
                <Input
                  id="license-key"
                  type="text"
                  placeholder="Enter the license key..."
                  value={licenseKey}
                  onChange={(e) => setLicenseKey(e.target.value)}
                  className="font-mono text-sm"
                />
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  The public key used to verify the license signature
                </p>
              </div>

              {/* File Upload */}
              <div className="space-y-2">
                <Label htmlFor="license-file">License File</Label>
                <div className="flex items-center gap-2">
                  <Input
                    id="license-file"
                    type="file"
                    accept=".lic"
                    onChange={handleFileChange}
                    className="flex-1"
                  />
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => document.getElementById('license-file')?.click()}
                  >
                    <Upload className="w-4 h-4" />
                  </Button>
                </div>
                {licenseFile && (
                  <p className="text-xs text-green-600 dark:text-green-400">
                    Selected: {licenseFile.name}
                  </p>
                )}
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Upload the encrypted license file (.lic)
                </p>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-3">
              <Button
                onClick={validateLicense}
                disabled={isValidating || !licenseKey.trim() || !licenseFile}
                className="flex items-center gap-2"
              >
                {isValidating ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Shield className="w-4 h-4" />
                )}
                {isValidating ? 'Validating...' : 'Validate License'}
              </Button>
              <Button variant="outline" onClick={resetValidation}>
                Reset
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Validator Download Section */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Code className="w-5 h-5" />
              Download License Validator
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              Download pre-configured validator code for your preferred programming language. These validators include
              offline validation, daily online checks, and automatic license reissue functionality.
            </p>

            <Dialog open={downloadDialogOpen} onOpenChange={setDownloadDialogOpen}>
              <DialogTrigger asChild>
                <Button variant="outline" className="flex items-center gap-2">
                  <Download className="w-4 h-4" />
                  Download Validator
                  <ChevronDown className="w-4 h-4" />
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-md">
                <DialogHeader>
                  <DialogTitle>Select Programming Language</DialogTitle>
                  <DialogDescription>
                    Choose the programming language for your license validator code.
                  </DialogDescription>
                </DialogHeader>
                <div className="grid grid-cols-2 gap-3 py-4">
                  <Button
                    variant="outline"
                    onClick={() => downloadValidator('js')}
                    className="justify-start"
                  >
                    JavaScript
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => downloadValidator('ts')}
                    className="justify-start"
                  >
                    TypeScript
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => downloadValidator('py')}
                    className="justify-start"
                  >
                    Python
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => downloadValidator('java')}
                    className="justify-start"
                  >
                    Java
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => downloadValidator('rust')}
                    className="justify-start"
                  >
                    Rust
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => downloadValidator('dart')}
                    className="justify-start"
                  >
                    Dart
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => downloadValidator('go')}
                    className="justify-start"
                  >
                    Go
                  </Button>
                </div>
              </DialogContent>
            </Dialog>

            <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
              <div className="flex items-start gap-2">
                <Shield className="w-4 h-4 text-blue-500 mt-0.5" />
                <div className="text-sm text-blue-800 dark:text-blue-200">
                  <strong>Features included:</strong>
                  <ul className="mt-1 ml-4 list-disc space-y-1">
                    <li>Offline license validation using embedded master key</li>
                    <li>Daily online validation checks (cached for 24 hours)</li>
                    <li>Automatic license reissue on expiry with rate limiting</li>
                    <li>Robust error handling and retry mechanisms</li>
                  </ul>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Validation Results */}
        {validationResult && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                {validationResult.parsing === 'success' && validationResult.validity === 'valid' && validationResult.signature === 'verified' ? (
                  <CheckCircle className="w-5 h-5 text-green-500" />
                ) : (
                  <XCircle className="w-5 h-5 text-red-500" />
                )}
                Validation Results
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">Parsing:</span>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    validationResult.parsing === 'success'
                      ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400'
                      : 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400'
                  }`}>
                    {validationResult.parsing === 'success' ? 'Success' : 'Failed'}
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">Validity:</span>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    validationResult.validity === 'valid'
                      ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400'
                      : 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400'
                  }`}>
                    {validationResult.validity === 'valid' ? 'Valid' : 'Invalid'}
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">Signature:</span>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    validationResult.signature === 'verified'
                      ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400'
                      : 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400'
                  }`}>
                    {validationResult.signature === 'verified' ? 'Verified' : 'Failed'}
                  </span>
                </div>
              </div>

              {validationResult.error && (
                <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                  <div className="flex items-center gap-2">
                    <AlertCircle className="w-4 h-4 text-red-500" />
                    <span className="text-sm text-red-800 dark:text-red-200">{validationResult.error}</span>
                  </div>
                </div>
              )}

              {validationResult.licenseInfo && (
                <div className="space-y-3">
                  <h4 className="text-sm font-medium text-gray-900 dark:text-gray-50">License Information</h4>
                  <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="font-medium text-gray-500 dark:text-gray-400">License ID:</span>
                        <span className="ml-2 font-mono text-gray-900 dark:text-gray-50">{validationResult.licenseInfo.id}</span>
                      </div>
                      <div>
                        <span className="font-medium text-gray-500 dark:text-gray-400">Tenant ID:</span>
                        <span className="ml-2 font-mono text-gray-900 dark:text-gray-50">{validationResult.licenseInfo.tenant_id}</span>
                      </div>
                      <div>
                        <span className="font-medium text-gray-500 dark:text-gray-400">Issued:</span>
                        <span className="ml-2 text-gray-900 dark:text-gray-50">
                          {new Date(validationResult.licenseInfo.issued_at).toLocaleDateString()}
                        </span>
                      </div>
                      <div>
                        <span className="font-medium text-gray-500 dark:text-gray-400">Validity:</span>
                        <span className="ml-2 text-gray-900 dark:text-gray-50">{validationResult.licenseInfo.validity_days} days</span>
                      </div>
                    </div>
                    {validationResult.licenseInfo.payload && (
                      <div className="mt-4">
                        <span className="font-medium text-gray-500 dark:text-gray-400">Payload:</span>
                        <pre className="mt-1 text-xs text-gray-800 dark:text-gray-200 bg-white dark:bg-gray-900 p-2 rounded border overflow-x-auto">
                          {JSON.stringify(validationResult.licenseInfo.payload, null, 2)}
                        </pre>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </ProtectedRoute>
  );
}