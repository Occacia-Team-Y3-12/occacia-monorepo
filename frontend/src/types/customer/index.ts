// src/types/customer/index.ts
export * from './auth';
export * from './task';

export type ServiceResult<T> = {
  ok: boolean;
  status: number;
  data?: T;
  error?: string;
};

export interface Customer {
  id: string;
  email: string;
  username: string;
  fullName: string;
  mobileNumber: string;
  isEmailVerified: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface CustomerRegistrationData {
  fullName: string;
  email: string;
  phone: string;
  password: string;
  locale?: string;
}

export interface VerifyEmailResponse {
  status: string;
  message: string;
}
