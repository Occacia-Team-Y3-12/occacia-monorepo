'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import Image from 'next/image';
import { toast } from 'sonner';

import RegisterForm from '@/components/customer/auth/RegisterForm';
import SocialLoginButtons from '@/components/ui/SocialLoginButtons';
import { RegisterFormValues } from '@/lib/validators';
import { ROUTES } from '@/lib/routes';
import { customerAuthService } from '@/services/customer/authServices';
import type { RegisterFormData } from '@/types/customer/auth';

const getCustomerAuthErrorMessage = (error: unknown, fallback: string) => {
  const response = (error as {
    response?: {
      status?: number;
      data?: {
        message?: string;
        detail?: string;
        errors?: Record<string, string[]>;
      };
    };
  })?.response;

  const data = response?.data;
  const message = data?.message || data?.detail;

  return {
    status: response?.status,
    message: message || fallback,
    errors: data?.errors,
  };
};

export default function RegisterPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);

  const onSubmit = async (data: RegisterFormValues) => {
    setIsLoading(true);

    try {
      const payload: RegisterFormData = {
        fullName: data.fullName,
        email: data.email,
        phone: data.mobileNumber,
        password: data.password,
      };

      const response = await customerAuthService.register(payload);
      toast.success(response.message || 'Registration successful. Please verify your email.');
      router.replace(`${ROUTES.CUSTOMER.VERIFY_EMAIL}?email=${encodeURIComponent(data.email)}`);
    } catch (error: unknown) {
      const { status, message, errors } = getCustomerAuthErrorMessage(
        error,
        'Registration failed. Please try again.'
      );

      if (status === 400 && message.toLowerCase().includes('already registered')) {
        toast.error('An account already exists with this email address.');
      } else if (errors) {
        Object.keys(errors).forEach((field) => {
          toast.error(`${field}: ${errors[field].join(', ')}`);
        });
      } else {
        toast.error(message);
      }
    } finally {
      setIsLoading(false);
    }
  };

  // Registration Form Screen
  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-8">
      <div className="w-full max-w-4xl bg-white/95 backdrop-blur rounded-xl shadow-xl flex flex-col md:flex-row overflow-hidden">
        
        {/* Left Section - Form */}
        <div className="flex-1 p-6 sm:p-8">
          <div className="flex items-center gap-2 sm:gap-3 mb-4 sm:mb-6">
            <img src="/images/customer/logo.png" alt="Occacia" className="h-10 sm:h-12 w-auto" />
            <span className="text-xl sm:text-2xl font-bold" style={{ color: '#1562CC' }}>Occacia</span>
          </div>

          <div className="mb-4 sm:mb-6">
            <h1 className="text-xl sm:text-2xl font-semibold text-gray-900 mb-1">Create an account</h1>
            <p className="text-gray-500 text-xs sm:text-sm">Let's create magic together.</p>
          </div>

          <RegisterForm onSubmit={onSubmit} isLoading={isLoading} />

          <div className="mt-4 space-y-2">
            <SocialLoginButtons />
          </div>

          <p className="text-xs sm:text-sm text-center text-gray-500 mt-4">
            Already have an account?{' '}
            <Link href="/customer/auth/login" className="text-blue-600 cursor-pointer hover:underline">
              Login
            </Link>
          </p>
        </div>

        {/* Right Section - Image */}
        <div className="relative hidden md:block w-80 flex-shrink-0">
          <Image
            src="/images/customer/customer register pic.png"
            alt="Customer Register"
            fill
            className="object-cover rounded-r-xl"
            priority
          />
          <div className="absolute inset-0 bg-black/40 flex items-center justify-center px-6 rounded-r-xl">
            <h2 className="text-white text-2xl font-semibold leading-snug text-center">
              <span className="text-yellow-300 text-3xl">P</span>lan<br />
              meaningful<br />
              moments,<br />
              effortlessly with<br />
              <span className="text-3xl font-bold">Occacia</span>
            </h2>
          </div>
        </div>
      </div>
    </div>
  );
}
