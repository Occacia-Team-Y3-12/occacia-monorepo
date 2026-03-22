'use client';

import Link from 'next/link';
import { AnimatePresence, motion } from 'framer-motion';
import { ChangeEvent, ClipboardEvent, FormEvent, KeyboardEvent, useEffect, useMemo, useRef, useState } from 'react';

type Step = 1 | 2 | 3 | 4;

const OTP_LENGTH = 6;
const RESEND_SECONDS = 30;
const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const stepMeta: Record<Exclude<Step, 4>, { title: string; subtitle: string }> = {
  1: {
    title: 'Forgot your password?',
    subtitle: 'Enter your customer account email and we will send a verification code.',
  },
  2: {
    title: 'Verify your email',
    subtitle: 'Enter the 6-digit code sent to your inbox.',
  },
  3: {
    title: 'Create a new password',
    subtitle: 'Set a secure password for your customer account.',
  },
};

export default function ForgotPasswordPage() {
  const [step, setStep] = useState<Step>(1);
  const [email, setEmail] = useState('');
  const [emailError, setEmailError] = useState('');

  const [otp, setOtp] = useState<string[]>(Array(OTP_LENGTH).fill(''));
  const [otpError, setOtpError] = useState('');
  const [secondsLeft, setSecondsLeft] = useState(RESEND_SECONDS);

  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordError, setPasswordError] = useState('');
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const otpRefs = useRef<Array<HTMLInputElement | null>>([]);

  const otpValue = useMemo(() => otp.join(''), [otp]);
  const maskedEmail = useMemo(() => {
    const [local, domain] = email.split('@');
    if (!local || !domain) return email;
    const visible = local.slice(0, 2);
    return `${visible}${'*'.repeat(Math.max(local.length - 2, 2))}@${domain}`;
  }, [email]);

  useEffect(() => {
    if (step !== 2 || secondsLeft <= 0) return;
    const timer = setTimeout(() => setSecondsLeft((prev) => prev - 1), 1000);
    return () => clearTimeout(timer);
  }, [step, secondsLeft]);

  useEffect(() => {
    if (step === 2) {
      otpRefs.current[0]?.focus();
    }
  }, [step]);

  const validateEmail = (value: string) => {
    if (!value.trim()) return 'Email is required.';
    if (!EMAIL_REGEX.test(value.trim())) return 'Please enter a valid email address.';
    return '';
  };

  const validatePassword = () => {
    if (newPassword.length < 8) return 'Password must be at least 8 characters.';
    if (confirmPassword.length < 8) return 'Confirm password must be at least 8 characters.';
    if (newPassword !== confirmPassword) return 'Passwords do not match.';
    return '';
  };

  const handleEmailSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const error = validateEmail(email);
    setEmailError(error);
    if (error) return;
    setSecondsLeft(RESEND_SECONDS);
    setOtp(Array(OTP_LENGTH).fill(''));
    setOtpError('');
    setStep(2);
  };

  const handleOtpChange = (index: number, event: ChangeEvent<HTMLInputElement>) => {
    const value = event.target.value.replace(/\D/g, '');
    if (!value) {
      const next = [...otp];
      next[index] = '';
      setOtp(next);
      return;
    }

    const next = [...otp];
    next[index] = value.slice(-1);
    setOtp(next);
    setOtpError('');

    if (index < OTP_LENGTH - 1) {
      otpRefs.current[index + 1]?.focus();
    }
  };

  const handleOtpKeyDown = (index: number, event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Backspace' && !otp[index] && index > 0) {
      otpRefs.current[index - 1]?.focus();
    }
    if (event.key === 'ArrowLeft' && index > 0) {
      otpRefs.current[index - 1]?.focus();
    }
    if (event.key === 'ArrowRight' && index < OTP_LENGTH - 1) {
      otpRefs.current[index + 1]?.focus();
    }
  };

  const handleOtpPaste = (event: ClipboardEvent<HTMLInputElement>) => {
    event.preventDefault();
    const pasted = event.clipboardData.getData('text').replace(/\D/g, '').slice(0, OTP_LENGTH);
    if (!pasted) return;
    const next = Array(OTP_LENGTH).fill('');
    pasted.split('').forEach((digit, idx) => {
      next[idx] = digit;
    });
    setOtp(next);
    setOtpError('');
    otpRefs.current[Math.min(pasted.length, OTP_LENGTH) - 1]?.focus();
  };

  const handleVerifyOtp = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (otpValue.length !== OTP_LENGTH) {
      setOtpError('Please enter the full 6-digit OTP code.');
      return;
    }
    setStep(3);
  };

  const handleResendOtp = () => {
    if (secondsLeft > 0) return;
    setSecondsLeft(RESEND_SECONDS);
    setOtp(Array(OTP_LENGTH).fill(''));
    setOtpError('');
    otpRefs.current[0]?.focus();
  };

  const handleResetPassword = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const error = validatePassword();
    setPasswordError(error);
    if (error) return;
    setStep(4);
  };

  const resetFlow = () => {
    setStep(1);
    setEmail('');
    setEmailError('');
    setOtp(Array(OTP_LENGTH).fill(''));
    setOtpError('');
    setSecondsLeft(RESEND_SECONDS);
    setNewPassword('');
    setConfirmPassword('');
    setPasswordError('');
    setShowNewPassword(false);
    setShowConfirmPassword(false);
  };

  return (
    <main className="relative flex min-h-screen items-center justify-center overflow-hidden bg-gradient-to-br from-[#F4F8FA] via-[#FAFAFA] to-[#FFFFFF] px-4 py-10">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute -left-12 top-12 h-48 w-48 rounded-full bg-[#4285F4]/15 blur-3xl" />
        <div className="absolute -right-16 bottom-8 h-56 w-56 rounded-full bg-[#FBBC05]/20 blur-3xl" />
        <div className="absolute left-1/2 top-1/3 h-44 w-44 -translate-x-1/2 rounded-full bg-[#0D47A1]/10 blur-3xl" />
      </div>

      <section className="relative z-10 w-full max-w-md rounded-3xl border border-[#EAEAEA] bg-[#FFFFFF]/85 p-6 shadow-[0_20px_60px_-32px_rgba(13,71,161,0.45)] backdrop-blur-xl sm:p-8">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#4285F4]">Customer Security</p>
            <h1 className="mt-2 text-2xl font-bold text-[#0D47A1] sm:text-[30px]">Password Recovery</h1>
          </div>
          {step !== 4 && (
            <span className="rounded-full border border-[#EAEAEA] bg-[#F4F8FA] px-3 py-1 text-xs font-semibold text-[#666666]">
              Step {step} of 4
            </span>
          )}
        </div>

        {step !== 4 && (
          <div className="mb-6 h-2 w-full overflow-hidden rounded-full bg-[#EAEAEA]">
            <motion.div
              className="h-full rounded-full bg-gradient-to-r from-[#0D47A1] to-[#4285F4]"
              initial={false}
              animate={{ width: `${(step / 4) * 100}%` }}
              transition={{ duration: 0.35, ease: 'easeInOut' }}
            />
          </div>
        )}

        <AnimatePresence mode="wait">
          <motion.div
            key={step}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.28, ease: 'easeOut' }}
          >
            {step === 1 && (
              <form onSubmit={handleEmailSubmit} className="space-y-5">
                <div>
                  <h2 className="text-lg font-semibold text-[#0D47A1]">{stepMeta[1].title}</h2>
                  <p className="mt-1 text-sm text-[#666666]">{stepMeta[1].subtitle}</p>
                </div>

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
                    className={`h-12 w-full rounded-xl border bg-[#FAFAFA] px-4 text-[#666666] outline-none transition ${
                      emailError ? 'border-[#EA4335] focus:ring-2 focus:ring-[#EA4335]/20' : 'border-[#CCCCCC] focus:border-[#4285F4] focus:ring-2 focus:ring-[#4285F4]/20'
                    }`}
                  />
                  {emailError && <p className="mt-2 text-sm font-medium text-[#EA4335]">{emailError}</p>}
                </div>

                <button
                  type="submit"
                  disabled={!email.trim()}
                  className="h-12 w-full rounded-xl bg-[#0D47A1] text-sm font-semibold text-[#FFFFFF] transition hover:bg-[#4285F4] disabled:cursor-not-allowed disabled:opacity-50"
                >
                  Send OTP Code
                </button>
              </form>
            )}

            {step === 2 && (
              <form onSubmit={handleVerifyOtp} className="space-y-5">
                <div>
                  <h2 className="text-lg font-semibold text-[#0D47A1]">{stepMeta[2].title}</h2>
                  <p className="mt-1 text-sm text-[#666666]">
                    {stepMeta[2].subtitle} <span className="font-medium text-[#0D47A1]">{maskedEmail}</span>
                  </p>
                </div>

                <div className="flex items-center justify-between gap-2">
                  {otp.map((digit, index) => (
                    <input
                      key={`otp-${index}`}
                      ref={(node) => {
                        otpRefs.current[index] = node;
                      }}
                      type="text"
                      inputMode="numeric"
                      maxLength={1}
                      value={digit}
                      onChange={(event) => handleOtpChange(index, event)}
                      onKeyDown={(event) => handleOtpKeyDown(index, event)}
                      onPaste={handleOtpPaste}
                      className={`h-12 w-12 rounded-xl border bg-[#FAFAFA] text-center text-lg font-semibold text-[#0D47A1] outline-none transition sm:h-14 sm:w-14 ${
                        otpError ? 'border-[#EA4335] focus:ring-2 focus:ring-[#EA4335]/20' : 'border-[#CCCCCC] focus:border-[#4285F4] focus:ring-2 focus:ring-[#4285F4]/20'
                      }`}
                    />
                  ))}
                </div>
                {otpError && <p className="text-sm font-medium text-[#EA4335]">{otpError}</p>}

                <div className="flex items-center justify-between text-sm">
                  <button
                    type="button"
                    onClick={() => setStep(1)}
                    className="font-medium text-[#666666] transition hover:text-[#0D47A1]"
                  >
                    Back
                  </button>
                  <button
                    type="button"
                    onClick={handleResendOtp}
                    disabled={secondsLeft > 0}
                    className="font-semibold text-[#4285F4] transition hover:text-[#0D47A1] disabled:cursor-not-allowed disabled:text-[#C9C9C9]"
                  >
                    {secondsLeft > 0 ? `Resend in ${secondsLeft}s` : 'Resend OTP'}
                  </button>
                </div>

                <button
                  type="submit"
                  disabled={otpValue.length !== OTP_LENGTH}
                  className="h-12 w-full rounded-xl bg-[#0D47A1] text-sm font-semibold text-[#FFFFFF] transition hover:bg-[#4285F4] disabled:cursor-not-allowed disabled:opacity-50"
                >
                  Verify OTP
                </button>
              </form>
            )}

            {step === 3 && (
              <form onSubmit={handleResetPassword} className="space-y-5">
                <div>
                  <h2 className="text-lg font-semibold text-[#0D47A1]">{stepMeta[3].title}</h2>
                  <p className="mt-1 text-sm text-[#666666]">{stepMeta[3].subtitle}</p>
                </div>

                <div>
                  <label htmlFor="new-password" className="mb-2 block text-sm font-medium text-[#666666]">
                    New Password
                  </label>
                  <div className={`flex h-12 items-center rounded-xl border bg-[#FAFAFA] pr-2 ${passwordError ? 'border-[#EA4335]' : 'border-[#CCCCCC]'}`}>
                    <input
                      id="new-password"
                      type={showNewPassword ? 'text' : 'password'}
                      value={newPassword}
                      onChange={(event) => {
                        setNewPassword(event.target.value);
                        setPasswordError('');
                      }}
                      placeholder="At least 8 characters"
                      className="h-full w-full bg-transparent px-4 text-[#666666] outline-none"
                    />
                    <button
                      type="button"
                      onClick={() => setShowNewPassword((prev) => !prev)}
                      className="rounded-lg px-3 py-1.5 text-xs font-semibold text-[#0D47A1] transition hover:bg-[#F4F8FA]"
                    >
                      {showNewPassword ? 'Hide' : 'Show'}
                    </button>
                  </div>
                </div>

                <div>
                  <label htmlFor="confirm-password" className="mb-2 block text-sm font-medium text-[#666666]">
                    Confirm Password
                  </label>
                  <div className={`flex h-12 items-center rounded-xl border bg-[#FAFAFA] pr-2 ${passwordError ? 'border-[#EA4335]' : 'border-[#CCCCCC]'}`}>
                    <input
                      id="confirm-password"
                      type={showConfirmPassword ? 'text' : 'password'}
                      value={confirmPassword}
                      onChange={(event) => {
                        setConfirmPassword(event.target.value);
                        setPasswordError('');
                      }}
                      placeholder="Re-enter your password"
                      className="h-full w-full bg-transparent px-4 text-[#666666] outline-none"
                    />
                    <button
                      type="button"
                      onClick={() => setShowConfirmPassword((prev) => !prev)}
                      className="rounded-lg px-3 py-1.5 text-xs font-semibold text-[#0D47A1] transition hover:bg-[#F4F8FA]"
                    >
                      {showConfirmPassword ? 'Hide' : 'Show'}
                    </button>
                  </div>
                </div>

                {passwordError && <p className="text-sm font-medium text-[#EA4335]">{passwordError}</p>}

                <div className="flex items-center justify-between text-sm">
                  <button
                    type="button"
                    onClick={() => setStep(2)}
                    className="font-medium text-[#666666] transition hover:text-[#0D47A1]"
                  >
                    Back
                  </button>
                  <span className="text-[#666666]">Use 8+ chars for stronger security</span>
                </div>

                <button
                  type="submit"
                  disabled={!newPassword || !confirmPassword}
                  className="h-12 w-full rounded-xl bg-[#0D47A1] text-sm font-semibold text-[#FFFFFF] transition hover:bg-[#4285F4] disabled:cursor-not-allowed disabled:opacity-50"
                >
                  Reset Password
                </button>
              </form>
            )}

            {step === 4 && (
              <div className="space-y-5 text-center">
                <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-[#F4F8FA]">
                  <svg viewBox="0 0 24 24" className="h-8 w-8 text-[#0D47A1]" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="m5 12 4 4L19 6" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-[#0D47A1]">Password Reset Successful</h2>
                  <p className="mt-2 text-sm text-[#666666]">Your password has been updated. You can now log in to your customer account.</p>
                </div>
                <Link
                  href="/customer/auth/login"
                  className="inline-flex h-12 w-full items-center justify-center rounded-xl bg-[#0D47A1] text-sm font-semibold text-[#FFFFFF] transition hover:bg-[#4285F4]"
                >
                  Back to Login
                </Link>
                <button
                  type="button"
                  onClick={resetFlow}
                  className="text-sm font-medium text-[#666666] transition hover:text-[#0D47A1]"
                >
                  Reset another password
                </button>
              </div>
            )}
          </motion.div>
        </AnimatePresence>

        {step !== 4 && (
          <div className="mt-7 text-center text-sm text-[#666666]">
            Remember your password?{' '}
            <Link href="/customer/auth/login" className="font-semibold text-[#4285F4] hover:text-[#0D47A1]">
              Back to Login
            </Link>
          </div>
        )}
      </section>
    </main>
  );
}
