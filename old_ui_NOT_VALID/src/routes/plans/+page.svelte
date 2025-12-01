<script lang="ts">
  import { onMount } from 'svelte';
  import { toast } from 'svelte-french-toast';
  import { CreditCard, Plus, Edit, Trash2, RefreshCw } from 'lucide-svelte';
  import { planApi } from '$lib/api';

  let plans: any[] = [];
  let loading = true;
  let currentPage = 1;
  let totalPages = 1;
  let pageSize = 10;

  onMount(async () => {
    const token = sessionStorage.getItem('access_token');
    if (token) {
      await loadPlans();
    }
  });

  async function loadPlans(page = 1) {
    try {
      loading = true;
      currentPage = page;
      const response = await planApi.getPlans(page, pageSize);
      plans = response.items || [];
      totalPages = Math.ceil((response.total || 0) / pageSize);
    } catch (error) {
      console.error('Error loading plans:', error);
      toast.error('Failed to load plans');
    } finally {
      loading = false;
    }
  }
</script>

<svelte:head>
  <title>Plans - Sigma Permit</title>
</svelte:head>

<div class="space-y-6">
  <div class="flex items-center justify-between">
    <div>
      <h1 class="text-3xl font-bold text-gray-900 dark:text-gray-50">Plans</h1>
      <p class="text-gray-600 dark:text-gray-400 mt-2">Manage subscription plans</p>
    </div>
    <div class="flex items-center space-x-3">
      <button class="btn btn-primary p-2" on:click={() => loadPlans(currentPage)} title="Refresh">
        <RefreshCw size={18} />
      </button>
      <button class="btn btn-primary flex items-center space-x-2">
        <Plus size={18} />
        <span>Add Plan</span>
      </button>
    </div>
  </div>

  <div class="card">
    <div class="table-container">
      {#if loading}
        <div class="flex items-center justify-center py-12">
          <div class="spinner mr-3"></div>
          <span class="text-gray-600 dark:text-gray-400">Loading plans...</span>
        </div>
      {:else if plans.length === 0}
        <div class="text-center py-12">
          <CreditCard class="mx-auto text-gray-400 dark:text-gray-500 mb-4" size={48} />
          <h3 class="text-lg font-medium text-gray-900 dark:text-gray-50 mb-2">No plans found</h3>
          <p class="text-gray-600 dark:text-gray-400 mb-4">Get started by creating your first plan.</p>
        </div>
      {:else}
        <table class="table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Product</th>
              <th>Price</th>
              <th>Billing</th>
              <th>Status</th>
              <th class="text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {#each plans as plan}
              <tr class="hover:bg-gray-50 dark:hover:bg-gray-800">
                <td class="font-medium text-gray-900 dark:text-gray-50">{plan.name}</td>
                <td class="text-gray-600 dark:text-gray-400">{plan.product?.name || 'Unknown'}</td>
                <td class="text-gray-900 dark:text-gray-50">${plan.price}</td>
                <td class="text-gray-900 dark:text-gray-50">{plan.billing_interval}</td>
                <td>
                  <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {plan.is_active ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400' : 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400'}">
                    {plan.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td class="text-right">
                  <div class="flex items-center justify-end space-x-2">
                    <button class="p-1 text-gray-400 dark:text-gray-500 hover:text-blue-500 rounded" title="Edit plan">
                      <Edit size={16} />
                    </button>
                    <button class="p-1 text-gray-400 dark:text-gray-500 hover:text-red-500 rounded" title="Delete plan">
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