'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { featureApi, productApi } from '@/lib/api';
import { toast } from '@/lib/toast';

interface Feature {
  id?: string;
  product_id: string;
  product_name?: string;
  key: string;
  type: string;
  default_value?: any;
  validation_rules?: any;
}

interface FeatureFormProps {
  feature?: Feature | null;
  onSuccess: () => void;
  onCancel: () => void;
}

interface Product {
  id: string;
  name: string;
}

export default function FeatureForm({ feature, onSuccess, onCancel }: FeatureFormProps) {
  const [formData, setFormData] = useState<Feature>({
    product_id: '',
    key: '',
    type: 'boolean',
    default_value: null,
    validation_rules: null,
  });
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [products, setProducts] = useState<Product[]>([]);
  const [dataLoading, setDataLoading] = useState(true);
  const [defaultValueText, setDefaultValueText] = useState('');
  const [validationRulesText, setValidationRulesText] = useState('');

  const isEditing = !!feature;

  useEffect(() => {
    loadProducts();
  }, []);

  useEffect(() => {
    if (feature) {
      setFormData({
        id: feature.id,
        product_id: feature.product_id || '',
        key: feature.key || '',
        type: feature.type || 'boolean',
        default_value: feature.default_value,
        validation_rules: feature.validation_rules,
      });
      setDefaultValueText(feature.default_value ? JSON.stringify(feature.default_value, null, 2) : '');
      setValidationRulesText(feature.validation_rules ? JSON.stringify(feature.validation_rules, null, 2) : '');
    } else {
      // Reset to defaults when creating new feature
      setFormData({
        product_id: '',
        key: '',
        type: 'boolean',
        default_value: null,
        validation_rules: null,
      });
      setDefaultValueText('');
      setValidationRulesText('');
    }
  }, [feature]);

  const loadProducts = async () => {
    try {
      setDataLoading(true);
      const response = await productApi.getProducts(1, 200); // Load up to 200 products
      setProducts(response.items || []);
    } catch (error) {
      console.error('Error loading products:', error);
      toast.error('Failed to load products for dropdown');
    } finally {
      setDataLoading(false);
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    // Always validate product_id and key (they should never be empty)
    if (!formData.product_id) {
      newErrors.product_id = 'Product is required';
    }

    if (!formData.key.trim()) {
      newErrors.key = 'Key is required';
    }

    if (!formData.type) {
      newErrors.type = 'Type is required';
    }

    // Validate JSON if provided
    if (defaultValueText.trim()) {
      try {
        JSON.parse(defaultValueText);
      } catch (error) {
        newErrors.default_value = 'Invalid JSON format';
      }
    }

    if (validationRulesText.trim()) {
      try {
        JSON.parse(validationRulesText);
      } catch (error) {
        newErrors.validation_rules = 'Invalid JSON format';
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
        product_id: formData.product_id,
        key: formData.key.trim(),
        type: formData.type,
      };

      // Parse JSON fields if provided
      if (defaultValueText.trim()) {
        submitData.default_value = JSON.parse(defaultValueText);
      }

      if (validationRulesText.trim()) {
        submitData.validation_rules = JSON.parse(validationRulesText);
      }

      if (isEditing && formData.id) {
        await featureApi.updateFeature(formData.id, submitData);
        toast.success(`Feature "${formData.key}" updated successfully`);
      } else {
        await featureApi.createFeature(submitData);
        toast.success(`Feature "${formData.key}" created successfully`);
      }

      onSuccess();
    } catch (error: any) {
      console.error('Error saving feature:', error);

      if (error.message?.includes('Invalid data')) {
        toast.error('Please check your input and try again.');
      } else {
        toast.error(isEditing ? 'Failed to update feature' : 'Failed to create feature');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleDefaultValueChange = (value: string) => {
    setDefaultValueText(value);
    try {
      if (value.trim()) {
        JSON.parse(value);
        setErrors(prev => ({ ...prev, default_value: '' }));
      }
    } catch (error) {
      setErrors(prev => ({ ...prev, default_value: 'Invalid JSON format' }));
    }
  };

  const handleValidationRulesChange = (value: string) => {
    setValidationRulesText(value);
    try {
      if (value.trim()) {
        JSON.parse(value);
        setErrors(prev => ({ ...prev, validation_rules: '' }));
      }
    } catch (error) {
      setErrors(prev => ({ ...prev, validation_rules: 'Invalid JSON format' }));
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
        {/* Product */}
        <div className="space-y-2">
          <Label htmlFor="product_id">Product *</Label>
          <Select
            value={formData.product_id}
            onValueChange={(value) => setFormData(prev => ({ ...prev, product_id: value }))}
            disabled={loading || dataLoading || isEditing} // Don't allow changing product when editing
          >
            <SelectTrigger className={errors.product_id ? 'border-red-500' : ''}>
              <SelectValue placeholder="Select a product">
                {isEditing ? (feature?.product_name || feature?.product_id) : undefined}
              </SelectValue>
            </SelectTrigger>
            <SelectContent>
              {products.map((product) => (
                <SelectItem key={product.id} value={product.id}>
                  {product.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {errors.product_id && (
            <p className="text-sm text-red-600 dark:text-red-400">{errors.product_id}</p>
          )}
        </div>

        {/* Key */}
        <div className="space-y-2">
          <Label htmlFor="key">Key *</Label>
          <Input
            id="key"
            type="text"
            value={formData.key}
            onChange={(e) => setFormData(prev => ({ ...prev, key: e.target.value }))}
            placeholder="feature_key"
            disabled={loading || isEditing} // Don't allow changing key when editing
            className={errors.key ? 'border-red-500' : ''}
          />
          {errors.key && (
            <p className="text-sm text-red-600 dark:text-red-400">{errors.key}</p>
          )}
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Unique identifier for this feature within the product.
          </p>
        </div>

        {/* Type */}
        <div className="space-y-2">
          <Label htmlFor="type">Type *</Label>
          <Select
            value={formData.type}
            onValueChange={(value) => setFormData(prev => ({ ...prev, type: value }))}
            disabled={loading}
          >
            <SelectTrigger className={errors.type ? 'border-red-500' : ''}>
              <SelectValue placeholder="Select a type">
                {formData.type ? (
                  formData.type.charAt(0).toUpperCase() + formData.type.slice(1)
                ) : (
                  "Select a type"
                )}
              </SelectValue>
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="boolean">Boolean</SelectItem>
              <SelectItem value="integer">Integer</SelectItem>
              <SelectItem value="string">String</SelectItem>
              <SelectItem value="json">JSON</SelectItem>
            </SelectContent>
          </Select>
          {errors.type && (
            <p className="text-sm text-red-600 dark:text-red-400">{errors.type}</p>
          )}
        </div>

        {/* Default Value */}
        <div className="space-y-2">
          <Label htmlFor="default_value">Default Value (JSON)</Label>
          <Textarea
            id="default_value"
            value={defaultValueText}
            onChange={(e) => handleDefaultValueChange(e.target.value)}
            placeholder='true, 42, "default", {"key": "value"}'
            disabled={loading}
            rows={3}
            className={`font-mono text-sm ${errors.default_value ? 'border-red-500' : ''}`}
          />
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Default value for this feature. Leave empty for null.
          </p>
          {errors.default_value && (
            <p className="text-sm text-red-600 dark:text-red-400">{errors.default_value}</p>
          )}
        </div>

        {/* Validation Rules */}
        <div className="space-y-2">
          <Label htmlFor="validation_rules">Validation Rules (JSON)</Label>
          <Textarea
            id="validation_rules"
            value={validationRulesText}
            onChange={(e) => handleValidationRulesChange(e.target.value)}
            placeholder='{"min": 0, "max": 100}'
            disabled={loading}
            rows={3}
            className={`font-mono text-sm ${errors.validation_rules ? 'border-red-500' : ''}`}
          />
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Validation rules for this feature. Leave empty for no validation.
          </p>
          {errors.validation_rules && (
            <p className="text-sm text-red-600 dark:text-red-400">{errors.validation_rules}</p>
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
          disabled={loading || (!isEditing && (!formData.product_id || !formData.key.trim()))}
        >
          {loading ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              {isEditing ? 'Updating...' : 'Creating...'}
            </>
          ) : (
            isEditing ? 'Update Feature' : 'Create Feature'
          )}
        </Button>
      </div>
    </form>
  );
}