import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { ROUTES } from '@/lib/routes';
import { vendorAuthService } from '@/services/vendor/authService';

export const useVendorVerifyEmail = (token: string | null) => {
  const router = useRouter();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');

  useEffect(() => {
    let redirectTimer: ReturnType<typeof setTimeout> | undefined;

    vendorAuthService.verifyEmail(token).then((result) => {
      if (result.ok) {
        setStatus('success');
        redirectTimer = setTimeout(() => {
          router.push(ROUTES.VENDOR.PENDING_APPROVAL);
        }, 2000);
      } else {
        setStatus('error');
      }
    });

    return () => {
      if (redirectTimer) {
        clearTimeout(redirectTimer);
      }
    };
  }, [router, token]);

  return { status };
};
