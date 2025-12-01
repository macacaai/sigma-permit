<script lang="ts">
  import { onMount } from 'svelte';
  import { toast } from 'svelte-french-toast';
  import {
    FileText,
    Plus,
    Edit,
    Trash2,
    Search,
    CheckCircle,
    XCircle,
    Code,
    RefreshCw
  } from 'lucide-svelte';

  import { templateApi } from '$lib/api';
  import Modal from '$components/Modal.svelte';
  import TemplateForm from '$components/TemplateForm.svelte';

  let templates: any[] = [];
  let loading = true;
  let searchQuery = '';
  let currentPage = 1;
  let totalPages = 1;
  let pageSize = 10;

  // Modal states
  let showCreateModal = false;
  let showEditModal = false;
  let showDeleteModal = false;
  let showSchemaModal = false;
  let selectedTemplate: any = null;

  onMount(async () => {
    // Check if user is authenticated before loading data
    const token = sessionStorage.getItem('access_token');
    if (token) {
      await loadTemplates();
    }
  });

  async function loadTemplates(page = 1) {
    try {
      loading = true;
      currentPage = page;

      const response = await templateApi.getTemplates(page, pageSize);
      templates = response.items || [];
      totalPages = Math.ceil((response.total || 0) / pageSize);
    } catch (error) {
      console.error('Error loading templates:', error);
      toast.error('Failed to load templates');
    } finally {
      loading = false;
    }
  }

  function filteredTemplates() {
    if (!searchQuery) return templates;
    return templates.filter(template =>
      template.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      template.description.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }

  function handleCreate() {
    selectedTemplate = null;
    showCreateModal = true;
  }

  function handleEdit(template: any) {
    selectedTemplate = template;
    showEditModal = true;
  }

  function handleDelete(template: any) {
    selectedTemplate = template;
    showDeleteModal = true;
  }

  function handleViewSchema(template: any) {
    selectedTemplate = template;
    showSchemaModal = true;
  }

  async function confirmDelete() {
    if (!selectedTemplate) return;

    try {
      await templateApi.deleteTemplate(selectedTemplate.id);
      toast.success(`Template "${selectedTemplate.name}" deleted successfully`);
      showDeleteModal = false;
      await loadTemplates(currentPage);
    } catch (error) {
      console.error('Error deleting template:', error);
    }
  }

  async function handleFormSuccess() {
    showCreateModal = false;
    showEditModal = false;
    // Add a small delay to ensure database transaction completes
    setTimeout(() => loadTemplates(currentPage), 500);
  }
</script>

<svelte:head>
  <title>Templates - Sigma Permit</title>
</svelte:head>

<div class="space-y-6">
  <!-- Header -->
  <div class="flex items-center justify-between">
    <div>
      <h1 class="text-3xl font-bold text-gray-900 dark:text-gray-50">Templates</h1>
      <p class="text-gray-600 dark:text-gray-400 mt-2">Manage license templates with JSON schema validation</p>
    </div>
    <div class="flex items-center space-x-3">
      <button
        class="btn btn-primary p-2"
        on:click={() => loadTemplates(currentPage)}
        title="Refresh"
      >
        <RefreshCw size={18} />
      </button>
      <button
        class="btn btn-primary flex items-center space-x-2"
        on:click={handleCreate}
      >
        <Plus size={18} />
        <span>Add Template</span>
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
            placeholder="Search templates..."
            class="form-input w-full"
            bind:value={searchQuery}
          />
        </div>
        <div class="ml-2 p-2 text-gray-400 dark:text-gray-500">
          <Search size={18} />
        </div>
      </div>
      <div class="text-sm text-gray-600 dark:text-gray-400">
        {filteredTemplates().length} of {templates.length} templates
      </div>
    </div>
  </div>

  <!-- Templates Table -->
  <div class="card">
    <div class="table-container">
      {#if loading}
        <div class="flex items-center justify-center py-12">
          <div class="spinner mr-3"></div>
          <span class="text-gray-600 dark:text-gray-400">Loading templates...</span>
        </div>
      {:else if filteredTemplates().length === 0}
        <div class="text-center py-12">
          <FileText class="mx-auto text-gray-400 mb-4" size={48} />
          <h3 class="text-lg font-medium text-gray-900 dark:text-gray-50 mb-2">No templates found</h3>
          <p class="text-gray-600 dark:text-gray-400 mb-4">
            {searchQuery ? 'Try adjusting your search terms.' : 'Get started by creating your first template.'}
          </p>
          {#if !searchQuery}
            <button class="btn btn-primary flex items-center space-x-2 mx-auto" on:click={handleCreate}>
              <Plus size={18} />
              <span>Create Template</span>
            </button>
          {/if}
        </div>
      {:else}
        <table class="table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Description</th>
              <th>Status</th>
              <th>Created</th>
              <th class="text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {#each filteredTemplates() as template}
              <tr class="hover:bg-gray-50 dark:hover:bg-gray-800">
                <td class="font-medium text-gray-900 dark:text-gray-50">{template.name}</td>
                <td class="max-w-xs truncate text-gray-600 dark:text-gray-400" title={template.description}>
                  {template.description}
                </td>
                <td>
                  <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {template.is_active ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400' : 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400'}">
                    {#if template.is_active}
                      <CheckCircle size={12} class="mr-1" />
                      Active
                    {:else}
                      <XCircle size={12} class="mr-1" />
                      Inactive
                    {/if}
                  </span>
                </td>
                <td class="text-gray-600 dark:text-gray-400">
                  {new Date(template.created_at).toLocaleDateString()}
                </td>
                <td class="text-right">
                  <div class="flex items-center justify-end space-x-2">
                    <button
                      class="p-1 text-gray-400 hover:text-purple-500 rounded"
                      on:click={() => handleViewSchema(template)}
                      title="View schema"
                    >
                      <Code size={16} />
                    </button>
                    <button
                      class="p-1 text-gray-400 hover:text-blue-500 rounded"
                      on:click={() => handleEdit(template)}
                      title="Edit template"
                    >
                      <Edit size={16} />
                    </button>
                    <button
                      class="p-1 text-gray-400 hover:text-red-500 rounded"
                      on:click={() => handleDelete(template)}
                      title="Delete template"
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
            on:change={() => { currentPage = 1; loadTemplates(1); }}
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
          Showing {Math.min((currentPage - 1) * pageSize + 1, templates.length)} to {Math.min(currentPage * pageSize, templates.length)} of {templates.length} templates
        </div>
      </div>

      <!-- Page Navigation -->
      {#if totalPages > 1}
        <div class="flex items-center space-x-2">
          <!-- First Page -->
          <button
            class="btn btn-secondary"
            disabled={currentPage === 1}
            on:click={() => loadTemplates(1)}
            title="First page"
          >
            ««
          </button>

          <!-- Previous Page -->
          <button
            class="btn btn-secondary"
            disabled={currentPage === 1}
            on:click={() => loadTemplates(currentPage - 1)}
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
                  on:click={() => loadTemplates(pageNum)}
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
            on:click={() => loadTemplates(currentPage + 1)}
            title="Next page"
          >
            ›
          </button>

          <!-- Last Page -->
          <button
            class="btn btn-secondary"
            disabled={currentPage === totalPages}
            on:click={() => loadTemplates(totalPages)}
            title="Last page"
          >
            »»
          </button>
        </div>
      {/if}
    </div>
  </div>
</div>

<!-- Create Template Modal -->
<Modal bind:open={showCreateModal} title="Create New Template" size="lg" onClose={() => showCreateModal = false}>
  <TemplateForm
    on:success={handleFormSuccess}
    on:cancel={() => showCreateModal = false}
  />
</Modal>

<!-- Edit Template Modal -->
<Modal bind:open={showEditModal} title="Edit Template" size="lg" onClose={() => showEditModal = false}>
  <TemplateForm
    template={selectedTemplate}
    on:success={handleFormSuccess}
    on:cancel={() => showEditModal = false}
  />
</Modal>

<!-- Schema View Modal -->
<Modal bind:open={showSchemaModal} title="Template Schema" size="lg" onClose={() => showSchemaModal = false}>
  <div class="space-y-4">
    <div>
      <h3 class="text-lg font-medium text-gray-900 dark:text-gray-50 mb-2">{selectedTemplate?.name} Schema</h3>
      <div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
        <pre class="text-sm text-gray-800 dark:text-gray-200 overflow-x-auto"><code>{JSON.stringify(selectedTemplate?.payload_schema, null, 2)}</code></pre>
      </div>
    </div>
    {#if selectedTemplate?.validation_rules}
      <div>
        <h4 class="text-md font-medium text-gray-900 dark:text-gray-50 mb-2">Validation Rules</h4>
        <div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
          <pre class="text-sm text-gray-800 dark:text-gray-200 overflow-x-auto"><code>{JSON.stringify(selectedTemplate?.validation_rules, null, 2)}</code></pre>
        </div>
      </div>
    {/if}
  </div>

  <div slot="footer" class="flex justify-end">
    <button
      class="btn btn-secondary"
      on:click={() => showSchemaModal = false}
    >
      Close
    </button>
  </div>
</Modal>

<!-- Delete Confirmation Modal -->
<Modal bind:open={showDeleteModal} title="Delete Template" size="sm">
  <div class="space-y-4">
    <div class="flex items-start space-x-3">
      <div class="flex-shrink-0">
        <div class="w-10 h-10 bg-red-100 dark:bg-red-900/20 rounded-full flex items-center justify-center">
          <Trash2 class="text-red-600" size={20} />
        </div>
      </div>
      <div class="flex-1">
        <h3 class="text-lg font-medium text-gray-900 dark:text-gray-50">
          Delete Template
        </h3>
        <p class="text-gray-600 dark:text-gray-400 mt-1">
          Are you sure you want to delete <strong>{selectedTemplate?.name}</strong>?
          This action cannot be undone.
        </p>
        <div class="mt-3 p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
          <p class="text-sm text-yellow-800 dark:text-yellow-200">
            All licenses using this template will remain but won't be able to use this template for new licenses.
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
      Delete Template
    </button>
  </div>
</Modal>

