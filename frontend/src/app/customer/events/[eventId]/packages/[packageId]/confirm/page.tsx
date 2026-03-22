'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft, CheckCircle2, AlertCircle, Clock, Tag, AlertTriangle, Loader2, Sparkles } from 'lucide-react';
import { ROUTES } from '@/lib/routes';
import { packageService } from '@/services/customer/packageService';
import type { RecommendationPackage, PackageType } from '@/types/customer/package';
import { toast } from 'sonner';

const PACKAGE_CONFIG: Record<PackageType, { label: string; accentClass: string; borderClass: string; badgeClass: string; buttonClass: string; icon: React.ReactNode }> = {
  BUDGET: {
    label: 'Budget',
    accentClass: 'text-gray-800',
    borderClass: 'border-gray-200',
    badgeClass: 'bg-gray-100 text-gray-600 border border-gray-200',
    buttonClass: 'bg-gray-700 hover:bg-gray-800 text-white',
    icon: <CheckCircle2 size={13} />,
  },
  RECOMMENDED: {
    label: 'Recommended',
    accentClass: 'text-emerald-600',
    borderClass: 'border-emerald-300',
    badgeClass: 'bg-emerald-50 text-emerald-600 border border-emerald-200',
    buttonClass: 'bg-emerald-500 hover:bg-emerald-600 text-white',
    icon: <svg viewBox="0 0 24 24" className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" /></svg>,
  },
  HIGH_QUALITY: {
    label: 'High-Quality',
    accentClass: 'text-purple-600',
    borderClass: 'border-purple-200',
    badgeClass: 'bg-purple-50 text-purple-600 border border-purple-200',
    buttonClass: 'bg-purple-600 hover:bg-purple-700 text-white',
    icon: <Sparkles size={13} />,
  },
};

