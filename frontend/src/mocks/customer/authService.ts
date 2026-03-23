import type {
  CustomerAuthService,
  CustomerLoginPayload,
} from '@/services/customer/authService.shared';
import {
  customerAuthSessionMethods,
  logoutCustomerSession,
  persistCustomerLoginResult,
} from '@/services/customer/authService.shared';
import type { LoginResponse } from '@/types/customer/auth';

const sleep = (ms: number) =>
  new Promise((resolve) => setTimeout(resolve, ms));

const isValidMockToken = (token: string) =>
  token.startsWith('mock_') ||
  token.startsWith('mock_customer_') ||
  token.startsWith('token_');

const createMockCustomerLoginResponse = (email: string): LoginResponse => {
  const fallbackEmail = email || 'customer@occacia.test';

  return {
    status: 'success',
    message: 'Mock login success',
    accessToken: `mock_customer_token_${Date.now()}`,
    refreshToken: `mock_customer_refresh_${Date.now()}`,
    user: {
      id: 'mock-customer-1',
      email: fallbackEmail,
      username: fallbackEmail.split('@')[0] || 'customer',
      fullName: 'Mock Customer',
    },
  };
};

export const mockCustomerAuthService: CustomerAuthService = {
  register: async () => {
    await sleep(350);

    return {
      status: 'success',
      message: 'Registration successful. Please verify your email.',
    };
  },

  verifyEmail: async (token) => {
    await sleep(800);

    if (!token || !isValidMockToken(token)) {
      throw new Error('Invalid mock verification token.');
    }

    return {
      status: 'success',
      message: 'Email verified successfully.',
    };
  },

  resendVerification: async () => {
    await sleep(300);
  },

  forgotPassword: async () => {
    await sleep(300);

    return {
      message: 'If this email is registered, a password reset link has been sent.',
    };
  },

  resetPassword: async ({ token, password }) => {
    await sleep(500);

    if (!token || !isValidMockToken(token)) {
      throw new Error('Invalid or expired reset link.');
    }

    if (!password.trim()) {
      throw new Error('Password is required.');
    }

    return {
      message: 'Password updated successfully.',
    };
  },

  login: async (data) => {
    await sleep(350);

    return persistCustomerLoginResult(
      createMockCustomerLoginResponse(data.email) as CustomerLoginPayload
    );
  },

  refreshToken: async () => {
    await sleep(250);

    return persistCustomerLoginResult(
      createMockCustomerLoginResponse('customer@occacia.test') as CustomerLoginPayload
    );
  },

  logout: async () => {
    await sleep(150);
    logoutCustomerSession();
  },

  ...customerAuthSessionMethods,
};
