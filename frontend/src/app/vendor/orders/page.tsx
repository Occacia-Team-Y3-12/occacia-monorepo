'use client';

import { useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import VendorPortalShell from '@/components/features/vendor/VendorPortalShell';
import { formatCurrency } from '@/lib/currency';

interface VendorOrder {
  id: string;
  customerName: string;
  date: string;
  amount: number;
  status: 'pending' | 'processing' | 'completed' | 'cancelled';
}

type OrderStatusFilter = 'all' | VendorOrder['status'];

function getOrderStatusFilter(value: string | null): OrderStatusFilter {
  if (value === 'pending' || value === 'processing' || value === 'completed' || value === 'cancelled') {
    return value;
  }

  return 'all';
}

export default function VendorOrdersPage() {
  const searchParams = useSearchParams();
  const [statusFilter, setStatusFilter] = useState<OrderStatusFilter>(() => getOrderStatusFilter(searchParams.get('status')));
  const orders: VendorOrder[] = [];

  useEffect(() => {
    setStatusFilter(getOrderStatusFilter(searchParams.get('status')));
  }, [searchParams]);

  const statuses: Array<{ value: OrderStatusFilter; label: string; count: number }> = [
    { value: 'all', label: 'All Orders', count: 0 },
    { value: 'pending', label: 'Pending', count: 0 },
    { value: 'processing', label: 'Processing', count: 0 },
    { value: 'completed', label: 'Completed', count: 0 },
    { value: 'cancelled', label: 'Cancelled', count: 0 },
  ];

  return (
    <VendorPortalShell>
      <div className="max-w-7xl mx-auto">
        <div className="bg-white border border-gray-200 rounded-2xl py-4 md:py-6 px-4 sm:px-8 shadow-[0_4px_16px_rgba(15,23,42,0.06)]">
          <h1 className="text-2xl sm:text-3xl md:text-4xl font-bold text-gray-900">Orders</h1>
          <p className="text-gray-600 mt-1 md:mt-2 text-sm md:text-base">Manage and track your orders</p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-0 py-8 md:py-12">
        {/* Status Tabs */}
        <div className="mb-6 grid grid-cols-1 gap-3 sm:grid-cols-3 md:gap-4 lg:grid-cols-5 md:mb-8">
          {statuses.map((status) => (
            <button
              key={status.value}
              onClick={() => setStatusFilter(status.value)}
              className={`p-3 md:p-4 rounded-lg font-semibold transition-all text-sm md:text-base ${
                statusFilter === status.value
                  ? 'bg-[#1565c0] text-white'
                  : 'bg-white text-[#1F293F] border border-[#E2E5EC] hover:border-[#4285F4]'
              }`}
            >
              <div className="text-base md:text-lg">{status.label}</div>
              <div className={statusFilter === status.value ? 'text-[#D7E6FF] text-xs md:text-sm' : 'text-[#5B6478] text-xs md:text-sm'}>
                {status.count}
              </div>
            </button>
          ))}
        </div>

        {/* Orders List */}
        <div className="space-y-4">
          {orders.length === 0 ? (
            <div className="bg-white rounded-lg shadow-md p-8 md:p-12 text-center">
              <div className="text-4xl md:text-6xl mb-3 md:mb-4">📋</div>
              <h2 className="text-xl md:text-2xl font-bold text-gray-900 mb-3 md:mb-4">No orders found</h2>
              <p className="text-gray-600 text-sm md:text-base">Orders will appear here once customers place them</p>
            </div>
          ) : (
            orders.map((_, index) => (
              <div key={index} className="bg-white rounded-lg shadow-md p-4 md:p-6 hover:shadow-lg transition-shadow">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 md:gap-4">
                  <div className="flex-1">
                    <h3 className="font-bold text-gray-900 text-sm md:text-base">Order #12345</h3>
                    <p className="text-gray-600 text-sm">Customer: John Doe | Date: N/A</p>
                  </div>
                  <div className="flex flex-col sm:flex-row sm:items-center gap-3">
                    <span className="text-base md:text-lg font-semibold text-[#1565c0]">{formatCurrency(0)}</span>
                    <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-semibold">Pending</span>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </VendorPortalShell>
  );
}
