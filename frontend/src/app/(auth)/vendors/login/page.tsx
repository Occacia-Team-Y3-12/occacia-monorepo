'use client';

import { useState } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { ROUTES } from '@/lib/routes';


export default function VendorLogin() {
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
        router.push(ROUTES.VENDORS.DASHBOARD);
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

      <div className="flex bg-white rounded-3xl shadow-2xl overflow-hidden max-w-4xl w-full relative z-10">
        <div className="w-2/5 bg-gradient-to-br from-[#f5f7f9] to-white p-12 flex flex-col items-center justify-center">
          <div className="mb-8">
            <Image src="/images/logo.png" alt="Occacia Logo" width={180} height={180} priority />
          </div>
          <h1 className="text-4xl font-bold text-[#2c3e50] mb-2">OCCACIA</h1>
          <p className="text-xl text-[#5a6c7d] font-medium">VENDOR PORTAL</p>
        </div>

        <div className="w-3/5 p-12 flex flex-col justify-center">
          <h2 className="text-3xl font-semibold text-[#5a6c7d] mb-8 text-center">VENDOR SIGN IN</h2>

          <form onSubmit={handleSubmit} className="space-y-6">
            <input
              type="email"
              name="email"
              placeholder="User Name"
              value={formData.email}
              onChange={handleChange}
              required
              className="w-full px-4 py-3 border border-[#d1dce5] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#1e88e5] text-[#2c3e50] placeholder-[#8b9db0] bg-[#f8fafb]"
            />

            <input
              type="password"
              name="password"
              placeholder="Password"
              value={formData.password}
              onChange={handleChange}
              required
              className="w-full px-4 py-3 border border-[#d1dce5] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#1e88e5] text-[#2c3e50] placeholder-[#8b9db0] bg-[#f8fafb]"
            />

            <div className="flex justify-end">
              <Link href={ROUTES.VENDORS.FORGOT_PASSWORD} className="text-sm text-[#1e88e5] hover:underline">
                Forgot Password?
              </Link>
            </div>


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
              {loading ? 'Logging in...' : 'Login →'}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-[#5a6c7d] text-sm">
              Don't have an account?{' '}
              <Link href={ROUTES.VENDORS.REGISTER} className="text-[#1e88e5] hover:underline font-medium">
                Register
              </Link>
            </p>
          </div>


          <div className="mt-8 text-center text-xs text-[#8b9db0]">
            Copyright © 2025 Occacia
          </div>
        </div>
      </div>
    </div>
  );
}
