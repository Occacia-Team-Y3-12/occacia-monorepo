'use client';

import { useState } from 'react';
import { RegisterFormValues, registerSchema } from '@/lib/validators';
import { Eye, EyeOff } from 'lucide-react';

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
  const [showPassword, setShowPassword] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    
    if (errors[name as keyof RegisterFormValues]) {
      setErrors(prev => ({ ...prev, [name]: undefined }));
    }
  };

  const validateField = (name: keyof RegisterFormValues, value: string) => {
    try {
      const fieldSchema = registerSchema.shape[name];
      fieldSchema.parse(value);
      setErrors(prev => ({ ...prev, [name]: undefined }));
    } catch (error: any) {
      if (error.errors?.[0]) {
        setErrors(prev => ({ ...prev, [name]: error.errors[0].message }));
      }
    }
  };

  const handleBlur = (e: React.FocusEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    if (value.trim()) {
      validateField(name as keyof RegisterFormValues, value);
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
      <input
        type="text"
        name="username"
        value={formData.username}
        onChange={handleChange}
        onBlur={handleBlur}
        placeholder="Username"
        disabled={isLoading}
        className={`w-full border rounded-md px-3 py-2.5 text-sm focus:outline-none focus:ring-2 disabled:bg-gray-100 ${
          errors.username ? 'border-red-500 focus:ring-red-500' : 'border-gray-300 focus:ring-blue-500'
        }`}
      />
      {errors.username && <p className="text-xs text-red-500 -mt-2">{errors.username}</p>}

      <input
        type="text"
        name="fullName"
        value={formData.fullName}
        onChange={handleChange}
        onBlur={handleBlur}
        placeholder="Full Name"
        disabled={isLoading}
        className={`w-full border rounded-md px-3 py-2.5 text-sm focus:outline-none focus:ring-2 disabled:bg-gray-100 ${
          errors.fullName ? 'border-red-500 focus:ring-red-500' : 'border-gray-300 focus:ring-blue-500'
        }`}
      />
      {errors.fullName && <p className="text-xs text-red-500 -mt-2">{errors.fullName}</p>}

      <input
        type="email"
        name="email"
        value={formData.email}
        onChange={handleChange}
        onBlur={handleBlur}
        placeholder="Email Address"
        disabled={isLoading}
        className={`w-full border rounded-md px-3 py-2.5 text-sm focus:outline-none focus:ring-2 disabled:bg-gray-100 ${
          errors.email ? 'border-red-500 focus:ring-red-500' : 'border-gray-300 focus:ring-blue-500'
        }`}
      />
      {errors.email && <p className="text-xs text-red-500 -mt-2">{errors.email}</p>}

      <input
        type="tel"
        name="mobileNumber"
        value={formData.mobileNumber}
        onChange={handleChange}
        onBlur={handleBlur}
        placeholder="Mobile Number"
        disabled={isLoading}
        className={`w-full border rounded-md px-3 py-2.5 text-sm focus:outline-none focus:ring-2 disabled:bg-gray-100 ${
          errors.mobileNumber ? 'border-red-500 focus:ring-red-500' : 'border-gray-300 focus:ring-blue-500'
        }`}
      />
      {errors.mobileNumber && <p className="text-xs text-red-500 -mt-2">{errors.mobileNumber}</p>}

      <div className="relative">
        <input
          type={showPassword ? "text" : "password"}
          name="password"
          value={formData.password}
          onChange={handleChange}
          onBlur={handleBlur}
          placeholder="Password"
          disabled={isLoading}
          className={`w-full border rounded-md px-3 py-2.5 pr-10 text-sm focus:outline-none focus:ring-2 disabled:bg-gray-100 ${
            errors.password ? 'border-red-500 focus:ring-red-500' : 'border-gray-300 focus:ring-blue-500'
          }`}
        />
        <button
          type="button"
          onClick={() => setShowPassword(!showPassword)}
          className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500"
        >
          {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
        </button>
      </div>
      {errors.password && <p className="text-xs text-red-500 -mt-2">{errors.password}</p>}

      <p className="text-xs text-gray-400 -mt-2">Must be at least 8 characters</p>

      <button
        type="submit"
        disabled={isLoading}
        className="w-full bg-blue-600 text-white py-2.5 rounded-md font-medium hover:bg-blue-700 transition disabled:bg-blue-400 disabled:cursor-not-allowed"
      >
        {isLoading ? 'Creating Account...' : 'Create Account'}
      </button>
    </form>
  );
}