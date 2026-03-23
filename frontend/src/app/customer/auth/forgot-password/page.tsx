'use client';

import Link from 'next/link';
import { FormEvent, useState } from 'react';
import { toast } from 'sonner';

import { ROUTES } from '@/lib/routes';
import { customerAuthService } from '@/services/customer/authServices';

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [emailError, setEmailError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [submittedEmail, setSubmittedEmail] = useState('');

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const normalizedEmail = email.trim();

    if (!normalizedEmail) {
      setEmailError('Email is required.');
      return;
    }

    if (!EMAIL_REGEX.test(normalizedEmail)) {
      setEmailError('Please enter a valid email address.');
      return;
    }

    setIsLoading(true);
    setEmailError('');

    try {
      const response = await customerAuthService.forgotPassword(normalizedEmail);
      setSubmittedEmail(normalizedEmail);
      toast.success(
        response.message || 'If this email is registered, a password reset link has been sent.'
      );
    } catch (error) {
      const message =
        (error as { response?: { data?: { detail?: string; message?: string } } })?.response?.data?.detail ||
        (error as { response?: { data?: { detail?: string; message?: string } } })?.response?.data?.message ||
        (error instanceof Error ? error.message : '') ||
        'Unable to send password reset email. Please try again.';
      toast.error(message);
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
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#4285F4]">Customer Security</p>
        <h1 className="mt-2 text-2xl font-bold text-[#0D47A1] sm:text-[30px]">Forgot your password?</h1>
        <p className="mt-3 text-sm leading-6 text-[#666666]">
          Enter your customer account email and we will send you a secure password reset link.
        </p>

        {submittedEmail ? (
          <div className="mt-8 rounded-2xl border border-[#D7E6FF] bg-[#F4F8FA] p-5">
            <h2 className="text-lg font-semibold text-[#0D47A1]">Check your inbox</h2>
            <p className="mt-2 text-sm leading-6 text-[#666666]">
              If <span className="font-medium text-[#0D47A1]">{submittedEmail}</span> is registered, a password reset
              link has been sent. Open the email and use the link to set a new password.
            </p>
            <div className="mt-6 flex flex-col gap-3">
              <button
                type="button"
                onClick={() => {
                  setSubmittedEmail('');
                  setEmail('');
                }}
                className="h-11 rounded-xl border border-[#CCCCCC] bg-[#FFFFFF] text-sm font-semibold text-[#0D47A1] transition hover:border-[#4285F4]"
              >
                Use another email
              </button>
              <Link
                href={ROUTES.CUSTOMER.LOGIN}
                className="inline-flex h-11 items-center justify-center rounded-xl bg-[#0D47A1] text-sm font-semibold text-[#FFFFFF] transition hover:bg-[#4285F4]"
              >
                Back to Login
              </Link>
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="mt-8 space-y-5">
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
                  setEmailError('');
                }}
                placeholder="you@example.com"
                disabled={isLoading}
                className={`h-12 w-full rounded-xl border bg-[#FAFAFA] px-4 text-[#666666] outline-none transition ${
                  emailError
                    ? 'border-[#EA4335] focus:ring-2 focus:ring-[#EA4335]/20'
                    : 'border-[#CCCCCC] focus:border-[#4285F4] focus:ring-2 focus:ring-[#4285F4]/20'
                }`}
              />
              {emailError ? <p className="mt-2 text-sm font-medium text-[#EA4335]">{emailError}</p> : null}
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="h-12 w-full rounded-xl bg-[#0D47A1] text-sm font-semibold text-[#FFFFFF] transition hover:bg-[#4285F4] disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isLoading ? 'Sending reset link...' : 'Send Reset Link'}
            </button>
          </form>
        )}

        <p className="mt-8 text-center text-sm text-[#666666]">
          Remembered your password?{' '}
          <Link href={ROUTES.CUSTOMER.LOGIN} className="font-semibold text-[#4285F4] hover:text-[#0D47A1] hover:underline">
            Back to login
          </Link>
        </p>
      </section>
    </main>
  );
}
