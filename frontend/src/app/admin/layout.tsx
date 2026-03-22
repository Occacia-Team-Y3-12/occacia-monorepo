'use client';

import React, { useEffect, useState } from 'react';
import { usePathname, useRouter } from 'next/navigation';

import AdminSidebar from '@/components/admin/AdminSidebar';
import { ROUTES } from '@/lib/routes';
import { adminAuthService } from '@/services/admin/authService';

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const [isAllowed, setIsAllowed] = useState(false);

  useEffect(() => {
    if (pathname === ROUTES.ADMIN.LOGIN) {
      setIsAllowed(true);
      return;
    }

    const role = adminAuthService.detectSessionRole();
    if (role === 'ADMIN') {
      setIsAllowed(true);
      return;
    }

    if (role === 'CUSTOMER') {
      router.replace(ROUTES.CUSTOMER.LOGIN);
      return;
    }

    if (role === 'VENDOR') {
      router.replace(ROUTES.VENDOR.LOGIN);
      return;
    }

    router.replace(ROUTES.ADMIN.LOGIN);
  }, [pathname, router]);

  if (!isAllowed) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50 text-sm text-gray-600">
        Checking access...
      </div>
    );
  }

  if (pathname === ROUTES.ADMIN.LOGIN) {
    return <>{children}</>;
  }

  return (
    <div className="flex min-h-screen bg-gray-50">
      <AdminSidebar />
      <main className="flex-1 pl-64">
        <div className="min-h-screen bg-gray-50/50">
          {children}
        </div>
      </main>
    </div>
  );
}
