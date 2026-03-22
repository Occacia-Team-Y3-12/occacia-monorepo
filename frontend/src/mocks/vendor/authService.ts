import type { VendorAuthService } from '@/services/vendor/authService.shared';
import { persistVendorSession } from '@/services/vendor/authService.shared';

const sleep = (ms: number) =>
  new Promise((resolve) => setTimeout(resolve, ms));

export const mockVendorAuthService: VendorAuthService = {
  async login(payload) {
    await sleep(350);

    const isValid =
      payload.email.trim().length > 0 && payload.password.trim().length > 0;

    if (isValid) {
      persistVendorSession(`mock_vendor_token_${Date.now()}`);
    }

    return { ok: isValid };
  },

  async register() {
    await sleep(350);

    return {
      ok: true,
      data: {
        status: 'pending_verification',
        message: 'Please verify your email',
        data: { token: `mock_${Date.now()}` },
      },
    };
  },

  async forgotPassword(email) {
    await sleep(1200);
    return { ok: email.trim().length > 0 };
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
    return { ok: Boolean(token && token.startsWith('mock_')) };
  },
};
