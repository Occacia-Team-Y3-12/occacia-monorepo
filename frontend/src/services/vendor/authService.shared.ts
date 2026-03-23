import { VendorFormData } from '@/lib/validation';

export type VendorLoginResponse = {
  access_token?: string;
  accessToken?: string;
  refresh_token?: string;
  refreshToken?: string;
  token_type?: string;
  detail?: string;
  user?: {
    userId?: string;
    email?: string;
    role?: string;
    status?: string;
  };
  data?: {
    access_token?: string;
    accessToken?: string;
    refresh_token?: string;
    refreshToken?: string;
    token_type?: string;
    role?: string;
    detail?: string;
    message?: string;
    user?: {
      userId?: string;
      email?: string;
      role?: string;
      status?: string;
    };
  };
  role?: string;
  message?: string;
};

export type RegisterResponse = {
  status?: string;
  data?: { token?: string };
  message?: string;
  detail?: string;
};

export type RegisterResult = {
  ok: boolean;
  data: RegisterResponse;
  message?: string;
};

export type VendorAuthService = {
  login: (payload: { email: string; password: string }) => Promise<{
    ok: boolean;
    message?: string;
  }>;
  refreshToken: (refreshToken?: string) => Promise<{
    ok: boolean;
    message?: string;
  }>;
  logout: () => Promise<{ ok: boolean; message?: string }>;
  register: (
    payload: VendorFormData & { organizationType: 'join' | 'create' }
  ) => Promise<RegisterResult>;
  resendVerification: (email: string) => Promise<{ ok: boolean; message?: string }>;
  forgotPassword: (email: string) => Promise<{ ok: boolean }>;
  resetPassword: (payload: {
    token: string;
    password: string;
  }) => Promise<{ ok: boolean; message?: string }>;
  verifyEmail: (token: string | null) => Promise<{ ok: boolean; message?: string }>;
};

export const persistVendorSession = (
  accessToken: string,
  refreshToken?: string
) => {
  if (typeof window === 'undefined') {
    return;
  }

  localStorage.setItem('vendorToken', accessToken);
  localStorage.setItem('access_token', accessToken);
  localStorage.setItem('accessToken', accessToken);
  localStorage.setItem('vendor_role', 'VENDOR');
  if (refreshToken) {
    localStorage.setItem('vendorRefreshToken', refreshToken);
    sessionStorage.setItem('vendorRefreshToken', refreshToken);
  }
  localStorage.removeItem('admin_token');
};

export const clearVendorSession = () => {
  if (typeof window === 'undefined') {
    return;
  }

  localStorage.removeItem('vendorToken');
  localStorage.removeItem('access_token');
  localStorage.removeItem('accessToken');
  localStorage.removeItem('vendor_role');
  localStorage.removeItem('vendorRefreshToken');
  sessionStorage.removeItem('vendorToken');
  sessionStorage.removeItem('access_token');
  sessionStorage.removeItem('accessToken');
  sessionStorage.removeItem('vendor_role');
  sessionStorage.removeItem('vendorRefreshToken');
};

export const getStoredVendorToken = (): string | null => {
  if (typeof window === 'undefined') {
    return null;
  }

  return (
    localStorage.getItem('vendorToken') ||
    localStorage.getItem('access_token') ||
    localStorage.getItem('accessToken')
  );
};

export const getStoredVendorRefreshToken = (): string | null => {
  if (typeof window === 'undefined') {
    return null;
  }

  return (
    localStorage.getItem('vendorRefreshToken') ||
    sessionStorage.getItem('vendorRefreshToken')
  );
};

export const isVendorAuthenticated = (): boolean => {
  if (typeof window === 'undefined') {
    return false;
  }

  const vendorRole = localStorage.getItem('vendor_role');
  const token = getStoredVendorToken();

  return Boolean(token && (!vendorRole || vendorRole === 'VENDOR'));
};

export const getVendorAccessToken = (data: VendorLoginResponse) =>
  data.access_token ||
  data.accessToken ||
  data.data?.access_token ||
  data.data?.accessToken;

export const getVendorRefreshToken = (data: VendorLoginResponse) =>
  data.refresh_token ||
  data.refreshToken ||
  data.data?.refresh_token ||
  data.data?.refreshToken;
