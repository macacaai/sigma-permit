<script lang="ts">
  import { createEventDispatcher, onMount } from 'svelte';
  import { toast } from 'svelte-french-toast';
  import { Loader } from 'lucide-svelte';

  import { licenseApi, templateApi } from '$lib/api';

  export let license: any = null; // For editing
  export let tenants: any[] = [];
  export let templates: any[] = [];

  const dispatch = createEventDispatcher();

  // Helper function to format date for datetime-local input
  function formatDateForInput(dateStr: string): string {
    const date = new Date(dateStr);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${year}-${month}-${day}T${hours}:${minutes}`;
  }

  let formData = {
    tenant_id: license?.tenant_id || '',
    template_id: license?.template_id || '',
    issued_at: license?.issued_at ? formatDateForInput(license.issued_at) : formatDateForInput(new Date().toISOString()),
    validity_days: license?.validity_days || 30,
    payload: license?.payload ? JSON.stringify(license.payload, null, 2) : '{}'
  };

  let loading = false;
  let errors: Record<string, string> = {};
  let payloadError = '';

  // Handle template selection - always update payload when template changes (except when editing)
  function handleTemplateChange(event: Event) {
    const target = event.target as HTMLSelectElement;
    const templateId = target.value;
    
    console.log('Template changed to:', templateId);
    console.log('Templates available:', templates.map(t => ({id: t.id, name: t.name})));
    
    // Set template_id as string to match option values
    formData.template_id = templateId;

    if (templateId && !license) {
      loadTemplatePayload(templateId);
    } else if (!templateId && !license) {
      // Reset payload to empty object if no template is selected
      formData.payload = '{}';
    }
  }

  function loadTemplatePayload(templateId: string) {
    try {
      const template = templates.find(t => t.id === templateId);
      console.log('Found template:', template);
      if (template && template.payload_schema) {
        formData.payload = JSON.stringify(template.payload_schema, null, 2);
        payloadError = '';
        console.log('Loaded template payload for:', template.name);
      } else {
        formData.payload = '{}';
        console.log('No payload schema found, using empty object');
      }
    } catch (error) {
      console.error('Error loading template payload:', error);
      formData.payload = '{}';
    }
  }

  // Reactive statement to ensure template selection is properly tracked
  $: {
    if (formData.template_id && templates.length > 0) {
      const selectedTemplate = templates.find(t => t.id === formData.template_id);
      if (selectedTemplate && !license) {
        console.log('Reactive: Template selected', selectedTemplate.name);
      }
    }
  }

  // No auto-selection - keep empty by default for "Custom" option
  // Template selection will only happen when user explicitly selects one

  async function handleSubmit() {
    // Reset errors
    errors = {};
    payloadError = '';

    // Basic validation
    if (!formData.tenant_id) {
      errors.tenant_id = 'Tenant is required';
      return;
    }

    // Validate JSON payload
    let parsedPayload;
    try {
      if (formData.payload.trim()) {
        parsedPayload = JSON.parse(formData.payload);
      } else {
        parsedPayload = {};
      }
    } catch (error) {
      payloadError = 'Invalid JSON in payload';
      return;
    }

    try {
      loading = true;

      // Format the data according to the new API structure
      const submitData = {
        tenant_id: formData.tenant_id,
        template_id: formData.template_id || undefined,
        issued_at: new Date(formData.issued_at).toISOString().replace(/\.\d{3}Z$/, 'Z'),
        validity_days: parseInt(formData.validity_days.toString()),
        payload: parsedPayload || {}
      };

      console.log('Submitting license data:', submitData);

      if (license) {
        // Update existing license
        await licenseApi.updateLicense(license.id, submitData);
        toast.success('License updated successfully');
      } else {
        // Create new license
        await licenseApi.createLicense(submitData);
        toast.success('License created successfully');
      }

      dispatch('success');
    } catch (error: any) {
      console.error('Form submission error:', error);

      // Handle validation errors
      if (error.message) {
        // Check if it's a backend validation error
        if (error.message.includes('HTTP') || error.message.includes('detail')) {
          toast.error(error.message);
        } else {
          toast.error('An error occurred while saving the license: ' + error.message);
        }
      } else {
        toast.error('An error occurred while saving the license');
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
      if (formData.payload.trim()) {
        const parsed = JSON.parse(formData.payload);
        formData.payload = JSON.stringify(parsed, null, 2);
        payloadError = '';
      }
    } catch (error) {
      payloadError = 'Invalid JSON format';
    }
  }
</script>

<form on:submit|preventDefault={handleSubmit} class="space-y-6">
  <!-- Tenant Selection -->
  <div>
    <label for="tenant_id" class="form-label">Tenant</label>
    <select
      id="tenant_id"
      class="form-input {license ? 'bg-gray-100 dark:bg-gray-700 cursor-not-allowed' : ''}"
      bind:value={formData.tenant_id}
      disabled={license ? true : false}
      required
    >
      <option value="">Select a tenant</option>
      {#each tenants.filter(t => t.is_active) as tenant}
        <option value={tenant.id}>{tenant.name}</option>
      {/each}
    </select>
    {#if errors.tenant_id}
      <p class="mt-1 text-sm text-red-600">{errors.tenant_id}</p>
    {/if}
    <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
      {license ? 'Tenant cannot be changed in edit mode' : 'The tenant this license will be issued to'}
    </p>
  </div>

  <!-- Issue Date -->
  <div>
    <label for="issued_at" class="form-label">Issue Date & Time</label>
    <input
      type="datetime-local"
      id="issued_at"
      class="form-input"
      bind:value={formData.issued_at}
      required
    />
    <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">When the license becomes active</p>
  </div>

  <!-- Validity Days -->
  <div>
    <label for="validity_days" class="form-label">Validity Days</label>
    <input
      type="number"
      id="validity_days"
      class="form-input"
      bind:value={formData.validity_days}
      min="1"
      required
    />
    <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">Number of days the license will be valid</p>
  </div>

  <!-- Template Selection -->
  <div>
    <label for="template_id" class="form-label">License Template (Optional)</label>
    <select
      id="template_id"
      class="form-input"
      bind:value={formData.template_id}
      on:change={handleTemplateChange}
    >
      <option value="">Custom Payload</option>
      {#each templates.filter(t => t.is_active) as template}
        <option value={template.id}>{template.name}</option>
      {/each}
    </select>
    <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">Choose a template to pre-fill the license payload</p>
    
    <!-- Debug info - remove in production -->
    {#if formData.template_id}
      <p class="mt-1 text-xs text-blue-600">Selected: {templates.find(t => t.id === formData.template_id)?.name || 'Unknown'}</p>
    {/if}
  </div>

  <!-- Payload Field -->
  <div>
    <div class="flex items-center justify-between mb-2">
      <label for="payload" class="form-label">License Payload (JSON)</label>
      <button
        type="button"
        class="text-xs bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 px-2 py-1 rounded hover:bg-gray-200 dark:hover:bg-gray-700"
        on:click={formatJson}
      >
        Format JSON
      </button>
    </div>
    <textarea
      id="payload"
      class="form-input font-mono text-sm"
      placeholder="Enter custom license payload data..."
      rows="8"
      bind:value={formData.payload}
    ></textarea>
    {#if payloadError}
      <p class="mt-1 text-sm text-red-600">{payloadError}</p>
    {/if}
    <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">Custom data associated with this license (JSON format)</p>
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
        <span>{license ? 'Updating...' : 'Issuing...'}</span>
      {:else}
        <span>{license ? 'Update License' : 'Issue License'}</span>
      {/if}
    </button>
  </div>
</form>
