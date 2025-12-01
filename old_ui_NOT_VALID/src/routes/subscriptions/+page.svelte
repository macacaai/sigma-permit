<script lang="ts">
  import { onMount } from 'svelte';
  import { toast } from 'svelte-french-toast';
  import { UserCheck, Plus, Edit, Trash2, RefreshCw } from 'lucide-svelte';
  import { subscriptionApi } from '$lib/api';

  let subscriptions: any[] = [];
  let loading = true;
  let currentPage = 1;
  let totalPages = 1;
  let pageSize = 10;

  onMount(async () => {
    const token = sessionStorage.getItem('access_token');
    if (token) {
      await loadSubscriptions();
    }
  });

  async function loadSubscriptions(page = 1) {
    try {
      loading = true;
      currentPage = page;
      const response = await subscriptionApi.getSubscriptions(page, pageSize);
      subscriptions = response.items || [];
      totalPages = Math.ceil((response.total || 0) / pageSize);
    } catch (error) {
      console.error('Error loading subscriptions:', error);
      toast.error('Failed to load subscriptions');
    } finally {
      loading = false;
    }
  }
</script>

<svelte:head>
  <title>Subscriptions - Sigma Permit</title>
</svelte:head>

<div class="space-y-6">
  <div class="flex items-center justify-between">
    <div>
      <h1 class="text-3xl font-bold text-gray-900 dark:text-gray-50">Subscriptions</h1>
      <p class="text-gray-600 dark:text-gray-400 mt-2">Manage tenant subscriptions</p>
    </div>
    <div class="flex items-center space-x-3">
      <button class="btn btn-primary p-2" on:click={() => loadSubscriptions(currentPage)} title="Refresh">
        <RefreshCw size={18} />
      </button>
      <button class="btn btn-primary flex items-center space-x-2">
        <Plus size={18} />
        <span>Add Subscription</span>
      </button>
    </div>
  </div>

  <div class="card">
    <div class="table-container">
      {#if loading}
        <div class="flex items-center justify-center py-12">
          <div class="spinner mr-3"></div>
          <span class="text-gray-600 dark:text-gray-400">Loading subscriptions...</span>
        </div>
      {:else if subscriptions.length === 0}
        <div class="text-center py-12">
          <UserCheck class="mx-auto text-gray-400 dark:text-gray-500 mb-4" size={48} />
          <h3 class="text-lg font-medium text-gray-900 dark:text-gray-50 mb-2">No subscriptions found</h3>
          <p class="text-gray-600 dark:text-gray-400 mb-4">Get started by creating your first subscription.</p>
        </div>
      {:else}
        <table class="table">
          <thead>
            <tr>
              <th>Tenant</th>
              <th>Plan</th>
              <th>Status</th>
              <th>Start Date</th>
              <th>End Date</th>
              <th class="text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {#each subscriptions as subscription}
              <tr class="hover:bg-gray-50 dark:hover:bg-gray-800">
                <td class="font-medium text-gray-900 dark:text-gray-50">{subscription.tenant?.name || 'Unknown'}</td>
                <td class="text-gray-600 dark:text-gray-400">{subscription.plan?.name || 'Unknown'}</td>
                <td>
                  <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {subscription.status === 'active' ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400' : subscription.status === 'trialing' ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400' : 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400'}">
                    {subscription.status}
                  </span>
                </td>
                <td class="text-gray-900 dark:text-gray-50">{new Date(subscription.start_date).toLocaleDateString()}</td>
                <td class="text-gray-600 dark:text-gray-400">{subscription.end_date ? new Date(subscription.end_date).toLocaleDateString() : '-'}</td>
                <td class="text-right">
                  <div class="flex items-center justify-end space-x-2">
                    <button class="p-1 text-gray-400 dark:text-gray-500 hover:text-blue-500 rounded" title="Edit subscription">
                      <Edit size={16} />
                    </button>
                    <button class="p-1 text-gray-400 dark:text-gray-500 hover:text-red-500 rounded" title="Delete subscription">
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