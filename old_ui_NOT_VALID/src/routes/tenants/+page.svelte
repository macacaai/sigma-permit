<script lang="ts">
  import { onMount } from 'svelte';
  import { toast } from 'svelte-french-toast';
  import {
    Building,
    Plus,
    Edit,
    Trash2,
    Search,
    MoreVertical,
    CheckCircle,
    XCircle,
    RefreshCw
  } from 'lucide-svelte';

  import { tenantApi } from '$lib/api';
  import Modal from '$components/Modal.svelte';
  import TenantForm from '$components/TenantForm.svelte';

  let tenants: any[] = [];
  let loading = true;
  let searchQuery = '';
  let currentPage = 1;
  let totalPages = 1;
  let pageSize = 10;

  // Modal states
  let showCreateModal = false;
  let showEditModal = false;
  let showDeleteModal = false;
  let selectedTenant: any = null;

  onMount(async () => {
    // Check if user is authenticated before loading data
    const token = sessionStorage.getItem('access_token');
    if (token) {
      await loadTenants();
    }
  });

  async function loadTenants(page = 1) {
    try {
      loading = true;
      currentPage = page;

      const response = await tenantApi.getTenants(page, pageSize);
      tenants = response.items || [];
      totalPages = Math.ceil((response.total || 0) / pageSize);
    } catch (error) {
      console.error('Error loading tenants:', error);
      toast.error('Failed to load tenants');
    } finally {
      loading = false;
    }
  }

  function filteredTenants() {
    if (!searchQuery) return tenants;
    return tenants.filter(tenant =>
      tenant.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      tenant.slug.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }

  function handleCreate() {
    selectedTenant = null;
    showCreateModal = true;
  }

  function handleEdit(tenant: any) {
    selectedTenant = tenant;
    showEditModal = true;
  }

  function handleDelete(tenant: any) {
    selectedTenant = tenant;
    showDeleteModal = true;
  }

  async function confirmDelete() {
    if (!selectedTenant) return;

    try {
      await tenantApi.deleteTenant(selectedTenant.id);
      toast.success(`Tenant "${selectedTenant.name}" deleted successfully`);
      showDeleteModal = false;
      await loadTenants(currentPage);
    } catch (error) {
      console.error('Error deleting tenant:', error);
    }
  }

  async function handleFormSuccess() {
    showCreateModal = false;
    showEditModal = false;
    // Add a small delay to ensure database transaction completes
    setTimeout(() => loadTenants(currentPage), 500);
  }
</script>

<svelte:head>
  <title>Tenants - Sigma Permit</title>
</svelte:head>

<div class="space-y-6">
  <!-- Header -->
  <div class="flex items-center justify-between">
    <div>
      <h1 class="text-3xl font-bold text-gray-900 dark:text-gray-50">Tenants</h1>
      <p class="text-gray-600 dark:text-gray-400 mt-2">Manage tenant organizations and their license limits</p>
    </div>
    <div class="flex items-center space-x-3">
      <button
        class="btn btn-primary p-2"
        on:click={() => loadTenants(currentPage)}
        title="Refresh"
      >
        <RefreshCw size={18} />
      </button>
      <button
        class="btn btn-primary flex items-center space-x-2"
        on:click={handleCreate}
      >
        <Plus size={18} />
        <span>Add Tenant</span>
      </button>
    </div>
  </div>

  <!-- Search and Filters -->
  <div class="card p-4">
    <div class="flex flex-col sm:flex-row gap-4">
      <div class="flex-1 flex items-center">
        <div class="relative flex-1">
          <input
            type="text"
            placeholder="Search tenants..."
            class="form-input w-full"
            bind:value={searchQuery}
          />
        </div>
        <div class="ml-2 p-2 text-gray-400 dark:text-gray-500">
          <Search size={18} />
        </div>
      </div>
      <div class="text-sm text-gray-600 dark:text-gray-400">
        {filteredTenants().length} of {tenants.length} tenants
      </div>
    </div>
  </div>

  <!-- Tenants Table -->
  <div class="card">
    <div class="table-container">
      {#if loading}
        <div class="flex items-center justify-center py-12">
          <div class="spinner mr-3"></div>
          <span class="text-gray-600 dark:text-gray-400">Loading tenants...</span>
        </div>
      {:else if filteredTenants().length === 0}
        <div class="text-center py-12">
          <Building class="mx-auto text-gray-400 dark:text-gray-500 mb-4" size={48} />
          <h3 class="text-lg font-medium text-gray-900 dark:text-gray-50 mb-2">No tenants found</h3>
          <p class="text-gray-600 dark:text-gray-400 mb-4">
            {searchQuery ? 'Try adjusting your search terms.' : 'Get started by creating your first tenant.'}
          </p>
          {#if !searchQuery}
            <button class="btn btn-primary flex items-center space-x-2 mx-auto" on:click={handleCreate}>
              <Plus size={18} />
              <span>Add Tenant</span>
            </button>
          {/if}
        </div>
      {:else}
        <table class="table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Slug</th>
              <th>Max Licenses</th>
              <th>Status</th>
              <th>Created</th>
              <th class="text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {#each filteredTenants() as tenant}
              <tr class="hover:bg-gray-50 dark:hover:bg-gray-800">
                <td class="font-medium text-gray-900 dark:text-gray-50">{tenant.name}</td>
                <td>
                  <code class="bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded text-sm text-gray-800 dark:text-gray-200">{tenant.slug}</code>
                </td>
                <td class="text-gray-900 dark:text-gray-50">{tenant.max_licenses}</td>
                <td>
                  <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {tenant.is_active ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400' : 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400'}">
                    {#if tenant.is_active}
                      <CheckCircle size={12} class="mr-1" />
                      Active
                    {:else}
                      <XCircle size={12} class="mr-1" />
                      Inactive
                    {/if}
                  </span>
                </td>
                <td class="text-gray-600 dark:text-gray-400">
                  {new Date(tenant.created_at).toLocaleDateString()}
                </td>
                <td class="text-right">
                  <div class="flex items-center justify-end space-x-2">
                    <button
                      class="p-1 text-gray-400 dark:text-gray-500 hover:text-blue-500 rounded"
                      on:click={() => handleEdit(tenant)}
                      title="Edit tenant"
                    >
                      <Edit size={16} />
                    </button>
                    <button
                      class="p-1 text-gray-400 dark:text-gray-500 hover:text-red-500 rounded"
                      on:click={() => handleDelete(tenant)}
                      title="Delete tenant"
                    >
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

    <!-- Pagination -->
    <div class="flex items-center justify-between px-6 py-4 border-t border-gray-200 dark:border-gray-700">
      <div class="flex items-center space-x-4">
        <!-- Page Size Selector -->
        <div class="flex items-center space-x-2">
          <label for="pageSize" class="text-sm text-gray-600 dark:text-gray-400">Show:</label>
          <select
            id="pageSize"
            class="form-input w-20"
            bind:value={pageSize}
            on:change={() => { currentPage = 1; loadTenants(1); }}
          >
            <option value={10}>10</option>
            <option value={20}>20</option>
            <option value={50}>50</option>
            <option value={100}>100</option>
            <option value={150}>150</option>
            <option value={200}>200</option>
          </select>
          <span class="text-sm text-gray-600 dark:text-gray-400">per page</span>
        </div>

        <!-- Results Info -->
        <div class="text-sm text-gray-600 dark:text-gray-400">
          Showing {Math.min((currentPage - 1) * pageSize + 1, tenants.length)} to {Math.min(currentPage * pageSize, tenants.length)} of {tenants.length} tenants
        </div>
      </div>

      <!-- Page Navigation -->
      {#if totalPages > 1}
        <div class="flex items-center space-x-2">
          <!-- First Page -->
          <button
            class="btn btn-secondary"
            disabled={currentPage === 1}
            on:click={() => loadTenants(1)}
            title="First page"
          >
            ««
          </button>

          <!-- Previous Page -->
          <button
            class="btn btn-secondary"
            disabled={currentPage === 1}
            on:click={() => loadTenants(currentPage - 1)}
            title="Previous page"
          >
            ‹
          </button>

          <!-- Page Numbers -->
          <div class="flex items-center space-x-1">
            {#each Array(Math.min(5, totalPages)) as _, i}
              {@const pageNum = Math.max(1, Math.min(totalPages - 4, currentPage - 2)) + i}
              {#if pageNum <= totalPages}
                <button
                  class="px-3 py-2 text-sm font-medium rounded-lg border transition-colors {pageNum === currentPage ? 'bg-blue-500 text-white border-blue-500 shadow-sm' : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700'}"
                  on:click={() => loadTenants(pageNum)}
                >
                  {pageNum}
                </button>
              {/if}
            {/each}
          </div>

          <!-- Next Page -->
          <button
            class="btn btn-secondary"
            disabled={currentPage === totalPages}
            on:click={() => loadTenants(currentPage + 1)}
            title="Next page"
          >
            ›
          </button>

          <!-- Last Page -->
          <button
            class="btn btn-secondary"
            disabled={currentPage === totalPages}
            on:click={() => loadTenants(totalPages)}
            title="Last page"
          >
            »»
          </button>
        </div>
      {/if}
    </div>
  </div>
</div>

<!-- Create Tenant Modal -->
<Modal bind:open={showCreateModal} title="Create New Tenant" onClose={() => showCreateModal = false}>
  <TenantForm
    on:success={handleFormSuccess}
    on:cancel={() => showCreateModal = false}
  />
</Modal>

<!-- Edit Tenant Modal -->
<Modal bind:open={showEditModal} title="Edit Tenant" onClose={() => showEditModal = false}>
  <TenantForm
    tenant={selectedTenant}
    on:success={handleFormSuccess}
    on:cancel={() => showEditModal = false}
  />
</Modal>

<!-- Delete Confirmation Modal -->
<Modal bind:open={showDeleteModal} title="Delete Tenant" size="sm">
  <div class="space-y-4">
    <div class="flex items-start space-x-3">
      <div class="flex-shrink-0">
        <div class="w-10 h-10 bg-red-100 dark:bg-red-900/20 rounded-full flex items-center justify-center">
          <Trash2 class="text-red-600 dark:text-red-400" size={20} />
        </div>
      </div>
      <div class="flex-1">
        <h3 class="text-lg font-medium text-gray-900 dark:text-gray-50">
          Delete Tenant
        </h3>
        <p class="text-gray-600 dark:text-gray-400 mt-1">
          Are you sure you want to delete <strong>{selectedTenant?.name}</strong>?
          This action cannot be undone.
        </p>
        <div class="mt-3 p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
          <p class="text-sm text-yellow-800 dark:text-yellow-200">
            All associated licenses will remain in the system but become orphaned.
          </p>
        </div>
      </div>
    </div>
  </div>

  <div slot="footer" class="flex justify-end space-x-3">
    <button
      class="btn btn-secondary"
      on:click={() => showDeleteModal = false}
    >
      Cancel
    </button>
    <button
      class="btn btn-danger"
      on:click={confirmDelete}
    >
      Delete Tenant
    </button>
  </div>
</Modal>
