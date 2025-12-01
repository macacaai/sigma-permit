<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { toast } from 'svelte-french-toast';
  import { Loader } from 'lucide-svelte';

  import { templateApi } from '$lib/api';

  export let template: any = null; // For editing

  const dispatch = createEventDispatcher();

  let formData = {
    name: template?.name || '',
    description: template?.description || '',
    payload_schema: template?.payload_schema ? JSON.stringify(template.payload_schema, null, 2) : '',
    validation_rules: template?.validation_rules ? JSON.stringify(template.validation_rules, null, 2) : '',
    is_active: template?.is_active ?? true
  };

  let loading = false;
  let errors: Record<string, string> = {};
  let schemaError = '';
  let validationError = '';

  async function handleSubmit() {
    // Reset errors
    errors = {};
    schemaError = '';
    validationError = '';

    // Basic validation
    if (!formData.name.trim()) {
      errors.name = 'Template name is required';
      return;
    }

    if (!formData.description.trim()) {
      errors.description = 'Description is required';
      return;
    }

    // Validate JSON schema
    let parsedSchema;
    try {
      if (formData.payload_schema.trim()) {
        parsedSchema = JSON.parse(formData.payload_schema);
      }
    } catch (error) {
      schemaError = 'Invalid JSON in payload schema';
      return;
    }

    // Validate JSON validation rules
    let parsedValidation;
    try {
      if (formData.validation_rules.trim()) {
        parsedValidation = JSON.parse(formData.validation_rules);
      }
    } catch (error) {
      validationError = 'Invalid JSON in validation rules';
      return;
    }

    try {
      loading = true;

      const submitData = {
        name: formData.name.trim(),
        description: formData.description.trim(),
        payload_schema: parsedSchema || null,
        validation_rules: parsedValidation || null,
        is_active: formData.is_active
      };

      if (template) {
        // Update existing template
        await templateApi.updateTemplate(template.id, submitData);
        toast.success('Template updated successfully');
      } else {
        // Create new template
        await templateApi.createTemplate(submitData);
        toast.success('Template created successfully');
      }

      dispatch('success');
    } catch (error: any) {
      console.error('Form submission error:', error);

      // Handle validation errors
      if (error.message && error.message.includes('detail')) {
        try {
          const errorData = JSON.parse(error.message);
          if (errorData.detail) {
            toast.error(errorData.detail);
          }
        } catch {
          toast.error('An error occurred while saving the template');
        }
      } else {
        toast.error('An error occurred while saving the template');
      }
    } finally {
      loading = false;
    }
  }

  function handleCancel() {
    dispatch('cancel');
  }

  function formatJson() {
    try {
      if (formData.payload_schema.trim()) {
        const parsed = JSON.parse(formData.payload_schema);
        formData.payload_schema = JSON.stringify(parsed, null, 2);
        schemaError = '';
      }
    } catch (error) {
      schemaError = 'Invalid JSON format';
    }
  }

  function formatValidation() {
    try {
      if (formData.validation_rules.trim()) {
        const parsed = JSON.parse(formData.validation_rules);
        formData.validation_rules = JSON.stringify(parsed, null, 2);
        validationError = '';
      }
    } catch (error) {
      validationError = 'Invalid JSON format';
    }
  }
</script>

<form on:submit|preventDefault={handleSubmit} class="space-y-6">
  <!-- Name Field -->
  <div>
    <label for="name" class="form-label">Template Name</label>
    <input
      type="text"
      id="name"
      class="form-input"
      placeholder="Enter template name"
      bind:value={formData.name}
      required
    />
    {#if errors.name}
      <p class="mt-1 text-sm text-red-600">{errors.name}</p>
    {/if}
    <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">Display name for the license template</p>
  </div>

  <!-- Description Field -->
  <div>
    <label for="description" class="form-label">Description</label>
    <textarea
      id="description"
      class="form-input"
      placeholder="Describe what this template is for..."
      rows="3"
      bind:value={formData.description}
      required
    ></textarea>
    {#if errors.description}
      <p class="mt-1 text-sm text-red-600">{errors.description}</p>
    {/if}
    <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">Brief description of the template's purpose</p>
  </div>

  <!-- Payload Schema Field -->
  <div>
    <div class="flex items-center justify-between mb-2">
      <label for="payload_schema" class="form-label">JSON Schema (Optional)</label>
      <button
        type="button"
        class="text-xs bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 px-2 py-1 rounded hover:bg-gray-200 dark:hover:bg-gray-700"
        on:click={formatJson}
      >
        Format JSON
      </button>
    </div>
    <textarea
      id="payload_schema"
      class="form-input font-mono text-sm"
      placeholder="Enter JSON schema for license validation..."
      rows="8"
      bind:value={formData.payload_schema}
    ></textarea>
    {#if schemaError}
      <p class="mt-1 text-sm text-red-600">{schemaError}</p>
    {/if}
    <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">JSON schema for validating license payloads</p>
  </div>

  <!-- Validation Rules Field -->
  <div>
    <div class="flex items-center justify-between mb-2">
      <label for="validation_rules" class="form-label">Validation Rules (Optional)</label>
      <button
        type="button"
        class="text-xs bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 px-2 py-1 rounded hover:bg-gray-200 dark:hover:bg-gray-700"
        on:click={formatValidation}
      >
        Format JSON
      </button>
    </div>
    <textarea
      id="validation_rules"
      class="form-input font-mono text-sm"
      placeholder="Enter additional validation rules..."
      rows="6"
      bind:value={formData.validation_rules}
    ></textarea>
    {#if validationError}
      <p class="mt-1 text-sm text-red-600">{validationError}</p>
    {/if}
    <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">Additional validation rules for the template</p>
  </div>

  <!-- Active Status -->
  <div>
    <label class="form-label">Status</label>
    <div class="flex items-center space-x-3">
      <input
        type="checkbox"
        id="is_active"
        class="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
        bind:checked={formData.is_active}
      />
      <label for="is_active" class="text-sm font-medium text-gray-700 dark:text-gray-200">
        Active template
      </label>
    </div>
    <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">Inactive templates cannot be used for new licenses</p>
  </div>

  <!-- Form Actions -->
  <div class="flex justify-end space-x-3 pt-4 border-t border-gray-200 dark:border-gray-700">
    <button
      type="button"
      class="btn btn-secondary"
      on:click={handleCancel}
      disabled={loading}
    >
      Cancel
    </button>
    <button
      type="submit"
      class="btn btn-primary flex items-center space-x-2"
      disabled={loading}
    >
      {#if loading}
        <Loader size={16} class="animate-spin" />
        <span>{template ? 'Updating...' : 'Creating...'}</span>
      {:else}
        <span>{template ? 'Update Template' : 'Create Template'}</span>
      {/if}
    </button>
  </div>
</form>
