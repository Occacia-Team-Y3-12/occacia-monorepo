'use client';

import React, { useState, useEffect } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import CustomerSidebar from '@/components/features/customer/CustomerSidebar';
import CustomerHeader from '@/components/features/customer/CustomerHeader';
import { CustomerAuthProvider } from '@/app/context/AuthContext';
import { customerAuthService } from '@/services/customer/authServices';

function CustomerLayoutInner({ children }: { children: React.ReactNode }) {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isDesktopSidebarCollapsed, setIsDesktopSidebarCollapsed] = useState(false);
  const pathname = usePathname();
  const router = useRouter();
  const isAuthPage = pathname?.startsWith('/customer/auth');

  useEffect(() => {
    if (!isAuthPage && !customerAuthService.isAuthenticated()) {
      router.replace('/customer/auth/login');
    }
  }, [isAuthPage, router]);

  if (isAuthPage) return <div className="customer-portal-font">{children}</div>;

  return (
    <div className="customer-portal-font min-h-screen overflow-x-hidden bg-[#F7F7FA]">
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
