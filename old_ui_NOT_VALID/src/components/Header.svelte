<script lang="ts">
  import { Sun, Moon, User, FileText, LogOut } from 'lucide-svelte';
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { toast } from 'svelte-french-toast';
  import { authApi } from '$lib/api';

  let theme: 'light' | 'dark' = 'dark';
  let currentUser: any = null;
  let showUserMenu = false;

  // Initialize theme and user on mount
  onMount(async () => {
    // Check for saved theme preference or default to dark
    const savedTheme = localStorage.getItem('theme') as 'light' | 'dark' | null;
    theme = savedTheme || 'dark';
    applyTheme(theme);

    // Load current user info only if token exists
    const token = sessionStorage.getItem('access_token');
    if (token) {
      await loadCurrentUser();
    }
  });

  async function loadCurrentUser() {
    try {
      currentUser = await authApi.getCurrentUser();
    } catch (error) {
      console.error('Failed to load user info:', error);
      // If we can't get user info, token might be invalid
      handleLogout();
    }
  }

  function toggleTheme() {
    theme = theme === 'light' ? 'dark' : 'light';
    applyTheme(theme);
    localStorage.setItem('theme', theme);
  }

  function applyTheme(newTheme: 'light' | 'dark') {
    const root = document.documentElement;
    if (newTheme === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
  }

  async function handleLogout() {
    try {
      await authApi.logout();
    } catch (error) {
      console.error('Logout error:', error);
    }

    // Clear tokens and redirect to login
    sessionStorage.removeItem('access_token');
    sessionStorage.removeItem('refresh_token');
    toast.success('Logged out successfully');
    goto('/login');
  }
</script>

<!-- Top Header -->
<header class="fixed top-0 left-0 right-0 z-50 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 px-4 sm:px-6 lg:px-8">
  <div class="flex items-center justify-between h-16">
    <!-- Left side - Logo -->
    <div class="flex items-center space-x-3">
      <div class="p-2 rounded-lg bg-blue-500 text-white">
        <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M10 1L3 7v10a2 2 0 002 2h10a2 2 0 002-2V7l-7-6zM5 9a1 1 0 011-1h8a1 1 0 110 2H6a1 1 0 01-1-1zm0 4a1 1 0 011-1h8a1 1 0 110 2H6a1 1 0 01-1-1z" clip-rule="evenodd"></path>
        </svg>
      </div>
      <div>
        <h1 class="text-lg font-bold font-elounda bg-gradient-to-r from-yellow-500 via-yellow-400 to-green-500 bg-clip-text text-transparent">Sigma Permit</h1>
        <p class="text-xs text-gray-500 dark:text-gray-400">License Management</p>
      </div>
    </div>

    <!-- Right side - Theme toggle, API docs, and user profile -->
    <div class="flex items-center space-x-4">
      <!-- Theme Toggle -->
      <button
        on:click={toggleTheme}
        class="p-2 rounded-lg bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
        aria-label="Toggle theme"
      >
        {#if theme === 'light'}
          <Moon size={20} />
        {:else}
          <Sun size={20} />
        {/if}
      </button>

      <!-- API Documentation -->
      <a
        href="/docs"
        target="_blank"
        rel="noopener noreferrer"
        class="p-2 rounded-lg bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
        aria-label="API Documentation"
        title="Open API Documentation"
      >
        <FileText size={20} />
      </a>

      <!-- User Profile Dropdown -->
      <div class="relative">
        <button
          on:click={() => showUserMenu = !showUserMenu}
          class="flex items-center space-x-3 p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
        >
          <div class="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
            <User class="text-white" size={16} />
          </div>
          <div class="hidden sm:block text-left">
            <p class="text-sm font-medium text-gray-900 dark:text-gray-50">
              {currentUser?.full_name || currentUser?.username || 'User'}
            </p>
            <p class="text-xs text-gray-500 dark:text-gray-400">
              {currentUser?.is_superuser ? 'Administrator' : 'User'}
            </p>
          </div>
        </button>

        <!-- User Menu Dropdown -->
        {#if showUserMenu}
          <div class="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 rounded-md shadow-lg border border-gray-200 dark:border-gray-700 z-50">
            <div class="py-1">
              <div class="px-4 py-2 border-b border-gray-200 dark:border-gray-700">
                <p class="text-sm font-medium text-gray-900 dark:text-gray-50">
                  {currentUser?.full_name || currentUser?.username}
                </p>
                <p class="text-xs text-gray-500 dark:text-gray-400">
                  {currentUser?.email}
                </p>
              </div>
              <button
                on:click={handleLogout}
                class="flex items-center w-full px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                <LogOut size={16} class="mr-2" />
                Sign out
              </button>
            </div>
          </div>
        {/if}
      </div>

      <!-- Click outside to close menu -->
      {#if showUserMenu}
        <div class="fixed inset-0 z-40" on:click={() => showUserMenu = false}></div>
      {/if}
    </div>
  </div>
</header>

<style>
  @font-face {
    font-family: 'Elounda';
    src: url('/Elounda-Regular.otf') format('opentype');
    font-weight: normal;
    font-style: normal;
  }

  .font-elounda {
    font-family: 'Elounda', serif;
  }
</style>
