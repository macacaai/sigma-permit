'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { licenseApi, tenantApi, templateApi, subscriptionApi } from '@/lib/api';
import { toast } from '@/lib/toast';

interface License {
  id?: string;
  tenant_id: string;
  template_id?: string;
  linked_subscription?: string;
  issued_at?: string;
  validity_days?: number;
  payload: any;
}

interface Tenant {
  id: string;
  name: string;
  slug: string;
  max_licenses: number;
}

interface Template {
  id: string;
  name: string;
  description: string;
  is_active: boolean;
  payload_schema?: any;
}

interface Subscription {
  id: string;
  tenant_id: string;
  plan_id: string;
  plan_name: string;
  status: string;
  start_date: string;
  issue_date?: string;
  end_date?: string;
  validity_days?: number;
}

interface LicenseFormProps {
  license?: License | null;
  onSuccess: () => void;
  onCancel: () => void;
}

export default function LicenseForm({ license, onSuccess, onCancel }: LicenseFormProps) {
  const [formData, setFormData] = useState<License>({
    tenant_id: '',
    template_id: undefined,
    linked_subscription: undefined,
    issued_at: '',
    validity_days: 30,
    payload: {},
  });
  const [loading, setLoading] = useState(false);
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [dataLoading, setDataLoading] = useState(true);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [payloadText, setPayloadText] = useState('');
  const [selectedTemplateData, setSelectedTemplateData] = useState<Template | null>(null);
  const [selectedTenantId, setSelectedTenantId] = useState('');
  const [selectedTemplateId, setSelectedTemplateId] = useState('custom');
  const [selectedSubscriptionId, setSelectedSubscriptionId] = useState('');
  const [linkSubscription, setLinkSubscription] = useState(false);
  const [tenantSubscriptions, setTenantSubscriptions] = useState<Subscription[]>([]);

  const isEditing = !!license;

  useEffect(() => {
    loadTenantsAndTemplates();
    // Set default date on client side to avoid hydration mismatch (only if not editing)
    if (!license) {
      setFormData(prev => ({
        ...prev,
        issued_at: new Date().toISOString().split('T')[0]
      }));
    }
  }, [license]);

  useEffect(() => {
    if (license) {
      const hasLinkedSubscription = !!license.linked_subscription;
      setLinkSubscription(hasLinkedSubscription);
      setFormData({
        id: license.id,
        tenant_id: license.tenant_id.toString(),
        template_id: license.template_id?.toString(),
        linked_subscription: license.linked_subscription,
        issued_at: hasLinkedSubscription ? undefined : (license.issued_at ? new Date(license.issued_at).toISOString().split('T')[0] : ''),
        validity_days: hasLinkedSubscription ? undefined : (license.validity_days || 30),
        payload: license.payload,
      });
      setSelectedTenantId(license.tenant_id.toString());
      setSelectedTemplateId(license.template_id?.toString() || 'custom');
      setSelectedSubscriptionId(license.linked_subscription || '');
      setPayloadText(license.payload ? JSON.stringify(license.payload, null, 2) : '');

      // Load tenant subscriptions if editing a license with a linked subscription
      if (hasLinkedSubscription) {
        loadTenantSubscriptions(license.tenant_id.toString());
      }
    }
  }, [license]);

  const loadTenantsAndTemplates = async () => {
    try {
      setDataLoading(true);
      const [tenantsRes, templatesRes] = await Promise.all([
        tenantApi.getTenants(1, 100), // Get all tenants
        templateApi.getTemplates(1, 100), // Get all templates
      ]);

      setTenants(tenantsRes.items || []);
      setTemplates((templatesRes.items || []).filter((t: Template) => t.is_active));
    } catch (error) {
      console.error('Error loading data:', error);
      toast.error('Failed to load tenants and templates');
    } finally {
      setDataLoading(false);
    }
  };

  const loadTenantSubscriptions = async (tenantId: string) => {
    try {
      const response = await tenantApi.getTenantSubscriptions(tenantId, 1, 100);
      const activeSubscriptions = (response.items || []).filter((s: Subscription) => s.status === 'active');
      setTenantSubscriptions(activeSubscriptions);
    } catch (error) {
      console.error('Error loading tenant subscriptions:', error);
      setTenantSubscriptions([]);
    }
  };

  const handleTemplateChange = (value: string) => {
    setSelectedTemplateId(value);
    const templateId = value === 'custom' ? undefined : value;

    setFormData(prev => ({
      ...prev,
      template_id: templateId
    }));

    if (templateId) {
      // Find template from loaded templates
      const templateData = templates.find(t => t.id === templateId);
      if (templateData) {
        setSelectedTemplateData(templateData);

        // Populate payload with template schema if available
        let payloadToUse;
        if (templateData.payload_schema) {
          payloadToUse = templateData.payload_schema;
        } else {
          // Provide template-specific defaults based on name
          if (templateData.name.toLowerCase().includes('basic')) {
            payloadToUse = {
              "features": [
                "user_management",
                "basic_reporting",
                "email_support"
              ],
              "user_limit": 5,
              "api_access": false,
              "support_level": "basic",
              "license_type": "basic"
            };
          } else {
            // General default
            payloadToUse = {
              "permissions": ["read", "write"],
              "features": ["basic"],
              "limits": {
                "users": 10,
                "storage_gb": 5
              }
            };
          }
        }
        const schemaText = JSON.stringify(payloadToUse, null, 2);
        setPayloadText(schemaText);
        setFormData(prev => ({
          ...prev,
          payload: payloadToUse
        }));
      }
    } else {
      // Custom template - clear payload
      setSelectedTemplateData(null);
      setPayloadText('');
      setFormData(prev => ({
        ...prev,
        payload: {}
      }));
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.tenant_id) {
      newErrors.tenant_id = 'Tenant is required';
    }

    // Validate based on subscription linking
    if (linkSubscription) {
      // If linking to subscription, ensure a subscription is selected
      if (!formData.linked_subscription) {
        newErrors.linked_subscription = 'Please select a subscription to link to';
      }
    } else {
      // If not linking to subscription, validate issued_at and validity_days
      if (!formData.issued_at) {
        newErrors.issued_at = 'Issue date is required when not linked to subscription';
      }

      if (!formData.validity_days || formData.validity_days < 1) {
        newErrors.validity_days = 'Validity days must be at least 1';
      }

      if (formData.validity_days && formData.validity_days > 3650) {
        newErrors.validity_days = 'Validity days cannot exceed 10 years';
      }
    }

    // Validate JSON payload if provided
    if (payloadText.trim()) {
      try {
        JSON.parse(payloadText);
      } catch (error) {
        newErrors.payload = 'Invalid JSON format';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    try {
      setLoading(true);

      const submitData: any = {
        tenant_id: formData.tenant_id,
      };

      if (formData.template_id) {
        submitData.template_id = formData.template_id;
      }

      if (linkSubscription && formData.linked_subscription) {
        submitData.linked_subscription = formData.linked_subscription;
      } else if (!linkSubscription) {
        submitData.issued_at = new Date(formData.issued_at!).toISOString();
        submitData.validity_days = formData.validity_days;
      }

      // Parse JSON payload if provided
      if (payloadText.trim()) {
        submitData.payload = JSON.parse(payloadText);
      } else {
        submitData.payload = {};
      }

      if (isEditing && formData.id) {
        await licenseApi.updateLicense(formData.id.toString(), submitData);
        toast.success(`License updated successfully`);
      } else {
        await licenseApi.createLicense(submitData);
        toast.success(`License created successfully`);
      }

      onSuccess();
    } catch (error: any) {
      console.error('Error saving license:', error);

      if (error.message?.includes('Maximum licenses reached')) {
        setErrors({ tenant_id: 'Maximum licenses reached for this tenant' });
      } else if (error.message?.includes('Invalid data')) {
        toast.error('Please check your input and try again.');
      } else {
        toast.error(isEditing ? 'Failed to update license' : 'Failed to create license');
      }
    } finally {
      setLoading(false);
    }
  };

  const handlePayloadChange = (value: string) => {
    setPayloadText(value);
    try {
      if (value.trim()) {
        JSON.parse(value);
        setErrors(prev => ({ ...prev, payload: '' }));
      }
    } catch (error) {
      setErrors(prev => ({ ...prev, payload: 'Invalid JSON format' }));
    }
  };

  const selectedTenant = tenants.find(t => t.id === formData.tenant_id);
  const selectedTemplate = templates.find(t => t.id === formData.template_id);

  if (dataLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mr-3"></div>
        <span className="text-gray-600 dark:text-gray-400">Loading form data...</span>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="space-y-4">
        {/* Tenant Selection */}
        <div className="space-y-2">
          <Label htmlFor="tenant_id">Tenant *</Label>
          <Select
            value={selectedTenantId}
            onValueChange={(value) => {
              setSelectedTenantId(value);
              setFormData(prev => ({ ...prev, tenant_id: value }));
              // Load subscriptions for the selected tenant
              if (value) {
                loadTenantSubscriptions(value);
              } else {
                setTenantSubscriptions([]);
              }
              // Reset subscription selection if tenant changes
              setSelectedSubscriptionId('');
              setFormData(prev => ({ ...prev, linked_subscription: undefined }));
            }}
            disabled={loading || dataLoading || isEditing}
          >
            <SelectTrigger className={errors.tenant_id ? 'border-red-500' : ''}>
              <SelectValue placeholder="Select a tenant" />
            </SelectTrigger>
            <SelectContent>
              {tenants.map((tenant) => (
                <SelectItem key={tenant.id} value={tenant.id.toString()}>
                  {tenant.name} ({tenant.slug})
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {errors.tenant_id && (
            <p className="text-sm text-red-600 dark:text-red-400">{errors.tenant_id}</p>
          )}
          {selectedTenant && (
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Max licenses: {selectedTenant.max_licenses}
            </p>
          )}
        </div>

        {/* Template Selection */}
        <div className="space-y-2">
          <Label htmlFor="template_id">Template</Label>
          <Select
            value={selectedTemplateId}
            onValueChange={handleTemplateChange}
            disabled={loading || dataLoading}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select a template" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="custom">Custom</SelectItem>
              {templates.map((template) => (
                <SelectItem key={template.id} value={template.id.toString()}>
                  {template.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {selectedTemplateData && (
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {selectedTemplateData.description}
            </p>
          )}
        </div>

        {/* Link to Subscription Switch */}
        <div className="space-y-2">
          <div className="flex items-center space-x-2">
            <Switch
              id="link_subscription"
              checked={linkSubscription}
              onCheckedChange={(checked) => {
                if (checked && !selectedTenantId) {
                  toast.error('Please select a tenant first before linking to a subscription');
                  return;
                }
                setLinkSubscription(checked);
                if (!checked) {
                  // Clear subscription selection when disabling
                  setSelectedSubscriptionId('');
                  setFormData(prev => ({
                    ...prev,
                    linked_subscription: undefined,
                    // Reset to default values when disabling subscription link
                    issued_at: new Date().toISOString().split('T')[0],
                    validity_days: 30
                  }));
                } else {
                  // Clear manual date fields when enabling subscription link
                  setFormData(prev => ({
                    ...prev,
                    issued_at: undefined,
                    validity_days: undefined
                  }));
                }
              }}
              disabled={loading || isEditing}
            />
            <Label htmlFor="link_subscription" className="text-sm font-medium">
              Link to Subscription
            </Label>
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            When enabled, the license will inherit validity from the selected subscription.
          </p>
        </div>

        {/* Subscription Selection - Only show when switch is enabled */}
        {linkSubscription && (
          <div className="space-y-2">
            <Label htmlFor="linked_subscription">Subscription</Label>
            <Select
              value={selectedSubscriptionId}
              onValueChange={(value) => {
                setSelectedSubscriptionId(value);
                setFormData(prev => ({ ...prev, linked_subscription: value }));
              }}
              disabled={loading || !selectedTenantId}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select a subscription" />
              </SelectTrigger>
              <SelectContent>
                {tenantSubscriptions.map((subscription) => (
                  <SelectItem key={subscription.id} value={subscription.id.toString()}>
                    {subscription.plan_name} ({subscription.validity_days} days)
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {!selectedTenantId && (
              <p className="text-sm text-amber-600 dark:text-amber-400">
                Please select a tenant first to see available subscriptions.
              </p>
            )}
            {selectedTenantId && tenantSubscriptions.length === 0 && (
              <p className="text-sm text-gray-600 dark:text-gray-400">
                No active subscriptions found for this tenant.
              </p>
            )}

            {/* Show subscription details when selected */}
            {selectedSubscriptionId && (
              <div className="mt-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <h4 className="text-sm font-medium text-gray-900 dark:text-gray-50 mb-2">
                  Subscription Details
                </h4>
                {(() => {
                  const selectedSub = tenantSubscriptions.find(s => s.id.toString() === selectedSubscriptionId);
                  return selectedSub ? (
                    <div className="space-y-1 text-sm text-gray-600 dark:text-gray-400">
                      {selectedSub.issue_date && (
                        <p><span className="font-medium">Issue Date:</span> {new Date(selectedSub.issue_date).toLocaleDateString()}</p>
                      )}
                      <p><span className="font-medium">Validity Days:</span> {selectedSub.validity_days}</p>
                      {selectedSub.end_date && (
                        <p><span className="font-medium">End Date:</span> {new Date(selectedSub.end_date).toLocaleDateString()}</p>
                      )}
                    </div>
                  ) : null;
                })()}
              </div>
            )}
          </div>
        )}

        {/* Issue Date - Only show if not linked to subscription */}
        {!linkSubscription && (
          <div className="space-y-2">
            <Label htmlFor="issued_at">Issue Date *</Label>
            <Input
              id="issued_at"
              type="date"
              value={formData.issued_at}
              onChange={(e) => setFormData(prev => ({ ...prev, issued_at: e.target.value }))}
              disabled={loading}
            />
          </div>
        )}

        {/* Validity Days - Only show if not linked to subscription */}
        {!linkSubscription && (
          <div className="space-y-2">
            <Label htmlFor="validity_days">Validity Days *</Label>
            <Input
              id="validity_days"
              type="number"
              min="1"
              max="3650"
              value={formData.validity_days}
              onChange={(e) => setFormData(prev => ({ ...prev, validity_days: parseInt(e.target.value) || 1 }))}
              disabled={loading}
              className={errors.validity_days ? 'border-red-500' : ''}
            />
            {formData.validity_days && (
              <p className="text-sm text-gray-600 dark:text-gray-400">
                License will expire on {new Date(Date.now() + formData.validity_days * 24 * 60 * 60 * 1000).toLocaleDateString('en-US', { day: 'numeric', month: 'short', year: 'numeric' })}
              </p>
            )}
            {errors.validity_days && (
              <p className="text-sm text-red-600 dark:text-red-400">{errors.validity_days}</p>
            )}
          </div>
        )}

        {/* Payload */}
        <div className="space-y-2">
          <Label htmlFor="payload">License Payload (JSON)</Label>
          <Textarea
            id="payload"
            value={payloadText}
            onChange={(e) => handlePayloadChange(e.target.value)}
            placeholder={formData.template_id ? 'Payload loaded from template (editable)' : '{"key": "value", "permissions": ["read", "write"]}'}
            disabled={loading}
            rows={10}
            className={`font-mono text-sm ${errors.payload ? 'border-red-500' : ''}`}
          />
          <p className="text-sm text-gray-600 dark:text-gray-400">
            {formData.template_id
              ? 'Payload loaded from template. You can edit it before creating the license.'
              : 'Custom data to include in the license. Must be valid JSON.'
            }
          </p>
          {errors.payload && (
            <p className="text-sm text-red-600 dark:text-red-400">{errors.payload}</p>
          )}
        </div>
      </div>

      {/* Form Actions */}
      <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200 dark:border-gray-700">
        <Button
          type="button"
          variant="outline"
          onClick={onCancel}
          disabled={loading}
        >
          Cancel
        </Button>
        <Button
          type="submit"
          disabled={loading || !formData.tenant_id || (linkSubscription && !formData.linked_subscription)}
        >
          {loading ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              {isEditing ? 'Updating...' : 'Creating...'}
            </>
          ) : (
            isEditing ? 'Update License' : 'Create License'
          )}
        </Button>
      </div>
    </form>
  );
}