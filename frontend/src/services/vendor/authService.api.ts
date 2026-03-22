import { API_BASE_URL } from '@/services/api';

import type {
  RegisterResponse,
  VendorAuthService,
  VendorLoginResponse,
} from './authService.shared';
import {
  getVendorAccessToken,
  persistVendorSession,
} from './authService.shared';

export const apiVendorAuthService: VendorAuthService = {
  async login(payload) {
    const response = await fetch(`${API_BASE_URL}/auth/vendor/login`, {
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

    if (!response.ok || !accessToken) {
      return {
        ok: false,
        message:
          (data as { message?: string }).message ||
          'Invalid credentials. Please try again.',
      };
    }

    persistVendorSession(accessToken);
    return { ok: true };
  },

  async register(payload) {
    const backendPayload = {
      email: payload.email,
      password: payload.password,
      business_name: payload.businessName,
      display_name: payload.fullName,
      contact_phone: payload.businessPhone,
      phone: payload.businessPhone,
      location_base: payload.businessAddress,
    };

    const response = await fetch(`${API_BASE_URL}/auth/vendor/register`, {
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
      message: 'Registration successful. Please login.',
    };
  },

  async forgotPassword() {
    return { ok: false };
  },

  async resetPassword(payload) {
    const response = await fetch(
      `${API_BASE_URL}/auth/vendor/reset-password`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
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

  async verifyEmail(token) {
    if (!token) {
      return { ok: false };
    }

    const response = await fetch(
      `${API_BASE_URL}/auth/vendor/verify-email?token=${encodeURIComponent(token)}`
    );

    return { ok: response.ok };
  },
};
