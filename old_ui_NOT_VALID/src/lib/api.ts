import { toast } from 'svelte-french-toast';

// Base API configuration
const API_BASE = '/api';

// Generic API response type
export interface ApiResponse<T> {
  items?: T[];
  total?: number;
  page?: number;
  size?: number;
  data?: T;
  message?: string;
}

// Generic error type
export interface ApiError {
  detail: string;
  errors?: Record<string, string[]>;
}

// Master Key type
export interface MasterKey {
  id: string;
  public_key: string;
  private_key_masked: string;
  created_at: string;
}

// HTTP methods
class ApiClient {
  public baseURL: string;

  constructor(baseURL: string = API_BASE) {
    this.baseURL = baseURL;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    retryOn401 = true
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;

    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...this.getAuthHeaders(),
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);

      if (!response.ok) {
        // Handle 401 Unauthorized - try to refresh token
        if (response.status === 401 && retryOn401 && this.canRefreshToken()) {
          try {
            await this.refreshAccessToken();
            // Retry the request with new token
            return this.request<T>(endpoint, options, false);
          } catch (refreshError) {
            // Refresh failed, logout user
            this.logoutUser();
            throw new Error('Your session has expired. Please login again.');
          }
        }

        // Handle other HTTP errors
        if (response.status === 401) {
          // Token is invalid and can't be refreshed
          this.logoutUser();
          throw new Error('Your session has expired. Please login again.');
        }

        const errorData: ApiError = await response.json().catch(() => ({
          detail: `HTTP ${response.status}: ${response.statusText}`
        }));

        // Show user-friendly error messages
        let errorMessage = errorData.detail || 'An error occurred';

        // Handle specific error types
        if (response.status === 403) {
          errorMessage = 'You do not have permission to perform this action.';
        } else if (response.status === 404) {
          errorMessage = 'The requested resource was not found.';
        } else if (response.status === 422) {
          errorMessage = 'Invalid data provided. Please check your input.';
        } else if (response.status >= 500) {
          errorMessage = 'Server error. Please try again later.';
        }

        // Show error toast
        toast.error(errorMessage);

        throw new Error(errorMessage);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      if (error instanceof Error && error.message.includes('HTTP')) {
        throw error; // Already handled above
      }

      toast.error('Network error occurred');
      throw new Error('Network error occurred');
    }
  }

  // GET request
  async get<T>(endpoint: string, params?: Record<string, any>): Promise<T> {
    const url = params
      ? `${endpoint}?${new URLSearchParams(params).toString()}`
      : endpoint;
    return this.request<T>(url);
  }

  // POST request
  async post<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  // POST request with FormData (for file uploads)
  async postForm<T>(endpoint: string, formData: FormData): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    
    try {
      const response = await fetch(url, {
        method: 'POST',
        body: formData,
        headers: {
          ...this.getAuthHeaders(),
          // Don't set Content-Type for FormData, let browser set it with boundary
        },
      });

      if (!response.ok) {
        const errorData: ApiError = await response.json().catch(() => ({
          detail: `HTTP ${response.status}: ${response.statusText}`
        }));

        toast.error(errorData.detail || 'An error occurred');
        throw new Error(errorData.detail || 'An error occurred');
      }

      const data = await response.json();
      return data;
    } catch (error) {
      if (error instanceof Error && error.message.includes('HTTP')) {
        throw error;
      }

      toast.error('Network error occurred');
      throw new Error('Network error occurred');
    }
  }

  // PUT request
  async put<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  // DELETE request
  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'DELETE',
    });
  }

  // Download file request
  async downloadFile(endpoint: string, filename?: string): Promise<void> {
    const url = `${this.baseURL}${endpoint}`;
    
    try {
      const response = await fetch(url, {
        headers: {
          ...this.getAuthHeaders(),
        },
      });

      if (!response.ok) {
        const errorData: ApiError = await response.json().catch(() => ({
          detail: `HTTP ${response.status}: ${response.statusText}`
        }));
        toast.error(errorData.detail || 'Download failed');
        throw new Error(errorData.detail || 'Download failed');
      }

      // Get the blob from the response
      const blob = await response.blob();
      
      // Create download link
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = filename || this.getFilenameFromResponse(response) || 'download';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      // Clean up the object URL
      window.URL.revokeObjectURL(downloadUrl);
      
      toast.success('File downloaded successfully');
    } catch (error) {
      console.error('Download error:', error);
      if (error instanceof Error && !error.message.includes('HTTP')) {
        toast.error('Download failed: ' + error.message);
      }
      throw error;
    }
  }

  public getAuthHeaders(): Record<string, string> {
    // Add auth headers if token exists
    const token = sessionStorage.getItem('access_token');
    if (token) {
      return {
        'Authorization': `Bearer ${token}`,
      };
    }
    return {};
  }

  private canRefreshToken(): boolean {
    const refreshToken = sessionStorage.getItem('refresh_token');
    return !!refreshToken;
  }

  private async refreshAccessToken(): Promise<void> {
    const refreshToken = sessionStorage.getItem('refresh_token');
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    const formData = new URLSearchParams();
    formData.append('refresh_token', refreshToken);

    const url = `${this.baseURL}/auth/refresh`;
    const response = await fetch(url, {
      method: 'POST',
      body: formData,
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });

    if (!response.ok) {
      throw new Error('Failed to refresh token');
    }

    const data = await response.json();

    // Store new tokens
    sessionStorage.setItem('access_token', data.access_token);
    sessionStorage.setItem('refresh_token', data.refresh_token);
  }

  private logoutUser(): void {
    sessionStorage.removeItem('access_token');
    sessionStorage.removeItem('refresh_token');
    // Redirect to login page
    window.location.href = '/login';
  }

  private getFilenameFromResponse(response: Response): string | null {
    const contentDisposition = response.headers.get('content-disposition');
    if (contentDisposition) {
      const match = contentDisposition.match(/filename="(.+)"/);
      if (match) {
        return match[1];
      }
    }
    return null;
  }
}

