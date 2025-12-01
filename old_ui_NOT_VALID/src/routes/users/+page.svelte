<script lang="ts">
  import { onMount } from 'svelte';
  import { toast } from 'svelte-french-toast';
  import {
    Users,
    Plus,
    Edit,
    Trash2,
    Search,
    Shield,
    ShieldCheck,
    UserCheck,
    UserX,
    RefreshCw
  } from 'lucide-svelte';

  import { authApi } from '$lib/api';
  import Modal from '$components/Modal.svelte';
  import UserForm from '$components/UserForm.svelte';

  let users: any[] = [];
  let loading = true;
  let searchQuery = '';
  let currentPage = 1;
  let totalPages = 1;
  let pageSize = 10;

  // Modal states
  let showCreateModal = false;
  let showEditModal = false;
  let showDeleteModal = false;
  let selectedUser: any = null;

  onMount(async () => {
    await loadUsers();
  });

  async function loadUsers(page = 1) {
    try {
      loading = true;
      currentPage = page;

      const response = await authApi.getUsers((page - 1) * pageSize, pageSize);
      users = response.items || [];
      totalPages = Math.ceil((response.total || 0) / pageSize);
    } catch (error) {
      console.error('Error loading users:', error);
      toast.error('Failed to load users');
    } finally {
      loading = false;
    }
  }

  function filteredUsers() {
    if (!searchQuery) return users;
    return users.filter(user =>
      user.username.toLowerCase().includes(searchQuery.toLowerCase()) ||
      user.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (user.full_name && user.full_name.toLowerCase().includes(searchQuery.toLowerCase()))
    );
  }

  function handleCreate() {
    selectedUser = null;
    showCreateModal = true;
  }

  function handleEdit(user: any) {
    selectedUser = user;
    showEditModal = true;
  }

  function handleDelete(user: any) {
    selectedUser = user;
    showDeleteModal = true;
  }

  async function confirmDelete() {
    if (!selectedUser) return;

    try {
      await authApi.deleteUser(selectedUser.id);
      toast.success(`User "${selectedUser.username}" deleted successfully`);
      showDeleteModal = false;
      await loadUsers(currentPage);
    } catch (error) {
      console.error('Error deleting user:', error);
    }
  }

  async function handleFormSuccess() {
    showCreateModal = false;
    showEditModal = false;
    await loadUsers(currentPage);
  }
</script>

<svelte:head>
  <title>Users - Sigma Permit</title>
</svelte:head>

