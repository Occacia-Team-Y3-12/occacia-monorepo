import type { CustomerAuthService, CustomerLoginPayload } from './authService.shared';
import {
  customerAuthApi,
  customerAuthSessionMethods,
  persistCustomerLoginResult,
} from './authService.shared';

export const apiCustomerAuthService: CustomerAuthService = {
  register: async (data) => {
    const response = await customerAuthApi.post('/auth/customer/register', data);
    return response.data;
  },

  verifyEmail: async (token) => {
    const response = await customerAuthApi.get(
      `/auth/customer/verify-email?token=${encodeURIComponent(token)}`
    );
    return response.data;
  },

  resendVerification: async (email) => {
    await customerAuthApi.post('/auth/customer/email-verification/resend', {
      email,
    });
  },

  login: async (data) => {
    const response = await customerAuthApi.post('/auth/customer/login', data);
    return persistCustomerLoginResult(response.data as CustomerLoginPayload);
  },

  ...customerAuthSessionMethods,
};