// Create API client instance
export const api = new ApiClient();

// Tenant API
export const tenantApi = {
  // Get all tenants with pagination
  getTenants: (page = 1, size = 10) =>
    api.get<ApiResponse<any>>(`/tenants?page=${page}&size=${size}`),

  // Get tenant by ID
  getTenant: (id: string) =>
    api.get<any>(`/tenants/${id}`),

  // Create tenant
  createTenant: (data: any) =>
    api.post<any>('/tenants', data),

  // Update tenant
  updateTenant: (id: string, data: any) =>
    api.put<any>(`/tenants/${id}`, data),

  // Delete tenant
  deleteTenant: (id: string) =>
    api.delete<any>(`/tenants/${id}`),
};

// Template API
export const templateApi = {
  // Get all templates with pagination
  getTemplates: (page = 1, size = 10) =>
    api.get<ApiResponse<any>>(`/templates?page=${page}&size=${size}`),

  // Get template by ID
  getTemplate: (id: string) =>
    api.get<any>(`/templates/${id}`),

  // Create template
  createTemplate: (data: any) =>
    api.post<any>('/templates', data),

  // Update template
  updateTemplate: (id: string, data: any) =>
    api.put<any>(`/templates/${id}`, data),

  // Delete template
  deleteTemplate: (id: string) =>
    api.delete<any>(`/templates/${id}`),
};

// License API
export const licenseApi = {
  // Get all licenses with pagination and optional filtering
  getLicenses: (page = 1, size = 10, tenantId?: string) => {
    const params = new URLSearchParams({ page: page.toString(), size: size.toString() });
    if (tenantId) params.append('tenant_id', tenantId);
    return api.get<ApiResponse<any>>(`/licenses?${params.toString()}`);
  },

  // Get license by ID
  getLicense: (id: string) =>
    api.get<any>(`/licenses/${id}`),

  // Create license with new API structure
  createLicense: (data: {
    tenant_id: string;
    template_id?: string;
    issued_at: string;
    validity_days: number;
    payload: any;
  }) => {
    return api.post<any>('/licenses', data);
  },

  // Update license with new API structure
  updateLicense: (id: string, data: {
    tenant_id: string;
    template_id?: string;
    issued_at: string;
    validity_days: number;
    payload: any;
  }) => {
    return api.put<any>(`/licenses/${id}`, data);
  },

  // Delete license
  deleteLicense: (id: string) =>
    api.delete<any>(`/licenses/${id}`),

  // Download license file using /issue endpoint
  downloadLicense: async (licenseKey: string) => {
    if (!licenseKey) {
      throw new Error('License key is required for download');
    }

    // Encode license key in base64
    const encodedLicenseKey = btoa(licenseKey);

    // Call the /issue endpoint with encoded license key
    return api.downloadFile(`/licenses/issue?encoded_license_key=${encodeURIComponent(encodedLicenseKey)}`);
  },

  // Validate license file
  validateFile: async (licenseKey: string, file: File) => {
    if (!licenseKey) {
      throw new Error('License key is required for validation');
    }

    if (!file) {
      throw new Error('License file is required for validation');
    }

    const formData = new FormData();
    formData.append('license_key', licenseKey);
    formData.append('file', file);

    return api.postForm<any>('/licenses/validate-file', formData);
  },

  // Generate validator code
  generateValidator: (language: string) =>
    api.get<any>(`/licenses/generate-validator?language=${language}`),
};

