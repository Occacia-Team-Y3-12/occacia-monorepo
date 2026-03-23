import axios from 'axios';

import { API_BASE_URL } from '@/services/api';
import type {
  ForgotPasswordResponse,
  LoginFormData,
  LoginResponse,
  RegisterFormData,
  RegisterResponse,
  ResetPasswordPayload,
  ResetPasswordResponse,
  VerifyEmailResponse,
} from '@/types/customer/auth';

export type CustomerAuthService = {
  register: (data: RegisterFormData) => Promise<RegisterResponse>;
  verifyEmail: (token: string) => Promise<VerifyEmailResponse>;
  resendVerification: (email: string) => Promise<void>;
  forgotPassword: (email: string) => Promise<ForgotPasswordResponse>;
  resetPassword: (payload: ResetPasswordPayload) => Promise<ResetPasswordResponse>;
  login: (data: LoginFormData) => Promise<LoginResponse>;
  refreshToken: (refreshToken?: string) => Promise<LoginResponse>;
  logout: () => Promise<void>;
  getToken: () => string | null;
  getRefreshToken: () => string | null;
  getUser: () => NonNullable<LoginResponse['user']> | null;
  isAuthenticated: () => boolean;
};

export type CustomerLoginPayload = LoginResponse & Record<string, unknown>;

export const customerAuthApi = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
});

const CUSTOMER_TOKEN_COOKIE = 'customerToken';
const CUSTOMER_AUTH_FLAG = 'customerAuthVerified';

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

  if (!match) {
    return null;
  }

  const value = match.split('=').slice(1).join('=');
  return value ? decodeURIComponent(value) : null;
};

const pickString = (value: unknown): string | undefined =>
  typeof value === 'string' && value.trim() ? value : undefined;

const pickObject = (
  value: unknown
): Record<string, unknown> | undefined =>
  value && typeof value === 'object' && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : undefined;

export const persistCustomerLoginResult = (
  result: CustomerLoginPayload
): LoginResponse => {
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

  if (typeof window !== 'undefined') {
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
  }

  return result;
};

export const logoutCustomerSession = () => {
  if (typeof window !== 'undefined') {
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
  }

  clearAuthCookie();
};

export const getStoredCustomerToken = (): string | null => {
  if (typeof window === 'undefined') return null;

  return (
    localStorage.getItem('customerToken') ||
    localStorage.getItem('accessToken') ||
    sessionStorage.getItem('customerToken') ||
    sessionStorage.getItem('accessToken') ||
    getAuthCookie()
  );
};

export const getStoredCustomerRefreshToken = (): string | null => {
  if (typeof window === 'undefined') return null;

  return (
    localStorage.getItem('customerRefreshToken') ||
    sessionStorage.getItem('customerRefreshToken')
  );
};

export const getStoredCustomerUser = (): NonNullable<LoginResponse['user']> | null => {
  if (typeof window === 'undefined') return null;

  const stored =
    localStorage.getItem('customerUser') ||
    sessionStorage.getItem('customerUser');

  if (!stored) {
    return null;
  }

  try {
    return JSON.parse(stored) as NonNullable<LoginResponse['user']>;
  } catch {
    return null;
  }
};

export const isCustomerAuthenticated = (): boolean => {
  if (typeof window === 'undefined') return false;

  return Boolean(
    getStoredCustomerToken() ||
      localStorage.getItem(CUSTOMER_AUTH_FLAG) ||
      sessionStorage.getItem(CUSTOMER_AUTH_FLAG)
  );
};

export const customerAuthSessionMethods = {
  getToken: getStoredCustomerToken,
  getRefreshToken: getStoredCustomerRefreshToken,
  getUser: getStoredCustomerUser,
  isAuthenticated: isCustomerAuthenticated,
};
