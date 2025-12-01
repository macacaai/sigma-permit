<script lang="ts">
  import { onMount } from 'svelte';
  import { toast } from 'svelte-french-toast';
  import { Settings, Plus, Edit, Trash2, RefreshCw } from 'lucide-svelte';
  import { featureApi } from '$lib/api';

  let features: any[] = [];
  let loading = true;
  let currentPage = 1;
  let totalPages = 1;
  let pageSize = 10;

  onMount(async () => {
    const token = sessionStorage.getItem('access_token');
    if (token) {
      await loadFeatures();
    }
  });

  async function loadFeatures(page = 1) {
    try {
      loading = true;
      currentPage = page;
      const response = await featureApi.getFeatures(page, pageSize);
      features = response.items || [];
      totalPages = Math.ceil((response.total || 0) / pageSize);
    } catch (error) {
      console.error('Error loading features:', error);
      toast.error('Failed to load features');
    } finally {
      loading = false;
    }
  }
</script>

<svelte:head>
  <title>Features - Sigma Permit</title>
</svelte:head>

<div class="space-y-6">
  <div class="flex items-center justify-between">
    <div>
      <h1 class="text-3xl font-bold text-gray-900 dark:text-gray-50">Features</h1>
      <p class="text-gray-600 dark:text-gray-400 mt-2">Manage product features</p>
    </div>
    <div class="flex items-center space-x-3">
      <button class="btn btn-primary p-2" on:click={() => loadFeatures(currentPage)} title="Refresh">
        <RefreshCw size={18} />
      </button>
      <button class="btn btn-primary flex items-center space-x-2">
        <Plus size={18} />
        <span>Add Feature</span>
      </button>
    </div>
  </div>

  <div class="card">
    <div class="table-container">
      {#if loading}
        <div class="flex items-center justify-center py-12">
          <div class="spinner mr-3"></div>
          <span class="text-gray-600 dark:text-gray-400">Loading features...</span>
        </div>
      {:else if features.length === 0}
        <div class="text-center py-12">
          <Settings class="mx-auto text-gray-400 dark:text-gray-500 mb-4" size={48} />
          <h3 class="text-lg font-medium text-gray-900 dark:text-gray-50 mb-2">No features found</h3>
          <p class="text-gray-600 dark:text-gray-400 mb-4">Get started by creating your first feature.</p>
        </div>
      {:else}
        <table class="table">
          <thead>
            <tr>
              <th>Key</th>
              <th>Product</th>
              <th>Type</th>
              <th>Default Value</th>
              <th class="text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {#each features as feature}
              <tr class="hover:bg-gray-50 dark:hover:bg-gray-800">
                <td class="font-medium text-gray-900 dark:text-gray-50">{feature.key}</td>
                <td class="text-gray-600 dark:text-gray-400">{feature.product?.name || 'Unknown'}</td>
                <td class="text-gray-900 dark:text-gray-50">{feature.type}</td>
                <td class="text-gray-600 dark:text-gray-400">{JSON.stringify(feature.default_value) || '-'}</td>
                <td class="text-right">
                  <div class="flex items-center justify-end space-x-2">
                    <button class="p-1 text-gray-400 dark:text-gray-500 hover:text-blue-500 rounded" title="Edit feature">
                      <Edit size={16} />
                    </button>
                    <button class="p-1 text-gray-400 dark:text-gray-500 hover:text-red-500 rounded" title="Delete feature">
                      <Trash2 size={16} />
                    </button>
                  </div>
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      {/if}
    </div>
  </div>
</div>