// Authentication API
export const authApi = {
  // Login - uses base64 encoded credentials
  login: async (username: string, password: string) => {
    // Base64 encode username:password
    const credentials = btoa(`${username}:${password}`);

    const formData = new URLSearchParams();
    formData.append('credentials', credentials);

    const url = `${api.baseURL}/auth/login`;
    const response = await fetch(url, {
      method: 'POST',
      body: formData,
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        ...api.getAuthHeaders(),
      },
    });

    if (!response.ok) {
      const errorData: any = await response.json().catch(() => ({
        detail: `HTTP ${response.status}: ${response.statusText}`
      }));

      // Handle FastAPI validation errors
      let errorMessage = 'Login failed';
      if (Array.isArray(errorData.detail)) {
        // Pydantic validation errors
        errorMessage = errorData.detail.map((err: any) => err.msg).join(', ');
      } else if (typeof errorData.detail === 'string') {
        // Simple error message
        errorMessage = errorData.detail;
      }

      toast.error(errorMessage);
      throw new Error(errorMessage);
    }

    const data = await response.json();
    return data;
  },

  // Logout
  logout: () =>
    api.post<any>('/auth/logout'),

  // Get current user
  getCurrentUser: () =>
    api.get<any>('/auth/me'),

  // Change password
  changePassword: (currentPassword: string, newPassword: string) =>
    api.post<any>('/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword
    }),

  // User management (admin only)
  getUsers: async (skip = 0, limit = 100) => {
    const users = await api.get<any[]>(`/auth/users?skip=${skip}&limit=${limit}`);
    return {
      items: users,
      total: users.length,
      page: Math.floor(skip / limit) + 1,
      size: limit
    };
  },

  createUser: (userData: any) =>
    api.post<any>('/auth/users', userData),

  getUser: (userId: string) =>
    api.get<any>(`/auth/users/${userId}`),

  updateUser: (userId: string, userData: any) =>
    api.put<any>(`/auth/users/${userId}`, userData),

  deleteUser: (userId: string) =>
    api.delete<any>(`/auth/users/${userId}`),
};

// Product API
export const productApi = {
  // Get all products with pagination
  getProducts: (page = 1, size = 10) =>
    api.get<ApiResponse<any>>(`/products?page=${page}&size=${size}`),

  // Get product by ID
  getProduct: (id: string) =>
    api.get<any>(`/products/${id}`),

  // Create product
  createProduct: (data: any) =>
    api.post<any>('/products', data),

  // Update product
  updateProduct: (id: string, data: any) =>
    api.put<any>(`/products/${id}`, data),

  // Delete product
  deleteProduct: (id: string) =>
    api.delete<any>(`/products/${id}`),
};

// Plan API
export const planApi = {
  // Get all plans with pagination and optional filtering
  getPlans: (page = 1, size = 10, productId?: string) => {
    const params = new URLSearchParams({ page: page.toString(), size: size.toString() });
    if (productId) params.append('product_id', productId);
    return api.get<ApiResponse<any>>(`/plans?${params.toString()}`);
  },

  // Get plan by ID
  getPlan: (id: string) =>
    api.get<any>(`/plans/${id}`),

  // Create plan
  createPlan: (data: any) =>
    api.post<any>('/plans', data),

  // Update plan
  updatePlan: (id: string, data: any) =>
    api.put<any>(`/plans/${id}`, data),

  // Delete plan
  deletePlan: (id: string) =>
    api.delete<any>(`/plans/${id}`),
};

// Feature API
export const featureApi = {
  // Get all features with pagination and optional filtering
  getFeatures: (page = 1, size = 10, productId?: string) => {
    const params = new URLSearchParams({ page: page.toString(), size: size.toString() });
    if (productId) params.append('product_id', productId);
    return api.get<ApiResponse<any>>(`/features?${params.toString()}`);
  },

  // Get feature by ID
  getFeature: (id: string) =>
    api.get<any>(`/features/${id}`),

  // Create feature
  createFeature: (data: any) =>
    api.post<any>('/features', data),

  // Update feature
  updateFeature: (id: string, data: any) =>
    api.put<any>(`/features/${id}`, data),

  // Delete feature
  deleteFeature: (id: string) =>
    api.delete<any>(`/features/${id}`),
};

// Subscription API
export const subscriptionApi = {
  // Get all subscriptions with pagination and optional filtering
  getSubscriptions: (page = 1, size = 10, tenantId?: string) => {
    const params = new URLSearchParams({ page: page.toString(), size: size.toString() });
    if (tenantId) params.append('tenant_id', tenantId);
    return api.get<ApiResponse<any>>(`/subscriptions?${params.toString()}`);
  },

  // Get subscription by ID
  getSubscription: (id: string) =>
    api.get<any>(`/subscriptions/${id}`),

  // Create subscription
  createSubscription: (data: any) =>
    api.post<any>('/subscriptions', data),

  // Update subscription
  updateSubscription: (id: string, data: any) =>
    api.put<any>(`/subscriptions/${id}`, data),

  // Delete subscription
  deleteSubscription: (id: string) =>
    api.delete<any>(`/subscriptions/${id}`),

  // Get subscription entitlements
  getSubscriptionEntitlements: (subscriptionId: string) =>
    api.get<any[]>(`/subscriptions/${subscriptionId}/entitlements`),
};

// Health check
export const healthApi = {
  check: () => api.get<any>('/health'),
  metrics: () => api.get<any>('/metrics'),
};
