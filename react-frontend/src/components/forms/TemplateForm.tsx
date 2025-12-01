'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { templateApi } from '@/lib/api';
import { toast } from '@/lib/toast';

interface Template {
  id?: number;
  name: string;
  description: string;
  payload_schema?: any;
  validation_rules?: any;
  is_active: boolean;
}

interface TemplateFormProps {
  template?: Template | null;
  onSuccess: () => void;
  onCancel: () => void;
}

export default function TemplateForm({ template, onSuccess, onCancel }: TemplateFormProps) {
  const [formData, setFormData] = useState<Template>({
    name: '',
    description: '',
    payload_schema: null,
    validation_rules: null,
    is_active: true,
  });
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [schemaText, setSchemaText] = useState('');
  const [rulesText, setRulesText] = useState('');

  const isEditing = !!template;

  useEffect(() => {
    if (template) {
      setFormData({
        id: template.id,
        name: template.name,
        description: template.description,
        payload_schema: template.payload_schema,
        validation_rules: template.validation_rules,
        is_active: template.is_active,
      });
      setSchemaText(template.payload_schema ? JSON.stringify(template.payload_schema, null, 2) : '');
      setRulesText(template.validation_rules ? JSON.stringify(template.validation_rules, null, 2) : '');
    }
  }, [template]);

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
    }

    if (!formData.description.trim()) {
      newErrors.description = 'Description is required';
    }

    // Validate JSON if provided
    if (schemaText.trim()) {
      try {
        JSON.parse(schemaText);
      } catch (error) {
        newErrors.payload_schema = 'Invalid JSON format';
      }
    }

    if (rulesText.trim()) {
      try {
        JSON.parse(rulesText);
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
        name: formData.name.trim(),
        description: formData.description.trim(),
        is_active: formData.is_active,
      };

      // Parse JSON fields if provided
      if (schemaText.trim()) {
        submitData.payload_schema = JSON.parse(schemaText);
      }

      if (rulesText.trim()) {
        submitData.validation_rules = JSON.parse(rulesText);
      }

      if (isEditing && formData.id) {
        await templateApi.updateTemplate(formData.id.toString(), submitData);
        toast.success(`Template "${formData.name}" updated successfully`);
      } else {
        await templateApi.createTemplate(submitData);
        toast.success(`Template "${formData.name}" created successfully`);
      }

      onSuccess();
    } catch (error: any) {
      console.error('Error saving template:', error);

      if (error.message?.includes('Invalid data')) {
        toast.error('Please check your input and try again.');
      } else {
        toast.error(isEditing ? 'Failed to update template' : 'Failed to create template');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSchemaChange = (value: string) => {
    setSchemaText(value);
    try {
      if (value.trim()) {
        JSON.parse(value);
        setErrors(prev => ({ ...prev, payload_schema: '' }));
      }
    } catch (error) {
      setErrors(prev => ({ ...prev, payload_schema: 'Invalid JSON format' }));
    }
  };

  const handleRulesChange = (value: string) => {
    setRulesText(value);
    try {
      if (value.trim()) {
        JSON.parse(value);
        setErrors(prev => ({ ...prev, validation_rules: '' }));
      }
    } catch (error) {
      setErrors(prev => ({ ...prev, validation_rules: 'Invalid JSON format' }));
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
            placeholder="Enter template name"
            disabled={loading}
            className={errors.name ? 'border-red-500' : ''}
          />
          {errors.name && (
            <p className="text-sm text-red-600 dark:text-red-400">{errors.name}</p>
          )}
        </div>

        {/* Description */}
        <div className="space-y-2">
          <Label htmlFor="description">Description *</Label>
          <Textarea
            id="description"
            value={formData.description}
            onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
            placeholder="Describe what this template is for"
            disabled={loading}
            rows={3}
            className={errors.description ? 'border-red-500' : ''}
          />
          {errors.description && (
            <p className="text-sm text-red-600 dark:text-red-400">{errors.description}</p>
          )}
        </div>

        {/* Payload Schema */}
        <div className="space-y-2">
          <Label htmlFor="payload_schema">Payload Schema (JSON)</Label>
          <Textarea
            id="payload_schema"
            value={schemaText}
            onChange={(e) => handleSchemaChange(e.target.value)}
            placeholder='{"type": "object", "properties": {...}}'
            disabled={loading}
            rows={6}
            className={`font-mono text-sm ${errors.payload_schema ? 'border-red-500' : ''}`}
          />
          <p className="text-sm text-gray-600 dark:text-gray-400">
            JSON schema for validating license payloads. Leave empty for no validation.
          </p>
          {errors.payload_schema && (
            <p className="text-sm text-red-600 dark:text-red-400">{errors.payload_schema}</p>
          )}
        </div>

        {/* Validation Rules */}
        <div className="space-y-2">
          <Label htmlFor="validation_rules">Validation Rules (JSON)</Label>
          <Textarea
            id="validation_rules"
            value={rulesText}
            onChange={(e) => handleRulesChange(e.target.value)}
            placeholder='{"required": ["field1"], "customRules": {...}}'
            disabled={loading}
            rows={4}
            className={`font-mono text-sm ${errors.validation_rules ? 'border-red-500' : ''}`}
          />
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Additional validation rules. Leave empty for basic schema validation only.
          </p>
          {errors.validation_rules && (
            <p className="text-sm text-red-600 dark:text-red-400">{errors.validation_rules}</p>
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
          Inactive templates cannot be used to create new licenses.
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
          disabled={loading || !formData.name.trim() || !formData.description.trim()}
        >
          {loading ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              {isEditing ? 'Updating...' : 'Creating...'}
            </>
          ) : (
            isEditing ? 'Update Template' : 'Create Template'
          )}
        </Button>
      </div>
    </form>
  );
}