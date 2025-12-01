<script lang="ts">
  import { onMount } from 'svelte';
  import { toast } from 'svelte-french-toast';
  import {
    Key,
    Plus,
    Edit,
    Trash2,
    Search,
    Filter,
    Eye,
    Calendar,
    Download,
    RefreshCw
  } from 'lucide-svelte';

  import { licenseApi, tenantApi, templateApi } from '$lib/api';
  import Modal from '$components/Modal.svelte';
  import LicenseForm from '$components/LicenseForm.svelte';

  let licenses: any[] = [];
  let templates: any[] = [];
  let loading = true;
  let searchQuery = '';
  let selectedTenant = '';
  let currentPage = 1;
  let totalPages = 1;
  let pageSize = 10;

  // Modal states
  let showCreateModal = false;
  let showEditModal = false;
  let showDeleteModal = false;
  let showViewModal = false;
  let selectedLicense: any = null;

  // Tenants data for form dropdowns only
  let tenants: any[] = [];

  onMount(async () => {
    // Check if user is authenticated before loading data
    const token = sessionStorage.getItem('access_token');
    if (token) {
      await Promise.all([loadLicenses(), loadTenants(), loadTemplates()]);
    }
  });

  async function loadLicenses(page = 1) {
    try {
      loading = true;
      currentPage = page;

      const response = await licenseApi.getLicenses(page, pageSize, selectedTenant || undefined);
      licenses = response.items || [];
      totalPages = Math.ceil((response.total || 0) / pageSize);
      
      console.log('Loaded licenses:', licenses.length);
      if (licenses.length > 0) {
        console.log('Sample license with tenant_name:', {
          id: licenses[0].id,
          tenant_id: licenses[0].tenant_id,
          tenant_name: licenses[0].tenant_name
        });
      }
    } catch (error) {
      console.error('Error loading licenses:', error);
      toast.error('Failed to load licenses');
    } finally {
      loading = false;
    }
  }

  async function loadTenants() {
    try {
      // Only load for form dropdowns, not for table display
      const response = await tenantApi.getTenants(1, 200);
      tenants = response.items || [];
      console.log('Loaded tenants for forms:', tenants.length);
    } catch (error) {
      console.error('Error loading tenants:', error);
    }
  }

  async function loadTemplates() {
    try {
      const response = await templateApi.getTemplates(1, 200);
      templates = response.items || [];
    } catch (error) {
      console.error('Error loading templates:', error);
    }
  }

  function filteredLicenses() {
    if (!searchQuery) return licenses;
    return licenses.filter(license =>
      license.id.toString().includes(searchQuery) ||
      license.tenant_name.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }

  function handleCreate() {
    selectedLicense = null;
    showCreateModal = true;
  }

  function handleEdit(license: any) {
    selectedLicense = license;
    showEditModal = true;
  }

  function handleDelete(license: any) {
    selectedLicense = license;
    showDeleteModal = true;
  }

  function handleView(license: any) {
    selectedLicense = license;
    showViewModal = true;
  }

  async function handleDownload(license: any) {
    try {
      console.log('Downloading license:', license.id);
      console.log('License key:', license.license_key);
      
      // Pass the license key to the API which will handle base64 encoding
      await licenseApi.downloadLicense(license.license_key);
      toast.success('License Download Complete\nThe license file has been downloaded successfully.');
    } catch (error) {
      console.error('Error downloading license:', error);
      toast.error('Failed to download license file');
    }
  }

  async function confirmDelete() {
    if (!selectedLicense) return;

    try {
      await licenseApi.deleteLicense(selectedLicense.id);
      toast.success('License revoked successfully');
      showDeleteModal = false;
      await loadLicenses(currentPage);
    } catch (error) {
      console.error('Error deleting license:', error);
    }
  }

  async function handleFormSuccess() {
    showCreateModal = false;
    showEditModal = false;
    // Add a small delay to ensure database transaction completes
    setTimeout(() => loadLicenses(currentPage), 500);
  }

  function handleTenantFilter() {
    currentPage = 1;
    loadLicenses(1);
  }
</script>

<svelte:head>
  <title>Licenses - Sigma Permit</title>
</svelte:head>

<div class="space-y-6">
  <!-- Header -->
  <div class="flex items-center justify-between">
    <div>
      <h1 class="text-3xl font-bold text-gray-900 dark:text-gray-50">Licenses</h1>
      <p class="text-gray-600 dark:text-gray-400 mt-2">Issue and manage license keys for your tenants</p>
    </div>
    <div class="flex items-center space-x-3">
      <button
        class="btn btn-primary p-2"
        on:click={() => loadLicenses(currentPage)}
        title="Refresh"
      >
        <RefreshCw size={18} />
      </button>
      <button
        class="btn btn-primary flex items-center space-x-2"
        on:click={handleCreate}
      >
        <Plus size={18} />
        <span>Create License</span>
      </button>
    </div>
  </div>

  <!-- Search and Filters -->
  <div class="card p-4">
    <div class="flex flex-col sm:flex-row gap-4">
      <div class="flex-1">
        <input
          type="text"
          placeholder="Search licenses..."
          class="form-input w-full"
          bind:value={searchQuery}
        />
      </div>
      <div class="flex items-center space-x-2">
        <select
          class="form-input"
          bind:value={selectedTenant}
          on:change={handleTenantFilter}
        >
          <option value="">All Tenants</option>
          {#each tenants as tenant}
            <option value={tenant.id}>{tenant.name}</option>
          {/each}
        </select>
      </div>
      <div class="text-sm text-gray-600 dark:text-gray-400">
        {filteredLicenses().length} of {licenses.length} licenses
      </div>
    </div>
  </div>

  <!-- Licenses Table -->
  <div class="card">
    <div class="table-container">
      {#if loading}
        <div class="flex items-center justify-center py-12">
          <div class="spinner mr-3"></div>
          <span class="text-gray-600 dark:text-gray-400">Loading licenses...</span>
        </div>
      {:else if filteredLicenses().length === 0}
        <div class="text-center py-12">
          <Key class="mx-auto text-gray-400 mb-4" size={48} />
          <h3 class="text-lg font-medium text-gray-900 dark:text-gray-50 mb-2">No licenses found</h3>
          <p class="text-gray-600 dark:text-gray-400 mb-4">
            {searchQuery || selectedTenant ? 'Try adjusting your filters.' : 'Get started by issuing your first license.'}
          </p>
          {#if !searchQuery && !selectedTenant}
            <button class="btn btn-primary flex items-center space-x-2 mx-auto" on:click={handleCreate}>
              <Plus size={18} />
              <span>Create License</span>
            </button>
          {/if}
        </div>
      {:else}
        <table class="table">
          <thead>
            <tr>
              <th>License ID</th>
              <th>Tenant</th>
              <th>Issued</th>
              <th>Validity Days</th>
              <th>Status</th>
              <th class="text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {#each filteredLicenses() as license}
              <tr class="hover:bg-gray-50 dark:hover:bg-gray-800">
                <td class="font-mono text-sm font-medium text-gray-900 dark:text-gray-50">
                  {license.id.toString().substring(0, 8)}
                </td>
                <td class="text-gray-600 dark:text-gray-400">
                  {license.tenant_name}
                </td>
                <td class="text-gray-600 dark:text-gray-400">
                  <div class="flex items-center space-x-1">
                    <Calendar size={14} />
                    <span>{new Date(license.issued_at).toLocaleDateString()}</span>
                  </div>
                </td>
                <td class="text-gray-600 dark:text-gray-400">
                  {license.validity_days} days
                </td>
                <td>
                  <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400">
                    Active
                  </span>
                </td>
                <td class="text-right">
                  <div class="flex items-center justify-end space-x-2">
                    <button
                      class="p-1 text-gray-400 hover:text-blue-500 rounded"
                      on:click={() => handleView(license)}
                      title="View license details"
                    >
                      <Eye size={16} />
                    </button>
                    <button
                      class="p-1 text-gray-400 hover:text-green-500 rounded"
                      on:click={() => handleDownload(license)}
                      title="Download license file"
                    >
                      <Download size={16} />
                    </button>
                    <button
                      class="p-1 text-gray-400 hover:text-blue-500 rounded"
                      on:click={() => handleEdit(license)}
                      title="Edit license"
                    >
                      <Edit size={16} />
                    </button>
                    <button
                      class="p-1 text-gray-400 hover:text-red-500 rounded"
                      on:click={() => handleDelete(license)}
                      title="Revoke license"
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
            on:change={() => { currentPage = 1; loadLicenses(1); }}
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
          Showing {Math.min((currentPage - 1) * pageSize + 1, licenses.length)} to {Math.min(currentPage * pageSize, licenses.length)} of {licenses.length} licenses
        </div>
      </div>

      <!-- Page Navigation -->
      {#if totalPages > 1}
        <div class="flex items-center space-x-2">
          <!-- First Page -->
          <button
            class="btn btn-secondary"
            disabled={currentPage === 1}
            on:click={() => loadLicenses(1)}
            title="First page"
          >
            ««
          </button>

          <!-- Previous Page -->
          <button
            class="btn btn-secondary"
            disabled={currentPage === 1}
            on:click={() => loadLicenses(currentPage - 1)}
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
                  on:click={() => loadLicenses(pageNum)}
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
            on:click={() => loadLicenses(currentPage + 1)}
            title="Next page"
          >
            ›
          </button>

          <!-- Last Page -->
          <button
            class="btn btn-secondary"
            disabled={currentPage === totalPages}
            on:click={() => loadLicenses(totalPages)}
            title="Last page"
          >
            »»
          </button>
        </div>
      {/if}
    </div>
  </div>
</div>

<!-- Create License Modal -->
<Modal bind:open={showCreateModal} title="Create New License" size="lg" onClose={() => showCreateModal = false}>
  <LicenseForm
    tenants={tenants}
    templates={templates}
    on:success={handleFormSuccess}
    on:cancel={() => showCreateModal = false}
  />
</Modal>

<!-- Edit License Modal -->
<Modal bind:open={showEditModal} title="Edit License" size="lg" onClose={() => showEditModal = false}>
  <LicenseForm
    license={selectedLicense}
    tenants={tenants}
    templates={templates}
    on:success={handleFormSuccess}
    on:cancel={() => showEditModal = false}
  />
</Modal>

<!-- View License Modal -->
<Modal bind:open={showViewModal} title="License Details" size="lg" onClose={() => showViewModal = false}>
  <div class="space-y-6">
    <div class="grid grid-cols-2 gap-4">
      <div>
        <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400">License ID</h3>
        <p class="text-lg font-mono font-medium text-gray-900 dark:text-gray-50">{selectedLicense?.id}</p>
      </div>
      <div>
        <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400">Tenant</h3>
        <p class="text-lg font-medium text-gray-900 dark:text-gray-50">{selectedLicense?.tenant_name || 'Unknown'}</p>
      </div>
      <div>
        <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400">Issued Date</h3>
        <p class="text-lg text-gray-900 dark:text-gray-50">{new Date(selectedLicense?.issued_at).toLocaleDateString()}</p>
      </div>
      <div>
        <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400">Validity Days</h3>
        <p class="text-lg text-gray-900 dark:text-gray-50">{selectedLicense?.validity_days} days</p>
      </div>
    </div>

    {#if selectedLicense?.license_key}
      <div>
        <h3 class="text-lg font-medium text-gray-900 dark:text-gray-50 mb-3">License Key</h3>
        <div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
          <p class="text-sm font-mono text-gray-800 dark:text-gray-200 break-all">{selectedLicense.license_key}</p>
        </div>
        <p class="mt-2 text-sm text-gray-600 dark:text-gray-400">
          This key should be shared with the customer for offline license validation.
        </p>
      </div>
    {/if}

    {#if selectedLicense?.payload}
      <div>
        <h3 class="text-lg font-medium text-gray-900 dark:text-gray-50 mb-3">License Payload</h3>
        <div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
          <pre class="text-sm text-gray-800 dark:text-gray-200 overflow-x-auto"><code>{JSON.stringify(selectedLicense.payload, null, 2)}</code></pre>
        </div>
      </div>
    {/if}
  </div>

  <div slot="footer" class="flex justify-end">
    <button
      class="btn btn-secondary"
      on:click={() => showViewModal = false}
    >
      Close
    </button>
  </div>
</Modal>

<!-- Delete Confirmation Modal -->
<Modal bind:open={showDeleteModal} title="Revoke License" size="sm">
  <div class="space-y-4">
    <div class="flex items-start space-x-3">
      <div class="flex-shrink-0">
        <div class="w-10 h-10 bg-red-100 dark:bg-red-900/20 rounded-full flex items-center justify-center">
          <Trash2 class="text-red-600" size={20} />
        </div>
      </div>
      <div class="flex-1">
        <h3 class="text-lg font-medium text-gray-900 dark:text-gray-50">
          Revoke License
        </h3>
        <p class="text-gray-600 dark:text-gray-400 mt-1">
          Are you sure you want to revoke license <strong class="font-mono">{selectedLicense?.id}</strong>?
          This action cannot be undone.
        </p>
        <div class="mt-3 p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
          <p class="text-sm text-yellow-800 dark:text-yellow-200">
            The license will become invalid and the tenant will lose access to the associated features.
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
      Revoke License
    </button>
  </div>
</Modal>

