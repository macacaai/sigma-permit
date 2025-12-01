<script lang="ts">
  import { onMount } from 'svelte';
  import { toast } from 'svelte-french-toast';
  import { Package, Plus, Edit, Trash2, RefreshCw } from 'lucide-svelte';
  import { productApi } from '$lib/api';
  import Modal from '$components/Modal.svelte';

  let products: any[] = [];
  let loading = true;
  let currentPage = 1;
  let totalPages = 1;
  let pageSize = 10;

  // Modal states
  let showCreateModal = false;
  let showEditModal = false;
  let showDeleteModal = false;
  let selectedProduct: any = null;

  onMount(async () => {
    const token = sessionStorage.getItem('access_token');
    if (token) {
      await loadProducts();
    }
  });

  async function loadProducts(page = 1) {
    try {
      loading = true;
      currentPage = page;
      const response = await productApi.getProducts(page, pageSize);
      products = response.items || [];
      totalPages = Math.ceil((response.total || 0) / pageSize);
    } catch (error) {
      console.error('Error loading products:', error);
      toast.error('Failed to load products');
    } finally {
      loading = false;
    }
  }

  function handleCreate() {
    selectedProduct = null;
    showCreateModal = true;
  }

  function handleEdit(product: any) {
    selectedProduct = product;
    showEditModal = true;
  }

  function handleDelete(product: any) {
    selectedProduct = product;
    showDeleteModal = true;
  }

  async function confirmDelete() {
    if (!selectedProduct) return;
    try {
      await productApi.deleteProduct(selectedProduct.id);
      toast.success(`Product "${selectedProduct.name}" deleted successfully`);
      showDeleteModal = false;
      await loadProducts(currentPage);
    } catch (error) {
      console.error('Error deleting product:', error);
    }
  }

  async function handleFormSuccess() {
    showCreateModal = false;
    showEditModal = false;
    setTimeout(() => loadProducts(currentPage), 500);
  }
</script>

<svelte:head>
  <title>Products - Sigma Permit</title>
</svelte:head>

<div class="space-y-6">
  <!-- Header -->
  <div class="flex items-center justify-between">
    <div>
      <h1 class="text-3xl font-bold text-gray-900 dark:text-gray-50">Products</h1>
      <p class="text-gray-600 dark:text-gray-400 mt-2">Manage subscription products</p>
    </div>
    <div class="flex items-center space-x-3">
      <button
        class="btn btn-primary p-2"
        on:click={() => loadProducts(currentPage)}
        title="Refresh"
      >
        <RefreshCw size={18} />
      </button>
      <button
        class="btn btn-primary flex items-center space-x-2"
        on:click={handleCreate}
      >
        <Plus size={18} />
        <span>Add Product</span>
      </button>
    </div>
  </div>

  <!-- Products Table -->
  <div class="card">
    <div class="table-container">
      {#if loading}
        <div class="flex items-center justify-center py-12">
          <div class="spinner mr-3"></div>
          <span class="text-gray-600 dark:text-gray-400">Loading products...</span>
        </div>
      {:else if products.length === 0}
        <div class="text-center py-12">
          <Package class="mx-auto text-gray-400 dark:text-gray-500 mb-4" size={48} />
          <h3 class="text-lg font-medium text-gray-900 dark:text-gray-50 mb-2">No products found</h3>
          <p class="text-gray-600 dark:text-gray-400 mb-4">Get started by creating your first product.</p>
          <button class="btn btn-primary flex items-center space-x-2 mx-auto" on:click={handleCreate}>
            <Plus size={18} />
            <span>Add Product</span>
          </button>
        </div>
      {:else}
        <table class="table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Description</th>
              <th>Version</th>
              <th class="text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {#each products as product}
              <tr class="hover:bg-gray-50 dark:hover:bg-gray-800">
                <td class="font-medium text-gray-900 dark:text-gray-50">{product.name}</td>
                <td class="text-gray-600 dark:text-gray-400">{product.description || '-'}</td>
                <td class="text-gray-900 dark:text-gray-50">{product.version}</td>
                <td class="text-right">
                  <div class="flex items-center justify-end space-x-2">
                    <button
                      class="p-1 text-gray-400 dark:text-gray-500 hover:text-blue-500 rounded"
                      on:click={() => handleEdit(product)}
                      title="Edit product"
                    >
                      <Edit size={16} />
                    </button>
                    <button
                      class="p-1 text-gray-400 dark:text-gray-500 hover:text-red-500 rounded"
                      on:click={() => handleDelete(product)}
                      title="Delete product"
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
    {#if totalPages > 1}
      <div class="flex items-center justify-between px-6 py-4 border-t border-gray-200 dark:border-gray-700">
        <div class="flex items-center space-x-4">
          <div class="text-sm text-gray-600 dark:text-gray-400">
            Showing {Math.min((currentPage - 1) * pageSize + 1, products.length)} to {Math.min(currentPage * pageSize, products.length)} of {products.length} products
          </div>
        </div>

        <div class="flex items-center space-x-2">
          <button
            class="btn btn-secondary"
            disabled={currentPage === 1}
            on:click={() => loadProducts(currentPage - 1)}
            title="Previous page"
          >
            ‹
          </button>

          <span class="px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-300">
            Page {currentPage} of {totalPages}
          </span>

          <button
            class="btn btn-secondary"
            disabled={currentPage === totalPages}
            on:click={() => loadProducts(currentPage + 1)}
            title="Next page"
          >
            ›
          </button>
        </div>
      </div>
    {/if}
  </div>
</div>

<!-- Create Product Modal -->
<Modal bind:open={showCreateModal} title="Create New Product" onClose={() => showCreateModal = false}>
  <div class="space-y-4">
    <p>Product form component would go here</p>
  </div>
  <div slot="footer" class="flex justify-end space-x-3">
    <button class="btn btn-secondary" on:click={() => showCreateModal = false}>Cancel</button>
    <button class="btn btn-primary" on:click={handleFormSuccess}>Create</button>
  </div>
</Modal>

<!-- Edit Product Modal -->
<Modal bind:open={showEditModal} title="Edit Product" onClose={() => showEditModal = false}>
  <div class="space-y-4">
    <p>Product form component would go here</p>
  </div>
  <div slot="footer" class="flex justify-end space-x-3">
    <button class="btn btn-secondary" on:click={() => showEditModal = false}>Cancel</button>
    <button class="btn btn-primary" on:click={handleFormSuccess}>Update</button>
  </div>
</Modal>

<!-- Delete Confirmation Modal -->
<Modal bind:open={showDeleteModal} title="Delete Product" size="sm">
  <div class="space-y-4">
    <div class="flex items-start space-x-3">
      <div class="flex-shrink-0">
        <div class="w-10 h-10 bg-red-100 dark:bg-red-900/20 rounded-full flex items-center justify-center">
          <Trash2 class="text-red-600 dark:text-red-400" size={20} />
        </div>
      </div>
      <div class="flex-1">
        <h3 class="text-lg font-medium text-gray-900 dark:text-gray-50">Delete Product</h3>
        <p class="text-gray-600 dark:text-gray-400 mt-1">
          Are you sure you want to delete <strong>{selectedProduct?.name}</strong>?
          This action cannot be undone.
        </p>
      </div>
    </div>
  </div>

  <div slot="footer" class="flex justify-end space-x-3">
    <button class="btn btn-secondary" on:click={() => showDeleteModal = false}>Cancel</button>
    <button class="btn btn-danger" on:click={confirmDelete}>Delete Product</button>
  </div>
</Modal>