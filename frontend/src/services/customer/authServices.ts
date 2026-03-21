// src/services/customer/authService.ts
import axios from 'axios';
import { RegisterFormData, RegisterResponse, VerifyEmailResponse, LoginFormData, LoginResponse } from '@/types/customer/auth';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

const CUSTOMER_TOKEN_COOKIE = 'customerToken';
const CUSTOMER_AUTH_FLAG = 'customerAuthVerified';
const ENABLE_CUSTOMER_AUTH_MOCK =
  process.env.NEXT_PUBLIC_CUSTOMER_AUTH_MOCK === 'true' ||
  process.env.NODE_ENV === 'development';

const setAuthCookie = (token: string) => {
  if (typeof document === 'undefined') return;
  document.cookie = `${CUSTOMER_TOKEN_COOKIE}=${encodeURIComponent(token)}; Path=/; Max-Age=604800; SameSite=Lax`;
};

const clearAuthCookie = () => {
  if (typeof document === 'undefined') return;
  document.cookie = `${CUSTOMER_TOKEN_COOKIE}=; Path=/; Max-Age=0; SameSite=Lax`;
};

const getAuthCookie = (): string | null => {
  if (typeof document === 'undefined') return null;
  const match = document.cookie
    .split('; ')
    .find((row) => row.startsWith(`${CUSTOMER_TOKEN_COOKIE}=`));
  if (!match) return null;
  const value = match.split('=').slice(1).join('=');
  return value ? decodeURIComponent(value) : null;
};

const persistCustomerSession = (
  accessToken?: string,
  refreshToken?: string,
  user?: LoginResponse['user']
) => {
  if (accessToken) {
    localStorage.setItem('customerToken', accessToken);
    localStorage.setItem('accessToken', accessToken);
    sessionStorage.setItem('customerToken', accessToken);
    sessionStorage.setItem('accessToken', accessToken);
    setAuthCookie(accessToken);
  }
  if (refreshToken) {
    localStorage.setItem('customerRefreshToken', refreshToken);
    sessionStorage.setItem('customerRefreshToken', refreshToken);
  }
  if (user) {
    localStorage.setItem('customerUser', JSON.stringify(user));
    sessionStorage.setItem('customerUser', JSON.stringify(user));
  }
  if (accessToken || user) {
    localStorage.setItem(CUSTOMER_AUTH_FLAG, '1');
    sessionStorage.setItem(CUSTOMER_AUTH_FLAG, '1');
  }
};

const createMockLoginResponse = (email: string): LoginResponse => {
  const fallbackEmail = email || 'customer@occacia.test';
  return {
    status: 'success',
    message: 'Mock login success',
    accessToken: `mock_customer_token_${Date.now()}`,
    refreshToken: `mock_customer_refresh_${Date.now()}`,
    user: {
      id: 'mock-customer-1',
      email: fallbackEmail,
      username: fallbackEmail.split('@')[0] || 'customer',
      fullName: 'Mock Customer',
    },
  };
};

export const customerAuthService = {
  register: async (data: RegisterFormData): Promise<RegisterResponse> => {
    const response = await api.post('/auth/register', data);
    return response.data;
  },

  verifyEmail: async (token: string): Promise<VerifyEmailResponse> => {
    const response = await api.get(`/auth/verify-email?token=${token}`);
    return response.data;
  },

  resendVerification: async (email: string): Promise<void> => {
    await api.post('/auth/resend-verification', { email });
  },

  login: async (data: LoginFormData): Promise<LoginResponse> => {
    let result: LoginResponse & Record<string, unknown>;
    try {
      const response = await api.post('/auth/customer/login', data);
      result = response.data as LoginResponse & Record<string, unknown>;
    } catch (error) {
      if (!ENABLE_CUSTOMER_AUTH_MOCK) {
        throw error;
      }
      result = createMockLoginResponse(data.email) as LoginResponse & Record<string, unknown>;
    }

    const pickString = (value: unknown): string | undefined => (typeof value === 'string' && value.trim() ? value : undefined);
    const pickObject = (value: unknown): Record<string, unknown> | undefined =>
      value && typeof value === 'object' && !Array.isArray(value) ? (value as Record<string, unknown>) : undefined;

    const nestedData = pickObject(result.data);
    const deepData = pickObject(nestedData?.data);

    const accessToken =
      pickString(result.token) ??
      pickString(result.accessToken) ??
      pickString(result.access_token) ??
      pickString(nestedData?.token) ??
      pickString(nestedData?.accessToken) ??
      pickString(nestedData?.access_token) ??
      pickString(deepData?.token) ??
      pickString(deepData?.accessToken) ??
      pickString(deepData?.access_token);

    const refreshToken =
      pickString(result.refreshToken) ??
      pickString(result.refresh_token) ??
      pickString(nestedData?.refreshToken) ??
      pickString(nestedData?.refresh_token) ??
      pickString(deepData?.refreshToken) ??
      pickString(deepData?.refresh_token);

    const user =
      (pickObject(result.user) as LoginResponse['user'] | undefined) ??
      (pickObject(nestedData?.user) as LoginResponse['user'] | undefined) ??
      (pickObject(deepData?.user) as LoginResponse['user'] | undefined);

    persistCustomerSession(accessToken, refreshToken, user);
    return result;
  },

  logout: (): void => {
    localStorage.removeItem('customerToken');
    localStorage.removeItem('accessToken');
    localStorage.removeItem('customerRefreshToken');
    localStorage.removeItem('customerUser');
    sessionStorage.removeItem('customerToken');
    sessionStorage.removeItem('accessToken');
    sessionStorage.removeItem('customerRefreshToken');
    sessionStorage.removeItem('customerUser');
    localStorage.removeItem(CUSTOMER_AUTH_FLAG);
    sessionStorage.removeItem(CUSTOMER_AUTH_FLAG);
    clearAuthCookie();
  },

  getToken: (): string | null => {
    if (typeof window === 'undefined') return null;
    return (
      localStorage.getItem('customerToken') ||
      localStorage.getItem('accessToken') ||
      sessionStorage.getItem('customerToken') ||
      sessionStorage.getItem('accessToken') ||
      localStorage.getItem(CUSTOMER_AUTH_FLAG) ||
      sessionStorage.getItem(CUSTOMER_AUTH_FLAG) ||
      getAuthCookie()
    );
  },

  getUser: () => {
    if (typeof window === 'undefined') return null;
    const stored = localStorage.getItem('customerUser') || sessionStorage.getItem('customerUser');
    return stored ? JSON.parse(stored) : null;
  },

  isAuthenticated: (): boolean => {
    if (typeof window === 'undefined') return false;
    return !!(
      localStorage.getItem('customerToken') ||
      localStorage.getItem('accessToken') ||
      sessionStorage.getItem('customerToken') ||
      sessionStorage.getItem('accessToken') ||
      localStorage.getItem(CUSTOMER_AUTH_FLAG) ||
      sessionStorage.getItem(CUSTOMER_AUTH_FLAG) ||
      getAuthCookie()
    );
  },
};
