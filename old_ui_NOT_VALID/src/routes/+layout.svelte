<script lang="ts">
  import '../app.css';
  import Navigation from '$components/Navigation.svelte';
  import Header from '$components/Header.svelte';
  import { Toaster } from 'svelte-french-toast';
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { page } from '$app/stores';

  let sidebarOpen = false;
  let sidebarCollapsed = false;
  let isAuthenticated = false;
  let isLoading = true;

  onMount(() => {
    // Check authentication status
    checkAuth();

    // Listen for page changes to re-check auth
    const unsubscribe = page.subscribe(() => {
      checkAuth();
    });

    return unsubscribe;
  });

  function checkAuth() {
    const token = sessionStorage.getItem('access_token');
    isAuthenticated = !!token;
    isLoading = false;

    // Redirect to login if not authenticated and not on login page
    if (!isAuthenticated && !$page.url.pathname.startsWith('/login')) {
      goto('/login');
    }

    // Redirect to home if authenticated and on login page
    if (isAuthenticated && $page.url.pathname === '/login') {
      goto('/');
    }
  }

  function handleToggleCollapse(event: CustomEvent) {
    sidebarCollapsed = event.detail.collapsed;
  }
</script>

{#if isLoading}
  <!-- Loading state -->
  <div class="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
    <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
  </div>
{:else if isAuthenticated}
  <!-- Authenticated layout -->
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900">
    <!-- Top Header - Fixed at top of browser -->
    <Header />

    <!-- Navigation Sidebar - Below header -->
    <Navigation bind:sidebarOpen {sidebarCollapsed} on:toggleCollapse={handleToggleCollapse} />

    <!-- Main Content Area - Below header with proper spacing -->
    <div class="transition-all duration-300 ease-in-out {sidebarCollapsed ? 'lg:pl-16' : 'lg:pl-64'}">
      <!-- Add top padding to account for fixed header -->
      <div class="pt-16">
        <main class="min-h-screen">
          <div class="p-4 sm:p-6 lg:p-8">
            <slot />
          </div>
        </main>
      </div>
    </div>

    <!-- Toast Notifications -->
    <Toaster
      position="bottom-right"
      toastOptions={{
        duration: 3000,
        style: `
          background: #1f2937;
          color: #f9fafb;
          border: 1px solid #374151;
          border-radius: 8px;
          box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
          max-width: 400px;
        `,
        iconTheme: {
          primary: '#3b82f6',
          secondary: '#1f2937'
        }
      }}
    />
  </div>
{:else}
  <!-- Unauthenticated layout (login page) -->
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900">
    <main class="min-h-screen">
      <slot />
    </main>

    <!-- Toast Notifications -->
    <Toaster />
  </div>
{/if}

<style>
  :global(html) {
    font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  }

  :global(body) {
    @apply antialiased;
  }
</style>
