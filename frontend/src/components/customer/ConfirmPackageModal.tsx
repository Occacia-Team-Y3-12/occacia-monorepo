'use client';

import { X, AlertCircle, CheckCircle2, Loader2 } from 'lucide-react';
import type { RecommendationPackage } from '@/types/customer/package';
import { formatCurrency } from '@/lib/currency';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => Promise<void>;
  pkg: RecommendationPackage;
  loading: boolean;
}

export default function ConfirmPackageModal({ isOpen, onClose, onConfirm, pkg, loading }: Props) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={() => !loading && onClose()} />

      <div className="relative bg-white rounded-2xl shadow-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b border-gray-100 px-6 py-4 flex items-center justify-between rounded-t-2xl">
          <h2 className="text-lg font-bold text-gray-900">Confirm Package Order</h2>
          <button
            onClick={onClose}
            disabled={loading}
            className="text-gray-400 hover:text-gray-600 transition disabled:opacity-40"
          >
            <X size={20} />
          </button>
        </div>

        {/* Body */}
        <div className="px-6 py-5 space-y-5">
          {/* Warning */}
          <div className="flex items-start gap-3 bg-amber-50 border border-amber-200 rounded-xl px-4 py-3">
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

          {/* Price summary */}
          <div className="bg-gray-50 rounded-xl border border-gray-100 p-4 flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-400 uppercase tracking-widest mb-1">Total Price</p>
              <p className="text-2xl font-bold text-gray-900">
                {formatCurrency(pkg.packageTotalPrice, pkg.currency || 'LKR')}
                <span className="text-xs font-normal text-gray-400 ml-1">{pkg.currency}</span>
              </p>
            </div>
            <p className="text-xs text-gray-500 capitalize">
              {pkg.type.toLowerCase().replace('_', ' ')} package
            </p>
          </div>

          {/* Tasks */}
          <div>
            <p className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-3">
              Tasks ({pkg.items.length})
            </p>
            <div className="space-y-2">
              {pkg.items.map(item => (
                <div key={item.taskId} className="flex items-center justify-between bg-gray-50 rounded-xl px-4 py-3">
                  <div className="flex items-center gap-3">
                    <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
                    <div>
                      <p className="text-sm font-semibold text-gray-900">{item.taskName}</p>
                      <p className="text-xs text-gray-500">{item.vendorName}</p>
                    </div>
                  </div>
                  <span className="text-sm font-bold text-gray-700">{formatCurrency(item.taskPrice, pkg.currency || 'LKR')}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Cash note */}
          <p className="text-xs text-center text-gray-400">
            💵 Payment is cash-on-pickup. No in-app payment required.
          </p>
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 bg-white border-t border-gray-100 px-6 py-4 flex gap-3 rounded-b-2xl">
          <button
            onClick={onClose}
            disabled={loading}
            className="flex-1 py-3 rounded-xl border border-gray-200 bg-white hover:bg-gray-50 text-gray-700 font-semibold text-sm transition disabled:opacity-40"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={loading}
            className="flex-1 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {loading ? (
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
    </div>
  );
}
