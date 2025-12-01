<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { toast } from 'svelte-french-toast';
  import { Loader, Lock, User, Eye, EyeOff } from 'lucide-svelte';

  import { authApi } from '$lib/api';

  let username = '';
  let password = '';
  let showPassword = false;
  let loading = false;
  let errors: Record<string, string> = {};

  onMount(() => {
    // Check if user is already logged in
    const token = sessionStorage.getItem('access_token');
    const refreshToken = sessionStorage.getItem('refresh_token');
    if (token && refreshToken) {
      goto('/');
    }
  });

  async function handleSubmit() {
    // Reset errors
    errors = {};

    // Basic validation
    if (!username.trim()) {
      errors.username = 'Username is required';
      return;
    }

    if (!password.trim()) {
      errors.password = 'Password is required';
      return;
    }

    try {
      loading = true;

      const response = await authApi.login(username.trim(), password);

      // Store tokens in sessionStorage
      sessionStorage.setItem('access_token', response.access_token);
      sessionStorage.setItem('refresh_token', response.refresh_token);

      toast.success('Login successful!');

      // Redirect to home page
      goto('/');

    } catch (error: any) {
      console.error('Login error:', error);

      // Handle different error types
      if (error.message && error.message.includes('401')) {
        toast.error('Invalid username or password');
      } else if (error.message && error.message.includes('detail')) {
        try {
          const errorData = JSON.parse(error.message);
          if (errorData.detail) {
            toast.error(errorData.detail);
          }
        } catch {
          toast.error('Login failed. Please try again.');
        }
      } else {
        toast.error('Login failed. Please try again.');
      }
    } finally {
      loading = false;
    }
  }
</script>

<svelte:head>
  <title>Login - Sigma Permit</title>
</svelte:head>

<div class="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 py-12 px-4 sm:px-6 lg:px-8">
  <div class="max-w-md w-full space-y-8">
    <!-- Header -->
    <div class="text-center">
      <div class="mx-auto h-12 w-12 bg-blue-600 rounded-full flex items-center justify-center">
        <Lock class="h-6 w-6 text-white" />
      </div>
      <h2 class="mt-6 text-3xl font-extrabold text-gray-900 dark:text-gray-50">
        Sign in to your account
      </h2>
      <p class="mt-2 text-sm text-gray-600 dark:text-gray-400">
        Access the Sigma Permit management system
      </p>
    </div>

    <!-- Login Form -->
    <form class="mt-8 space-y-6" on:submit|preventDefault={handleSubmit}>
      <div class="space-y-4">
        <!-- Username Field -->
        <div>
          <label for="username" class="form-label">Username</label>
          <div class="relative">
            <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <User class="h-5 w-5 text-gray-400" />
            </div>
            <input
              id="username"
              name="username"
              type="text"
              autocomplete="username"
              required
              class="form-input"
              style="padding-left: 2.5rem"
              placeholder="Username or Email"
              bind:value={username}
            />
          </div>
          {#if errors.username}
            <p class="mt-1 text-sm text-red-600 dark:text-red-400">{errors.username}</p>
          {/if}
        </div>

        <!-- Password Field -->
        <div>
          <label for="password" class="form-label">Password</label>
          <div class="relative">
            <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Lock class="h-5 w-5 text-gray-400" />
            </div>
            {#if showPassword}
              <input
                id="password"
                name="password"
                type="text"
                autocomplete="current-password"
                required
                class="form-input pr-12"
                style="padding-left: 2.5rem"
                placeholder="Password"
                bind:value={password}
              />
            {:else}
              <input
                id="password"
                name="password"
                type="password"
                autocomplete="current-password"
                required
                class="form-input pr-12"
                style="padding-left: 2.5rem"
                placeholder="Password"
                bind:value={password}
              />
            {/if}
            <button
              type="button"
              class="absolute inset-y-0 right-0 pr-3 flex items-center hover:bg-gray-100 dark:hover:bg-gray-700 rounded-r-lg transition-colors"
              on:click={() => showPassword = !showPassword}
              aria-label={showPassword ? "Hide password" : "Show password"}
            >
              {#if showPassword}
                <EyeOff class="h-5 w-5 text-gray-400 hover:text-gray-600" />
              {:else}
                <Eye class="h-5 w-5 text-gray-400 hover:text-gray-600" />
              {/if}
            </button>
          </div>
          {#if errors.password}
            <p class="mt-1 text-sm text-red-600 dark:text-red-400">{errors.password}</p>
          {/if}
        </div>
      </div>

      <!-- Submit Button -->
      <div>
        <button
          type="submit"
          disabled={loading}
          class="btn btn-primary w-full flex items-center justify-center space-x-2"
        >
          {#if loading}
            <Loader size={16} class="animate-spin" />
            <span>Signing in...</span>
          {:else}
            <span>Sign in</span>
          {/if}
        </button>
      </div>

      <!-- Default Credentials Info -->
      <div class="text-center">
        <div class="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-md p-4">
          <div class="text-sm text-blue-800 dark:text-blue-200">
            <strong>Default Admin Credentials:</strong><br>
            Username: <code class="bg-blue-100 dark:bg-blue-800 px-1 rounded">admin</code><br>
            Password: <code class="bg-blue-100 dark:bg-blue-800 px-1 rounded">admin123</code>
          </div>
        </div>
      </div>
    </form>
  </div>
</div>

<style>
  /* Additional styles if needed */
</style>
