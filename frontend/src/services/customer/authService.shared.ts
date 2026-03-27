import axios from 'axios';

import { API_BASE_URL } from '@/services/api';
import type {
  ForgotPasswordResponse,
  LoginFormData,
  LoginResponse,
  RegisterFormData,
  RegisterResponse,
  ResetPasswordPayload,
  ResetPasswordResponse,
  VerifyEmailResponse,
} from '@/types/customer/auth';
import {
  getStoredCustomerRefreshToken,
  getStoredCustomerToken,
  getStoredCustomerUser,
  isCustomerAuthenticated,
  persistCustomerSession,
} from '@/services/customer/session';

export type CustomerAuthService = {
  register: (data: RegisterFormData) => Promise<RegisterResponse>;
  verifyEmail: (token: string) => Promise<VerifyEmailResponse>;
  resendVerification: (email: string) => Promise<void>;
  forgotPassword: (email: string) => Promise<ForgotPasswordResponse>;
  resetPassword: (payload: ResetPasswordPayload) => Promise<ResetPasswordResponse>;
  login: (data: LoginFormData) => Promise<LoginResponse>;
  refreshToken: (refreshToken?: string) => Promise<LoginResponse>;
  logout: () => Promise<void>;
  getToken: () => string | null;
  getRefreshToken: () => string | null;
  getUser: () => NonNullable<LoginResponse['user']> | null;
  isAuthenticated: () => boolean;
};

export type CustomerLoginPayload = LoginResponse & Record<string, unknown>;

export const customerAuthApi = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
});

const pickString = (value: unknown): string | undefined =>
  typeof value === 'string' && value.trim() ? value : undefined;

const pickObject = (
  value: unknown
): Record<string, unknown> | undefined =>
  value && typeof value === 'object' && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : undefined;

export const persistCustomerLoginResult = (
  result: CustomerLoginPayload
): LoginResponse => {
  const nestedData = pickObject(result.data);
  const deepData = pickObject(nestedData?.data);

  const accessToken =
    pickString(result.token) ??
    pickString(result.accessToken) ??
    pickString(result.access_token) ??
    pickString(nestedData?.token) ??
    pickString(nestedData?.accessToken) ??
    pickString(nestedData?.access_token) ??
    pickString(deepData?.token) ??
    pickString(deepData?.accessToken) ??
    pickString(deepData?.access_token);

  const refreshToken =
    pickString(result.refreshToken) ??
    pickString(result.refresh_token) ??
    pickString(nestedData?.refreshToken) ??
    pickString(nestedData?.refresh_token) ??
    pickString(deepData?.refreshToken) ??
    pickString(deepData?.refresh_token);

  const user =
    (pickObject(result.user) as LoginResponse['user'] | undefined) ??
    (pickObject(nestedData?.user) as LoginResponse['user'] | undefined) ??
    (pickObject(deepData?.user) as LoginResponse['user'] | undefined);

  persistCustomerSession(accessToken, refreshToken, user);

  return result;
};

export const customerAuthSessionMethods = {
  getToken: getStoredCustomerToken,
  getRefreshToken: getStoredCustomerRefreshToken,
  getUser: getStoredCustomerUser,
  isAuthenticated: isCustomerAuthenticated,
};

export {
  getStoredCustomerToken,
  getStoredCustomerRefreshToken,
  getStoredCustomerUser,
  isCustomerAuthenticated,
  logoutCustomerSession,
} from '@/services/customer/session';
