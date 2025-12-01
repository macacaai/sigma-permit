<script lang="ts">
  import { onMount } from 'svelte';
  import { toast } from 'svelte-french-toast';
  import {
    Building,
    FileText,
    Key,
    TrendingUp,
    Users,
    Activity
  } from 'lucide-svelte';

  import { tenantApi, templateApi, licenseApi, healthApi } from '$lib/api';

  let stats = {
    tenants: { total: 0, active: 0 },
    templates: { total: 0, active: 0 },
    licenses: { total: 0, recent: 0 },
  };

  let loading = true;
  let health = { status: 'unknown' };

  onMount(async () => {
    await loadDashboardData();
  });

  async function loadDashboardData() {
    try {
      loading = true;

      // Load health status
      try {
        const healthData = await healthApi.check();
        health = { status: 'healthy' };
      } catch (error) {
        health = { status: 'unhealthy' };
      }

      // Load stats in parallel (using size=1 to get totals without fetching all data)
      const [tenantsRes, templatesRes, licensesRes] = await Promise.allSettled([
        tenantApi.getTenants(1, 1),
        templateApi.getTemplates(1, 1),
        licenseApi.getLicenses(1, 1)
      ]);

      // Process tenants
      if (tenantsRes.status === 'fulfilled') {
        stats.tenants.total = tenantsRes.value.total || 0;
        // To get active count, we'd need a separate endpoint or fetch all data
        // For now, we'll just show total and note that active count requires full data
        stats.tenants.active = 0; // Placeholder - would need separate API call
      }

      // Process templates
      if (templatesRes.status === 'fulfilled') {
        stats.templates.total = templatesRes.value.total || 0;
        stats.templates.active = 0; // Placeholder - would need separate API call
      }

      // Process licenses
      if (licensesRes.status === 'fulfilled') {
        stats.licenses.total = licensesRes.value.total || 0;
        stats.licenses.recent = 0; // Placeholder - would need separate API call for date filtering
      }

    } catch (error) {
      console.error('Error loading dashboard data:', error);
      toast.error('Failed to load dashboard data');
    } finally {
      loading = false;
    }
  }
</script>

<svelte:head>
  <title>Dashboard - Sigma Permit</title>
</svelte:head>

