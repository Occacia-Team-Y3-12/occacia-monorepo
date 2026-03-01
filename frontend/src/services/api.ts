import { CustomerRegistrationData, Customer, VerifyEmailResponse } from '@/types/customer';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080/api/v1';

export const authApi = {
  register: async (data: CustomerRegistrationData): Promise<Customer> => {
    const response = await fetch(`${API_BASE_URL}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Registration failed');
    return response.json();
  },

  verifyEmail: async (token: string): Promise<VerifyEmailResponse> => {
    const response = await fetch(`${API_BASE_URL}/auth/verify-email?token=${token}`);
    if (!response.ok) throw new Error('Email verification failed');
    return response.json();
  },
};
