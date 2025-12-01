'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { subscriptionApi, tenantApi, planApi } from '@/lib/api';
import { toast } from '@/lib/toast';

interface Subscription {
  id?: string;
  tenant_id: string;
  tenant_name?: string;
  plan_id: string;
  plan_name?: string;
  status: string;
  start_date: string;
  issue_date?: string;
  end_date?: string;
  auto_renew: boolean;
  payment_provider_id?: string;
}

interface SubscriptionFormProps {
  subscription?: Subscription | null;
  onSuccess: () => void;
  onCancel: () => void;
}

interface Tenant {
  id: string;
  name: string;
}

interface Plan {
  id: string;
  name: string;
  price: number;
  billing_interval: string;
}

export default function SubscriptionForm({ subscription, onSuccess, onCancel }: SubscriptionFormProps) {
  const [formData, setFormData] = useState<Subscription>({
    tenant_id: '',
    plan_id: '',
    status: 'active',
    start_date: new Date().toISOString().split('T')[0],
    issue_date: new Date().toISOString().split('T')[0],
    end_date: '',
    auto_renew: true,
    payment_provider_id: '',
  });
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [plans, setPlans] = useState<Plan[]>([]);
  const [dataLoading, setDataLoading] = useState(true);

  const isEditing = !!subscription;

  useEffect(() => {
    loadTenantsAndPlans();
  }, []);

  useEffect(() => {
    if (subscription) {
      setFormData({
        id: subscription.id,
        tenant_id: subscription.tenant_id,
        plan_id: subscription.plan_id,
        status: subscription.status,
        start_date: subscription.start_date.split('T')[0], // Convert to date input format
        issue_date: (subscription as any).issue_date ? (subscription as any).issue_date.split('T')[0] : new Date().toISOString().split('T')[0],
        end_date: subscription.end_date ? subscription.end_date.split('T')[0] : '',
        auto_renew: subscription.auto_renew,
        payment_provider_id: subscription.payment_provider_id || '',
      });
    }
  }, [subscription]);

  const loadTenantsAndPlans = async () => {
    try {
      setDataLoading(true);
      const [tenantsRes, plansRes] = await Promise.all([
        tenantApi.getTenants(1, 200), // Load up to 200 tenants
        planApi.getPlans(1, 200), // Load up to 200 plans
      ]);

      setTenants(tenantsRes.items || []);
      setPlans(plansRes.items || []);
    } catch (error) {
      console.error('Error loading data:', error);
      toast.error('Failed to load tenants and plans for dropdown');
    } finally {
      setDataLoading(false);
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    // Skip tenant validation when editing (tenant is disabled and should already be set)
    if (!isEditing && !formData.tenant_id) {
      newErrors.tenant_id = 'Tenant is required';
    }

    if (!formData.plan_id) {
      newErrors.plan_id = 'Plan is required';
    }

    if (!formData.start_date) {
      newErrors.start_date = 'Start date is required';
    }

    if (!formData.issue_date) {
      newErrors.issue_date = 'Issue date is required';
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
        plan_id: formData.plan_id,
        status: formData.status,
        start_date: new Date(formData.start_date).toISOString(),
        auto_renew: formData.auto_renew,
      };

      if (formData.issue_date) {
        submitData.issue_date = new Date(formData.issue_date).toISOString();
      }

      if (formData.end_date) {
        submitData.end_date = new Date(formData.end_date).toISOString();
      }

      if (formData.payment_provider_id) {
        submitData.payment_provider_id = formData.payment_provider_id;
      }

      if (isEditing && formData.id) {
        await subscriptionApi.updateSubscription(formData.id, submitData);
        toast.success('Subscription updated successfully');
      } else {
        await subscriptionApi.createSubscription(submitData);
        toast.success('Subscription created successfully');
      }

      onSuccess();
    } catch (error: any) {
      console.error('Error saving subscription:', error);

      if (error.message?.includes('Invalid data')) {
        toast.error('Please check your input and try again.');
      } else {
        toast.error(isEditing ? 'Failed to update subscription' : 'Failed to create subscription');
      }
    } finally {
      setLoading(false);
    }
  };

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
        {/* Tenant */}
        <div className="space-y-2">
          <Label htmlFor="tenant_id">Tenant *</Label>
          <Select
            value={formData.tenant_id}
            onValueChange={(value) => setFormData(prev => ({ ...prev, tenant_id: value }))}
            disabled={loading || dataLoading || isEditing} // Don't allow changing tenant when editing
          >
            <SelectTrigger className={errors.tenant_id ? 'border-red-500' : ''}>
              <SelectValue placeholder="Select a tenant">
                {isEditing ? (subscription?.tenant_name || subscription?.tenant_id) : undefined}
              </SelectValue>
            </SelectTrigger>
            <SelectContent>
              {tenants.map((tenant) => (
                <SelectItem key={tenant.id} value={tenant.id}>
                  {tenant.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {errors.tenant_id && (
            <p className="text-sm text-red-600 dark:text-red-400">{errors.tenant_id}</p>
          )}
        </div>

        {/* Plan */}
        <div className="space-y-2">
          <Label htmlFor="plan_id">Plan *</Label>
          <Select
            value={formData.plan_id}
            onValueChange={(value) => setFormData(prev => ({ ...prev, plan_id: value }))}
            disabled={loading || dataLoading}
          >
            <SelectTrigger className={errors.plan_id ? 'border-red-500' : ''}>
              <SelectValue placeholder="Select a plan" />
            </SelectTrigger>
            <SelectContent>
              {plans.map((plan) => (
                <SelectItem key={plan.id} value={plan.id}>
                  {plan.name} - ${plan.price}/{plan.billing_interval}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {errors.plan_id && (
            <p className="text-sm text-red-600 dark:text-red-400">{errors.plan_id}</p>
          )}
        </div>

        {/* Status */}
        <div className="space-y-2">
          <Label htmlFor="status">Status</Label>
          <Select
            value={formData.status}
            onValueChange={(value) => setFormData(prev => ({ ...prev, status: value }))}
            disabled={loading}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="active">Active</SelectItem>
              <SelectItem value="trialing">Trialing</SelectItem>
              <SelectItem value="past_due">Past Due</SelectItem>
              <SelectItem value="canceled">Canceled</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Start Date */}
        <div className="space-y-2">
          <Label htmlFor="start_date">Start Date *</Label>
          <Input
            id="start_date"
            type="date"
            value={formData.start_date}
            onChange={(e) => setFormData(prev => ({ ...prev, start_date: e.target.value }))}
            disabled={loading || isEditing} // Disable editing start_date when editing
            className={errors.start_date ? 'border-red-500' : ''}
          />
          {errors.start_date && (
            <p className="text-sm text-red-600 dark:text-red-400">{errors.start_date}</p>
          )}
          {isEditing && (
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Start date cannot be modified after creation.
            </p>
          )}
        </div>

        {/* Issue Date */}
        <div className="space-y-2">
          <Label htmlFor="issue_date">Issue Date *</Label>
          <Input
            id="issue_date"
            type="date"
            value={formData.issue_date}
            onChange={(e) => setFormData(prev => ({ ...prev, issue_date: e.target.value }))}
            disabled={loading}
            className={errors.issue_date ? 'border-red-500' : ''}
          />
          {errors.issue_date && (
            <p className="text-sm text-red-600 dark:text-red-400">{errors.issue_date}</p>
          )}
        </div>

        {/* End Date */}
        <div className="space-y-2">
          <Label htmlFor="end_date">End Date</Label>
          <Input
            id="end_date"
            type="date"
            value={formData.end_date}
            onChange={(e) => setFormData(prev => ({ ...prev, end_date: e.target.value }))}
            disabled={loading}
          />
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Leave empty for ongoing subscriptions.
          </p>
        </div>

        {/* Payment Provider ID */}
        <div className="space-y-2">
          <Label htmlFor="payment_provider_id">Payment Provider ID</Label>
          <Input
            id="payment_provider_id"
            type="text"
            value={formData.payment_provider_id}
            onChange={(e) => setFormData(prev => ({ ...prev, payment_provider_id: e.target.value }))}
            placeholder="External payment provider reference"
            disabled={loading}
          />
        </div>

        {/* Auto Renew */}
        <div className="flex items-center space-x-2">
          <Switch
            id="auto_renew"
            checked={formData.auto_renew}
            onCheckedChange={(checked) => setFormData(prev => ({ ...prev, auto_renew: checked }))}
            disabled={loading}
          />
          <Label htmlFor="auto_renew" className="text-sm font-medium">
            Auto Renew
          </Label>
        </div>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Automatically renew the subscription at the end of the billing period.
        </p>
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
          disabled={loading || (!isEditing && (!formData.tenant_id || !formData.plan_id || !formData.start_date || !formData.issue_date))}
        >
          {loading ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              {isEditing ? 'Updating...' : 'Creating...'}
            </>
          ) : (
            isEditing ? 'Update Subscription' : 'Create Subscription'
          )}
        </Button>
      </div>
    </form>
  );
}