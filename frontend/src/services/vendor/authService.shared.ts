import { VendorFormData } from '@/lib/validation';

export type VendorLoginResponse = {
  access_token?: string;
  accessToken?: string;
  token_type?: string;
  data?: {
    access_token?: string;
    accessToken?: string;
    token_type?: string;
    role?: string;
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
  register: (
    payload: VendorFormData & { organizationType: 'join' | 'create' }
  ) => Promise<RegisterResult>;
  forgotPassword: (email: string) => Promise<{ ok: boolean }>;
  resetPassword: (payload: {
    token: string;
    password: string;
  }) => Promise<{ ok: boolean; message?: string }>;
  verifyEmail: (token: string | null) => Promise<{ ok: boolean }>;
};

export const persistVendorSession = (accessToken: string) => {
  if (typeof window === 'undefined') {
    return;
  }

  localStorage.setItem('vendorToken', accessToken);
  localStorage.setItem('access_token', accessToken);
  localStorage.setItem('accessToken', accessToken);
  localStorage.setItem('vendor_role', 'VENDOR');
  localStorage.removeItem('admin_token');
};

export const getVendorAccessToken = (data: VendorLoginResponse) =>
  data.access_token ||
  data.accessToken ||
  data.data?.access_token ||
  data.data?.accessToken;
