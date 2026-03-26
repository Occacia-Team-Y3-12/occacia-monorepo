import { featureFlags } from '@/config/featureFlags';
import { adminAuthServiceMock } from '@/mocks/admin/authService';
import { api } from '@/services/api';
import type {
  AdminForgotPasswordResponse,
  AdminLoginRequest,
  AdminLoginResponse,
  AdminRegisterRequest,
  AdminRegisterResponse,
  AdminResetPasswordResponse,
  AdminVerifyEmailResponse,
  AdminVerifyOtpResponse,
} from '@/types/admin/auth';

const ADMIN_TOKEN_KEY = 'admin_token';
const ADMIN_ROLE_KEY = 'admin_role';

function parseJwtPayload(token: string): Record<string, unknown> | null {
  try {
    const [, payload] = token.split('.');
    if (!payload) return null;
    const normalized = payload.replace(/-/g, '+').replace(/_/g, '/');
    const decoded = atob(normalized);
    return JSON.parse(decoded) as Record<string, unknown>;
  } catch {
    return null;
  }
}

function persistAdminSession(data: AdminLoginResponse) {
  localStorage.setItem(ADMIN_TOKEN_KEY, data.access_token);
  localStorage.setItem(ADMIN_ROLE_KEY, data.role);
}

const sharedAdminAuthMethods = {
  logout(): void {
    localStorage.removeItem(ADMIN_TOKEN_KEY);
    localStorage.removeItem(ADMIN_ROLE_KEY);
  },

  getToken(): string | null {
    return localStorage.getItem(ADMIN_TOKEN_KEY);
  },

  getRole(): string | null {
    return localStorage.getItem(ADMIN_ROLE_KEY);
  },

  isAdminToken(token: string | null): boolean {
    if (!token) return false;
    const payload = parseJwtPayload(token);
    return payload?.type === 'admin';
  },

  detectSessionRole(): 'ADMIN' | 'CUSTOMER' | 'VENDOR' | 'UNKNOWN' {
    const adminToken = localStorage.getItem('admin_token');
    if (this.isAdminToken(adminToken)) {
      return 'ADMIN';
    }

    const candidateToken =
      localStorage.getItem('customerToken') ||
      localStorage.getItem('accessToken') ||
      localStorage.getItem('auth_token');
    if (!candidateToken) {
      return 'UNKNOWN';
    }

    const payload = parseJwtPayload(candidateToken);
    const role = String(payload?.role ?? '').toUpperCase();
    if (role === 'CUSTOMER') return 'CUSTOMER';
    if (role === 'VENDOR') return 'VENDOR';
    return 'UNKNOWN';
  },
};

const apiAdminAuthService = {
  async register(payload: AdminRegisterRequest): Promise<AdminRegisterResponse> {
    const { data } = await api.post<AdminRegisterResponse>('/auth/admin/register', {
      email: payload.email,
      password: payload.password,
      staff_role: payload.staffRole ?? 'staff',
    });
    return data;
  },

  async verifyEmail(token: string): Promise<AdminVerifyEmailResponse> {
    const { data } = await api.get<AdminVerifyEmailResponse>('/auth/admin/verify-email', {
      params: { token },
    });
    return data;
  },

  async resendVerification(email: string): Promise<AdminVerifyEmailResponse> {
    const { data } = await api.post<AdminVerifyEmailResponse>('/auth/admin/email-verification/resend', {
      email,
    });
    return data;
  },

  async forgotPassword(email: string): Promise<AdminForgotPasswordResponse> {
    const { data } = await api.post<AdminForgotPasswordResponse>('/auth/admin/password/forgot', {
      email,
    });
    return data;
  },

  async verifyPasswordOtp(email: string, otp: string): Promise<AdminVerifyOtpResponse> {
    const { data } = await api.post<AdminVerifyOtpResponse>('/auth/admin/password/verify-otp', {
      email,
      otp,
    });
    return data;
  },

  async resetPassword(resetToken: string, newPassword: string): Promise<AdminResetPasswordResponse> {
    const { data } = await api.post<AdminResetPasswordResponse>('/auth/admin/password/reset', {
      reset_token: resetToken,
      new_password: newPassword,
    });
    return data;
  },

  async login(payload: AdminLoginRequest): Promise<AdminLoginResponse> {
    const formData = new URLSearchParams();
    formData.set('username', payload.email);
    formData.set('password', payload.password);

    const { data } = await api.post<AdminLoginResponse>(
      '/auth/admin/login',
      formData,
      {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      }
    );

    persistAdminSession(data);
    return data;
  },

  ...sharedAdminAuthMethods,
};

export const adminAuthService = featureFlags.useAdminAuthMock
  ? adminAuthServiceMock
  : apiAdminAuthService;
