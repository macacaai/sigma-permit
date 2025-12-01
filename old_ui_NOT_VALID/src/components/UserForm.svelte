<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { toast } from 'svelte-french-toast';
  import { Loader, Eye, EyeOff } from 'lucide-svelte';

  import { authApi } from '$lib/api';

  export let user: any = null; // For editing

  const dispatch = createEventDispatcher();

  let formData = {
    username: user?.username || '',
    email: user?.email || '',
    full_name: user?.full_name || '',
    password: '',
    confirmPassword: '',
    is_active: user?.is_active ?? true,
    is_superuser: user?.is_superuser ?? false,
    avatar_url: user?.avatar_url || '',
    bio: user?.bio || '',
    phone_number: user?.phone_number || ''
  };

  // Separate variables for password inputs (can't use bind:value with dynamic type)
  let passwordValue = '';
  let confirmPasswordValue = '';

  // Sync password values with formData
  $: formData.password = passwordValue;
  $: formData.confirmPassword = confirmPasswordValue;

  let loading = false;
  let errors: Record<string, string> = {};
  let showPassword = false;
  let showConfirmPassword = false;

  async function handleSubmit() {
    // Reset errors
    errors = {};

    // Basic validation
    if (!formData.username.trim()) {
      errors.username = 'Username is required';
      return;
    }

    if (!formData.email.trim()) {
      errors.email = 'Email is required';
      return;
    }

    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(formData.email)) {
      errors.email = 'Please enter a valid email address';
      return;
    }

    // Username validation
    if (!/^[a-zA-Z0-9_-]+$/.test(formData.username)) {
      errors.username = 'Username can only contain letters, numbers, underscores, and hyphens';
      return;
    }

    // Password validation for new users
    if (!user) {
      if (!formData.password) {
        errors.password = 'Password is required';
        return;
      }

      if (formData.password.length < 8) {
        errors.password = 'Password must be at least 8 characters long';
        return;
      }

      if (formData.password !== formData.confirmPassword) {
        errors.confirmPassword = 'Passwords do not match';
        return;
      }
    }

    try {
      loading = true;

      const submitData = {
        username: formData.username.trim(),
        email: formData.email.trim(),
        full_name: formData.full_name.trim() || null,
        is_active: formData.is_active,
        is_superuser: formData.is_superuser,
        avatar_url: formData.avatar_url.trim() || null,
        bio: formData.bio.trim() || null,
        phone_number: formData.phone_number.trim() || null
      };

      if (user) {
        // Update existing user
        if (formData.password) {
          (submitData as any).password = formData.password;
        }
        await authApi.updateUser(user.id, submitData);
        toast.success('User updated successfully');
      } else {
        // Create new user
        (submitData as any).password = formData.password;
        await authApi.createUser(submitData);
        toast.success('User created successfully');
      }

      dispatch('success');
    } catch (error: any) {
      console.error('Form submission error:', error);

      // Handle validation errors
      if (error.message && error.message.includes('detail')) {
        try {
          const errorData = JSON.parse(error.message);
          if (errorData.detail) {
            if (typeof errorData.detail === 'string') {
              toast.error(errorData.detail);
            } else if (Array.isArray(errorData.detail)) {
              // Handle field-specific errors
              errorData.detail.forEach((err: any) => {
                if (err.loc && err.loc.length > 1) {
                  const field = err.loc[1];
                  errors[field] = err.msg;
                }
              });
            }
          }
        } catch {
          toast.error('An error occurred while saving the user');
        }
      } else {
        toast.error('An error occurred while saving the user');
      }
    } finally {
      loading = false;
    }
  }

  function handleCancel() {
    dispatch('cancel');
  }
</script>

