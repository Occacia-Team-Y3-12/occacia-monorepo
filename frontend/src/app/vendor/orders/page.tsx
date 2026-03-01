'use client';

import { useState } from 'react';

export default function VendorOrdersPage() {
  const [statusFilter, setStatusFilter] = useState('all');
  const orders = [];

  const statuses = [
    { value: 'all', label: 'All Orders', count: 0 },
    { value: 'pending', label: 'Pending', count: 0 },
    { value: 'processing', label: 'Processing', count: 0 },
    { value: 'completed', label: 'Completed', count: 0 },
    { value: 'cancelled', label: 'Cancelled', count: 0 },
  ];

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 py-4 md:py-6 px-4 sm:px-8">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-2xl sm:text-3xl md:text-4xl font-bold text-gray-900">Orders</h1>
          <p className="text-gray-600 mt-1 md:mt-2 text-sm md:text-base">Manage and track your orders</p>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-8 py-8 md:py-12">
        {/* Status Tabs */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 md:gap-4 mb-6 md:mb-8">
          {statuses.map((status) => (
            <button
              key={status.value}
              onClick={() => setStatusFilter(status.value)}
              className={`p-3 md:p-4 rounded-lg font-semibold transition-all text-sm md:text-base ${
                statusFilter === status.value
                  ? 'bg-emerald-600 text-white'
                  : 'bg-white text-gray-900 border border-gray-200 hover:border-emerald-500'
              }`}
            >
              <div className="text-base md:text-lg">{status.label}</div>
              <div className={statusFilter === status.value ? 'text-emerald-100 text-xs md:text-sm' : 'text-gray-500 text-xs md:text-sm'}>
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
            orders.map((order, index) => (
              <div key={index} className="bg-white rounded-lg shadow-md p-4 md:p-6 hover:shadow-lg transition-shadow">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 md:gap-4">
                  <div className="flex-1">
                    <h3 className="font-bold text-gray-900 text-sm md:text-base">Order #12345</h3>
                    <p className="text-gray-600 text-sm">Customer: John Doe | Date: N/A</p>
                  </div>
                  <div className="flex flex-col sm:flex-row sm:items-center gap-3">
                    <span className="text-base md:text-lg font-semibold text-emerald-600">$0.00</span>
                    <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-semibold">Pending</span>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
