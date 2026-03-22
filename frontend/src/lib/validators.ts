// src/lib/validators.ts
import { z } from 'zod';

// Customer Registration Schema
export const registerSchema = z.object({
  username: z.string()
    .min(1, 'Username is required')
    .min(3, 'Username must be at least 3 characters')
    .max(50, 'Username must not exceed 50 characters')
    .regex(/^[a-zA-Z0-9_]+$/, 'Username can only contain letters, numbers and underscores')
    .regex(/^[a-zA-Z]/, 'Username must start with a letter')
    .refine(val => !/^(admin|root|system)$/i.test(val), 'This username is not allowed')
    .trim(),
  
  fullName: z.string()
    .min(1, 'Full name is required')
    .min(2, 'Full name must be at least 2 characters')
    .max(100, 'Full name must not exceed 100 characters')
    .regex(/^[a-zA-Z\s]+$/, 'Full name can only contain letters and spaces')
    .refine(val => val.trim().split(/\s+/).length >= 2, 'Please enter your full name (first and last name)')
    .trim(),
  
  email: z.string()
    .min(1, 'Email is required')
    .email('Please enter a valid email address')
    .max(255, 'Email must not exceed 255 characters')
    .refine(val => !val.includes('..'), 'Email cannot contain consecutive dots')
    .refine(val => /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(val), 'Please enter a valid email format')
    .toLowerCase()
    .trim(),
  
  mobileNumber: z.string()
    .min(1, 'Mobile number is required')
    .regex(/^[0-9+\s()-]+$/, 'Mobile number can only contain digits, +, -, (, ), and spaces')
    .transform(val => val.replace(/[\s()-]/g, ''))
    .refine(val => val.length >= 10, 'Mobile number must be at least 10 digits')
    .refine(val => val.length <= 15, 'Mobile number must not exceed 15 digits')
    .refine(val => /^[+]?[0-9]{10,15}$/.test(val), 'Please enter a valid mobile number'),
  
  password: z.string()
    .min(1, 'Password is required')
    .min(8, 'Password must be at least 8 characters')
    .max(100, 'Password must not exceed 100 characters')
    .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
    .regex(/[a-z]/, 'Password must contain at least one lowercase letter')
    .regex(/[0-9]/, 'Password must contain at least one number')
    .regex(/[!@#$%^&*(),.?":{}|<>]/, 'Password must contain at least one special character')
    .refine(val => !/\s/.test(val), 'Password cannot contain spaces')
    .refine(val => !/^(password|12345678|qwerty)$/i.test(val), 'Password is too common'),
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