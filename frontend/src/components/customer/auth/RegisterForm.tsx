'use client';

import { useState } from 'react';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import { RegisterFormValues, registerSchema } from '@/lib/validators';

interface RegisterFormProps {
  onSubmit: (data: RegisterFormValues) => Promise<void>;
  isLoading: boolean;
}

export default function RegisterForm({ onSubmit, isLoading }: RegisterFormProps) {
  const [formData, setFormData] = useState<RegisterFormValues>({
    username: '',
    fullName: '',
    email: '',
    mobileNumber: '',
    password: '',
  });
  const [errors, setErrors] = useState<Partial<Record<keyof RegisterFormValues, string>>>({});

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    
    // Clear error when user starts typing
    if (errors[name as keyof RegisterFormValues]) {
      setErrors(prev => ({ ...prev, [name]: undefined }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      const validatedData = registerSchema.parse(formData);
      await onSubmit(validatedData);
    } catch (error: any) {
      if (error.errors) {
        const fieldErrors: Partial<Record<keyof RegisterFormValues, string>> = {};
        error.errors.forEach((err: any) => {
          fieldErrors[err.path[0] as keyof RegisterFormValues] = err.message;
        });
        setErrors(fieldErrors);
      }
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <Input
        label="Username"
        name="username"
        value={formData.username}
        onChange={handleChange}
        error={errors.username}
        placeholder="Enter your username"
        disabled={isLoading}
      />

      <Input
        label="Full Name"
        name="fullName"
        value={formData.fullName}
        onChange={handleChange}
        error={errors.fullName}
        placeholder="Enter your full name"
        disabled={isLoading}
      />

      <Input
        label="Email"
        name="email"
        type="email"
        value={formData.email}
        onChange={handleChange}
        error={errors.email}
        placeholder="Enter your email"
        disabled={isLoading}
      />

      <Input
        label="Mobile Number"
        name="mobileNumber"
        value={formData.mobileNumber}
        onChange={handleChange}
        error={errors.mobileNumber}
        placeholder="Enter your mobile number"
        disabled={isLoading}
      />

      <Input
        label="Password"
        name="password"
        type="password"
        value={formData.password}
        onChange={handleChange}
        error={errors.password}
        placeholder="Enter your password"
        showPasswordToggle
        disabled={isLoading}
      />

      <Button
        type="submit"
        variant="primary"
        loading={isLoading}
        className="w-full mt-6"
      >
        Create Account
      </Button>
    </form>
  );
}