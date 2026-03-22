'use client';

import React, { useEffect, useState } from 'react';
import { usePathname, useRouter } from 'next/navigation';

import { ROUTES } from '@/lib/routes';
import { isVendorAuthenticated } from '@/services/vendor/authService.shared';

export default function VendorLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const [authChecked, setAuthChecked] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const isAuthPage = pathname?.startsWith('/vendor/auth');

  useEffect(() => {
    if (isAuthPage) {
      setAuthChecked(true);
      setIsAuthenticated(false);
      return;
    }

    const authenticated = isVendorAuthenticated();
    setIsAuthenticated(authenticated);
    setAuthChecked(true);

    if (!authenticated) {
      router.replace(ROUTES.VENDOR.LOGIN);
    }
  }, [isAuthPage, router]);

  if (isAuthPage) {
    return <>{children}</>;
  }

  if (!authChecked || !isAuthenticated) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50 text-sm text-slate-600">
        Checking access...
      </div>
    );
  }

  return <>{children}</>;
}
