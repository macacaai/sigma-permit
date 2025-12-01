'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import {
  Settings,
  Mail,
  Shield,
  Zap,
  Globe,
  Eye,
  EyeOff,
  Plus,
  TestTube,
  CheckCircle,
  AlertCircle
} from 'lucide-react';
import DashboardLayout from '@/components/layout/DashboardLayout';

interface ExternalProvider {
  id: string;
  name: string;
  type: 'email' | 'sms' | 'captcha' | 'payment' | 'storage' | 'analytics' | 'oauth_external' | 'saml' | 'sso';
  provider: string; // e.g., 'sendgrid', 'twilio', 'recaptcha', 'stripe', etc.
  is_active: boolean;
  configuration: Record<string, any>;
  last_tested?: string;
  test_status?: 'success' | 'failed' | 'pending';
}

export default function ProvidersPage() {
  const [providers, setProviders] = useState<ExternalProvider[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showSecrets, setShowSecrets] = useState<Record<string, boolean>>({});

  useEffect(() => {
    loadProviders();
  }, []);

  const loadProviders = async () => {
    try {
      setLoading(true);
      // Mock data - in real implementation, this would come from an API
      setProviders([
        {
          id: 'email-sendgrid',
          name: 'SendGrid Email Service',
          type: 'email',
          provider: 'sendgrid',
          is_active: true,
          configuration: {
            api_key: '••••••••••••••••••••••••••••••••••••••••',
            from_email: 'noreply@sigma-permit.com',
            from_name: 'Sigma Permit'
          },
          last_tested: '2025-12-01T10:30:00Z',
          test_status: 'success'
        },
        {
          id: 'captcha-recaptcha',
          name: 'Google reCAPTCHA',
          type: 'captcha',
          provider: 'recaptcha',
          is_active: true,
          configuration: {
            site_key: '6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI',
            secret_key: '••••••••••••••••••••••••••••••••••••••••'
          },
          last_tested: '2025-12-01T09:15:00Z',
          test_status: 'success'
        },
        {
          id: 'sms-twilio',
          name: 'Twilio SMS Service',
          type: 'sms',
          provider: 'twilio',
          is_active: false,
          configuration: {
            account_sid: 'AC••••••••••••••••••••••••••••••••••••',
            auth_token: '••••••••••••••••••••••••••••••••••••••••',
            from_number: '+1234567890'
          },
          last_tested: '2025-11-30T14:20:00Z',
          test_status: 'failed'
        },
        {
          id: 'oauth-google',
          name: 'Google OAuth (External)',
          type: 'oauth_external',
          provider: 'google',
          is_active: true,
          configuration: {
            client_id: 'google-oauth-client-id',
            client_secret: '••••••••••••••••••••••••••••••••••••••••',
            scopes: ['openid', 'profile', 'email']
          },
          last_tested: '2025-12-01T08:45:00Z',
          test_status: 'success'
        }
      ]);
    } catch (error) {
      console.error('Error loading providers:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleProvider = async (providerId: string, isActive: boolean) => {
    setProviders(providers =>
      providers.map(p =>
        p.id === providerId ? { ...p, is_active: isActive } : p
      )
    );
  };

  const testProvider = async (providerId: string) => {
    // Mock testing - in real implementation, this would call an API
    setProviders(providers =>
      providers.map(p =>
        p.id === providerId
          ? { ...p, test_status: 'pending' as const }
          : p
      )
    );

    // Simulate API call
    setTimeout(() => {
      setProviders(providers =>
        providers.map(p =>
          p.id === providerId
            ? {
                ...p,
                test_status: Math.random() > 0.3 ? 'success' : 'failed',
                last_tested: new Date().toISOString()
              }
            : p
        )
      );
    }, 2000);
  };

  const createProvider = async (formData: FormData) => {
    try {
      const providerData = {
        name: formData.get('name'),
        type: formData.get('type'),
        provider: formData.get('provider'),
        is_active: formData.get('is_active') === 'on'
      };

      // In real implementation, this would call an API
      console.log('Creating provider:', providerData);
      setShowCreateDialog(false);
      loadProviders();
    } catch (error) {
      console.error('Error creating provider:', error);
    }
  };

  const getProviderIcon = (type: string) => {
    switch (type) {
      case 'email': return <Mail size={20} />;
      case 'sms': return <Settings size={20} />;
      case 'captcha': return <Shield size={20} />;
      case 'oauth_external': return <Globe size={20} />;
      default: return <Settings size={20} />;
    }
  };

  const getProviderColor = (type: string) => {
    switch (type) {
      case 'email': return 'text-blue-600 bg-blue-100 dark:bg-blue-900/20';
      case 'sms': return 'text-green-600 bg-green-100 dark:bg-green-900/20';
      case 'captcha': return 'text-purple-600 bg-purple-100 dark:bg-purple-900/20';
      case 'oauth_external': return 'text-orange-600 bg-orange-100 dark:bg-orange-900/20';
      default: return 'text-gray-600 bg-gray-100 dark:bg-gray-900/20';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="space-y-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-50">External Providers</h1>
            <p className="text-gray-600 dark:text-gray-400 mt-2">Loading external service providers...</p>
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
            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-50">External Providers</h1>
            <p className="text-gray-600 dark:text-gray-400 mt-2">Configure external service providers for email, SMS, captcha, and more</p>
          </div>
          <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
            <DialogTrigger asChild>
              <Button className="flex items-center space-x-2">
                <Plus size={16} />
                <span>Add Provider</span>
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Add External Provider</DialogTitle>
              </DialogHeader>
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  const formData = new FormData(e.target as HTMLFormElement);
                  createProvider(formData);
                }}
                className="space-y-4"
              >
                <div>
                  <Label htmlFor="name">Provider Name</Label>
                  <Input id="name" name="name" required placeholder="e.g., SendGrid Email Service" />
                </div>
                <div>
                  <Label htmlFor="type">Provider Type</Label>
                  <Select name="type" required>
                    <SelectTrigger>
                      <SelectValue placeholder="Select provider type" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="email">Email Service</SelectItem>
                      <SelectItem value="sms">SMS Service</SelectItem>
                      <SelectItem value="captcha">Captcha Service</SelectItem>
                      <SelectItem value="payment">Payment Provider</SelectItem>
                      <SelectItem value="storage">File Storage</SelectItem>
                      <SelectItem value="analytics">Analytics</SelectItem>
                      <SelectItem value="oauth_external">OAuth Provider</SelectItem>
                      <SelectItem value="saml">SAML Provider</SelectItem>
                      <SelectItem value="sso">SSO Provider</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="provider">Service Provider</Label>
                  <Input id="provider" name="provider" required placeholder="e.g., sendgrid, twilio, recaptcha" />
                </div>
                <div className="flex items-center space-x-2">
                  <input type="checkbox" id="is_active" name="is_active" defaultChecked />
                  <Label htmlFor="is_active">Active</Label>
                </div>
                <div className="flex justify-end space-x-2">
                  <Button type="button" variant="outline" onClick={() => setShowCreateDialog(false)}>
                    Cancel
                  </Button>
                  <Button type="submit">Add Provider</Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Providers</p>
                  <p className="text-3xl font-bold text-gray-900 dark:text-gray-50">{providers.length}</p>
                </div>
                <Settings className="text-blue-500" size={24} />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Active Providers</p>
                  <p className="text-3xl font-bold text-green-600">
                    {providers.filter(p => p.is_active).length}
                  </p>
                </div>
                <CheckCircle className="text-green-500" size={24} />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Failed Tests</p>
                  <p className="text-3xl font-bold text-red-600">
                    {providers.filter(p => p.test_status === 'failed').length}
                  </p>
                </div>
                <AlertCircle className="text-red-500" size={24} />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Providers List */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Settings size={20} />
              <span>External Service Providers ({providers.length})</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {providers.map((provider) => (
                <div key={provider.id} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center space-x-3">
                      <div className={`p-2 rounded-lg ${getProviderColor(provider.type)}`}>
                        {getProviderIcon(provider.type)}
                      </div>
                      <div>
                        <h3 className="font-medium text-gray-900 dark:text-gray-50">{provider.name}</h3>
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                          {provider.provider} • {provider.type.replace('_', ' ').toUpperCase()}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-3">
                      {provider.test_status && (
                        <Badge variant={
                          provider.test_status === 'success' ? 'default' :
                          provider.test_status === 'failed' ? 'destructive' : 'secondary'
                        }>
                          {provider.test_status === 'pending' ? 'Testing...' : provider.test_status}
                        </Badge>
                      )}
                      <Badge variant={provider.is_active ? 'success' : 'destructive'}>
                        {provider.is_active ? 'Active' : 'Inactive'}
                      </Badge>
                      <Switch
                        checked={provider.is_active}
                        onCheckedChange={(checked) => toggleProvider(provider.id, checked)}
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                    {Object.entries(provider.configuration).map(([key, value]) => (
                      <div key={key}>
                        <Label className="text-sm capitalize">{key.replace('_', ' ')}</Label>
                        <div className="flex items-center space-x-2 mt-1">
                          <Input
                            value={typeof value === 'string' && value.startsWith('•') ? value :
                                   showSecrets[provider.id] ? value : '••••••••••••••••'}
                            readOnly
                            className="font-mono text-sm"
                            type={typeof value === 'string' && value.startsWith('•') ? 'password' :
                                  showSecrets[provider.id] ? 'text' : 'password'}
                          />
                          {typeof value === 'string' && value.startsWith('•') && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => setShowSecrets(prev => ({
                                ...prev,
                                [provider.id]: !prev[provider.id]
                              }))}
                            >
                              {showSecrets[provider.id] ? <EyeOff size={14} /> : <Eye size={14} />}
                            </Button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                    <div className="text-sm text-gray-600 dark:text-gray-400">
                      {provider.last_tested && (
                        <span>Last tested: {formatDate(provider.last_tested)}</span>
                      )}
                    </div>
                    <div className="flex space-x-2">
                      <Button variant="outline" size="sm" onClick={() => testProvider(provider.id)}>
                        <TestTube size={14} className="mr-1" />
                        Test
                      </Button>
                      <Button variant="outline" size="sm">
                        Configure
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {providers.length === 0 && (
              <div className="text-center py-12">
                <Settings size={48} className="mx-auto text-gray-400 mb-4" />
                <h3 className="text-lg font-medium text-gray-900 dark:text-gray-50 mb-2">No external providers configured</h3>
                <p className="text-gray-600 dark:text-gray-400 mb-4">Add external service providers for email, SMS, captcha, and other services.</p>
                <Button onClick={() => setShowCreateDialog(true)}>
                  <Plus size={16} className="mr-2" />
                  Add Provider
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}