import { CustomerRegistrationData, Customer, VerifyEmailResponse } from '@/types/customer/index';

function resolveApiBaseUrl() {
  const configuredBaseUrl = process.env.NEXT_PUBLIC_API_URL?.trim();

  if (!configuredBaseUrl) {
    // Use same-origin requests in frontend dev so Next.js rewrites can proxy to the backend.
    return '/api/v1';
  }

  const normalizedBaseUrl = configuredBaseUrl.replace(/\/+$/, '');
  return normalizedBaseUrl.endsWith('/api/v1')
    ? normalizedBaseUrl
    : `${normalizedBaseUrl}/api/v1`;
}

const API_BASE_URL = resolveApiBaseUrl();

export { API_BASE_URL, resolveApiBaseUrl };

export const authApi = {
  register: async (data: CustomerRegistrationData): Promise<Customer> => {
    const response = await fetch(`${API_BASE_URL}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Registration failed');
    return response.json();
  },

  verifyEmail: async (token: string): Promise<VerifyEmailResponse> => {
    const response = await fetch(`${API_BASE_URL}/auth/verify-email?token=${token}`);
    if (!response.ok) throw new Error('Email verification failed');
    return response.json();
  },
};

import axios from 'axios';
import { attachAdmin401Interceptor, attachAuthHeaderInterceptor } from '@/services/http';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

attachAuthHeaderInterceptor(api, () => {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('admin_token') || localStorage.getItem('auth_token');
});
attachAdmin401Interceptor(api);
