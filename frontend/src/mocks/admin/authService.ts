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

function createMockAdminToken() {
  const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/g, '');
  const payload = btoa(JSON.stringify({ type: 'admin', role: 'ADMIN' }))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/g, '');

  return `${header}.${payload}.mock-signature`;
}

export const adminAuthServiceMock = {
  async register(payload: AdminRegisterRequest): Promise<AdminRegisterResponse> {
    await new Promise((resolve) => setTimeout(resolve, 250));
    if (!payload.email.trim() || !payload.password.trim()) {
      throw new Error('Email and password are required.');
    }
    return {
      message: 'Registration successful. Please verify your email.',
      email: payload.email,
      staff_role: payload.staffRole ?? 'staff',
    };
  },

  async verifyEmail(): Promise<AdminVerifyEmailResponse> {
    await new Promise((resolve) => setTimeout(resolve, 250));
    return { message: 'Email verified successfully.' };
  },

  async resendVerification(): Promise<AdminVerifyEmailResponse> {
    await new Promise((resolve) => setTimeout(resolve, 250));
    return { message: 'Verification email resent successfully.' };
  },

  async forgotPassword(): Promise<AdminForgotPasswordResponse> {
    await new Promise((resolve) => setTimeout(resolve, 250));
    return { message: 'If this email is registered, a reset code has been sent.' };
  },

  async verifyPasswordOtp(): Promise<AdminVerifyOtpResponse> {
    await new Promise((resolve) => setTimeout(resolve, 250));
    return {
      resetToken: 'mock-reset-token',
      message: 'OTP verified. You may now reset your password.',
    };
  },

  async resetPassword(): Promise<AdminResetPasswordResponse> {
    await new Promise((resolve) => setTimeout(resolve, 250));
    return { message: 'Password updated successfully.' };
  },

  async login(payload: AdminLoginRequest): Promise<AdminLoginResponse> {
    await new Promise((resolve) => setTimeout(resolve, 250));

    if (!payload.email.trim() || !payload.password.trim()) {
      throw new Error('Email and password are required.');
    }

    const data: AdminLoginResponse = {
      access_token: createMockAdminToken(),
      token_type: 'bearer',
      role: 'ADMIN',
    };

    persistAdminSession(data);
    return data;
  },

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
