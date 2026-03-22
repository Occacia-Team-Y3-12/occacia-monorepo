// src/lib/validators.ts
import { z } from 'zod';
import { emailRegex, fullNameRegex, strongPasswordRegex } from './validation';

// Customer Registration Schema
export const registerSchema = z.object({
  username: z.string()
    .min(1, 'Username is required')
    .trim(),
  
  fullName: z.string()
    .min(1, 'Full name is required')
    .refine(val => val.trim().length > 0, 'Full name is required')
    .regex(fullNameRegex, 'Full name can contain only letters')
    .trim(),
  
  email: z.string()
    .min(1, 'Email is required')
    .regex(emailRegex, 'Invalid email format')
    .toLowerCase()
    .trim(),
  
  mobileNumber: z.string()
    .min(1, 'Mobile number is required')
    .regex(/^[0-9]+$/, 'Mobile number must contain numbers only')
    .refine(val => val.length >= 10, 'Mobile number must be at least 10 digits')
    .refine(val => val.length <= 15, 'Mobile number must not exceed 15 digits')
    .trim(),
  
  password: z.string()
    .min(1, 'Password is required')
    .regex(
      strongPasswordRegex,
      'Password must be at least 8 characters and include uppercase, lowercase, number, and special character'
    ),
});

export type RegisterFormValues = z.infer<typeof registerSchema>;

// Customer Login Schema
export const loginSchema = z.object({
  email: z.string()
    .min(1, 'Email is required')
    .email('Please enter a valid email address')
    .toLowerCase()
    .trim(),
  
  password: z.string()
    .min(1, 'Password is required')
    .min(8, 'Password must be at least 8 characters'),
});

export type LoginFormValues = z.infer<typeof loginSchema>;