<div class="space-y-6">
  <!-- Header -->
  <div class="flex items-center justify-between">
    <div>
      <h1 class="text-3xl font-bold text-gray-900 dark:text-gray-50">Users</h1>
      <p class="text-gray-600 dark:text-gray-400 mt-2">Manage system users and their permissions</p>
    </div>
    <div class="flex items-center space-x-3">
      <button
        class="btn btn-primary p-2"
        on:click={() => loadUsers(currentPage)}
        disabled={loading}
        title="Refresh"
      >
        <RefreshCw size={18} class={loading ? 'animate-spin' : ''} />
      </button>
      <button
        class="btn btn-primary flex items-center space-x-2"
        on:click={handleCreate}
      >
        <Plus size={18} />
        <span>Add User</span>
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
            placeholder="Search users..."
            class="form-input w-full"
            bind:value={searchQuery}
          />
        </div>
        <div class="ml-2 p-2 text-gray-400 dark:text-gray-500">
          <Search size={18} />
        </div>
      </div>
      <div class="text-sm text-gray-600 dark:text-gray-400">
        {filteredUsers().length} of {users.length} users
      </div>
    </div>
  </div>

  <!-- Users Table -->
  <div class="card">
    <div class="table-container">
      {#if loading}
        <div class="flex items-center justify-center py-12">
          <div class="spinner mr-3"></div>
          <span class="text-gray-600 dark:text-gray-400">Loading users...</span>
        </div>
      {:else if filteredUsers().length === 0}
        <div class="text-center py-12">
          <Users class="mx-auto text-gray-400 dark:text-gray-500 mb-4" size={48} />
          <h3 class="text-lg font-medium text-gray-900 dark:text-gray-50 mb-2">No users found</h3>
          <p class="text-gray-600 dark:text-gray-400 mb-4">
            {searchQuery ? 'Try adjusting your search terms.' : 'Get started by creating your first user.'}
          </p>
          {#if !searchQuery}
            <button class="btn btn-primary flex items-center space-x-2 mx-auto" on:click={handleCreate}>
              <Plus size={18} />
              <span>Add User</span>
            </button>
          {/if}
        </div>
      {:else}
        <table class="table">
          <thead>
            <tr>
              <th>Username</th>
              <th>Email</th>
              <th>Full Name</th>
              <th>Role</th>
              <th>Status</th>
              <th>Last Login</th>
              <th class="text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {#each filteredUsers() as user}
              <tr class="hover:bg-gray-50 dark:hover:bg-gray-800">
                <td class="font-medium text-gray-900 dark:text-gray-50">{user.username}</td>
                <td class="text-gray-600 dark:text-gray-400">{user.email}</td>
                <td class="text-gray-600 dark:text-gray-400">{user.full_name || '-'}</td>
                <td>
                  {#if user.is_superuser}
                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800 dark:bg-purple-900/20 dark:text-purple-400">
                      <ShieldCheck size={12} class="mr-1" />
                      Admin
                    </span>
                  {:else}
                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400">
                      <Shield size={12} class="mr-1" />
                      User
                    </span>
                  {/if}
                </td>
                <td>
                  {#if user.is_active}
                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400">
                      <UserCheck size={12} class="mr-1" />
                      Active
                    </span>
                  {:else}
                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400">
                      <UserX size={12} class="mr-1" />
                      Inactive
                    </span>
                  {/if}
                </td>
                <td class="text-gray-600 dark:text-gray-400">
                  {user.last_login ? new Date(user.last_login).toLocaleDateString() : 'Never'}
                </td>
                <td class="text-right">
                  <div class="flex items-center justify-end space-x-2">
                    <button
                      class="p-1 text-gray-400 dark:text-gray-500 hover:text-blue-500 rounded"
                      on:click={() => handleEdit(user)}
                      title="Edit user"
                    >
                      <Edit size={16} />
                    </button>
                    <button
                      class="p-1 text-gray-400 dark:text-gray-500 hover:text-red-500 rounded"
                      on:click={() => handleDelete(user)}
                      title="Delete user"
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
            on:change={() => { currentPage = 1; loadUsers(1); }}
          >
            <option value={10}>10</option>
            <option value={20}>20</option>
            <option value={50}>50</option>
            <option value={100}>100</option>
          </select>
          <span class="text-sm text-gray-600 dark:text-gray-400">per page</span>
        </div>

        <!-- Results Info -->
        <div class="text-sm text-gray-600 dark:text-gray-400">
          Showing {Math.min((currentPage - 1) * pageSize + 1, users.length)} to {Math.min(currentPage * pageSize, users.length)} of {users.length} users
        </div>
      </div>

      <!-- Page Navigation -->
      {#if totalPages > 1}
        <div class="flex items-center space-x-2">
          <!-- First Page -->
          <button
            class="btn btn-secondary"
            disabled={currentPage === 1}
            on:click={() => loadUsers(1)}
            title="First page"
          >
            ««
          </button>

          <!-- Previous Page -->
          <button
            class="btn btn-secondary"
            disabled={currentPage === 1}
            on:click={() => loadUsers(currentPage - 1)}
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
                  on:click={() => loadUsers(pageNum)}
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
            on:click={() => loadUsers(currentPage + 1)}
            title="Next page"
          >
            ›
          </button>

          <!-- Last Page -->
          <button
            class="btn btn-secondary"
            disabled={currentPage === totalPages}
            on:click={() => loadUsers(totalPages)}
            title="Last page"
          >
            »»
          </button>
        </div>
      {/if}
    </div>
  </div>
</div>

<!-- Create User Modal -->
<Modal bind:open={showCreateModal} title="Create New User" onClose={() => showCreateModal = false}>
  <UserForm
    on:success={handleFormSuccess}
    on:cancel={() => showCreateModal = false}
  />
</Modal>

<!-- Edit User Modal -->
<Modal bind:open={showEditModal} title="Edit User" onClose={() => showEditModal = false}>
  <UserForm
    user={selectedUser}
    on:success={handleFormSuccess}
    on:cancel={() => showEditModal = false}
  />
</Modal>

<!-- Delete Confirmation Modal -->
<Modal bind:open={showDeleteModal} title="Delete User" size="sm">
  <div class="space-y-4">
    <div class="flex items-start space-x-3">
      <div class="flex-shrink-0">
        <div class="w-10 h-10 bg-red-100 dark:bg-red-900/20 rounded-full flex items-center justify-center">
          <Trash2 class="text-red-600 dark:text-red-400" size={20} />
        </div>
      </div>
      <div class="flex-1">
        <h3 class="text-lg font-medium text-gray-900 dark:text-gray-50">
          Delete User
        </h3>
        <p class="text-gray-600 dark:text-gray-400 mt-1">
          Are you sure you want to delete <strong>{selectedUser?.username}</strong>?
          This action cannot be undone.
        </p>
        <div class="mt-3 p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
          <p class="text-sm text-yellow-800 dark:text-yellow-200">
            All user data will be permanently removed from the system.
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
      Delete User
    </button>
  </div>
</Modal>
