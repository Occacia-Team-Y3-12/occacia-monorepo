import React from 'react';
import AdminSidebar from '@/components/admin/AdminSidebar';

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
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