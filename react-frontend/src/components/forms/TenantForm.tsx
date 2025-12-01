'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { tenantApi } from '@/lib/api';
import { toast } from '@/lib/toast';

interface Tenant {
  id?: number;
  name: string;
  slug: string;
  max_licenses: number;
  is_active: boolean;
}

interface TenantFormProps {
  tenant?: Tenant | null;
  onSuccess: () => void;
  onCancel: () => void;
}

export default function TenantForm({ tenant, onSuccess, onCancel }: TenantFormProps) {
  const [formData, setFormData] = useState<Tenant>({
    name: '',
    slug: '',
    max_licenses: 100,
    is_active: true,
  });
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const isEditing = !!tenant;

  useEffect(() => {
    if (tenant) {
      setFormData({
        id: tenant.id,
        name: tenant.name,
        slug: tenant.slug,
        max_licenses: tenant.max_licenses,
        is_active: tenant.is_active,
      });
    }
  }, [tenant]);

  const generateSlug = (name: string) => {
    return name
      .toLowerCase()
      .replace(/[^a-z0-9\s-]/g, '')
      .replace(/\s+/g, '-')
      .replace(/-+/g, '-')
      .trim();
  };

  const handleNameChange = (name: string) => {
    const slug = generateSlug(name);
    setFormData(prev => ({ ...prev, name, slug }));
  };

  const handleSlugChange = (slug: string) => {
    const cleanSlug = slug.toLowerCase().replace(/[^a-z0-9-]/g, '');
    setFormData(prev => ({ ...prev, slug: cleanSlug }));
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
    }

    if (!formData.slug.trim()) {
      newErrors.slug = 'Slug is required';
    } else if (!/^[a-z0-9-]+$/.test(formData.slug)) {
      newErrors.slug = 'Slug can only contain lowercase letters, numbers, and hyphens';
    }

    if (formData.max_licenses < 1) {
      newErrors.max_licenses = 'Max licenses must be at least 1';
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

      const submitData = {
        name: formData.name.trim(),
        slug: formData.slug.trim(),
        max_licenses: formData.max_licenses,
        is_active: formData.is_active,
      };

      if (isEditing && formData.id) {
        await tenantApi.updateTenant(formData.id.toString(), submitData);
        toast.success(`Tenant "${formData.name}" updated successfully`);
      } else {
        await tenantApi.createTenant(submitData);
        toast.success(`Tenant "${formData.name}" created successfully`);
      }

      onSuccess();
    } catch (error: any) {
      console.error('Error saving tenant:', error);

      // Handle specific validation errors
      if (error.message?.includes('slug already exists')) {
        setErrors({ slug: 'This slug is already taken. Please choose a different one.' });
      } else if (error.message?.includes('Invalid data')) {
        toast.error('Please check your input and try again.');
      } else {
        toast.error(isEditing ? 'Failed to update tenant' : 'Failed to create tenant');
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
            onChange={(e) => handleNameChange(e.target.value)}
            placeholder="Enter tenant name"
            disabled={loading}
            className={errors.name ? 'border-red-500' : ''}
          />
          {errors.name && (
            <p className="text-sm text-red-600 dark:text-red-400">{errors.name}</p>
          )}
        </div>

        {/* Slug */}
        <div className="space-y-2">
          <Label htmlFor="slug">Slug *</Label>
          <Input
            id="slug"
            type="text"
            value={formData.slug}
            onChange={(e) => handleSlugChange(e.target.value)}
            placeholder="tenant-slug"
            disabled={loading}
            className={errors.slug ? 'border-red-500' : ''}
          />
          <p className="text-sm text-gray-600 dark:text-gray-400">
            URL-friendly identifier. Auto-generated from name.
          </p>
          {errors.slug && (
            <p className="text-sm text-red-600 dark:text-red-400">{errors.slug}</p>
          )}
        </div>

        {/* Max Licenses */}
        <div className="space-y-2">
          <Label htmlFor="max_licenses">Maximum Licenses *</Label>
          <Input
            id="max_licenses"
            type="number"
            min="1"
            value={formData.max_licenses}
            onChange={(e) => setFormData(prev => ({ ...prev, max_licenses: parseInt(e.target.value) || 1 }))}
            disabled={loading}
            className={errors.max_licenses ? 'border-red-500' : ''}
          />
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Maximum number of licenses this tenant can have.
          </p>
          {errors.max_licenses && (
            <p className="text-sm text-red-600 dark:text-red-400">{errors.max_licenses}</p>
          )}
        </div>

        {/* Active Status */}
        <div className="flex items-center space-x-2">
          <Switch
            id="is_active"
            checked={formData.is_active}
            onCheckedChange={(checked) => setFormData(prev => ({ ...prev, is_active: checked }))}
            disabled={loading}
          />
          <Label htmlFor="is_active" className="text-sm font-medium">
            Active
          </Label>
        </div>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Inactive tenants cannot issue new licenses.
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
          disabled={loading || !formData.name.trim() || !formData.slug.trim()}
        >
          {loading ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              {isEditing ? 'Updating...' : 'Creating...'}
            </>
          ) : (
            isEditing ? 'Update Tenant' : 'Create Tenant'
          )}
        </Button>
      </div>
    </form>
  );
}