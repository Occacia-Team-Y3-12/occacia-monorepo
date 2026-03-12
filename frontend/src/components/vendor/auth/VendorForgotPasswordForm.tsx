'use client';

import { useState } from 'react';
import Link from 'next/link';
import { toast } from 'sonner';
import { Mail, ArrowLeft } from 'lucide-react';

export default function VendorForgotPasswordForm() {
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [emailSent, setEmailSent] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!email) {
      toast.error('Please enter your email address');
      return;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      toast.error('Please enter a valid email address');
      return;
    }

    setIsLoading(true);

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/auth/vendor/forgot-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email }),
      });

      if (response.ok) {
        setEmailSent(true);
        toast.success('If an account exists, you will receive a password reset email');
      } else {
        setEmailSent(true);
        toast.success('If an account exists, you will receive a password reset email');
      }
    } catch (error) {
      setEmailSent(true);
      toast.success('If an account exists, you will receive a password reset email');
    } finally {
      setIsLoading(false);
    }
  };

  if (emailSent) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100 px-4">
        <div className="max-w-md w-full bg-white rounded-3xl shadow-xl p-8 text-center">
          <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <Mail className="w-10 h-10 text-blue-600" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-3">Check Your Email</h1>
          <p className="text-gray-600 mb-2">
            If an account exists with <span className="font-semibold">{email}</span>, you will receive a password reset link.
          </p>
          <p className="text-sm text-gray-500 mb-8">
            Please check your email and click the link to reset your password. 
            If you don't see the email, check your spam folder.
          </p>
          <Link
            href="/vendor/auth/login"
            className="inline-flex items-center justify-center w-full bg-blue-600 text-white py-3 rounded-md font-medium hover:bg-blue-700 transition"
          >
            Back to Login
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100 px-4">
      <div className="max-w-md w-full bg-white rounded-3xl shadow-xl p-8">
        <Link
          href="/vendor/auth/login"
          className="inline-flex items-center text-sm text-gray-600 hover:text-gray-900 mb-6"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Login
        </Link>

        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Forgot Password?</h1>
          <p className="text-gray-600">
            Enter your email address and we'll send you a link to reset your password.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
              Email Address
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="vendor@example.com"
              disabled={isLoading}
              className="w-full border border-gray-300 rounded-md px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
              required
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-blue-600 text-white py-3 rounded-md font-medium hover:bg-blue-700 transition disabled:bg-blue-400 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Sending...' : 'Send Reset Link'}
          </button>
        </form>

        <p className="text-center text-sm text-gray-600 mt-6">
          Remember your password?{' '}
          <Link href="/vendor/auth/login" className="text-blue-600 hover:text-blue-700 font-semibold hover:underline">
            Login
          </Link>
        </p>
      </div>
    </div>
  );
}
