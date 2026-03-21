// src/types/customer/auth.ts
export interface RegisterFormData {
  username: string;
  fullName: string;
  email: string;
  mobileNumber: string;
  password: string;
}

export interface RegisterResponse {
  status: string;
  message?: string;
}

export interface VerifyEmailResponse {
  status: string;
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

export interface LoginResponse {
  status: string;
  message?: string;
  token?: string;
  accessToken?: string;
  access_token?: string;
  refreshToken?: string;
  refresh_token?: string;
  user?: {
    id: string;
    email: string;
    username: string;
    fullName: string;
  };
}
