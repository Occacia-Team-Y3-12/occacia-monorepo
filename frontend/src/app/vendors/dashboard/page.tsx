'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { ROUTES } from '@/lib/routes';

export default function VendorDashboard() {
  const router = useRouter();

  useEffect(() => {
    // Add authentication check here
    const checkAuth = async () => {
      try {
        const response = await fetch('/api/v1/auth/check');
        if (!response.ok) {
          router.push(ROUTES.VENDORS.LOGIN);
        }
      } catch (error) {
        router.push(ROUTES.VENDORS.LOGIN);
      }
    };

    checkAuth();
  }, [router]);

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-4xl font-bold text-[#2c3e50] mb-8">Vendor Dashboard</h1>
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-[#5a6c7d]">Welcome to your vendor dashboard!</p>
        </div>
      </div>
    </div>
  );
}
