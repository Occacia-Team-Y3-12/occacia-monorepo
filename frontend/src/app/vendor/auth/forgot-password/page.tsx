'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

export default function ForgotPasswordPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!email) {
      setError('Please enter your email address.');
      return;
    }

    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      setSuccess(true);
    }, 1200);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
      <div className="bg-white shadow-2xl rounded-2xl p-8 w-full max-w-md">
        <h1 className="text-3xl font-semibold text-center text-[#5a6c7d] mb-3">
          Forgot Password
        </h1>

        <p className="text-sm text-[#8b9db0] text-center mb-8">
          Enter your vendor email and we'll send password reset instructions.
        </p>

        {!success ? (
          <form onSubmit={handleSubmit} className="space-y-6">
            <input
              type="email"
              placeholder="Vendor Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full px-4 py-3 border border-[#d1dce5] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#1e88e5] text-[#2c3e50] placeholder-[#8b9db0] bg-[#f8fafb]"
            />

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-[#1565c0] hover:bg-[#0d47a1] text-white font-medium py-3 rounded-lg transition-colors duration-200 disabled:opacity-50"
            >
              {loading ? 'Sending...' : 'Send Reset Link →'}
            </button>
          </form>
        ) : (
          <div className="text-center space-y-4">
            <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg">
              <p className="font-medium">✅ Password reset link sent!</p>
              <p className="text-sm mt-1">Please check your email inbox.</p>
            </div>
            <button
              onClick={() => router.push('/vendor/auth/login')}
              className="w-full bg-[#1565c0] hover:bg-[#0d47a1] text-white font-medium py-3 rounded-lg transition-colors duration-200"
            >
              Back to Login →
            </button>
          </div>
        )}

        {!success && (
          <div className="mt-6 text-center">
            <Link href="/vendor/auth/login" className="text-[#1e88e5] hover:underline text-sm font-medium">
              ← Back to Login
            </Link>
          </div>
        )}

        <div className="mt-8 text-center text-xs text-[#8b9db0]">
          Copyright © 2025 Occacia
        </div>
      </div>
    </div>
  );
}
