'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Package, Clock, CheckCircle2, XCircle, ArrowRight } from 'lucide-react';
import { ROUTES } from '@/lib/routes';
import type { PackageOrder } from '@/types/customer/order';
import { customerOrderService } from '@/services/customer/orderServices';
import { formatCurrency } from '@/lib/currency';

const STATUS_CONFIG: Record<string, { label: string; icon: React.ReactNode; className: string }> = {
  CREATED: {
    label: 'Pending',
    icon: <Clock size={11} />,
    className: 'bg-amber-50 border-amber-200 text-amber-700',
  },
  COMPLETED: {
    label: 'Completed',
    icon: <CheckCircle2 size={11} />,
    className: 'bg-emerald-50 border-emerald-200 text-emerald-700',
  },
  CANCELLED_ADMIN: {
    label: 'Cancelled',
    icon: <XCircle size={11} />,
    className: 'bg-red-50 border-red-200 text-red-600',
  },
};

export default function OrdersPage() {
  const router = useRouter();
  const [orders, setOrders] = useState<PackageOrder[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    customerOrderService.listOrders()
      .then(setOrders)
      .catch(() => setOrders([]))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="max-w-2xl mx-auto space-y-3 animate-pulse">
        <div className="h-8 bg-gray-100 rounded-xl w-40 mb-6" />
        {[1, 2, 3].map(i => <div key={i} className="h-24 bg-gray-100 rounded-2xl" />)}
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">My Orders</h1>
        <p className="text-sm text-gray-500 mt-1">All your package orders and their current status.</p>
      </div>

      {orders.length === 0 ? (
        <div className="bg-white rounded-2xl border border-gray-200 p-10 text-center">
          <div className="w-14 h-14 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-4">
            <Package className="w-7 h-7 text-gray-300" />
          </div>
          <p className="text-base font-semibold text-gray-700 mb-1">No orders yet</p>
          <p className="text-sm text-gray-400 mb-5">Confirm a package to create your first order.</p>
          <button
            onClick={() => router.push(ROUTES.CUSTOMER.PERSONA)}
            className="inline-flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-5 py-2.5 rounded-xl font-semibold text-sm transition"
          >
            Browse Events
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {orders.map(order => {
            const statusCfg = STATUS_CONFIG[order.status] ?? STATUS_CONFIG.CREATED;
            return (
              <div
                key={order.packageOrderId}
                className="bg-white rounded-2xl border border-gray-200 shadow-sm p-5 flex items-center justify-between gap-4 hover:border-indigo-200 transition cursor-pointer"
                onClick={() => router.push(ROUTES.CUSTOMER.EVENT_ORDER_CONFIRMATION(order.eventId, order.packageOrderId))}
              >
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 bg-indigo-50 rounded-xl flex items-center justify-center shrink-0">
                    <Package className="w-5 h-5 text-indigo-500" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-gray-900 font-mono">{order.packageOrderId}</p>
                    <p className="text-xs text-gray-400 mt-0.5">
                      {new Date(order.createdAt).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-4 shrink-0">
                  <div className="text-right">
                    <p className="text-sm font-bold text-gray-900">{formatCurrency(order.packageOrderTotalPrice)}</p>
                    <p className="text-xs text-gray-400">{order.currency}</p>
                  </div>
                  <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full border text-xs font-semibold ${statusCfg.className}`}>
                    {statusCfg.icon}
                    {statusCfg.label}
                  </span>
                  <ArrowRight size={16} className="text-gray-300" />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
