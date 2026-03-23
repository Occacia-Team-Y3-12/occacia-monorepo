import type {
  RegisterResponse,
  VendorAuthService,
  VendorLoginResponse,
} from './authService.shared';
import {
  clearVendorSession,
  getVendorAccessToken,
  getVendorRefreshToken,
  getStoredVendorToken,
  getStoredVendorRefreshToken,
  persistVendorSession,
} from './authService.shared';

const VENDOR_AUTH_API_BASE = '/api/v1/auth/vendor';

export const apiVendorAuthService: VendorAuthService = {
  async login(payload) {
    const response = await fetch(`${VENDOR_AUTH_API_BASE}/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    let data: VendorLoginResponse = {};
    try {
      data = (await response.json()) as VendorLoginResponse;
    } catch {
      data = {};
    }

    const accessToken = getVendorAccessToken(data);
    const refreshToken = getVendorRefreshToken(data);

    if (!response.ok || !accessToken) {
      return {
        ok: false,
        message:
          data.detail ||
          data.data?.detail ||
          data.data?.message ||
          (data as { message?: string }).message ||
          'Invalid credentials. Please try again.',
      };
    }

    persistVendorSession(accessToken, refreshToken);
    return { ok: true };
  },

  async refreshToken(refreshToken) {
    const resolvedRefreshToken = refreshToken || getStoredVendorRefreshToken();

    if (!resolvedRefreshToken) {
      return {
        ok: false,
        message: 'No vendor refresh token is available.',
      };
    }

    const response = await fetch(`${VENDOR_AUTH_API_BASE}/token/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refreshToken: resolvedRefreshToken }),
    });

    let data: VendorLoginResponse = {};
    try {
      data = (await response.json()) as VendorLoginResponse;
    } catch {
      data = {};
    }

    const accessToken = getVendorAccessToken(data);
    const nextRefreshToken = getVendorRefreshToken(data) || resolvedRefreshToken;

    if (!response.ok || !accessToken) {
      return {
        ok: false,
        message:
          data.detail ||
          data.data?.detail ||
          data.data?.message ||
          data.message ||
          'Unable to refresh vendor session.',
      };
    }

    persistVendorSession(accessToken, nextRefreshToken);
    return { ok: true };
  },

  async logout() {
    const token = getStoredVendorToken();

    if (!token) {
      clearVendorSession();
      return { ok: true };
    }

    const response = await fetch(`${VENDOR_AUTH_API_BASE}/logout`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
    });

    let data: { message?: string; detail?: string } = {};
    try {
      data = (await response.json()) as { message?: string; detail?: string };
    } catch {
      data = {};
    }

    if (response.ok || response.status === 401 || response.status === 403) {
      clearVendorSession();
      return {
        ok: true,
        message: data.message,
      };
    }

    return {
      ok: false,
      message: data.detail || data.message || 'Logout failed. Please try again.',
    };
  },

  async register(payload) {
    const backendPayload = {
      email: payload.email,
      password: payload.password,
      displayName: payload.fullName,
      contactPhone:
        payload.organizationType === 'create'
          ? payload.businessPhone
          : undefined,
      organizationCode:
        payload.organizationType === 'join'
          ? payload.organizationCode
          : undefined,
      organization:
        payload.organizationType === 'create'
          ? {
              name: payload.businessName,
              registrationNumber: payload.businessRegNumber,
              email: payload.businessEmail,
              phone: payload.businessPhone,
              address: payload.businessAddress,
              kymDetails: {
                username: payload.username,
                accountAddress: payload.address,
                nicNumber: payload.nicNumber,
                gender: payload.gender,
              },
            }
          : undefined,
      businessName:
        payload.organizationType === 'create' ? payload.businessName : undefined,
      locationBase:
        payload.organizationType === 'create'
          ? payload.businessAddress
          : undefined,
      phone:
        payload.organizationType === 'create'
          ? payload.businessPhone
          : undefined,
    };

    const response = await fetch(`${VENDOR_AUTH_API_BASE}/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(backendPayload),
    });

    let data: RegisterResponse = {};
    try {
      data = (await response.json()) as RegisterResponse;
    } catch {
      data = {};
    }

    if (!response.ok) {
      return {
        ok: false,
        data,
        message: data.detail || data.message || 'Registration failed. Please try again.',
      };
    }

    return {
      ok: true,
      data,
      message: data.message || 'Registration successful. Please verify your email.',
    };
  },

  async resendVerification(email) {
    const response = await fetch(
      `${VENDOR_AUTH_API_BASE}/email-verification/resend`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      }
    );

    let data: { message?: string } = {};
    try {
      data = (await response.json()) as { message?: string };
    } catch {
      data = {};
    }

    return {
      ok: response.ok,
      message: data.message,
    };
  },

  async forgotPassword(email) {
    const response = await fetch(`${VENDOR_AUTH_API_BASE}/forgot-password`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email }),
    });

    return { ok: response.ok };
  },

  async resetPassword(payload) {
    const response = await fetch(`${VENDOR_AUTH_API_BASE}/reset-password`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    let data: { message?: string } = {};
    try {
      data = (await response.json()) as { message?: string };
    } catch {
      data = {};
    }

    return {
      ok: response.ok,
      message: data.message,
    };
  },

  async verifyEmail(token) {
    if (!token) {
      return { ok: false, message: 'Verification token is required.' };
    }

    const response = await fetch(
      `${VENDOR_AUTH_API_BASE}/verify-email?token=${encodeURIComponent(token)}`
    );

    let data: { message?: string } = {};
    try {
      data = (await response.json()) as { message?: string };
    } catch {
      data = {};
    }

    return { ok: response.ok, message: data.message };
  },
};
