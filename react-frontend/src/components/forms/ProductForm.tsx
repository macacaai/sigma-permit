'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { productApi } from '@/lib/api';
import { toast } from '@/lib/toast';

interface Product {
  id?: string;
  name: string;
  description?: string;
  version: number;
}

interface ProductFormProps {
  product?: Product | null;
  onSuccess: () => void;
  onCancel: () => void;
}

export default function ProductForm({ product, onSuccess, onCancel }: ProductFormProps) {
  const [formData, setFormData] = useState<Product>({
    name: '',
    description: '',
    version: 1,
  });
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const isEditing = !!product;

  useEffect(() => {
    if (product) {
      setFormData({
        id: product.id,
        name: product.name,
        description: product.description || '',
        version: product.version,
      });
    }
  }, [product]);

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
    }

    if (formData.version < 1) {
      newErrors.version = 'Version must be at least 1';
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
        name: formData.name.trim(),
        version: formData.version,
      };

      if (formData.description && formData.description.trim()) {
        submitData.description = formData.description.trim();
      }

      if (isEditing && formData.id) {
        await productApi.updateProduct(formData.id, submitData);
        toast.success(`Product "${formData.name}" updated successfully`);
      } else {
        await productApi.createProduct(submitData);
        toast.success(`Product "${formData.name}" created successfully`);
      }

      onSuccess();
    } catch (error: any) {
      console.error('Error saving product:', error);

      if (error.message?.includes('Invalid data')) {
        toast.error('Please check your input and try again.');
      } else {
        toast.error(isEditing ? 'Failed to update product' : 'Failed to create product');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="space-y-4">
        {/* Name */}
        <div className="space-y-2">
          <Label htmlFor="name">Name *</Label>
          <Input
            id="name"
            type="text"
            value={formData.name}
            onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
            placeholder="Enter product name"
            disabled={loading}
            className={errors.name ? 'border-red-500' : ''}
          />
          {errors.name && (
            <p className="text-sm text-red-600 dark:text-red-400">{errors.name}</p>
          )}
        </div>

        {/* Description */}
        <div className="space-y-2">
          <Label htmlFor="description">Description</Label>
          <Textarea
            id="description"
            value={formData.description}
            onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
            placeholder="Describe what this product is for"
            disabled={loading}
            rows={3}
          />
        </div>

        {/* Version */}
        <div className="space-y-2">
          <Label htmlFor="version">Version *</Label>
          <Input
            id="version"
            type="number"
            min="1"
            value={formData.version}
            onChange={(e) => setFormData(prev => ({ ...prev, version: parseInt(e.target.value) || 1 }))}
            disabled={loading}
            className={errors.version ? 'border-red-500' : ''}
          />
          {errors.version && (
            <p className="text-sm text-red-600 dark:text-red-400">{errors.version}</p>
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
          disabled={loading || !formData.name.trim() || formData.version < 1}
        >
          {loading ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              {isEditing ? 'Updating...' : 'Creating...'}
            </>
          ) : (
            isEditing ? 'Update Product' : 'Create Product'
          )}
        </Button>
      </div>
    </form>
  );
}