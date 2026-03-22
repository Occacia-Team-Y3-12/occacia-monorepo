'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { toast } from 'sonner';

import LoginForm from '@/components/customer/auth/LoginForm';
import { customerAuthService } from '@/services/customer/authServices';

export default function LoginPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);

  const onSubmit = async (data: { email: string; password: string }) => {
    setIsLoading(true);
    try {
      await customerAuthService.login({ email: data.email, password: data.password });
      if (!customerAuthService.isAuthenticated()) {
        throw new Error('Authentication token was not returned from login response.');
      }
      toast.success('Login successful!');
      sessionStorage.setItem('customerAuthVerified', '1');
      router.replace('/customer/dashboard');
    } catch (error: unknown) {
      const msg = (error as { response?: { data?: { message?: string } } })?.response?.data?.message;
      toast.error(msg || 'Invalid email or password. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col lg:flex-row bg-gradient-to-br from-[#F4F8FA] via-[#FAFAFA] to-[#F4F8FA]">
      {/* Left Side - Login Form */}
      <div className="w-full lg:w-[65%] flex items-center justify-center px-4 sm:px-6 py-8 sm:py-12 lg:px-12">
        <div className="max-w-lg w-full">
          {/* Logo */}
          <div className="flex items-center justify-center gap-2 sm:gap-3 mb-6 sm:mb-10">
            <img src="/icons/logo.svg" alt="Occacia" className="h-10 sm:h-12 w-auto" />
            <span className="text-2xl sm:text-3xl font-bold bg-gradient-to-r from-[#0D47A1] to-[#4285F4] bg-clip-text text-transparent">Occacia</span>
          </div>

          {/* Welcome Card */}
          <div className="bg-white rounded-2xl sm:rounded-3xl shadow-xl sm:shadow-2xl p-6 sm:p-8 lg:p-10 mb-4 sm:mb-6">
            <div className="mb-6 sm:mb-8 lg:mb-10">
              <h1 className="text-2xl sm:text-3xl lg:text-4xl font-bold text-[#0D47A1] mb-2 sm:mb-3">Welcome back! 👋</h1>
              <p className="text-[#666666] text-base sm:text-lg">Login to continue your journey</p>
            </div>

            <LoginForm onSubmit={onSubmit} isLoading={isLoading} />

            <div className="mt-6 sm:mt-8 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 sm:gap-0">
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="remember"
                  className="w-4 h-4 text-[#4285F4] border-[#CCCCCC] rounded focus:ring-[#4285F4]"
                />
                <label htmlFor="remember" className="ml-2 text-sm text-[#666666]">
                  Remember me
                </label>
              </div>
              <Link href="/customer/auth/forgot-password" className="text-sm text-[#4285F4] hover:text-[#0D47A1] font-medium hover:underline">
                Forgot password?
              </Link>
            </div>

            {/* Sign Up Link - Inside Card */}
            <div className="mt-6 sm:mt-8 pt-6 border-t border-[#EAEAEA] text-center">
              <p className="text-[#666666] text-sm sm:text-base">
                Don't have an account?{' '}
                <Link href="/customer/auth/register" className="text-[#4285F4] hover:text-[#0D47A1] font-bold hover:underline text-base sm:text-lg">
                  Sign up →
                </Link>
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Right Side - Hero Section */}
      <div className="hidden lg:flex lg:w-[35%] relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-[#0D47A1] via-[#4285F4] to-[#4285F4]">
          {/* Animated Background Pattern */}
          <div className="absolute inset-0 opacity-20">
            <div className="absolute top-20 left-10 w-48 h-48 bg-white rounded-full mix-blend-overlay filter blur-3xl animate-blob"></div>
            <div className="absolute top-32 right-10 w-48 h-48 bg-[#FBBC05] rounded-full mix-blend-overlay filter blur-3xl animate-blob animation-delay-2000"></div>
            <div className="absolute bottom-20 left-20 w-48 h-48 bg-[#34A853] rounded-full mix-blend-overlay filter blur-3xl animate-blob animation-delay-4000"></div>
          </div>

          {/* Content */}
          <div className="relative h-full flex flex-col items-center justify-center p-8 text-white">
            <div className="max-w-sm text-center">
              {/* Icon */}
              <div className="mb-6 flex justify-center">
                <div className="bg-white/20 backdrop-blur-lg p-4 rounded-2xl">
                  <svg className="w-12 h-12 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v13m0-13V6a2 2 0 112 2h-2zm0 0V5.5A2.5 2.5 0 109.5 8H12zm-7 4h14M5 12a2 2 0 110-4h14a2 2 0 110 4M5 12v7a2 2 0 002 2h10a2 2 0 002-2v-7" />
                  </svg>
                </div>
              </div>

              {/* Heading */}
              <h2 className="text-3xl font-bold mb-4 leading-tight">
                Plan Meaningful
                <br />
                <span className="text-[#FBBC05]">Moments</span>
                <br />
                Effortlessly
              </h2>

              {/* Description */}
              <p className="text-sm text-white/90">
                Your AI-powered occasion planning marketplace
              </p>
            </div>
          </div>
        </div>
      </div>

      <style jsx>{`
        @keyframes blob {
          0%, 100% {
            transform: translate(0, 0) scale(1);
          }
          33% {
            transform: translate(30px, -50px) scale(1.1);
          }
          66% {
            transform: translate(-20px, 20px) scale(0.9);
          }
        }
        .animate-blob {
          animation: blob 7s infinite;
        }
        .animation-delay-2000 {
          animation-delay: 2s;
        }
        .animation-delay-4000 {
          animation-delay: 4s;
        }
      `}</style>
    </div>
  );
}
