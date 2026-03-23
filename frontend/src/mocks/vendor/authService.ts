import type { VendorAuthService } from '@/services/vendor/authService.shared';
import {
  clearVendorSession,
  persistVendorSession,
} from '@/services/vendor/authService.shared';

const sleep = (ms: number) =>
  new Promise((resolve) => setTimeout(resolve, ms));

export const mockVendorAuthService: VendorAuthService = {
  async login(payload) {
    await sleep(350);

    const isValid =
      payload.email.trim().length > 0 && payload.password.trim().length > 0;

    if (isValid) {
      persistVendorSession(
        `mock_vendor_token_${Date.now()}`,
        `mock_vendor_refresh_${Date.now()}`
      );
    }

    return { ok: isValid };
  },

  async refreshToken() {
    await sleep(250);
    persistVendorSession(
      `mock_vendor_token_${Date.now()}`,
      `mock_vendor_refresh_${Date.now()}`
    );
    return { ok: true };
  },

  async logout() {
    await sleep(150);
    clearVendorSession();
    return { ok: true };
  },

  async register() {
    await sleep(350);

    return {
      ok: true,
      data: {
        status: 'pending_verification',
        message: 'Registration successful. Please verify your email.',
        data: { token: `mock_${Date.now()}` },
      },
      message: 'Registration successful. Please verify your email.',
    };
  },

  async resendVerification(email) {
    await sleep(300);
    return {
      ok: email.trim().length > 0,
      message: email.trim().length > 0 ? 'Verification email resent successfully.' : 'Email is required.',
    };
  },

  async forgotPassword(email) {
    await sleep(350);
    return {
      ok: email.trim().length > 0,
      message: email.trim().length > 0
        ? 'If this email is registered, a password reset link has been sent.'
        : 'Email is required.',
    };
  },

  async resetPassword(payload) {
    await sleep(800);

    if (!payload.token?.startsWith('mock_')) {
      return { ok: false, message: 'Invalid or expired reset link' };
    }

    if (!payload.password.trim()) {
      return { ok: false, message: 'Password is required' };
    }

    return { ok: true };
  },

  async verifyEmail(token) {
    await sleep(2000);
    return {
      ok: Boolean(token && token.startsWith('mock_')),
      message: token && token.startsWith('mock_')
        ? 'Email verified successfully. Your account is pending admin approval.'
        : 'Invalid or expired verification token.',
    };
  },
};
