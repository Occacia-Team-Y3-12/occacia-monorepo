'use client';

import { Suspense, useEffect, useMemo, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { getStoredCustomerToken } from '@/services/customer/authService.shared';
import { ROUTES } from '@/lib/routes';

const resolveRedirectUri = () => {
  const configured = process.env.NEXT_PUBLIC_GOOGLE_REDIRECT_URI?.trim();
  if (configured) {
    return configured;
  }
  if (typeof window !== 'undefined') {
    return `${window.location.origin}/oauth/callback`;
  }
  return '';
};

function OAuthCallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [message, setMessage] = useState('Completing Google Calendar connection...');

  const code = useMemo(() => searchParams.get('code') || '', [searchParams]);
  const state = useMemo(() => searchParams.get('state') || '', [searchParams]);

  useEffect(() => {
    const run = async () => {
      const returnPath =
        (typeof window !== 'undefined' && window.sessionStorage.getItem('customer:calendarReturnPath'))
        || ROUTES.CUSTOMER.EVENTS;

      const token = getStoredCustomerToken();
      if (!token) {
        setMessage('Session expired. Please log in and connect calendar again.');
        router.replace(ROUTES.CUSTOMER.LOGIN);
        return;
      }

      if (!code) {
        setMessage('Missing authorization code.');
        router.replace(returnPath);
        return;
      }

      try {
        const response = await fetch('/api/v1/customers/calendar/exchange-code', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            provider: 'google',
            code,
            state: state || undefined,
            redirectUri: resolveRedirectUri(),
          }),
        });

        if (!response.ok) {
          setMessage('Failed to complete calendar connection.');
          router.replace(returnPath);
          return;
        }

        setMessage('Calendar connected. Redirecting...');
        router.replace(returnPath);
      } catch {
        setMessage('Failed to complete calendar connection.');
        router.replace(returnPath);
      } finally {
        if (typeof window !== 'undefined') {
          window.sessionStorage.removeItem('customer:calendarReturnPath');
        }
      }
    };

    void run();
  }, [code, router, state]);

  return (
    <main className="flex min-h-screen items-center justify-center bg-[#F4F8FA] p-6">
      <div className="w-full max-w-md rounded-2xl border border-[#EAEAEA] bg-white p-6 text-center">
        <h1 className="text-lg font-semibold text-[#0D47A1]">Calendar Authorization</h1>
        <p className="mt-2 text-sm text-[#666666]">{message}</p>
      </div>
    </main>
  );
}

export default function OAuthCallbackPage() {
  return (
    <Suspense fallback={
      <main className="flex min-h-screen items-center justify-center bg-[#F4F8FA] p-6">
        <div className="w-full max-w-md rounded-2xl border border-[#EAEAEA] bg-white p-6 text-center">
          <h1 className="text-lg font-semibold text-[#0D47A1]">Calendar Authorization</h1>
          <p className="mt-2 text-sm text-[#666666]">Preparing callback...</p>
        </div>
      </main>
    }
    >
      <OAuthCallbackContent />
    </Suspense>
  );
}