<div class="space-y-8">
  <!-- Header -->
  <div class="flex items-center justify-between">
    <div>
      <h1 class="text-3xl font-bold text-gray-900 dark:text-gray-50">Dashboard</h1>
      <p class="text-gray-600 dark:text-gray-400 mt-2">Welcome to Sigma Permit - Your License Management System</p>
    </div>
    <div class="flex items-center space-x-2">
      <div class="flex items-center space-x-2 px-3 py-1 rounded-full text-sm {health.status === 'healthy' ? 'bg-green-500/10 text-green-600' : 'bg-red-500/10 text-red-600'}">
        <Activity size={16} />
        <span class="capitalize">{health.status}</span>
      </div>
    </div>
  </div>

  <!-- Stats Cards -->
  {#if loading}
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {#each Array(4) as _}
        <div class="card card-hover p-6">
          <div class="animate-pulse">
            <div class="h-4 bg-gray-300 dark:bg-gray-600 rounded w-3/4 mb-2"></div>
            <div class="h-8 bg-gray-300 dark:bg-gray-600 rounded w-1/2"></div>
          </div>
        </div>
      {/each}
    </div>
  {:else}
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <!-- Tenants Card -->
      <div class="card card-hover p-6">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-gray-600 dark:text-gray-400">Total Tenants</p>
            <p class="text-3xl font-bold text-gray-900 dark:text-gray-50">{stats.tenants.total}</p>
            <p class="text-sm text-green-600">{stats.tenants.active} active</p>
          </div>
          <div class="p-3 rounded-lg bg-blue-500/10">
            <Building class="text-blue-600" size={24} />
          </div>
        </div>
      </div>

      <!-- Templates Card -->
      <div class="card card-hover p-6">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-gray-600 dark:text-gray-400">Templates</p>
            <p class="text-3xl font-bold text-gray-900 dark:text-gray-50">{stats.templates.total}</p>
            <p class="text-sm text-green-600">{stats.templates.active} active</p>
          </div>
          <div class="p-3 rounded-lg bg-purple-500/10">
            <FileText class="text-purple-600" size={24} />
          </div>
        </div>
      </div>

      <!-- Licenses Card -->
      <div class="card card-hover p-6">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-gray-600 dark:text-gray-400">Total Licenses</p>
            <p class="text-3xl font-bold text-gray-900 dark:text-gray-50">{stats.licenses.total}</p>
            <p class="text-sm text-blue-600">+{stats.licenses.recent} this month</p>
          </div>
          <div class="p-3 rounded-lg bg-indigo-500/10">
            <Key class="text-indigo-600" size={24} />
          </div>
        </div>
      </div>

      <!-- System Health Card -->
      <div class="card card-hover p-6">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-gray-600 dark:text-gray-400">System Status</p>
            <p class="text-3xl font-bold text-gray-900 dark:text-gray-50 capitalize">{health.status}</p>
            <p class="text-sm text-gray-500 dark:text-gray-400">All systems operational</p>
          </div>
          <div class="p-3 rounded-lg {health.status === 'healthy' ? 'bg-green-500/10' : 'bg-red-500/10'}">
            <Activity class="{health.status === 'healthy' ? 'text-green-600' : 'text-red-600'}" size={24} />
          </div>
        </div>
      </div>
    </div>
  {/if}

  <!-- Quick Actions -->
  <div class="card p-6">
    <h2 class="text-xl font-semibold text-gray-900 dark:text-gray-50 mb-4">Quick Actions</h2>
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <a href="/tenants" class="flex items-center p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
        <Building class="text-blue-500 mr-3" size={20} />
        <div>
          <h3 class="font-medium text-gray-900 dark:text-gray-50">Manage Tenants</h3>
          <p class="text-sm text-gray-600 dark:text-gray-400">Create and manage tenant organizations</p>
        </div>
      </a>

      <a href="/templates" class="flex items-center p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
        <FileText class="text-purple-500 mr-3" size={20} />
        <div>
          <h3 class="font-medium text-gray-900 dark:text-gray-50">Manage Templates</h3>
          <p class="text-sm text-gray-600 dark:text-gray-400">Create license templates with validation</p>
        </div>
      </a>

      <a href="/licenses" class="flex items-center p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
        <Key class="text-indigo-500 mr-3" size={20} />
        <div>
          <h3 class="font-medium text-gray-900 dark:text-gray-50">Issue Licenses</h3>
          <p class="text-sm text-gray-600 dark:text-gray-400">Create and manage license keys</p>
        </div>
      </a>

      <a href="/docs" target="_blank" rel="noopener noreferrer" class="flex items-center p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
        <TrendingUp class="text-green-500 mr-3" size={20} />
        <div>
          <h3 class="font-medium text-gray-900 dark:text-gray-50">API Documentation</h3>
          <p class="text-sm text-gray-600 dark:text-gray-400">Explore and test API endpoints</p>
        </div>
      </a>
    </div>
  </div>

  <!-- Recent Activity -->
  <div class="card p-6">
    <h2 class="text-xl font-semibold text-gray-900 dark:text-gray-50 mb-4">Getting Started</h2>
    <div class="space-y-4">
      <div class="flex items-start space-x-3">
        <div class="flex-shrink-0 w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white text-sm font-medium">
          1
        </div>
        <div>
          <h3 class="font-medium text-gray-900 dark:text-gray-50">Create Your First Tenant</h3>
          <p class="text-sm text-gray-600 dark:text-gray-400">Start by creating a tenant organization to represent your client or department.</p>
        </div>
      </div>

      <div class="flex items-start space-x-3">
        <div class="flex-shrink-0 w-8 h-8 bg-purple-500 rounded-full flex items-center justify-center text-white text-sm font-medium">
          2
        </div>
        <div>
          <h3 class="font-medium text-gray-900 dark:text-gray-50">Set Up License Templates</h3>
          <p class="text-sm text-gray-600 dark:text-gray-400">Create reusable templates with JSON schemas to standardize your license formats.</p>
        </div>
      </div>

      <div class="flex items-start space-x-3">
        <div class="flex-shrink-0 w-8 h-8 bg-indigo-500 rounded-full flex items-center justify-center text-white text-sm font-medium">
          3
        </div>
        <div>
          <h3 class="font-medium text-gray-900 dark:text-gray-50">Issue Your First License</h3>
          <p class="text-sm text-gray-600 dark:text-gray-400">Generate license keys for your tenants using the templates you've created.</p>
        </div>
      </div>
    </div>
  </div>
</div>
