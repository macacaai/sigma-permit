'use client';

import { useState, useEffect } from 'react';
import ProtectedRoute from '@/components/ProtectedRoute';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Shield, Copy, Loader2, RotateCcw, Key, ChevronDown, ChevronRight } from 'lucide-react';
import { masterKeyApi, MasterKey } from '@/lib/api';
import { toast } from '@/lib/toast';

export default function MasterKeysPage() {
  const [masterKeys, setMasterKeys] = useState<MasterKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [rotationDialogOpen, setRotationDialogOpen] = useState(false);
  const [overrideDialogOpen, setOverrideDialogOpen] = useState(false);
  const [overridePublicKey, setOverridePublicKey] = useState('');
  const [overridePrivateKey, setOverridePrivateKey] = useState('');
  const [operationLoading, setOperationLoading] = useState(false);
  const [inactiveKeysExpanded, setInactiveKeysExpanded] = useState(false);

  useEffect(() => {
    loadMasterKeys();
  }, []);

  const loadMasterKeys = async () => {
    try {
      setLoading(true);
      setError(null);
      const keys = await masterKeyApi.getMasterKeys();
      setMasterKeys(keys);
    } catch (err: any) {
      setError(err.message || 'Failed to load master keys');
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = async (text: string, label: string) => {
    try {
      await navigator.clipboard.writeText(text);
      toast.success(`${label} copied to clipboard`);
    } catch (err) {
      toast.error('Failed to copy to clipboard');
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const handleRotateMasterKey = async () => {
    try {
      setOperationLoading(true);
      await masterKeyApi.rotateMasterKey();
      toast.success('Master key rotated successfully');
      setRotationDialogOpen(false);
      loadMasterKeys(); // Refresh the list
    } catch (err: any) {
      toast.error(err.message || 'Failed to rotate master key');
    } finally {
      setOperationLoading(false);
    }
  };

  const handleOverrideMasterKey = async () => {
    if (!overridePublicKey.trim() || !overridePrivateKey.trim()) {
      toast.error('Both public key and private key are required');
      return;
    }

    try {
      setOperationLoading(true);
      await masterKeyApi.overrideMasterKey(overridePublicKey.trim(), overridePrivateKey.trim());
      toast.success('Master key overridden successfully');
      setOverrideDialogOpen(false);
      setOverridePublicKey('');
      setOverridePrivateKey('');
      loadMasterKeys(); // Refresh the list
    } catch (err: any) {
      toast.error(err.message || 'Failed to override master key');
    } finally {
      setOperationLoading(false);
    }
  };

  return (
    <ProtectedRoute>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-50">Master Keys</h1>
            <p className="text-gray-600 dark:text-gray-400 mt-2">
              View the master encryption keys used for license files.
            </p>
          </div>
          <div className="flex gap-2">
            <Dialog open={rotationDialogOpen} onOpenChange={setRotationDialogOpen}>
              <DialogTrigger asChild>
                <Button variant="destructive">
                  <RotateCcw className="w-4 h-4 mr-2" />
                  Rotate Key
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle className="text-red-600 dark:text-red-400">⚠️ Critical Operation</DialogTitle>
                  <DialogDescription className="text-red-700 dark:text-red-300">
                    <strong>This is a serious operation that may cause irreversible damage to license verification for applications with existing versions of keys.</strong>
                    <br /><br />
                    Rotating the master key will:
                    <ul className="list-disc list-inside mt-2 space-y-1">
                      <li>Generate a new RSA key pair</li>
                      <li>Mark the current active key as inactive</li>
                      <li>Set the new key pair as active</li>
                      <li>All existing licenses will become invalid</li>
                    </ul>
                    <br />
                    <strong>Only proceed if you understand the consequences and have a migration plan.</strong>
                  </DialogDescription>
                </DialogHeader>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setRotationDialogOpen(false)}>
                    Cancel
                  </Button>
                  <Button
                    variant="destructive"
                    onClick={handleRotateMasterKey}
                    disabled={operationLoading}
                  >
                    {operationLoading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
                    Proceed with Rotation
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>

            <Dialog open={overrideDialogOpen} onOpenChange={setOverrideDialogOpen}>
              <DialogTrigger asChild>
                <Button variant="destructive">
                  <Key className="w-4 h-4 mr-2" />
                  Override Key
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-2xl">
                <DialogHeader>
                  <DialogTitle className="text-red-600 dark:text-red-400">⚠️ Critical Operation</DialogTitle>
                  <DialogDescription className="text-red-700 dark:text-red-300">
                    <strong>This is a serious operation that may cause irreversible damage to license verification for applications with existing versions of keys.</strong>
                    <br /><br />
                    Overriding the master key will:
                    <ul className="list-disc list-inside mt-2 space-y-1">
                      <li>Mark the current active key as inactive</li>
                      <li>Replace it with the key pair you provide</li>
                      <li>All existing licenses may become invalid if keys don't match</li>
                    </ul>
                    <br />
                    <strong>Only proceed if you understand the consequences and have a migration plan.</strong>
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4 py-4">
                  <div className="space-y-2">
                    <Label htmlFor="public-key">Public Key (Base64-encoded DER)</Label>
                    <Textarea
                      id="public-key"
                      placeholder="Enter the public key..."
                      value={overridePublicKey}
                      onChange={(e) => setOverridePublicKey(e.target.value)}
                      rows={6}
                      className="font-mono text-xs resize-none w-full"
                      style={{
                        wordBreak: 'break-all',
                        whiteSpace: 'pre-wrap',
                        maxWidth: '100%',
                        overflowWrap: 'break-word'
                      }}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="private-key">Private Key (Base64-encoded DER)</Label>
                    <Textarea
                      id="private-key"
                      placeholder="Enter the private key..."
                      value={overridePrivateKey}
                      onChange={(e) => setOverridePrivateKey(e.target.value)}
                      rows={6}
                      className="font-mono text-xs resize-none w-full"
                      style={{
                        wordBreak: 'break-all',
                        whiteSpace: 'pre-wrap',
                        maxWidth: '100%',
                        overflowWrap: 'break-word'
                      }}
                    />
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setOverrideDialogOpen(false)}>
                    Cancel
                  </Button>
                  <Button
                    variant="destructive"
                    onClick={handleOverrideMasterKey}
                    disabled={operationLoading || !overridePublicKey.trim() || !overridePrivateKey.trim()}
                  >
                    {operationLoading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
                    Proceed with Override
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>

            <Button onClick={loadMasterKeys} disabled={loading} variant="outline">
              {loading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Shield className="w-4 h-4 mr-2" />}
              Refresh
            </Button>
          </div>
        </div>

        {loading ? (
          <Card>
            <CardContent className="flex items-center justify-center py-12">
              <div className="text-center">
                <Loader2 className="mx-auto text-gray-400 dark:text-gray-500 mb-4 animate-spin" size={48} />
                <p className="text-gray-600 dark:text-gray-400">Loading master keys...</p>
              </div>
            </CardContent>
          </Card>
        ) : error ? (
          <Card>
            <CardContent className="py-12">
              <div className="text-center">
                <Shield className="mx-auto text-red-400 dark:text-red-500 mb-4" size={48} />
                <h3 className="text-lg font-medium text-red-900 dark:text-red-50 mb-2">Error</h3>
                <p className="text-red-600 dark:text-red-400 mb-4">{error}</p>
                <Button onClick={loadMasterKeys} variant="outline">
                  Try Again
                </Button>
              </div>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-6">
            {/* Active Keys Section */}
            {(() => {
              const activeKeys = masterKeys.filter(key => key.is_active);
              const inactiveKeys = masterKeys.filter(key => !key.is_active);

              return (
                <>
                  {activeKeys.length === 0 && inactiveKeys.length === 0 ? (
                    <Card>
                      <CardContent className="flex items-center justify-center py-12">
                        <div className="text-center">
                          <Shield className="mx-auto text-gray-400 dark:text-gray-500 mb-4" size={48} />
                          <h3 className="text-lg font-medium text-gray-900 dark:text-gray-50 mb-2">No Master Keys</h3>
                          <p className="text-gray-600 dark:text-gray-400">No master keys have been configured yet.</p>
                        </div>
                      </CardContent>
                    </Card>
                  ) : (
                    <>
                      {/* Active Keys */}
                      {activeKeys.length > 0 && (
                        <div className="space-y-4">
                          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-50">Active Master Key</h3>
                          {activeKeys.map((key) => (
                            <Card key={key.id} className="border-green-200 dark:border-green-800">
                              <CardHeader>
                                <CardTitle className="flex items-center gap-2">
                                  <Shield className="w-5 h-5" />
                                  Key ID: {key.id}
                                  <span className="px-2 py-1 text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200 rounded-full">
                                    Active
                                  </span>
                                </CardTitle>
                              </CardHeader>
                              <CardContent className="space-y-4">
                                {/* Public Key Section */}
                                <div className="space-y-2">
                                  <div className="flex items-center justify-between">
                                    <label className="text-sm font-medium text-gray-700 dark:text-gray-300 uppercase tracking-wide">
                                      Public Key
                                    </label>
                                    <Button
                                      variant="ghost"
                                      size="sm"
                                      onClick={() => copyToClipboard(key.public_key, 'Public key')}
                                      className="text-xs"
                                    >
                                      <Copy className="w-3 h-3 mr-1" />
                                      Copy
                                    </Button>
                                  </div>
                                  <div className="bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-md p-3">
                                    <code className="text-xs text-gray-800 dark:text-gray-200 break-all font-mono">
                                      {key.public_key}
                                    </code>
                                  </div>
                                </div>

                                {/* Private Key Section */}
                                <div className="space-y-2">
                                  <div className="flex items-center justify-between">
                                    <label className="text-sm font-medium text-gray-700 dark:text-gray-300 uppercase tracking-wide">
                                      Private Key (Masked)
                                    </label>
                                    {key.private_key_masked !== 'Not generated' && (
                                      <Button
                                        variant="ghost"
                                        size="sm"
                                        onClick={() => copyToClipboard(key.private_key_masked, 'Private key')}
                                        className="text-xs"
                                      >
                                        <Copy className="w-3 h-3 mr-1" />
                                        Copy
                                      </Button>
                                    )}
                                  </div>
                                  <div className="bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-md p-3">
                                    <code className="text-xs text-gray-800 dark:text-gray-200 break-all font-mono">
                                      {key.private_key_masked}
                                    </code>
                                  </div>
                                </div>

                                {/* Created Date */}
                                <div className="flex justify-end pt-2 border-t border-gray-200 dark:border-gray-700">
                                  <div className="text-right text-sm text-gray-500 dark:text-gray-400">
                                    <div className="font-medium">Created</div>
                                    <div>{formatDate(key.created_at)}</div>
                                  </div>
                                </div>
                              </CardContent>
                            </Card>
                          ))}
                        </div>
                      )}

                      {/* Inactive Keys Section */}
                      {inactiveKeys.length > 0 && (
                        <div className="space-y-4">
                          <button
                            onClick={() => setInactiveKeysExpanded(!inactiveKeysExpanded)}
                            className="flex items-center gap-2 text-lg font-semibold text-gray-900 dark:text-gray-50 hover:text-gray-700 dark:hover:text-gray-300 transition-colors"
                          >
                            {inactiveKeysExpanded ? <ChevronDown className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}
                            Old Master Keys ({inactiveKeys.length})
                          </button>

                          {inactiveKeysExpanded && (
                            <div className="space-y-4 pl-7">
                              {inactiveKeys.map((key) => (
                                <Card key={key.id} className="border-gray-200 dark:border-gray-700 opacity-75">
                                  <CardHeader>
                                    <CardTitle className="flex items-center gap-2">
                                      <Shield className="w-5 h-5" />
                                      Key ID: {key.id}
                                      <span className="px-2 py-1 text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200 rounded-full">
                                        Inactive
                                      </span>
                                    </CardTitle>
                                  </CardHeader>
                                  <CardContent className="space-y-4">
                                    {/* Public Key Section */}
                                    <div className="space-y-2">
                                      <div className="flex items-center justify-between">
                                        <label className="text-sm font-medium text-gray-700 dark:text-gray-300 uppercase tracking-wide">
                                          Public Key
                                        </label>
                                        <Button
                                          variant="ghost"
                                          size="sm"
                                          onClick={() => copyToClipboard(key.public_key, 'Public key')}
                                          className="text-xs"
                                        >
                                          <Copy className="w-3 h-3 mr-1" />
                                          Copy
                                        </Button>
                                      </div>
                                      <div className="bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-md p-3">
                                        <code className="text-xs text-gray-800 dark:text-gray-200 break-all font-mono">
                                          {key.public_key}
                                        </code>
                                      </div>
                                    </div>

                                    {/* Private Key Section */}
                                    <div className="space-y-2">
                                      <div className="flex items-center justify-between">
                                        <label className="text-sm font-medium text-gray-700 dark:text-gray-300 uppercase tracking-wide">
                                          Private Key (Masked)
                                        </label>
                                        {key.private_key_masked !== 'Not generated' && (
                                          <Button
                                            variant="ghost"
                                            size="sm"
                                            onClick={() => copyToClipboard(key.private_key_masked, 'Private key')}
                                            className="text-xs"
                                          >
                                            <Copy className="w-3 h-3 mr-1" />
                                            Copy
                                          </Button>
                                        )}
                                      </div>
                                      <div className="bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-md p-3">
                                        <code className="text-xs text-gray-800 dark:text-gray-200 break-all font-mono">
                                          {key.private_key_masked}
                                        </code>
                                      </div>
                                    </div>

                                    {/* Dates */}
                                    <div className="flex justify-between pt-2 border-t border-gray-200 dark:border-gray-700">
                                      <div className="text-sm text-gray-500 dark:text-gray-400">
                                        <div className="font-medium">Created</div>
                                        <div>{formatDate(key.created_at)}</div>
                                      </div>
                                      <div className="text-right text-sm text-gray-500 dark:text-gray-400">
                                        <div className="font-medium">Inactive Since</div>
                                        <div>{formatDate(key.updated_at)}</div>
                                      </div>
                                    </div>
                                  </CardContent>
                                </Card>
                              ))}
                            </div>
                          )}
                        </div>
                      )}
                    </>
                  )}
                </>
              );
            })()}
          </div>
        )}
      </div>
    </ProtectedRoute>
  );
}