<script lang="ts">
  import { page } from '$app/stores';
  import { createEventDispatcher } from 'svelte';
  import { writable } from 'svelte/store';
  import {
    Home,
    Building,
    FileText,
    Key,
    Shield,
    Users,
    Menu,
    X,
    ChevronLeft,
    ChevronRight,
    Package,
    CreditCard,
    Settings,
    UserCheck
  } from 'lucide-svelte';

  export let sidebarOpen = false;
  export let sidebarCollapsed = false;

  const dispatch = createEventDispatcher();

  // Track expanded menu names - collapsed by default
  const expandedMenusStore = writable<string[]>([]);

  // Reactive variable for template use
  let expandedMenus: string[] = [];
  expandedMenusStore.subscribe(value => expandedMenus = value);

  const navigation = [
    { name: 'Dashboard', href: '/', icon: Home },
    {
      name: 'Tenants',
      href: '/tenants',
      icon: Building
    },
    {
      name: 'Licensing',
      icon: Key,
      defaultChild: '/licenses',
      children: [
        { name: 'Templates', href: '/templates', icon: FileText },
        { name: 'Licenses', href: '/licenses', icon: Key },
        { name: 'Master Keys', href: '/master-keys', icon: Shield },
        { name: 'Validation', href: '/validate', icon: Shield }
      ]
    },
    {
      name: 'Subscriptions',
      icon: Package,
      defaultChild: '/subscriptions',
      children: [
        { name: 'Products', href: '/products', icon: Package },
        { name: 'Plans', href: '/plans', icon: CreditCard },
        { name: 'Features', href: '/features', icon: Settings },
        { name: 'Subscriptions', href: '/subscriptions', icon: UserCheck }
      ]
    },
    {
      name: 'Identity & Access',
      icon: Users,
      defaultChild: '/users',
      children: [
        { name: 'Users', href: '/users', icon: Users }
      ]
    }
  ];

  function closeSidebar() {
    sidebarOpen = false;
  }

  function toggleCollapse() {
    sidebarCollapsed = !sidebarCollapsed;
    dispatch('toggleCollapse', { collapsed: sidebarCollapsed });
  }

  function toggleMenu(menuName: string) {
    expandedMenusStore.update(current => {
      if (current.includes(menuName)) {
        return current.filter(name => name !== menuName);
      } else {
        return [...current, menuName];
      }
    });
  }

  function isMenuExpanded(menuName: string): boolean {
    return expandedMenus.includes(menuName);
  }

  function hasActiveChild(menu: any): boolean {
    if (!menu.children) return false;
    return menu.children.some((child: any) => $page.url.pathname === child.href);
  }

  function isChildActive(child: any, menu: any): boolean {
    // If the child matches the current URL, it's active
    if ($page.url.pathname === child.href) return true;

    // If the menu is expanded and this is the default child, highlight it
    if (isMenuExpanded(menu.name) && menu.defaultChild === child.href) {
      // Only highlight default if no other child is active
      return !menu.children.some((c: any) => $page.url.pathname === c.href);
    }

    return false;
  }
</script>

<!-- Sidebar -->
<div
  class="fixed top-16 left-0 z-40 h-[calc(100vh-4rem)] bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700 transform transition-all duration-300 ease-in-out flex flex-col {sidebarCollapsed ? 'w-16' : 'w-64'}"
>
  <!-- Collapse Button -->
  <div class="px-2 mb-4">
    <button
      on:click={toggleCollapse}
      class="w-full flex items-center justify-center p-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
      title={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
    >
      {#if sidebarCollapsed}
        <ChevronRight size={20} />
      {:else}
        <ChevronLeft size={20} />
      {/if}
    </button>
  </div>

  <!-- Navigation -->
  <nav class="px-2 flex-1">
    <ul class="space-y-2">
      {#each navigation as item}
        <li>
          {#if item.children}
            <!-- Parent menu item with children -->
            <div
              class="w-full flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-colors duration-200 cursor-pointer {(hasActiveChild(item) || isMenuExpanded(item.name))
                ? 'bg-blue-500 text-white'
                : 'text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-gray-50'}"
              on:click={() => toggleMenu(item.name)}
              role="button"
              tabindex="0"
              on:keydown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggleMenu(item.name); } }}
              title={sidebarCollapsed ? item.name : ''}
            >
              <svelte:component this={item.icon} size={18} class="{sidebarCollapsed ? '' : 'mr-3'}" />
              {#if !sidebarCollapsed}
                <span class="flex-1 text-left">{item.name}</span>
                <ChevronRight
                  size={16}
                  class="transition-transform duration-200 {isMenuExpanded(item.name) ? 'rotate-90' : ''}"
                />
              {/if}
            </div>

            <!-- Child menu items -->
            {#if !sidebarCollapsed && isMenuExpanded(item.name)}
              <ul class="ml-6 mt-1 space-y-1">
                {#each item.children as child}
                  <li>
                    <a
                      href={child.href}
                      class="flex items-center px-4 py-2 text-sm font-medium rounded-lg transition-colors duration-200 {isChildActive(child, item)
                        ? 'bg-blue-600 text-white'
                        : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-gray-50'}"
                      on:click={closeSidebar}
                      title={sidebarCollapsed ? child.name : ''}
                    >
                      <svelte:component this={child.icon} size={16} class="mr-3" />
                      {child.name}
                    </a>
                  </li>
                {/each}
              </ul>
            {/if}
          {:else}
            <!-- Regular menu item -->
            <a
              href={item.href}
              class="flex items-center {sidebarCollapsed ? 'justify-center px-2' : 'px-4'} py-3 text-sm font-medium rounded-lg transition-colors duration-200 {$page.url.pathname === item.href
                ? 'bg-blue-500 text-white'
                : 'text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-gray-50'}"
              on:click={closeSidebar}
              title={sidebarCollapsed ? item.name : ''}
            >
              <svelte:component this={item.icon} size={18} class="{sidebarCollapsed ? '' : 'mr-3'}" />
              {#if !sidebarCollapsed}
                {item.name}
              {/if}
            </a>
          {/if}
        </li>
      {/each}
    </ul>
  </nav>

  <!-- Footer -->
  <div class="p-2 border-t border-gray-200 dark:border-gray-700 flex-shrink-0">
    <div class="text-center">
      {#if !sidebarCollapsed}
        <p class="text-xs text-gray-500 dark:text-gray-400">Sigma Permit v1.0.0</p>
      {:else}
        <p class="text-xs text-gray-500 dark:text-gray-400">v1.0.0</p>
      {/if}
    </div>
  </div>
</div>

<!-- Mobile backdrop -->
{#if sidebarOpen}
  <div
    class="lg:hidden fixed inset-0 z-30 bg-black bg-opacity-50"
    on:click={closeSidebar}
  ></div>
{/if}
