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
    <div className="min-h-screen bg-[#F7F7FA]">
      <CustomerSidebar isOpen={isSidebarOpen} />
      <CustomerHeader isSidebarOpen={isSidebarOpen} onToggleSidebar={() => setIsSidebarOpen((prev) => !prev)} />
      <main className={`px-6 pb-6 pt-6 transition-all duration-300 ${isSidebarOpen ? 'ml-[240px]' : 'ml-0'}`}>
        {children}
      </main>
    </div>
  );
}
