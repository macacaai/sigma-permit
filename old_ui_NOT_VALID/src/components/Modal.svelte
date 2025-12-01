<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { fade, scale } from 'svelte/transition';
  import { X } from 'lucide-svelte';

  export let open = false;
  export let title = '';
  export let size = 'md'; // sm, md, lg, xl
  export let onClose: (() => void) | undefined = undefined;

  const dispatch = createEventDispatcher();

  function close() {
    open = false;
    if (onClose) {
      onClose();
    } else {
      dispatch('cancel');
    }
  }

  function handleBackdropClick(event: MouseEvent) {
    if (event.target === event.currentTarget) {
      close();
    }
  }

  // Handle escape key
  function handleKeydown(event: KeyboardEvent) {
    if (event.key === 'Escape') {
      close();
    }
  }

  // Size classes
  $: sizeClasses = {
    sm: 'max-w-md',
    md: 'max-w-lg',
    lg: 'max-w-2xl',
    xl: 'max-w-4xl'
  }[size] || 'max-w-lg';
</script>

<svelte:window on:keydown={handleKeydown} />

{#if open}
  <!-- Backdrop -->
  <div
    class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 dark:bg-black/70 backdrop-blur-sm"
    on:click={handleBackdropClick}
    transition:fade={{ duration: 150 }}
  >
    <!-- Modal -->
    <div
      class="w-full {sizeClasses} bg-white dark:bg-gray-900 rounded-xl shadow-2xl border border-gray-200 dark:border-gray-700 transform transition-all duration-200 scale-100 max-h-[90vh] overflow-hidden"
      transition:scale={{ duration: 150, start: 0.95 }}
    >
      <!-- Header -->
      {#if title}
        <div class="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-800/50">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-50">{title}</h3>
          <button
            class="p-2 rounded-lg text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors focus:ring-2 focus:ring-blue-500 focus:outline-none"
            on:click={close}
            aria-label="Close modal"
          >
            <X size={20} />
          </button>
        </div>
      {/if}

      <!-- Body -->
      <div class="p-6 overflow-y-auto max-h-[calc(90vh-140px)]">
        <slot />
      </div>

      <!-- Footer -->
      {#if $$slots.footer}
        <div class="flex items-center justify-end p-6 border-t border-gray-200 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-800/50 space-x-3">
          <slot name="footer" />
        </div>
      {/if}
    </div>
  </div>
{/if}

<style>
  .modal-backdrop {
    backdrop-filter: blur(4px);
  }
</style>
