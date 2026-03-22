'use client';

import React, { useEffect, useState } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import CustomerSidebar from '@/components/features/customer/CustomerSidebar';
import CustomerHeader from '@/components/features/customer/CustomerHeader';
import { CustomerAuthProvider } from '@/app/context/AuthContext';
import { ROUTES } from '@/lib/routes';
import { customerAuthService } from '@/services/customer/authServices';

function CustomerLayoutInner({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isDesktopSidebarCollapsed, setIsDesktopSidebarCollapsed] = useState(false);
  const [authChecked, setAuthChecked] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const pathname = usePathname();
  const isAuthPage = pathname?.startsWith('/customer/auth');

  useEffect(() => {
    if (isAuthPage) {
      setAuthChecked(true);
      setIsAuthenticated(false);
      return;
    }

    const authenticated = customerAuthService.isAuthenticated();
    setIsAuthenticated(authenticated);
    setAuthChecked(true);

    if (!authenticated) {
      router.replace(ROUTES.CUSTOMER.LOGIN);
    }
  }, [isAuthPage, router]);

  if (isAuthPage) return <div className="customer-portal-font">{children}</div>;
  if (!authChecked || !isAuthenticated) {
    return (
      <div className="customer-portal-font flex min-h-screen items-center justify-center bg-[#F4F8FA] text-sm text-[#5B6780]">
        Checking access...
      </div>
    );
  }

  return (
    <div className="customer-portal-font min-h-screen overflow-x-hidden bg-[#F4F8FA]">
      <CustomerSidebar
        isOpen={isSidebarOpen}
        isDesktopCollapsed={isDesktopSidebarCollapsed}
        onToggleDesktopSidebar={() => setIsDesktopSidebarCollapsed((prev) => !prev)}
      />
      {isSidebarOpen && (
        <button
          aria-label="Close sidebar overlay"
          onClick={() => setIsSidebarOpen(false)}
          className="fixed inset-0 z-30 bg-black/20 lg:hidden"
        />
      )}
      <CustomerHeader
        isSidebarOpen={isSidebarOpen}
        isDesktopSidebarCollapsed={isDesktopSidebarCollapsed}
        onToggleSidebar={() => setIsSidebarOpen((prev) => !prev)}
        onToggleDesktopSidebar={() => setIsDesktopSidebarCollapsed((prev) => !prev)}
      />
      <main className={`px-4 pb-6 pt-4 transition-all duration-300 sm:px-6 sm:pt-6 ${isDesktopSidebarCollapsed ? 'lg:ml-0' : 'lg:ml-[240px]'}`}>
        {children}
      </main>
    </div>
  );
}

export default function CustomerLayout({ children }: { children: React.ReactNode }) {
  return (
    <CustomerAuthProvider>
      <CustomerLayoutInner>{children}</CustomerLayoutInner>
    </CustomerAuthProvider>
  );
}
