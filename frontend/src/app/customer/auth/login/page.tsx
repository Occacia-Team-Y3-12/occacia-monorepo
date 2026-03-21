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

  const onSubmit = async (data: { username: string; password: string }) => {
    setIsLoading(true);
    try {
      await customerAuthService.login({ email: data.username, password: data.password });
      toast.success('Login successful!');
      router.push('/customer/dashboard');
    } catch (error: unknown) {
      const msg = (error as { response?: { data?: { message?: string } } })?.response?.data?.message;
      toast.error(msg || 'Invalid email or password. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex bg-gray-50">
      <div className="w-full lg:w-1/2 flex items-center justify-center px-6 py-12 lg:px-12">
        <div className="max-w-md w-full">
          <div className="flex items-center gap-3 mb-10">
            <img src="/images/customer/logo.png" alt="Occacia" className="h-12 w-auto" />
            <span className="text-2xl font-bold" style={{ color: '#1562CC' }}>OCCACIA</span>
          </div>

          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Welcome back</h1>
            <p className="text-gray-600">Login to your account</p>
          </div>

          <LoginForm onSubmit={onSubmit} isLoading={isLoading} />

          <p className="text-center text-sm text-gray-600 mt-8">
            Don't have an account?{' '}
            <Link href="/customer/auth/register" className="text-blue-600 hover:text-blue-700 font-semibold hover:underline">
              Sign up
            </Link>
          </p>
        </div>
      </div>

      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-blue-600 via-purple-600 to-purple-700">
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
