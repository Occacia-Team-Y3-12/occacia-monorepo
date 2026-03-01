'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import Image from 'next/image';
import { toast } from 'sonner';
import { Mail } from 'lucide-react';

import Button from '@/components/ui/Button';
import RegisterForm from '@/components/customer/auth/RegisterForm';
import SocialLoginButtons from '@/components/ui/SocialLoginButtons';
import { RegisterFormValues } from '@/lib/validators';
import { customerAuthService } from '@/services/customer/authServices';

export default function RegisterPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [registeredEmail, setRegisteredEmail] = useState<string | null>(null);

  const onSubmit = async (data: RegisterFormValues) => {
    setIsLoading(true);

    try {
      await customerAuthService.register(data);
      setRegisteredEmail(data.email);
      toast.success('Registration successful! Please check your email.');
    } catch (error: any) {
      const errorMessage = error.response?.data?.message || 'Registration failed. Please try again.';
      
      if (error.response?.status === 409) {
        toast.error('An account already exists with this email address.');
      } else if (error.response?.data?.errors) {
        const errors = error.response.data.errors;
        Object.keys(errors).forEach((field) => {
          toast.error(`${field}: ${errors[field].join(', ')}`);
        });
      } else {
        toast.error(errorMessage);
      }
    } finally {
      setIsLoading(false);
    }
  };

  // Check Your Email Screen
  if (registeredEmail) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100 px-4">
        <div className="max-w-md w-full bg-white rounded-3xl shadow-xl p-8 text-center">
          <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <Mail className="w-10 h-10 text-green-600" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-3">Check Your Email</h1>
          <p className="text-gray-600 mb-2">
            We've sent a verification link to
          </p>
          <p className="font-semibold text-gray-900 mb-6">{registeredEmail}</p>
          <p className="text-sm text-gray-500 mb-8">
            Please click the link in the email to verify your account. 
            If you don't see the email, check your spam folder.
          </p>
          <Button
            onClick={() => router.push('/customer/auth/login')}
            variant="primary"
            className="w-full"
          >
            Go to Login
          </Button>
        </div>
      </div>
    );
  }

  // Registration Form Screen
  return (
    <div className="min-h-screen flex bg-gray-50">
      {/* Left Side - Form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center px-6 py-12 lg:px-12">
        <div className="max-w-md w-full">
          {/* Logo */}
          <div className="flex items-center gap-2 mb-10">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 via-blue-600 to-cyan-500 rounded-lg flex items-center justify-center shadow-md">
              <span className="text-white font-bold text-xl">O</span>
            </div>
            <span className="text-2xl font-bold text-gray-900">OCCACIA</span>
          </div>

          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              Create an account
            </h1>
            <p className="text-gray-600">Let's create magic together.</p>
          </div>

          {/* Registration Form */}
          <RegisterForm onSubmit={onSubmit} isLoading={isLoading} />

          {/* Divider */}
          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-300"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-3 bg-gray-50 text-gray-500">Or continue with</span>
            </div>
          </div>

          {/* Social Login Buttons */}
          <SocialLoginButtons />

          {/* Login Link */}
          <p className="text-center text-sm text-gray-600 mt-8">
            Already have an account?{' '}
            <Link href="/customer/auth/login" className="text-blue-600 hover:text-blue-700 font-semibold hover:underline">
              Login
            </Link>
          </p>
        </div>
      </div>

      {/* Right Side - Image/Branding */}
      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-blue-600 via-purple-600 to-purple-700">
          {/* Background Pattern */}
          <div className="absolute inset-0 opacity-10">
            <svg className="w-full h-full" xmlns="http://www.w3.org/2000/svg">
              <defs>
                <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
                  <path d="M 40 0 L 0 0 0 40" fill="none" stroke="white" strokeWidth="1"/>
                </pattern>
              </defs>
              <rect width="100%" height="100%" fill="url(#grid)" />
            </svg>
          </div>

          {/* Content */}
          <div className="relative h-full flex items-center justify-center p-12">
            <div className="text-white max-w-lg">
              <h2 className="text-6xl font-bold mb-6 leading-tight">
                <span className="text-yellow-300">P</span>lan<br />
                meaningful<br />
                moments,<br />
                effortlessly with
              </h2>
              <p className="text-7xl font-bold">Occacia</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}