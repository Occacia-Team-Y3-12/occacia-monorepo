import type { AxiosInstance, InternalAxiosRequestConfig } from 'axios';

import { ROUTES } from '@/lib/routes';
import { logoutCustomerSession } from '@/services/customer/session';
import { clearVendorSession } from '@/services/vendor/authService.shared';
import { getStoredCustomerToken } from '@/services/customer/session';
import { getStoredVendorToken } from '@/services/vendor/authService.shared';

const redirectTo = (path: string) => {
  if (typeof window !== 'undefined') {
    window.location.href = path;
  }
};

export const handleCustomerUnauthorized = () => {
  logoutCustomerSession();
  redirectTo(ROUTES.CUSTOMER.LOGIN);
};

export const handleVendorUnauthorized = () => {
  clearVendorSession();
  redirectTo(ROUTES.VENDOR.LOGIN);
};

export const handleAdminUnauthorized = () => {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('admin_token');
    localStorage.removeItem('auth_token');
  }
  redirectTo(ROUTES.ADMIN.LOGIN);
};

export const withCustomerAuthHeaders = (headers?: HeadersInit) => {
  const merged = new Headers(headers);
  const token = getStoredCustomerToken();
  if (token && !merged.has('Authorization')) {
    merged.set('Authorization', `Bearer ${token}`);
  }
  return merged;
};

export const withVendorAuthHeaders = (headers?: HeadersInit) => {
  const merged = new Headers(headers);
  const token = getStoredVendorToken();
  if (token && !merged.has('Authorization')) {
    merged.set('Authorization', `Bearer ${token}`);
  }
  return merged;
};

export const withAdminAuthHeaders = (headers?: HeadersInit) => {
  const merged = new Headers(headers);
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('admin_token') || localStorage.getItem('auth_token');
    if (token && !merged.has('Authorization')) {
      merged.set('Authorization', `Bearer ${token}`);
    }
  }
  return merged;
};

export const attachAuthHeaderInterceptor = (
  api: AxiosInstance,
  getToken: () => string | null
) => {
  api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
    const token = getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  });
};

export const attachCustomer401Interceptor = (api: AxiosInstance) => {
  api.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error.response?.status === 401) {
        handleCustomerUnauthorized();
      }
      return Promise.reject(error);
    }
  );
};

export const attachVendor401Interceptor = (api: AxiosInstance) => {
  api.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error.response?.status === 401) {
        handleVendorUnauthorized();
      }
      return Promise.reject(error);
    }
  );
};

export const attachAdmin401Interceptor = (api: AxiosInstance) => {
  api.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error.response?.status === 401) {
        handleAdminUnauthorized();
      }
      return Promise.reject(error);
    }
  );
};

export const handleCustomerFetchUnauthorized = (response: Response): boolean => {
  if (response.status === 401) {
    handleCustomerUnauthorized();
    return true;
  }
  return false;
};