<form on:submit|preventDefault={handleSubmit} class="space-y-6">
  <!-- Username and Email Row -->
  <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
    <!-- Username Field -->
    <div>
      <label for="username" class="form-label">Username</label>
      <input
        type="text"
        id="username"
        class="form-input font-mono"
        placeholder="username"
        bind:value={formData.username}
        required
        disabled={!!user}
      />
      {#if errors.username}
        <p class="mt-1 text-sm text-red-600 dark:text-red-400">{errors.username}</p>
      {/if}
      <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">Unique username (letters, numbers, underscores, hyphens only)</p>
    </div>

    <!-- Email Field -->
    <div>
      <label for="email" class="form-label">Email Address</label>
      <input
        type="email"
        id="email"
        class="form-input"
        placeholder="user@example.com"
        bind:value={formData.email}
        required
      />
      {#if errors.email}
        <p class="mt-1 text-sm text-red-600 dark:text-red-400">{errors.email}</p>
      {/if}
      <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">User's email address</p>
    </div>
  </div>

  <!-- Full Name Field -->
  <div>
    <label for="full_name" class="form-label">Full Name</label>
    <input
      type="text"
      id="full_name"
      class="form-input"
      placeholder="John Doe"
      bind:value={formData.full_name}
    />
    <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">User's full display name (optional)</p>
  </div>

  <!-- Password Fields (only for new users or password changes) -->
  {#if !user || formData.password}
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <!-- Password Field -->
      <div>
        <label for="password" class="form-label">{user ? 'New Password' : 'Password'}</label>
        <div class="relative">
          {#if showPassword}
            <input
              type="text"
              id="password"
              class="form-input pr-10"
              placeholder="Enter password"
              bind:value={passwordValue}
              required={!user}
              minlength="8"
            />
          {:else}
            <input
              type="password"
              id="password"
              class="form-input pr-10"
              placeholder="Enter password"
              bind:value={passwordValue}
              required={!user}
              minlength="8"
            />
          {/if}
          <button
            type="button"
            class="absolute inset-y-0 right-0 pr-3 flex items-center"
            on:click={() => showPassword = !showPassword}
          >
            {#if showPassword}
              <EyeOff class="h-5 w-5 text-gray-400" />
            {:else}
              <Eye class="h-5 w-5 text-gray-400" />
            {/if}
          </button>
        </div>
        {#if errors.password}
          <p class="mt-1 text-sm text-red-600 dark:text-red-400">{errors.password}</p>
        {/if}
        <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">Minimum 8 characters</p>
      </div>

      <!-- Confirm Password Field -->
      <div>
        <label for="confirmPassword" class="form-label">Confirm Password</label>
        <div class="relative">
          {#if showConfirmPassword}
            <input
              type="text"
              id="confirmPassword"
              class="form-input pr-10"
              placeholder="Confirm password"
              bind:value={confirmPasswordValue}
              required={!user}
              minlength="8"
            />
          {:else}
            <input
              type="password"
              id="confirmPassword"
              class="form-input pr-10"
              placeholder="Confirm password"
              bind:value={confirmPasswordValue}
              required={!user}
              minlength="8"
            />
          {/if}
          <button
            type="button"
            class="absolute inset-y-0 right-0 pr-3 flex items-center"
            on:click={() => showConfirmPassword = !showConfirmPassword}
          >
            {#if showConfirmPassword}
              <EyeOff class="h-5 w-5 text-gray-400" />
            {:else}
              <Eye class="h-5 w-5 text-gray-400" />
            {/if}
          </button>
        </div>
        {#if errors.confirmPassword}
          <p class="mt-1 text-sm text-red-600 dark:text-red-400">{errors.confirmPassword}</p>
        {/if}
        <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">Re-enter password to confirm</p>
      </div>
    </div>
  {/if}

  <!-- Profile Fields -->
  <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
    <!-- Avatar URL Field -->
    <div>
      <label for="avatar_url" class="form-label">Avatar URL</label>
      <input
        type="url"
        id="avatar_url"
        class="form-input"
        placeholder="https://example.com/avatar.jpg"
        bind:value={formData.avatar_url}
      />
      <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">URL to user's profile picture (optional)</p>
    </div>

    <!-- Phone Number Field -->
    <div>
      <label for="phone_number" class="form-label">Phone Number</label>
      <input
        type="tel"
        id="phone_number"
        class="form-input"
        placeholder="+1 (555) 123-4567"
        bind:value={formData.phone_number}
      />
      <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">User's phone number (optional)</p>
    </div>
  </div>

  <!-- Bio Field -->
  <div>
    <label for="bio" class="form-label">Bio</label>
    <textarea
      id="bio"
      class="form-input"
      placeholder="Tell us about yourself..."
      bind:value={formData.bio}
      rows="3"
    ></textarea>
    <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">Short biography or description (optional)</p>
  </div>

  <!-- Permissions -->
  <div class="space-y-4">
    <h3 class="text-lg font-medium text-gray-900 dark:text-gray-50">Permissions</h3>

    <!-- Active Status -->
    <div>
      <label class="form-label">Account Status</label>
      <div class="flex items-center space-x-3">
        <input
          type="checkbox"
          id="is_active"
          class="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
          bind:checked={formData.is_active}
        />
        <label for="is_active" class="text-sm font-medium text-gray-700 dark:text-gray-200">
          Active account
        </label>
      </div>
      <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">Inactive users cannot log in to the system</p>
    </div>

    <!-- Superuser Status -->
    <div>
      <label class="form-label">Administrator Access</label>
      <div class="flex items-center space-x-3">
        <input
          type="checkbox"
          id="is_superuser"
          class="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
          bind:checked={formData.is_superuser}
        />
        <label for="is_superuser" class="text-sm font-medium text-gray-700 dark:text-gray-200">
          Superuser (Administrator)
        </label>
      </div>
      <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">Administrators have full access to all system features and user management</p>
    </div>
  </div>

  <!-- Form Actions -->
  <div class="flex justify-end space-x-3 pt-4 border-t border-gray-200 dark:border-gray-700">
    <button
      type="button"
      class="btn btn-secondary"
      on:click={handleCancel}
      disabled={loading}
    >
      Cancel
    </button>
    <button
      type="submit"
      class="btn btn-primary flex items-center space-x-2"
      disabled={loading}
    >
      {#if loading}
        <Loader size={16} class="animate-spin" />
        <span>{user ? 'Updating...' : 'Creating...'}</span>
      {:else}
        <span>{user ? 'Update User' : 'Create User'}</span>
      {/if}
    </button>
  </div>
</form>
