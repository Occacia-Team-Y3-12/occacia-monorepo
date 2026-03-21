'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { CheckCircle2, Clock, ArrowLeft, Bell } from 'lucide-react';
import { ROUTES } from '@/lib/routes';
import type { ConfirmPackageOrderResponse } from '@/types/customer/order';
import type { RecommendationPackage } from '@/types/customer/package';

export default function OrderConfirmationPage() {
  const params = useParams<{ eventId: string; packageOrderId: string }>();
  const router = useRouter();
  const eventId = params?.eventId || '';
  const packageOrderId = params?.packageOrderId || '';

  const [orderData, setOrderData] = useState<ConfirmPackageOrderResponse | null>(null);
  const [vendorMap, setVendorMap] = useState<Record<string, string>>({});

  useEffect(() => {
    const stored = sessionStorage.getItem(`order_${packageOrderId}`);
    if (!stored) return;
    const data: ConfirmPackageOrderResponse = JSON.parse(stored);
    setOrderData(data);

    // Build taskId → vendorName map from cached package
    const pkgStored = sessionStorage.getItem(`packages_${eventId}`);
    if (pkgStored && data.packageOrder?.packageId) {
      const pkgs: RecommendationPackage[] = JSON.parse(pkgStored);
      const pkg = pkgs.find(p => p.packageId === data.packageOrder.packageId);
      if (pkg) {
        const map: Record<string, string> = {};
        pkg.items.forEach(item => { map[item.taskId] = item.vendorName; });
        setVendorMap(map);
      }
    }
  }, [packageOrderId, eventId]);

  if (!orderData) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-pulse text-gray-400 text-sm">Loading order details...</div>
      </div>
    );
  }

  const { packageOrder, tasks, packageName, eventName, eventDate } = orderData;

  return (
    <div className="max-w-lg mx-auto">
      <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
        {/* Success header */}
        <div className="flex flex-col items-center pt-10 pb-6 px-8 text-center">
          <div className="w-14 h-14 rounded-full bg-emerald-100 flex items-center justify-center mb-4">
            <CheckCircle2 className="w-8 h-8 text-emerald-500" />
          </div>
          <h1 className="text-xl font-bold text-gray-900 mb-2">Package Order Confirmed!</h1>
          <p className="text-sm text-gray-500 leading-relaxed">
            Your package order{eventName ? <> for <span className="font-semibold text-gray-800">{eventName}</span></> : ''} has been
            created. All selected vendors have been notified.
          </p>
        </div>

        {/* Summary grid */}
        <div className="mx-6 mb-5 bg-gray-50 rounded-xl border border-gray-100 p-4 grid grid-cols-2 gap-4">
          <div>
            <p className="text-xs text-gray-400 mb-1">Package</p>
            <p className="text-sm font-semibold text-gray-800">{packageName ?? `Package #${packageOrder.packageId.slice(0, 8)}`}</p>
          </div>
          <div>
            <p className="text-xs text-gray-400 mb-1">Total Price</p>
            <p className="text-sm font-bold text-gray-900">${packageOrder.packageOrderTotalPrice.toLocaleString()}</p>
          </div>
          <div>
            <p className="text-xs text-gray-400 mb-1">Event Date</p>
            <p className="text-sm font-semibold text-gray-800">
              {eventDate
                ? new Date(eventDate).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })
                : new Date(packageOrder.createdAt).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-400 mb-1">Payment</p>
            <p className="text-sm font-semibold text-gray-800">Cash on Pickup</p>
          </div>
        </div>

        {/* Task Status */}
        <div className="px-6 mb-5">
          <h2 className="text-sm font-bold text-gray-900 mb-3">Task Status</h2>
          <div className="space-y-2">
            {tasks.map(task => (
              <div key={task.taskId} className="flex items-center justify-between bg-gray-50 rounded-xl px-4 py-3">
                <div className="flex items-center gap-3">
                  <Clock size={14} className="text-amber-400 shrink-0" />
                  <div>
                    <p className="text-sm font-semibold text-gray-900">{task.name}</p>
                    {vendorMap[task.taskId] && (
                      <p className="text-xs text-gray-400">{vendorMap[task.taskId]}</p>
                    )}
                  </div>
                </div>
                <span className="text-xs font-semibold text-amber-600 border border-amber-300 bg-amber-50 px-2.5 py-1 rounded-full">
                  Pending
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Vendor notification note */}
        <div className="mx-6 mb-6 flex items-start gap-2 bg-blue-50 border border-blue-100 rounded-xl px-3 py-3">
          <Bell size={13} className="text-blue-400 shrink-0 mt-0.5" />
          <p className="text-xs text-blue-600">
            Vendors have received Fulfillment Requests and will respond shortly. You&apos;ll be notified when vendors accept or respond to your tasks.
          </p>
        </div>

        {/* Back button */}
        <div className="px-6 pb-8 flex justify-center">
          <button
            onClick={() => router.push(ROUTES.CUSTOMER.EVENT_PACKAGE_DETAIL(eventId, packageOrder.packageId))}
            className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl border border-gray-200 bg-white hover:bg-gray-50 text-gray-700 font-semibold text-sm transition"
          >
            <ArrowLeft size={14} />
            Back to Package Review
          </button>
        </div>
      </div>
    </div>
  );
}
