import type { CustomerAuthService, CustomerLoginPayload } from './authService.shared';
import {
  customerAuthApi,
  customerAuthSessionMethods,
  getStoredCustomerToken,
  getStoredCustomerRefreshToken,
  logoutCustomerSession,
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

  forgotPassword: async (email) => {
    const response = await customerAuthApi.post('/auth/customer/password/forgot', {
      email,
    });
    return response.data;
  },

  resetPassword: async ({ token, password }) => {
    const response = await customerAuthApi.post('/auth/customer/password/reset', {
      reset_token: token,
      new_password: password,
    });
    return response.data;
  },

  login: async (data) => {
    const response = await customerAuthApi.post('/auth/customer/login', data);
    return persistCustomerLoginResult(response.data as CustomerLoginPayload);
  },

  refreshToken: async (refreshToken) => {
    const resolvedRefreshToken = refreshToken || getStoredCustomerRefreshToken();

    if (!resolvedRefreshToken) {
      throw new Error('No customer refresh token is available.');
    }

    const response = await customerAuthApi.post('/auth/customer/token/refresh', {
      refreshToken: resolvedRefreshToken,
    });

    return persistCustomerLoginResult(response.data as CustomerLoginPayload);
  },

  logout: async () => {
    const token = getStoredCustomerToken();

    if (!token) {
      logoutCustomerSession();
      return;
    }

    try {
      await customerAuthApi.post(
        '/auth/customer/logout',
        {},
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );
      logoutCustomerSession();
    } catch (error: unknown) {
      const status = (error as { response?: { status?: number } })?.response?.status;

      if (status === 401 || status === 403) {
        logoutCustomerSession();
        return;
      }

      throw error;
    }
  },

  ...customerAuthSessionMethods,
};
