import { api } from '@/services/api';
import type { AdminLoginRequest, AdminLoginResponse } from '@/types/admin/auth';

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

export const adminAuthService = {
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

    localStorage.setItem(ADMIN_TOKEN_KEY, data.access_token);
    localStorage.setItem(ADMIN_ROLE_KEY, data.role);
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
