'use client';

import { useState } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { ROUTES } from '@/lib/routes';

export default function LoginPage() {
  const router = useRouter();
  const [formData, setFormData] = useState({ email: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        router.push(ROUTES.CUSTOMER.DASHBOARD);
      } else {
        setError('Invalid email or password. Please try again.');
      }
    } catch (err) {
      setError('Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  return (
    <div className="min-h-screen flex items-center justify-center relative overflow-hidden p-4">
      <Image src="/images/background.png" alt="Background" fill className="object-cover" priority />

      <div className="flex bg-white rounded-2xl shadow-2xl overflow-hidden max-w-4xl w-full relative z-10">
        {/* Left Side - Illustration */}
        <div className="w-2/5 bg-gradient-to-br from-blue-500 to-blue-700 p-12 flex flex-col items-center justify-center text-white hidden lg:flex">
          <div className="text-6xl mb-6">👥</div>
          <h2 className="text-3xl font-bold mb-4 text-center">Welcome Back</h2>
          <p className="text-blue-100 text-center text-lg">Sign in to start shopping with exclusive deals and personalized recommendations</p>
        </div>

        {/* Right Side - Form */}
        <div className="flex-1 p-8 sm:p-12 flex flex-col justify-center">
          <div className="mb-8 text-center lg:hidden">
            <Image src="/images/logo.png" alt="Occacia Logo" width={60} height={60} priority />
          </div>

          <h1 className="text-3xl font-bold text-gray-900 mb-2 text-center">Customer Login</h1>
          <p className="text-gray-600 text-center mb-8">Sign in to your account</p>

          {error && (
            <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4 text-red-700 font-semibold">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-semibold text-gray-900 mb-2">Email Address</label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                required
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="you@example.com"
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-900 mb-2">Password</label>
              <input
                type="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                required
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="••••••••"
              />
            </div>

            <div className="flex items-center justify-between">
              <label className="flex items-center">
                <input type="checkbox" className="w-4 h-4 rounded border-gray-300" />
                <span className="ml-2 text-sm text-gray-600">Remember me</span>
              </label>
              <Link href="#" className="text-sm text-blue-600 hover:text-blue-700 font-semibold">
                Forgot password?
              </Link>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-semibold py-3 rounded-lg transition-colors"
            >
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          <div className="mt-8 pt-8 border-t border-gray-200">
            <p className="text-center text-gray-600">
              Don't have an account?{' '}
              <Link href={ROUTES.CUSTOMER.REGISTER} className="text-blue-600 hover:text-blue-700 font-semibold">
                Sign up
              </Link>
            </p>
          </div>

          <div className="mt-6 pt-6 border-t border-gray-200 text-center">
            <p className="text-sm text-gray-600 mb-4">Are you a vendor?</p>
            <Link
              href={ROUTES.VENDOR.LOGIN}
              className="inline-block px-6 py-2 border border-gray-300 rounded-lg text-gray-700 font-semibold hover:bg-gray-50 transition-colors"
            >
              Vendor Login
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
