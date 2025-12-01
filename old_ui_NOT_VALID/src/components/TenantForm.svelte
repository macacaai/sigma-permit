<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { toast } from 'svelte-french-toast';
  import { Loader } from 'lucide-svelte';

  import { tenantApi } from '$lib/api';

  export let tenant: any = null; // For editing

  const dispatch = createEventDispatcher();

  let formData = {
    name: tenant?.name || '',
    slug: tenant?.slug || '',
    max_licenses: tenant?.max_licenses || 100,
    is_active: tenant?.is_active ?? true
  };

  let loading = false;
  let errors: Record<string, string> = {};

  // Auto-generate slug from name
  $: if (formData.name && !tenant) {
    formData.slug = formData.name
      .toLowerCase()
      .replace(/[^a-z0-9\s-]/g, '')
      .replace(/\s+/g, '-')
      .replace(/-+/g, '-')
      .trim();
  }

  async function handleSubmit() {
    // Reset errors
    errors = {};

    // Basic validation
    if (!formData.name.trim()) {
      errors.name = 'Tenant name is required';
      return;
    }

    if (!formData.slug.trim()) {
      errors.slug = 'Slug is required';
      return;
    }

    // Validate slug format
    if (!/^[a-z0-9-]+$/.test(formData.slug)) {
      errors.slug = 'Slug can only contain lowercase letters, numbers, and hyphens';
      return;
    }

    if (formData.max_licenses < 1 || formData.max_licenses > 10000) {
      errors.max_licenses = 'Max licenses must be between 1 and 10,000';
      return;
    }

    try {
      loading = true;

      const submitData = {
        name: formData.name.trim(),
        slug: formData.slug.trim(),
        max_licenses: formData.max_licenses,
        is_active: formData.is_active
      };

      if (tenant) {
        // Update existing tenant
        await tenantApi.updateTenant(tenant.id, submitData);
        toast.success('Tenant updated successfully');
      } else {
        // Create new tenant
        await tenantApi.createTenant(submitData);
        toast.success('Tenant created successfully');
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
          toast.error('An error occurred while saving the tenant');
        }
      } else {
        toast.error('An error occurred while saving the tenant');
      }
    } finally {
      loading = false;
    }
  }

  function handleCancel() {
    dispatch('cancel');
  }
</script>

<form on:submit|preventDefault={handleSubmit} class="space-y-6">
  <!-- Name Field -->
  <div>
    <label for="name" class="form-label">Tenant Name</label>
    <input
      type="text"
      id="name"
      class="form-input"
      placeholder="Enter tenant name"
      bind:value={formData.name}
      required
    />
    {#if errors.name}
      <p class="mt-1 text-sm text-red-600 dark:text-red-400">{errors.name}</p>
    {/if}
    <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">Display name for the tenant organization</p>
  </div>

  <!-- Slug Field -->
  <div>
    <label for="slug" class="form-label">Slug</label>
    <input
      type="text"
      id="slug"
      class="form-input font-mono"
      placeholder="tenant-slug"
      bind:value={formData.slug}
      required
    />
    {#if errors.slug}
      <p class="mt-1 text-sm text-red-600 dark:text-red-400">{errors.slug}</p>
    {/if}
    <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">URL-friendly identifier (lowercase, numbers, hyphens only)</p>
  </div>

  <!-- Max Licenses Field -->
  <div>
    <label for="max_licenses" class="form-label">Maximum Licenses</label>
    <input
      type="number"
      id="max_licenses"
      class="form-input"
      min="1"
      max="10000"
      bind:value={formData.max_licenses}
      required
    />
    {#if errors.max_licenses}
      <p class="mt-1 text-sm text-red-600 dark:text-red-400">{errors.max_licenses}</p>
    {/if}
    <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">Maximum number of licenses this tenant can have</p>
  </div>

  <!-- Active Status -->
  <div>
    <label class="form-label">Status</label>
    <div class="flex items-center space-x-3">
      <input
        type="checkbox"
        id="is_active"
        class="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:focus:ring-blue-600"
        bind:checked={formData.is_active}
      />
      <label for="is_active" class="text-sm font-medium text-gray-700 dark:text-gray-200">
        Active tenant
      </label>
    </div>
    <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">Inactive tenants cannot receive new licenses</p>
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
        <span>{tenant ? 'Updating...' : 'Creating...'}</span>
      {:else}
        <span>{tenant ? 'Update Tenant' : 'Create Tenant'}</span>
      {/if}
    </button>
  </div>
</form>
