'use client';

import { useState } from 'react';
import { Eye, EyeOff, Mail, Lock } from 'lucide-react';

type LoginFormData = {
  email: string;
  password: string;
};

interface LoginFormProps {
  onSubmit: (data: LoginFormData) => Promise<void>;
  isLoading: boolean;
}

export default function LoginForm({ onSubmit, isLoading }: LoginFormProps) {
  const [formData, setFormData] = useState<LoginFormData>({
    email: '',
    password: '',
  });
  const [errors, setErrors] = useState<Partial<Record<keyof LoginFormData, string>>>({});
  const [showPassword, setShowPassword] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));

    if (errors[name as keyof LoginFormData]) {
      setErrors((prev) => ({ ...prev, [name]: undefined }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const nextErrors: Partial<Record<keyof LoginFormData, string>> = {};

    if (!formData.username.trim()) {
      nextErrors.username = 'Email is required';
    }

    if (!formData.password) {
      nextErrors.password = 'Password is required';
    }

    if (Object.keys(nextErrors).length > 0) {
      setErrors(nextErrors);
      return;
    }

    await onSubmit({
      email: formData.email.trim(),
      password: formData.password,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {/* Email Input */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Email Address
        </label>
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Mail className="h-5 w-5 text-gray-400" />
          </div>
          <input
            type="email"
            name="username"
            value={formData.username}
            onChange={handleChange}
            placeholder="you@example.com"
            disabled={isLoading}
            className={`w-full pl-10 pr-4 py-3 rounded-xl border-2 text-sm transition-all focus:outline-none disabled:bg-gray-50 disabled:cursor-not-allowed ${
              errors.username
                ? 'border-[#EA4335] focus:border-[#EA4335] focus:ring-4 focus:ring-red-100'
                : 'border-[#CCCCCC] focus:border-[#4285F4] focus:ring-4 focus:ring-blue-100'
            }`}
          />
        </div>
        {errors.username && (
          <p className="mt-1.5 text-xs text-red-600 flex items-center gap-1">
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            {errors.username}
          </p>
        )}
      </div>

      {/* Password Input */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Password
        </label>
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Lock className="h-5 w-5 text-gray-400" />
          </div>
          <input
            type={showPassword ? 'text' : 'password'}
            name="password"
            value={formData.password}
            onChange={handleChange}
            placeholder="Enter your password"
            disabled={isLoading}
            className={`w-full pl-10 pr-12 py-3 rounded-xl border-2 text-sm transition-all focus:outline-none disabled:bg-gray-50 disabled:cursor-not-allowed ${
              errors.password
                ? 'border-[#EA4335] focus:border-[#EA4335] focus:ring-4 focus:ring-red-100'
                : 'border-[#CCCCCC] focus:border-[#4285F4] focus:ring-4 focus:ring-blue-100'
            }`}
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
            aria-label={showPassword ? 'Hide password' : 'Show password'}
          >
            {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
          </button>
        </div>
        {errors.password && (
          <p className="mt-1.5 text-xs text-red-600 flex items-center gap-1">
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            {errors.password}
          </p>
        )}
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        disabled={isLoading}
        className="w-full bg-gradient-to-r from-[#0D47A1] to-[#4285F4] hover:from-[#0D47A1] hover:to-[#0D47A1] text-white font-semibold py-3.5 rounded-xl transition-all transform hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none shadow-lg hover:shadow-xl"
      >
        {isLoading ? (
          <span className="flex items-center justify-center gap-2">
            <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Logging in...
          </span>
        ) : (
          'Login to your account'
        )}
      </button>
    </form>
  );
}
