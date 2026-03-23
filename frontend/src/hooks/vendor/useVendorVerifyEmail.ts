import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { ROUTES } from '@/lib/routes';
import { vendorAuthService } from '@/services/vendor/authService';

type VerificationStatus = 'pending' | 'loading' | 'success' | 'error';

export const useVendorVerifyEmail = (
  token: string | null,
  email: string | null
) => {
  const router = useRouter();
  const [status, setStatus] = useState<VerificationStatus>(() => {
    if (token) {
      return 'loading';
    }
    if (email) {
      return 'pending';
    }
    return 'error';
  });
  const [message, setMessage] = useState<string | null>(null);
  const [isResending, setIsResending] = useState(false);

  useEffect(() => {
    let redirectTimer: ReturnType<typeof setTimeout> | undefined;

    if (!token) {
      setStatus(email ? 'pending' : 'error');
      setMessage(
        email
          ? 'We sent a verification link to your email address. Open it to move your account into admin review.'
          : 'The verification link is invalid or missing.'
      );
      return;
    }

    setStatus('loading');
    setMessage('Verifying your email...');

    vendorAuthService.verifyEmail(token).then((result) => {
      if (result.ok) {
        setStatus('success');
        setMessage(result.message || 'Email verified successfully. Your account is pending admin approval.');
        redirectTimer = setTimeout(() => {
          router.replace(ROUTES.VENDOR.PENDING_APPROVAL);
        }, 2000);
      } else {
        setStatus('error');
        setMessage(result.message || 'The verification link is invalid or expired.');
      }
    });

    return () => {
      if (redirectTimer) {
        clearTimeout(redirectTimer);
      }
    };
  }, [email, router, token]);

  const resendVerification = async () => {
    if (!email) {
      return;
    }

    setIsResending(true);
    const result = await vendorAuthService.resendVerification(email);
    setIsResending(false);

    if (result.ok) {
      setMessage(result.message || 'Verification email resent successfully.');
      return;
    }

    setStatus('error');
    setMessage(result.message || 'Unable to resend the verification email right now.');
  };

  return { status, message, isResending, resendVerification };
};
