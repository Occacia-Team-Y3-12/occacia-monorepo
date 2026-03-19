'use client';

import React, { useState } from 'react';
import { usePathname } from 'next/navigation';
import CustomerSidebar from '@/components/features/customer/CustomerSidebar';
import CustomerHeader from '@/components/features/customer/CustomerHeader';

export default function CustomerLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isDesktopSidebarCollapsed, setIsDesktopSidebarCollapsed] = useState(false);
  const pathname = usePathname();
  const isAuthPage = pathname?.startsWith('/customer/auth');

  if (isAuthPage) return <>{children}</>;

  return (
    <div className="min-h-screen overflow-x-hidden bg-[#F7F7FA]">
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
