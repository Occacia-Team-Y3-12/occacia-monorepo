// src/services/customer/authService.ts
import axios from 'axios';
import { RegisterFormData, RegisterResponse, VerifyEmailResponse, LoginFormData, LoginResponse } from '@/types/customer/auth';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const customerAuthService = {
  register: async (data: RegisterFormData): Promise<RegisterResponse> => {
    const response = await api.post('/auth/register', data);
    return response.data;
  },

  verifyEmail: async (token: string): Promise<VerifyEmailResponse> => {
    const response = await api.get(`/auth/verify-email?token=${token}`);
    return response.data;
  },

  resendVerification: async (email: string): Promise<void> => {
    await api.post('/auth/resend-verification', { email });
  },

  login: async (data: LoginFormData): Promise<LoginResponse> => {
    const response = await api.post('/auth/login', data);
    return response.data;
  },
};