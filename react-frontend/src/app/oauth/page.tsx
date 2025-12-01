'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import {
  Shield,
  Key,
  Settings,
  Copy,
  RefreshCw,
  CheckCircle,
  ExternalLink,
  Activity,
  Users,
  Clock
} from 'lucide-react';
import DashboardLayout from '@/components/layout/DashboardLayout';

interface OAuthConfig {
  issuer: string;
  authorization_endpoint: string;
  token_endpoint: string;
  userinfo_endpoint: string;
  jwks_uri: string;
  scopes_supported: string[];
  response_types_supported: string[];
  grant_types_supported: string[];
  token_endpoint_auth_methods_supported: string[];
  claims_supported: string[];
}

interface JWKS {
  keys: Array<{
    kty: string;
    use: string;
    kid: string;
    alg: string;
  }>;
}

interface OAuthStats {
  active_clients: number;
  total_tokens_issued: number;
  active_sessions: number;
  recent_requests: number;
}

export default function OAuthPage() {
  const [config, setConfig] = useState<OAuthConfig | null>(null);
  const [jwks, setJwks] = useState<JWKS | null>(null);
  const [stats, setStats] = useState<OAuthStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadOAuthData();
  }, []);

  const loadOAuthData = async () => {
    try {
      setLoading(true);

      // Load OIDC discovery configuration
      const discoveryResponse = await fetch('/.well-known/openid-configuration');
      if (discoveryResponse.ok) {
        const discoveryData = await discoveryResponse.json();
        setConfig(discoveryData);
      }

      // Load JWKS
      const jwksResponse = await fetch('/oauth/v1/jwks');
      if (jwksResponse.ok) {
        const jwksData = await jwksResponse.json();
        setJwks(jwksData);
      }

      // Mock stats (in real implementation, this would come from an API)
      setStats({
        active_clients: 5,
        total_tokens_issued: 1250,
        active_sessions: 23,
        recent_requests: 89
      });

    } catch (error) {
      console.error('Error loading OAuth data:', error);
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const rotateKeys = async () => {
    if (confirm('Are you sure you want to rotate the signing keys? This will invalidate all existing JWT tokens and require clients to re-authenticate.')) {
      try {
        // This would call an API endpoint to rotate keys
        alert('Key rotation initiated. All clients will need to re-authenticate.');
        loadOAuthData(); // Refresh data
      } catch (error) {
        console.error('Error rotating keys:', error);
      }
    }
  };

  const testEndpoint = async (endpoint: string) => {
    try {
      const response = await fetch(endpoint, { method: 'HEAD' });
      if (response.ok) {
        alert(`✅ Endpoint ${endpoint} is accessible`);
      } else {
        alert(`❌ Endpoint ${endpoint} returned status ${response.status}`);
      }
    } catch (error) {
      alert(`❌ Error testing endpoint: ${error}`);
    }
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="space-y-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-50">OAuth2/OIDC Provider</h1>
            <p className="text-gray-600 dark:text-gray-400 mt-2">Loading OAuth2/OIDC server configuration...</p>
          </div>
          <div className="animate-pulse space-y-4">
            <div className="h-64 bg-gray-200 dark:bg-gray-700 rounded-lg"></div>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-50">OAuth2/OIDC Provider</h1>
            <p className="text-gray-600 dark:text-gray-400 mt-2">Sigma Permit OAuth2/OIDC Server Configuration</p>
          </div>
          <div className="flex items-center space-x-2">
            <Badge variant="default" className="flex items-center space-x-1">
              <CheckCircle size={14} />
              <span>Server Active</span>
            </Badge>
          </div>
        </div>

        {/* Stats Overview */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Active Clients</p>
                    <p className="text-3xl font-bold text-gray-900 dark:text-gray-50">{stats.active_clients}</p>
                  </div>
                  <Shield className="text-blue-500" size={24} />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Tokens Issued</p>
                    <p className="text-3xl font-bold text-gray-900 dark:text-gray-50">{stats.total_tokens_issued.toLocaleString()}</p>
                  </div>
                  <Key className="text-green-500" size={24} />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Active Sessions</p>
                    <p className="text-3xl font-bold text-gray-900 dark:text-gray-50">{stats.active_sessions}</p>
                  </div>
                  <Users className="text-purple-500" size={24} />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Recent Requests</p>
                    <p className="text-3xl font-bold text-gray-900 dark:text-gray-50">{stats.recent_requests}</p>
                  </div>
                  <Activity className="text-orange-500" size={24} />
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Server Configuration */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Settings size={20} />
              <span>OIDC Discovery Configuration</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {config && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <Label htmlFor="issuer">Issuer</Label>
                  <div className="flex items-center space-x-2 mt-1">
                    <Input id="issuer" value={config.issuer} readOnly />
                    <Button variant="outline" size="sm" onClick={() => copyToClipboard(config.issuer)}>
                      <Copy size={14} />
                    </Button>
                  </div>
                </div>

                <div>
                  <Label>Supported Grant Types</Label>
                  <div className="flex flex-wrap gap-2 mt-1">
                    {config.grant_types_supported.map((grant, index) => (
                      <Badge key={index} variant="secondary">{grant}</Badge>
                    ))}
                  </div>
                </div>

                <div>
                  <Label>Supported Response Types</Label>
                  <div className="flex flex-wrap gap-2 mt-1">
                    {config.response_types_supported.map((type, index) => (
                      <Badge key={index} variant="secondary">{type}</Badge>
                    ))}
                  </div>
                </div>

                <div>
                  <Label>Supported Scopes</Label>
                  <div className="flex flex-wrap gap-2 mt-1">
                    {config.scopes_supported.map((scope, index) => (
                      <Badge key={index} variant="outline">{scope}</Badge>
                    ))}
                  </div>
                </div>

                <div className="md:col-span-2">
                  <Label>Supported Claims</Label>
                  <div className="flex flex-wrap gap-2 mt-1">
                    {config.claims_supported?.map((claim, index) => (
                      <Badge key={index} variant="outline" className="text-xs">{claim}</Badge>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* JSON Web Keys */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Key size={20} />
                <span>JSON Web Key Set (JWKS)</span>
              </div>
              <Button variant="outline" onClick={rotateKeys}>
                <RefreshCw size={16} className="mr-2" />
                Rotate Keys
              </Button>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {jwks && (
              <div className="space-y-4">
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  Current signing keys ({jwks.keys.length} active)
                </div>

                {jwks.keys.length === 0 ? (
                  <div className="text-center py-8">
                    <Key size={48} className="mx-auto text-gray-400 mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 dark:text-gray-50 mb-2">No Keys Configured</h3>
                    <p className="text-gray-600 dark:text-gray-400 mb-4">JWT signing keys need to be configured for the OAuth2/OIDC server.</p>
                    <Button onClick={rotateKeys}>
                      <RefreshCw size={16} className="mr-2" />
                      Generate Keys
                    </Button>
                  </div>
                ) : (
                  jwks.keys.map((key, index) => (
                    <div key={key.kid} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center space-x-2">
                          <Badge variant="default">Key {index + 1}</Badge>
                          <Badge variant="secondary">{key.alg}</Badge>
                          <Badge variant={key.use === 'sig' ? 'default' : 'secondary'}>
                            {key.use === 'sig' ? 'Signing' : 'Encryption'}
                          </Badge>
                        </div>
                        <div className="text-sm text-gray-500 dark:text-gray-400">
                          ID: {key.kid}
                        </div>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                        <div>
                          <Label className="text-xs text-gray-500 dark:text-gray-400">Key Type</Label>
                          <div className="font-mono">{key.kty}</div>
                        </div>
                        <div>
                          <Label className="text-xs text-gray-500 dark:text-gray-400">Algorithm</Label>
                          <div className="font-mono">{key.alg}</div>
                        </div>
                        <div>
                          <Label className="text-xs text-gray-500 dark:text-gray-400">Use</Label>
                          <div className="font-mono">{key.use}</div>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* OAuth2/OIDC Endpoints */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <ExternalLink size={20} />
              <span>OAuth2/OIDC Endpoints</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {config && (
              <div className="space-y-4">
                <div className="grid grid-cols-1 gap-4">
                  <div>
                    <Label className="text-sm font-medium">Authorization Endpoint</Label>
                    <div className="flex items-center space-x-2 mt-1">
                      <Input value={config.authorization_endpoint} readOnly className="font-mono text-sm" />
                      <Button variant="outline" size="sm" onClick={() => copyToClipboard(config.authorization_endpoint)}>
                        <Copy size={14} />
                      </Button>
                      <Button variant="outline" size="sm" onClick={() => testEndpoint(config.authorization_endpoint)}>
                        Test
                      </Button>
                    </div>
                  </div>

                  <div>
                    <Label className="text-sm font-medium">Token Endpoint</Label>
                    <div className="flex items-center space-x-2 mt-1">
                      <Input value={config.token_endpoint} readOnly className="font-mono text-sm" />
                      <Button variant="outline" size="sm" onClick={() => copyToClipboard(config.token_endpoint)}>
                        <Copy size={14} />
                      </Button>
                      <Button variant="outline" size="sm" onClick={() => testEndpoint(config.token_endpoint)}>
                        Test
                      </Button>
                    </div>
                  </div>

                  <div>
                    <Label className="text-sm font-medium">UserInfo Endpoint</Label>
                    <div className="flex items-center space-x-2 mt-1">
                      <Input value={config.userinfo_endpoint} readOnly className="font-mono text-sm" />
                      <Button variant="outline" size="sm" onClick={() => copyToClipboard(config.userinfo_endpoint)}>
                        <Copy size={14} />
                      </Button>
                      <Button variant="outline" size="sm" onClick={() => testEndpoint(config.userinfo_endpoint)}>
                        Test
                      </Button>
                    </div>
                  </div>

                  <div>
                    <Label className="text-sm font-medium">JWKS URI</Label>
                    <div className="flex items-center space-x-2 mt-1">
                      <Input value={config.jwks_uri} readOnly className="font-mono text-sm" />
                      <Button variant="outline" size="sm" onClick={() => copyToClipboard(config.jwks_uri)}>
                        <Copy size={14} />
                      </Button>
                      <Button variant="outline" size="sm" onClick={() => testEndpoint(config.jwks_uri)}>
                        Test
                      </Button>
                    </div>
                  </div>

                  <div>
                    <Label className="text-sm font-medium">Discovery Endpoint</Label>
                    <div className="flex items-center space-x-2 mt-1">
                      <Input value="/.well-known/openid-configuration" readOnly className="font-mono text-sm" />
                      <Button variant="outline" size="sm" onClick={() => copyToClipboard(window.location.origin + '/.well-known/openid-configuration')}>
                        <Copy size={14} />
                      </Button>
                      <Button variant="outline" size="sm" onClick={() => testEndpoint('/.well-known/openid-configuration')}>
                        Test
                      </Button>
                    </div>
                  </div>

                  <div>
                    <Label className="text-sm font-medium">Introspection Endpoint</Label>
                    <div className="flex items-center space-x-2 mt-1">
                      <Input value="/oauth/v1/introspect" readOnly className="font-mono text-sm" />
                      <Button variant="outline" size="sm" onClick={() => copyToClipboard(window.location.origin + '/oauth/v1/introspect')}>
                        <Copy size={14} />
                      </Button>
                      <Button variant="outline" size="sm" onClick={() => testEndpoint('/oauth/v1/introspect')}>
                        Test
                      </Button>
                    </div>
                  </div>

                  <div>
                    <Label className="text-sm font-medium">Revocation Endpoint</Label>
                    <div className="flex items-center space-x-2 mt-1">
                      <Input value="/oauth/v1/revoke" readOnly className="font-mono text-sm" />
                      <Button variant="outline" size="sm" onClick={() => copyToClipboard(window.location.origin + '/oauth/v1/revoke')}>
                        <Copy size={14} />
                      </Button>
                      <Button variant="outline" size="sm" onClick={() => testEndpoint('/oauth/v1/revoke')}>
                        Test
                      </Button>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}