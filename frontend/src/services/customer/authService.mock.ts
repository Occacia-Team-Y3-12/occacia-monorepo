import type { CustomerAuthService, CustomerLoginPayload } from './authService.shared';
import {
  createMockCustomerLoginResponse,
  customerAuthSessionMethods,
  persistCustomerLoginResult,
} from './authService.shared';

const sleep = (ms: number) =>
  new Promise((resolve) => setTimeout(resolve, ms));

const isValidMockToken = (token: string) =>
  token.startsWith('mock_') ||
  token.startsWith('mock_customer_') ||
  token.startsWith('token_');

export const mockCustomerAuthService: CustomerAuthService = {
  register: async () => {
    await sleep(350);

    return {
      status: 'success',
      message: 'Registration successful! Please check your email.',
    };
  },

  verifyEmail: async (token) => {
    await sleep(800);

    if (!token || !isValidMockToken(token)) {
      throw new Error('Invalid mock verification token.');
    }

    return {
      status: 'success',
      message: 'Email verified successfully!',
    };
  },

  resendVerification: async () => {
    await sleep(300);
  },

  login: async (data) => {
    await sleep(350);

    return persistCustomerLoginResult(
      createMockCustomerLoginResponse(data.email) as CustomerLoginPayload
    );
  },

  ...customerAuthSessionMethods,
};
