// src/types/customer/auth.ts
export interface RegisterFormData {
  fullName: string;
  email: string;
  phone: string;
  password: string;
  locale?: string;
}

export interface RegisterResponse {
  status?: string;
  message?: string;
}

export interface VerifyEmailResponse {
  status?: string;
  message: string;
}

export interface ApiError {
  message: string;
  errors?: Record<string, string[]>;
  statusCode?: number;
}

export interface LoginFormData {
  email: string;
  password: string;
}

export interface ForgotPasswordResponse {
  message: string;
}

export interface ResetPasswordPayload {
  token: string;
  password: string;
}

export interface ResetPasswordResponse {
  message: string;
}

export interface LoginResponse {
  status?: string;
  message?: string;
  token?: string;
  accessToken?: string;
  access_token?: string;
  refreshToken?: string;
  refresh_token?: string;
  user?: {
    id?: string;
    userId?: string;
    email: string;
    username?: string;
    fullName?: string;
    role?: string;
    status?: string;
  };
}
