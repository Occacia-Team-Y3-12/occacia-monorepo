'use client';

import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { FormEvent, Suspense, useMemo, useState } from 'react';
import { CheckCircle, Eye, EyeOff, XCircle } from 'lucide-react';
import { toast } from 'sonner';

import { ROUTES } from '@/lib/routes';
import { customerAuthService } from '@/services/customer/authServices';

function CustomerResetPasswordContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get('token');

  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [tokenError, setTokenError] = useState(false);
  const [resetSuccess, setResetSuccess] = useState(false);

  const passwordRules = useMemo(() => {
    const minLength = password.length >= 8;
    const hasUpperCase = /[A-Z]/.test(password);
    const hasLowerCase = /[a-z]/.test(password);
    const hasNumber = /[0-9]/.test(password);
    const hasSpecialChar = /[!@#$%^&*(),.?":{}|<>]/.test(password);

    return {
      minLength,
      hasUpperCase,
      hasLowerCase,
      hasNumber,
      hasSpecialChar,
      isValid: minLength && hasUpperCase && hasLowerCase && hasNumber && hasSpecialChar,
    };
  }, [password]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!token) {
      setTokenError(true);
      toast.error('Invalid or expired reset link.');
      return;
    }

    if (!passwordRules.isValid) {
      toast.error('Password does not meet the requirements.');
      return;
    }

    if (password !== confirmPassword) {
      toast.error('Passwords do not match.');
      return;
    }

    setIsLoading(true);

    try {
      await customerAuthService.resetPassword({ token, password });
      setResetSuccess(true);
      toast.success('Password updated successfully.');
      setTimeout(() => {
        router.replace(ROUTES.CUSTOMER.LOGIN);
      }, 2500);
    } catch (error) {
      const message =
        (error as { response?: { data?: { detail?: string; message?: string } } })?.response?.data?.detail ||
        (error as { response?: { data?: { detail?: string; message?: string } } })?.response?.data?.message ||
        (error instanceof Error ? error.message : '') ||
        'Unable to reset password. Please request a new reset link.';

      if (message.toLowerCase().includes('invalid') || message.toLowerCase().includes('expired')) {
        setTokenError(true);
      }

      toast.error(message);
    } finally {
      setIsLoading(false);
    }
  };

  if (tokenError || !token) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-gradient-to-br from-[#F4F8FA] via-[#FAFAFA] to-[#FFFFFF] px-4 py-10">
        <section className="w-full max-w-md rounded-3xl border border-[#EAEAEA] bg-[#FFFFFF] p-8 text-center shadow-[0_20px_60px_-32px_rgba(13,71,161,0.45)]">
          <div className="mx-auto mb-6 inline-flex h-20 w-20 items-center justify-center rounded-full bg-[#FDECEC] text-[#EA4335]">
            <XCircle className="h-10 w-10" />
          </div>
          <h1 className="text-3xl font-bold text-[#0D47A1]">Link Invalid or Expired</h1>
          <p className="mt-3 text-sm leading-6 text-[#666666]">
            This password reset link is invalid or has expired. Request a new password reset email to continue.
          </p>
          <div className="mt-8 flex flex-col gap-3">
            <Link
              href={ROUTES.CUSTOMER.FORGOT_PASSWORD}
              className="inline-flex h-11 items-center justify-center rounded-xl bg-[#0D47A1] text-sm font-semibold text-[#FFFFFF] transition hover:bg-[#4285F4]"
            >
              Request New Link
            </Link>
            <Link
              href={ROUTES.CUSTOMER.LOGIN}
              className="inline-flex h-11 items-center justify-center rounded-xl border border-[#CCCCCC] bg-[#FFFFFF] text-sm font-semibold text-[#0D47A1] transition hover:border-[#4285F4]"
            >
              Back to Login
            </Link>
          </div>
        </section>
      </main>
    );
  }

  if (resetSuccess) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-gradient-to-br from-[#F4F8FA] via-[#FAFAFA] to-[#FFFFFF] px-4 py-10">
        <section className="w-full max-w-md rounded-3xl border border-[#EAEAEA] bg-[#FFFFFF] p-8 text-center shadow-[0_20px_60px_-32px_rgba(13,71,161,0.45)]">
          <div className="mx-auto mb-6 inline-flex h-20 w-20 items-center justify-center rounded-full bg-[#EAF6EE] text-[#34A853]">
            <CheckCircle className="h-10 w-10" />
          </div>
          <h1 className="text-3xl font-bold text-[#0D47A1]">Password Reset Successful</h1>
          <p className="mt-3 text-sm leading-6 text-[#666666]">
            Your password has been updated. You can now sign in with your new password.
          </p>
          <Link
            href={ROUTES.CUSTOMER.LOGIN}
            className="mt-8 inline-flex h-11 w-full items-center justify-center rounded-xl bg-[#0D47A1] text-sm font-semibold text-[#FFFFFF] transition hover:bg-[#4285F4]"
          >
            Go to Login
          </Link>
        </section>
      </main>
    );
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-gradient-to-br from-[#F4F8FA] via-[#FAFAFA] to-[#FFFFFF] px-4 py-10">
      <section className="w-full max-w-md rounded-3xl border border-[#EAEAEA] bg-[#FFFFFF] p-8 shadow-[0_20px_60px_-32px_rgba(13,71,161,0.45)]">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#4285F4]">Customer Security</p>
        <h1 className="mt-2 text-3xl font-bold text-[#0D47A1]">Set a new password</h1>
        <p className="mt-3 text-sm leading-6 text-[#666666]">
          Choose a strong new password for your customer account.
        </p>

        <form onSubmit={handleSubmit} className="mt-8 space-y-5">
          <div>
            <label htmlFor="password" className="mb-2 block text-sm font-medium text-[#666666]">
              New Password
            </label>
            <div className="relative">
              <input
                id="password"
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                disabled={isLoading}
                placeholder="Enter new password"
                className="h-12 w-full rounded-xl border border-[#CCCCCC] bg-[#FAFAFA] px-4 pr-12 text-[#666666] outline-none transition focus:border-[#4285F4] focus:ring-2 focus:ring-[#4285F4]/20"
              />
              <button
                type="button"
                onClick={() => setShowPassword((prev) => !prev)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-[#666666]"
                aria-label={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>

          <div>
            <label htmlFor="confirmPassword" className="mb-2 block text-sm font-medium text-[#666666]">
              Confirm Password
            </label>
            <div className="relative">
              <input
                id="confirmPassword"
                type={showConfirmPassword ? 'text' : 'password'}
                value={confirmPassword}
                onChange={(event) => setConfirmPassword(event.target.value)}
                disabled={isLoading}
                placeholder="Confirm new password"
                className="h-12 w-full rounded-xl border border-[#CCCCCC] bg-[#FAFAFA] px-4 pr-12 text-[#666666] outline-none transition focus:border-[#4285F4] focus:ring-2 focus:ring-[#4285F4]/20"
              />
              <button
                type="button"
                onClick={() => setShowConfirmPassword((prev) => !prev)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-[#666666]"
                aria-label={showConfirmPassword ? 'Hide confirm password' : 'Show confirm password'}
              >
                {showConfirmPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>

          <div className="rounded-2xl border border-[#EAEAEA] bg-[#F4F8FA] p-4">
            <p className="mb-2 text-sm font-semibold text-[#0D47A1]">Password requirements</p>
            <div className="space-y-1 text-xs text-[#666666]">
              <p className={passwordRules.minLength ? 'text-[#34A853]' : undefined}>At least 8 characters</p>
              <p className={passwordRules.hasUpperCase ? 'text-[#34A853]' : undefined}>One uppercase letter</p>
              <p className={passwordRules.hasLowerCase ? 'text-[#34A853]' : undefined}>One lowercase letter</p>
              <p className={passwordRules.hasNumber ? 'text-[#34A853]' : undefined}>One number</p>
              <p className={passwordRules.hasSpecialChar ? 'text-[#34A853]' : undefined}>One special character</p>
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading || !passwordRules.isValid || password !== confirmPassword}
            className="h-12 w-full rounded-xl bg-[#0D47A1] text-sm font-semibold text-[#FFFFFF] transition hover:bg-[#4285F4] disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isLoading ? 'Resetting password...' : 'Reset Password'}
          </button>
        </form>
      </section>
    </main>
  );
}

export default function CustomerResetPasswordPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <CustomerResetPasswordContent />
    </Suspense>
  );
}
