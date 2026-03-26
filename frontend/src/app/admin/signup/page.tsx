'use client';

import { FormEvent, useState } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { toast } from 'sonner';

import { ROUTES } from '@/lib/routes';
import { adminAuthService } from '@/services/admin/authService';

export default function AdminSignupPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError('');
    setLoading(true);

    try {
      await adminAuthService.register({ email: email.trim(), password, staffRole: 'staff' });
      toast.success('Registration successful. Please verify your email.');
      router.replace(`${ROUTES.ADMIN.VERIFY_EMAIL}?email=${encodeURIComponent(email.trim())}`);
    } catch (err) {
      setError('Unable to create admin account. Please try again.');
      toast.error(
        err instanceof Error && err.message
          ? err.message
          : 'Unable to create admin account. Please try again.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 px-4 py-20">
      <div className="mx-auto max-w-md rounded-2xl border border-gray-200 bg-white p-8 shadow-sm">
        <div className="mb-8 flex items-center gap-3">
          <Image src="/icons/logo.svg" alt="Occacia" width={42} height={42} priority />
          <span className="text-2xl font-bold tracking-wide text-[#1562CC]">OCCACIA</span>
        </div>
        <h1 className="text-2xl font-bold text-gray-900">Admin Sign Up</h1>
        <p className="mt-2 text-sm text-gray-600">
          Create your internal admin account and verify your email to continue.
        </p>

        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">Email</label>
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"
            />
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">Password</label>
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
              minLength={8}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"
            />
          </div>

          {error ? <p className="text-sm text-red-600">{error}</p> : null}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-blue-300"
          >
            {loading ? 'Creating account...' : 'Create account'}
          </button>
        </form>

        <div className="mt-6 flex flex-col gap-2 text-sm text-gray-600">
          <Link href={ROUTES.ADMIN.FORGOT_PASSWORD} className="text-blue-600 hover:underline">
            Forgot your password?
          </Link>
          <Link href={ROUTES.ADMIN.LOGIN} className="text-blue-600 hover:underline">
            Already have an account? Sign in
          </Link>
        </div>
      </div>
    </div>
  );
}
