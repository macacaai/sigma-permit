'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { subscriptionApi, featureApi } from '@/lib/api';
import { toast } from '@/lib/toast';

interface SubscriptionEntitlement {
  subscription_id?: string;
  feature_id: string;
  effective_value: any;
  overridden: boolean;
}

interface SubscriptionEntitlementFormProps {
  subscriptionId: string;
  entitlement?: SubscriptionEntitlement | null;
  onSuccess: () => void;
  onCancel: () => void;
}

interface Feature {
  id: string;
  key: string;
  type: string;
  default_value?: any;
}

export default function SubscriptionEntitlementForm({
  subscriptionId,
  entitlement,
  onSuccess,
  onCancel
}: SubscriptionEntitlementFormProps) {
  const [formData, setFormData] = useState<SubscriptionEntitlement>({
    subscription_id: subscriptionId,
    feature_id: '',
    effective_value: null,
    overridden: false,
  });
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [features, setFeatures] = useState<Feature[]>([]);
  const [dataLoading, setDataLoading] = useState(true);
  const [valueText, setValueText] = useState('');

  const isEditing = !!entitlement;

  useEffect(() => {
    loadFeatures();
  }, []);

  useEffect(() => {
    if (entitlement) {
      setFormData({
        subscription_id: entitlement.subscription_id,
        feature_id: entitlement.feature_id,
        effective_value: entitlement.effective_value,
        overridden: entitlement.overridden,
      });
      setValueText(entitlement.effective_value ? JSON.stringify(entitlement.effective_value, null, 2) : '');
    }
  }, [entitlement]);

  const loadFeatures = async () => {
    try {
      setDataLoading(true);
      const response = await featureApi.getFeatures(1, 200); // Load up to 200 features
      setFeatures(response.items || []);
    } catch (error) {
      console.error('Error loading features:', error);
      toast.error('Failed to load features for dropdown');
    } finally {
      setDataLoading(false);
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.feature_id) {
      newErrors.feature_id = 'Feature is required';
    }

    // Validate JSON if provided
    if (valueText.trim()) {
      try {
        JSON.parse(valueText);
      } catch (error) {
        newErrors.effective_value = 'Invalid JSON format';
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
        subscription_id: subscriptionId,
        feature_id: formData.feature_id,
        overridden: formData.overridden,
      };

      // Parse JSON value if provided
      if (valueText.trim()) {
        submitData.effective_value = JSON.parse(valueText);
      } else {
        submitData.effective_value = null;
      }

      if (isEditing) {
        await subscriptionApi.updateSubscriptionEntitlement(subscriptionId, formData.feature_id, submitData);
        toast.success('Entitlement updated successfully');
      } else {
        await subscriptionApi.createSubscriptionEntitlement(subscriptionId, submitData);
        toast.success('Entitlement created successfully');
      }

      onSuccess();
    } catch (error: any) {
      console.error('Error saving entitlement:', error);

      if (error.message?.includes('Invalid data')) {
        toast.error('Please check your input and try again.');
      } else {
        toast.error(isEditing ? 'Failed to update entitlement' : 'Failed to create entitlement');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleValueChange = (value: string) => {
    setValueText(value);
    try {
      if (value.trim()) {
        JSON.parse(value);
        setErrors(prev => ({ ...prev, effective_value: '' }));
      }
    } catch (error) {
      setErrors(prev => ({ ...prev, effective_value: 'Invalid JSON format' }));
    }
  };

  const selectedFeature = features.find(f => f.id === formData.feature_id);

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
        {/* Feature */}
        <div className="space-y-2">
          <Label htmlFor="feature_id">Feature *</Label>
          <Select
            value={formData.feature_id}
            onValueChange={(value) => setFormData(prev => ({ ...prev, feature_id: value }))}
            disabled={loading || dataLoading || isEditing} // Don't allow changing feature when editing
          >
            <SelectTrigger className={errors.feature_id ? 'border-red-500' : ''}>
              <SelectValue placeholder="Select a feature" />
            </SelectTrigger>
            <SelectContent>
              {features.map((feature) => (
                <SelectItem key={feature.id} value={feature.id}>
                  {feature.key} ({feature.type})
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {errors.feature_id && (
            <p className="text-sm text-red-600 dark:text-red-400">{errors.feature_id}</p>
          )}
          {selectedFeature && (
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Type: {selectedFeature.type}
              {selectedFeature.default_value && (
                <> | Default: {JSON.stringify(selectedFeature.default_value)}</>
              )}
            </p>
          )}
        </div>

        {/* Effective Value */}
        <div className="space-y-2">
          <Label htmlFor="effective_value">Effective Value (JSON)</Label>
          <Textarea
            id="effective_value"
            value={valueText}
            onChange={(e) => handleValueChange(e.target.value)}
            placeholder='{"value": "example"}'
            disabled={loading}
            rows={4}
            className={`font-mono text-sm ${errors.effective_value ? 'border-red-500' : ''}`}
          />
          <p className="text-sm text-gray-600 dark:text-gray-400">
            The value for this feature entitlement. Leave empty to use the plan's default value.
          </p>
          {errors.effective_value && (
            <p className="text-sm text-red-600 dark:text-red-400">{errors.effective_value}</p>
          )}
        </div>

        {/* Overridden */}
        <div className="flex items-center space-x-2">
          <Switch
            id="overridden"
            checked={formData.overridden}
            onCheckedChange={(checked) => setFormData(prev => ({ ...prev, overridden: checked }))}
            disabled={loading}
          />
          <Label htmlFor="overridden" className="text-sm font-medium">
            Overridden
          </Label>
        </div>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Indicates if this value overrides the plan's default value for this feature.
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
          disabled={loading || !formData.feature_id}
        >
          {loading ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              {isEditing ? 'Updating...' : 'Creating...'}
            </>
          ) : (
            isEditing ? 'Update Entitlement' : 'Create Entitlement'
          )}
        </Button>
      </div>
    </form>
  );
}