export default function ConfirmPackagePage() {
  const params = useParams<{ eventId: string; packageId: string }>();
  const router = useRouter();
  const eventId = params?.eventId || '';
  const packageId = params?.packageId || '';

  const [pkg, setPkg] = useState<RecommendationPackage | null>(null);
  const [loading, setLoading] = useState(true);
  const [confirming, setConfirming] = useState(false);

  useEffect(() => {
    packageService.getPackageById(eventId, packageId)
      .then(data => setPkg(data))
      .catch(() => toast.error('Could not load package. Please go back and try again.'))
      .finally(() => setLoading(false));
  }, [eventId, packageId]);

  const handleConfirm = async () => {
    setConfirming(true);
    try {
      const idempotencyKey = crypto.randomUUID();
      const response = await packageService.confirmPackage(eventId, packageId, idempotencyKey);
      sessionStorage.setItem(`order_${response.packageOrder.packageOrderId}`, JSON.stringify(response));
      toast.success('Package order placed successfully!');
      router.push(ROUTES.CUSTOMER.EVENT_ORDER_CONFIRMATION(eventId, response.packageOrder.packageOrderId));
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number } })?.response?.status;
      if (status === 409) toast.error('This package has already been confirmed.');
      else if (status === 400) toast.error('Package validation failed. Please regenerate packages.');
      else toast.error('Failed to place order. Please try again.');
      setConfirming(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-2xl mx-auto animate-pulse space-y-4">
        <div className="h-8 bg-gray-100 rounded-xl w-48" />
        <div className="h-4 bg-gray-100 rounded w-64" />
        {[1, 2, 3].map(i => <div key={i} className="h-20 bg-gray-100 rounded-2xl" />)}
      </div>
    );
  }

  if (!pkg) {
    return (
      <div className="max-w-2xl mx-auto flex items-center justify-center min-h-[400px]">
        <div className="bg-white rounded-2xl border border-gray-200 p-10 text-center max-w-md w-full">
          <AlertTriangle className="w-10 h-10 text-red-400 mx-auto mb-4" />
          <p className="text-base font-bold text-gray-900 mb-2">Package Not Found</p>
          <p className="text-sm text-gray-500 mb-5">Could not load the package. Please go back and try again.</p>
          <button
            onClick={() => router.push(ROUTES.CUSTOMER.EVENT_PACKAGE_DETAIL(eventId, packageId))}
            className="inline-flex items-center gap-2 bg-gray-800 text-white px-5 py-2.5 rounded-xl font-semibold text-sm hover:bg-gray-900 transition"
          >
            <ArrowLeft size={15} />
            Back to Package
          </button>
        </div>
      </div>
    );
  }

  const config = PACKAGE_CONFIG[pkg.type];
  const unavailableItems = pkg.items.filter(i => i.isAvailable === false);
  const hasUnavailable = unavailableItems.length > 0;

  return (
    <div className="max-w-2xl mx-auto">
      {/* Back */}
      <button
        onClick={() => router.push(ROUTES.CUSTOMER.EVENT_PACKAGE_DETAIL(eventId, packageId))}
        className="inline-flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 mb-6 transition"
      >
        <ArrowLeft size={16} />
        Back to Package Details
      </button>

      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Confirm Package Order</h1>
        <p className="text-sm text-gray-500 mt-1">Review your selections before placing the order.</p>
      </div>

      {/* Warning — what this action does */}
      <div className="flex items-start gap-3 bg-amber-50 border border-amber-200 rounded-xl px-4 py-3 mb-5">
        <AlertCircle className="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
        <div>
          <p className="text-sm font-semibold text-amber-800">This action will:</p>
          <ul className="text-xs text-amber-700 mt-1 space-y-0.5 list-disc list-inside">
            <li>Lock your vendor selections</li>
            <li>Notify all selected vendors</li>
            <li>Set all tasks to Pending status</li>
          </ul>
        </div>
      </div>

      {/* Unavailable banner */}
      {hasUnavailable && (
        <div className="flex items-start gap-3 bg-red-50 border border-red-200 rounded-xl px-4 py-3 mb-5">
          <AlertTriangle className="w-4 h-4 text-red-500 shrink-0 mt-0.5" />
          <p className="text-sm text-red-700 font-medium">
            {unavailableItems.length} offering{unavailableItems.length > 1 ? 's are' : ' is'} unavailable. Please go back and regenerate packages.
          </p>
        </div>
      )}

      <div className={`bg-white rounded-2xl border-2 ${config.borderClass} shadow-sm overflow-hidden mb-5`}>
        {/* Package header */}
        <div className="p-6 border-b border-gray-100">
          <div className="flex items-center justify-between mb-4">
            <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold ${config.badgeClass}`}>
              {config.icon}
              {config.label}
            </span>
            <span className="text-xs text-gray-400 flex items-center gap-1">
              <Clock size={11} />
              {pkg.items.length} tasks
            </span>
          </div>
          <p className="text-xs text-gray-400 uppercase tracking-widest mb-1">Total Package Price</p>
          <p className={`text-4xl font-bold ${config.accentClass}`}>
            ${pkg.packageTotalPrice.toLocaleString()}
            <span className="text-sm font-normal text-gray-400 ml-2">{pkg.currency}</span>
          </p>
        </div>

        {/* Task breakdown */}
        <div className="p-6 space-y-3">
          <p className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-2">Selected Offerings per Task</p>
          {pkg.items.map(item => {
            const unavailable = item.isAvailable === false;
            return (
              <div key={item.taskId} className={`rounded-xl border p-4 ${unavailable ? 'border-red-100 bg-red-50' : 'border-gray-100 bg-gray-50'}`}>
                <div className="flex items-center justify-between mb-1">
                  <p className="text-[10px] font-bold tracking-widest text-gray-400">{item.taskName}</p>
                  {unavailable && (
                    <span className="text-[10px] font-semibold text-red-500 bg-red-100 px-2 py-0.5 rounded-full">Unavailable</span>
                  )}
                </div>
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <p className={`text-sm font-semibold ${unavailable ? 'text-red-400 line-through' : 'text-gray-900'}`}>
                      {item.offeringTitle}
                    </p>
                    <p className="text-xs text-gray-500 mt-0.5">{item.vendorName}</p>
                    <span className="inline-flex items-center gap-1 mt-2 px-2 py-0.5 rounded-full bg-white border border-gray-200 text-[10px] font-medium text-gray-500">
                      <Tag size={9} />
                      {item.offeringCategory}
                    </span>
                  </div>
                  <p className={`text-sm font-bold shrink-0 ${unavailable ? 'text-red-400' : 'text-gray-800'}`}>
                    ${item.taskPrice.toLocaleString()}
                  </p>
                </div>
              </div>
            );
          })}
        </div>

        {/* Price summary */}
        <div className="px-6 pb-6">
          <div className="rounded-xl bg-gray-50 border border-gray-100 p-4">
            <div className="space-y-2">
              {pkg.items.map(item => (
                <div key={item.taskId} className="flex justify-between text-sm">
                  <span className={`capitalize ${item.isAvailable === false ? 'text-red-400 line-through' : 'text-gray-500'}`}>
                    {item.taskName.toLowerCase()}
                  </span>
                  <span className={`font-medium ${item.isAvailable === false ? 'text-red-400' : 'text-gray-700'}`}>
                    ${item.taskPrice.toLocaleString()}
                  </span>
                </div>
              ))}
            </div>
            <div className="border-t border-gray-200 mt-3 pt-3 flex justify-between">
              <span className="font-semibold text-gray-900">Total</span>
              <span className={`font-bold text-lg ${config.accentClass}`}>
                ${pkg.packageTotalPrice.toLocaleString()}
                <span className="text-xs font-normal text-gray-400 ml-1">{pkg.currency}</span>
              </span>
            </div>
          </div>
          <p className="text-xs text-center text-gray-400 mt-3">
            💵 Payment is cash-on-pickup. No in-app payment required.
          </p>
        </div>
      </div>

      {/* Action buttons */}
      <div className="flex gap-3">
        <button
          onClick={() => router.push(ROUTES.CUSTOMER.EVENT_PACKAGE_DETAIL(eventId, packageId))}
          disabled={confirming}
          className="flex-1 py-3.5 rounded-xl border border-gray-200 bg-white hover:bg-gray-50 text-gray-700 font-semibold text-sm transition disabled:opacity-40"
        >
          Cancel
        </button>
        <button
          onClick={handleConfirm}
          disabled={confirming || hasUnavailable}
          className={`flex-1 py-3.5 rounded-xl font-semibold text-sm transition flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed ${config.buttonClass}`}
        >
          {confirming ? (
            <>
              <Loader2 size={15} className="animate-spin" />
              Placing Order...
            </>
          ) : (
            'Confirm & Place Order'
          )}
        </button>
      </div>
    </div>
  );
}
