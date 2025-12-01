'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { planApi, productApi } from '@/lib/api';
import { toast } from '@/lib/toast';

interface Plan {
  id?: string;
  product_id: string;
  product_name?: string;
  name: string;
  price: number;
  billing_interval: string;
  is_active: boolean;
  plan_metadata?: any;
}

interface PlanFormProps {
  plan?: Plan | null;
  onSuccess: () => void;
  onCancel: () => void;
}

interface Product {
  id: string;
  name: string;
}

export default function PlanForm({ plan, onSuccess, onCancel }: PlanFormProps) {
  const [formData, setFormData] = useState<Plan>({
    product_id: '',
    name: '',
    price: 0,
    billing_interval: 'monthly',
    is_active: true,
    plan_metadata: null,
  });
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [products, setProducts] = useState<Product[]>([]);
  const [dataLoading, setDataLoading] = useState(true);
  const [metadataText, setMetadataText] = useState('');

  const isEditing = !!plan;

  useEffect(() => {
    loadProducts();
  }, []);

  useEffect(() => {
    if (plan) {
      setFormData({
        id: plan.id,
        product_id: plan.product_id,
        name: plan.name,
        price: plan.price,
        billing_interval: plan.billing_interval,
        is_active: plan.is_active,
        plan_metadata: plan.plan_metadata,
      });
      setMetadataText(plan.plan_metadata ? JSON.stringify(plan.plan_metadata, null, 2) : '');
    }
  }, [plan]);

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

    // Skip product validation when editing (product is disabled and should already be set)
    if (!isEditing && !formData.product_id) {
      newErrors.product_id = 'Product is required';
    }

    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
    }

    if (formData.price < 0) {
      newErrors.price = 'Price must be non-negative';
    }

    // Validate JSON if provided
    if (metadataText.trim()) {
      try {
        JSON.parse(metadataText);
      } catch (error) {
        newErrors.plan_metadata = 'Invalid JSON format';
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
        name: formData.name.trim(),
        price: formData.price,
        billing_interval: formData.billing_interval,
        is_active: formData.is_active,
      };

      // Parse JSON metadata if provided
      if (metadataText.trim()) {
        submitData.plan_metadata = JSON.parse(metadataText);
      }

      if (isEditing && formData.id) {
        await planApi.updatePlan(formData.id, submitData);
        toast.success(`Plan "${formData.name}" updated successfully`);
      } else {
        await planApi.createPlan(submitData);
        toast.success(`Plan "${formData.name}" created successfully`);
      }

      onSuccess();
    } catch (error: any) {
      console.error('Error saving plan:', error);

      if (error.message?.includes('Invalid data')) {
        toast.error('Please check your input and try again.');
      } else {
        toast.error(isEditing ? 'Failed to update plan' : 'Failed to create plan');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleMetadataChange = (value: string) => {
    setMetadataText(value);
    try {
      if (value.trim()) {
        JSON.parse(value);
        setErrors(prev => ({ ...prev, plan_metadata: '' }));
      }
    } catch (error) {
      setErrors(prev => ({ ...prev, plan_metadata: 'Invalid JSON format' }));
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
                {isEditing ? (plan?.product_name || plan?.product_id) : undefined}
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

        {/* Name */}
        <div className="space-y-2">
          <Label htmlFor="name">Name *</Label>
          <Input
            id="name"
            type="text"
            value={formData.name}
            onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
            placeholder="Enter plan name"
            disabled={loading}
            className={errors.name ? 'border-red-500' : ''}
          />
          {errors.name && (
            <p className="text-sm text-red-600 dark:text-red-400">{errors.name}</p>
          )}
        </div>

        {/* Price */}
        <div className="space-y-2">
          <Label htmlFor="price">Price *</Label>
          <Input
            id="price"
            type="number"
            min="0"
            step="0.01"
            value={formData.price}
            onChange={(e) => setFormData(prev => ({ ...prev, price: parseFloat(e.target.value) || 0 }))}
            placeholder="0.00"
            disabled={loading}
            className={errors.price ? 'border-red-500' : ''}
          />
          {errors.price && (
            <p className="text-sm text-red-600 dark:text-red-400">{errors.price}</p>
          )}
        </div>

        {/* Billing Interval */}
        <div className="space-y-2">
          <Label htmlFor="billing_interval">Billing Interval</Label>
          <Select
            value={formData.billing_interval}
            onValueChange={(value) => setFormData(prev => ({ ...prev, billing_interval: value }))}
            disabled={loading}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="monthly">Monthly</SelectItem>
              <SelectItem value="yearly">Yearly</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Plan Metadata */}
        <div className="space-y-2">
          <Label htmlFor="plan_metadata">Plan Metadata (JSON)</Label>
          <Textarea
            id="plan_metadata"
            value={metadataText}
            onChange={(e) => handleMetadataChange(e.target.value)}
            placeholder='{"features": ["feature1", "feature2"]}'
            disabled={loading}
            rows={4}
            className={`font-mono text-sm ${errors.plan_metadata ? 'border-red-500' : ''}`}
          />
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Additional metadata for the plan. Leave empty for no metadata.
          </p>
          {errors.plan_metadata && (
            <p className="text-sm text-red-600 dark:text-red-400">{errors.plan_metadata}</p>
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
          disabled={loading || (!isEditing && (!formData.product_id || !formData.name.trim()))}
        >
          {loading ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              {isEditing ? 'Updating...' : 'Creating...'}
            </>
          ) : (
            isEditing ? 'Update Plan' : 'Create Plan'
          )}
        </Button>
      </div>
    </form>
  );
}