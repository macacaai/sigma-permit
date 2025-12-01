<script lang="ts">
  import { onMount } from 'svelte';
  import { api } from '$lib/api';
  import type { MasterKey } from '$lib/api';

  let masterKeys: MasterKey[] = [];
  let loading = true;
  let error = '';

  onMount(async () => {
    try {
      masterKeys = await api.get('/licenses/master-keys');
    } catch (err: any) {
      error = err.message || 'Failed to load master keys';
    } finally {
      loading = false;
    }
  });
</script>

<div class="px-4 sm:px-6 lg:px-8">
  <div class="sm:flex sm:items-center">
    <div class="sm:flex-auto">
      <h1 class="text-2xl font-semibold text-gray-900 dark:text-white">Master Keys</h1>
      <p class="mt-2 text-sm text-gray-700 dark:text-gray-300">
        View the master encryption keys used for license files.
      </p>
    </div>
  </div>

  <div class="mt-8">
    {#if loading}
      <div class="text-center py-12">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
        <p class="mt-2 text-sm text-gray-500">Loading master keys...</p>
      </div>
    {:else if error}
      <div class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md p-4">
        <div class="flex">
          <div class="ml-3">
            <h3 class="text-sm font-medium text-red-800 dark:text-red-200">Error</h3>
            <div class="mt-2 text-sm text-red-700 dark:text-red-300">{error}</div>
          </div>
        </div>
      </div>
    {:else}
      <div class="bg-white dark:bg-gray-800 shadow overflow-hidden sm:rounded-md">
        <ul role="list" class="divide-y divide-gray-200 dark:divide-gray-700">
          {#each masterKeys as key}
            <li>
              <div class="px-4 py-4 sm:px-6">
                <div class="flex items-start justify-between">
                  <div class="flex-1 min-w-0">
                    <div class="flex items-center mb-3">
                      <p class="text-sm font-medium text-gray-900 dark:text-white">
                        Key ID: {key.id}
                      </p>
                    </div>

                    <!-- Public Key Section -->
                    <div class="mb-3">
                      <div class="flex items-center justify-between mb-1">
                        <label class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">
                          Public Key
                        </label>
                        <button
                          class="text-xs text-blue-600 hover:text-blue-500 dark:text-blue-400 dark:hover:text-blue-300"
                          on:click={() => navigator.clipboard.writeText(key.public_key)}
                        >
                          Copy
                        </button>
                      </div>
                      <div class="bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-600 rounded-md p-3">
                        <code class="text-xs text-gray-800 dark:text-gray-200 break-all font-mono">
                          {key.public_key}
                        </code>
                      </div>
                    </div>

                    <!-- Private Key Section -->
                    <div class="mb-3">
                      <div class="flex items-center justify-between mb-1">
                        <label class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">
                          Private Key (Masked)
                        </label>
                        {#if key.private_key_masked !== 'Not generated'}
                          <button
                            class="text-xs text-blue-600 hover:text-blue-500 dark:text-blue-400 dark:hover:text-blue-300"
                            on:click={() => navigator.clipboard.writeText(key.private_key_masked)}
                          >
                            Copy
                          </button>
                        {/if}
                      </div>
                      <div class="bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-600 rounded-md p-3">
                        <code class="text-xs text-gray-800 dark:text-gray-200 break-all font-mono">
                          {key.private_key_masked}
                        </code>
                      </div>
                    </div>
                  </div>

                  <div class="flex-shrink-0 ml-4 text-sm text-gray-500 dark:text-gray-400">
                    <div class="text-right">
                      <div class="font-medium">Created</div>
                      <div>{new Date(key.created_at).toLocaleDateString()}</div>
                      <div class="text-xs mt-1">{new Date(key.created_at).toLocaleTimeString()}</div>
                    </div>
                  </div>
                </div>
              </div>
            </li>
          {/each}
        </ul>
        {#if masterKeys.length === 0}
          <div class="text-center py-12">
            <p class="text-sm text-gray-500 dark:text-gray-400">No master keys found.</p>
          </div>
        {/if}
      </div>
    {/if}
  </div>
</div>