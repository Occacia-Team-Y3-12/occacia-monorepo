'use client';

import React, { useState } from 'react';
import CustomerSidebar from '@/components/features/customer/CustomerSidebar';
import CustomerHeader from '@/components/features/customer/CustomerHeader';

export default function CustomerLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen overflow-x-hidden bg-[#F7F7FA]">
      <CustomerSidebar isOpen={isSidebarOpen} />
      {isSidebarOpen && (
        <button
          aria-label="Close sidebar overlay"
          onClick={() => setIsSidebarOpen(false)}
          className="fixed inset-0 z-30 bg-black/20 lg:hidden"
        />
      )}
      <CustomerHeader isSidebarOpen={isSidebarOpen} onToggleSidebar={() => setIsSidebarOpen((prev) => !prev)} />
      <main className={`px-4 pb-6 pt-4 transition-all duration-300 sm:px-6 sm:pt-6 ${isSidebarOpen ? 'lg:ml-[240px]' : 'ml-0'}`}>
        {children}
      </main>
    </div>
  );
}
