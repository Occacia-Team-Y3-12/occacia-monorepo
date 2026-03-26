'use client';

import Link from 'next/link';
import { FormEvent, useState } from 'react';
import { toast } from 'sonner';

import { ROUTES } from '@/lib/routes';
import { adminAuthService } from '@/services/admin/authService';

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

type Step = 'request' | 'verify' | 'done';

export default function AdminForgotPasswordPage() {
  const [step, setStep] = useState<Step>('request');
  const [email, setEmail] = useState('');
  const [otp, setOtp] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleRequest = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const normalizedEmail = email.trim();
    if (!normalizedEmail) {
      setError('Email is required.');
      return;
    }
    if (!EMAIL_REGEX.test(normalizedEmail)) {
      setError('Please enter a valid email address.');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      const response = await adminAuthService.forgotPassword(normalizedEmail);
      toast.success(response.message || 'If this email is registered, a reset code has been sent.');
      setStep('verify');
    } catch (err) {
      toast.error(
        err instanceof Error && err.message
          ? err.message
          : 'Unable to send reset code. Please try again.'
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleVerify = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!otp.trim()) {
      setError('OTP code is required.');
      return;
    }
    if (!newPassword.trim() || newPassword.length < 8) {
      setError('Password must be at least 8 characters.');
      return;
    }
    if (newPassword !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      const verification = await adminAuthService.verifyPasswordOtp(email.trim(), otp.trim());
      await adminAuthService.resetPassword(verification.resetToken, newPassword);
      toast.success('Password updated successfully.');
      setStep('done');
    } catch (err) {
      toast.error(
        err instanceof Error && err.message
          ? err.message
          : 'Unable to reset password. Please try again.'
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="relative flex min-h-screen items-center justify-center overflow-hidden bg-gradient-to-br from-[#F4F8FA] via-[#FAFAFA] to-[#FFFFFF] px-4 py-10">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute -left-12 top-12 h-48 w-48 rounded-full bg-[#4285F4]/15 blur-3xl" />
        <div className="absolute -right-16 bottom-8 h-56 w-56 rounded-full bg-[#FBBC05]/20 blur-3xl" />
        <div className="absolute left-1/2 top-1/3 h-44 w-44 -translate-x-1/2 rounded-full bg-[#0D47A1]/10 blur-3xl" />
      </div>

      <section className="relative z-10 w-full max-w-md rounded-3xl border border-[#EAEAEA] bg-[#FFFFFF]/90 p-6 shadow-[0_20px_60px_-32px_rgba(13,71,161,0.45)] backdrop-blur-xl sm:p-8">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#4285F4]">Admin Security</p>
        <h1 className="mt-2 text-2xl font-bold text-[#0D47A1] sm:text-[30px]">Reset your password</h1>
        <p className="mt-3 text-sm leading-6 text-[#666666]">
          {step === 'request'
            ? 'Enter your admin email and we will send you a one-time reset code.'
            : 'Enter the reset code from your email and choose a new password.'}
        </p>

        {step === 'done' ? (
          <div className="mt-8 rounded-2xl border border-[#D7E6FF] bg-[#F4F8FA] p-5">
            <h2 className="text-lg font-semibold text-[#0D47A1]">Password updated</h2>
            <p className="mt-2 text-sm leading-6 text-[#666666]">
              Your admin password has been reset. You can now sign in with your new credentials.
            </p>
            <div className="mt-6">
              <Link
                href={ROUTES.ADMIN.LOGIN}
                className="inline-flex h-11 w-full items-center justify-center rounded-xl bg-[#0D47A1] text-sm font-semibold text-[#FFFFFF] transition hover:bg-[#4285F4]"
              >
                Back to Login
              </Link>
            </div>
          </div>
        ) : step === 'request' ? (
          <form onSubmit={handleRequest} className="mt-8 space-y-5">
            <div>
              <label htmlFor="email" className="mb-2 block text-sm font-medium text-[#666666]">
                Email Address
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(event) => {
                  setEmail(event.target.value);
                  setError('');
                }}
                placeholder="you@example.com"
                disabled={isLoading}
                className={`h-12 w-full rounded-xl border bg-[#FAFAFA] px-4 text-[#666666] outline-none transition ${
                  error
                    ? 'border-[#EA4335] focus:ring-2 focus:ring-[#EA4335]/20'
                    : 'border-[#CCCCCC] focus:border-[#4285F4] focus:ring-2 focus:ring-[#4285F4]/20'
                }`}
              />
              {error ? <p className="mt-2 text-sm font-medium text-[#EA4335]">{error}</p> : null}
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="h-12 w-full rounded-xl bg-[#0D47A1] text-sm font-semibold text-[#FFFFFF] transition hover:bg-[#4285F4] disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isLoading ? 'Sending reset code...' : 'Send Reset Code'}
            </button>
          </form>
        ) : (
          <form onSubmit={handleVerify} className="mt-8 space-y-5">
            <div>
              <label htmlFor="otp" className="mb-2 block text-sm font-medium text-[#666666]">
                One-time code
              </label>
              <input
                id="otp"
                type="text"
                value={otp}
                onChange={(event) => {
                  setOtp(event.target.value);
                  setError('');
                }}
                placeholder="6-digit code"
                disabled={isLoading}
                className={`h-12 w-full rounded-xl border bg-[#FAFAFA] px-4 text-[#666666] outline-none transition ${
                  error
                    ? 'border-[#EA4335] focus:ring-2 focus:ring-[#EA4335]/20'
                    : 'border-[#CCCCCC] focus:border-[#4285F4] focus:ring-2 focus:ring-[#4285F4]/20'
                }`}
              />
            </div>

            <div>
              <label htmlFor="new-password" className="mb-2 block text-sm font-medium text-[#666666]">
                New password
              </label>
              <input
                id="new-password"
                type="password"
                value={newPassword}
                onChange={(event) => {
                  setNewPassword(event.target.value);
                  setError('');
                }}
                placeholder="Minimum 8 characters"
                disabled={isLoading}
                className={`h-12 w-full rounded-xl border bg-[#FAFAFA] px-4 text-[#666666] outline-none transition ${
                  error
                    ? 'border-[#EA4335] focus:ring-2 focus:ring-[#EA4335]/20'
                    : 'border-[#CCCCCC] focus:border-[#4285F4] focus:ring-2 focus:ring-[#4285F4]/20'
                }`}
              />
            </div>

            <div>
              <label htmlFor="confirm-password" className="mb-2 block text-sm font-medium text-[#666666]">
                Confirm password
              </label>
              <input
                id="confirm-password"
                type="password"
                value={confirmPassword}
                onChange={(event) => {
                  setConfirmPassword(event.target.value);
                  setError('');
                }}
                placeholder="Repeat new password"
                disabled={isLoading}
                className={`h-12 w-full rounded-xl border bg-[#FAFAFA] px-4 text-[#666666] outline-none transition ${
                  error
                    ? 'border-[#EA4335] focus:ring-2 focus:ring-[#EA4335]/20'
                    : 'border-[#CCCCCC] focus:border-[#4285F4] focus:ring-2 focus:ring-[#4285F4]/20'
                }`}
              />
              {error ? <p className="mt-2 text-sm font-medium text-[#EA4335]">{error}</p> : null}
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="h-12 w-full rounded-xl bg-[#0D47A1] text-sm font-semibold text-[#FFFFFF] transition hover:bg-[#4285F4] disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isLoading ? 'Resetting password...' : 'Reset Password'}
            </button>
          </form>
        )}

        <p className="mt-8 text-center text-sm text-[#666666]">
          Remembered your password?{' '}
          <Link href={ROUTES.ADMIN.LOGIN} className="font-semibold text-[#4285F4] hover:text-[#0D47A1] hover:underline">
            Back to login
          </Link>
        </p>
      </section>
    </main>
  );
}
