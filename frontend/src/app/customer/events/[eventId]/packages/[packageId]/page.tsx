'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {ArrowLeft, Sparkles, CheckCircle2, AlertTriangle} from 'lucide-react';
import { ROUTES } from '@/lib/routes';
import { packageService } from '@/services/customer/packageService';
import type { RecommendationPackage, PackageType } from '@/types/customer/package';
import { toast } from 'sonner';
import { formatCurrency } from '@/lib/currency';

const PACKAGE_CONFIG: Record<PackageType, {
  label: string; badgeClass: string; accentClass: string; buttonClass: string; borderClass: string; icon: React.ReactNode;
}> = {
  BUDGET: {
    label: 'Budget', badgeClass: 'bg-gray-100 text-gray-600 border border-gray-200',
    accentClass: 'text-gray-800', buttonClass: 'bg-gray-700 hover:bg-gray-800 text-white',
    borderClass: 'border-gray-200', icon: <CheckCircle2 size={13} />,
  },
  RECOMMENDED: {
    label: 'Recommended', badgeClass: 'bg-emerald-50 text-emerald-600 border border-emerald-200',
    accentClass: 'text-emerald-600', buttonClass: 'bg-blue-600 hover:bg-blue-700 text-white',
    borderClass: 'border-emerald-300',
    icon: <svg viewBox="0 0 24 24" className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" /></svg>,
  },
  HIGH_QUALITY: {
    label: 'High-Quality', badgeClass: 'bg-purple-50 text-purple-600 border border-purple-200',
    accentClass: 'text-purple-600', buttonClass: 'bg-blue-600 hover:bg-blue-700 text-white',
    borderClass: 'border-purple-200', icon: <Sparkles size={13} />,
  },
};
export default function PackageDetailPage() {
  const params = useParams<{ eventId: string; packageId: string }>();
  const router = useRouter();
  const eventId = params?.eventId || '';
  const packageId = params?.packageId || '';

  const [pkg, setPkg] = useState<RecommendationPackage | null>(null);
  const [loading, setLoading] = useState(true);
  const [expired, setExpired] = useState(false);

  useEffect(() => {
    packageService.getPackageById(eventId, packageId)
      .then(data => setPkg(data))
      .catch((err: unknown) => {
        const status = (err as { response?: { status?: number } })?.response?.status;
        if (status === 404) toast.error('Package not found.');
        else if (status === 403 || status === 401) toast.error('Access denied.');
        else toast.error('Could not load package.');
      })
      .finally(() => setLoading(false));
  }, [eventId, packageId]);

  useEffect(() => {
    if (!pkg?.expiresAt) return;
    const id = setInterval(() => {
      if (new Date(pkg.expiresAt).getTime() - Date.now() <= 0) {
        setExpired(true);
        clearInterval(id);
      }
    }, 1000);
    return () => clearInterval(id);
  }, [pkg?.expiresAt]);

  useEffect(() => {
    if (expired) {
      packageService.clearCachedPackages(eventId);
      toast.error('Package expired. Please regenerate.');
      router.push(ROUTES.CUSTOMER.EVENT_PACKAGES(eventId));
    }
  }, [expired, eventId, router]);

  const goToPackages = () => router.push(ROUTES.CUSTOMER.EVENT_PACKAGES(eventId));

  if (loading) {
    return (
      <div className="max-w-2xl mx-auto animate-pulse space-y-4">
        <div className="h-8 bg-gray-100 rounded-xl w-48" />
        <div className="h-32 bg-gray-100 rounded-2xl" />
        {[1, 2, 3].map(i => <div key={i} className="h-24 bg-gray-100 rounded-2xl" />)}
      </div>
    );
  }

  if (!pkg) {
    return (
      <div className="max-w-2xl mx-auto flex items-center justify-center min-h-[400px]">
        <div className="bg-white rounded-2xl border border-gray-200 p-10 text-center max-w-md w-full">
          <AlertTriangle className="w-10 h-10 text-red-400 mx-auto mb-4" />
          <p className="text-base font-bold text-gray-900 mb-2">Package Not Found</p>
          <button onClick={goToPackages}
            className="inline-flex items-center gap-2 bg-gray-800 text-white px-5 py-2.5 rounded-xl font-semibold text-sm hover:bg-gray-900 transition">
            <ArrowLeft size={15} /> Back to Packages
          </button>
        </div>
      </div>
    );
  }

  const config = PACKAGE_CONFIG[pkg.type];
  const unavailableItems = pkg.items.filter(i => !i.isAvailable);
  const hasUnavailable = unavailableItems.length > 0;
  const packageName = pkg.name ?? `${config.label} Package`;
  const statusText = expired ? 'Expired' : hasUnavailable ? 'Needs regeneration' : 'Ready to confirm';
  const currency = pkg.currency || 'LKR';

  return (
    <main className="min-h-screen bg-[#F3F5F9] text-[#1D273C]">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-10 space-y-6">
        <button
          onClick={goToPackages}
          className="inline-flex items-center gap-2 rounded-full border border-transparent bg-white px-4 py-2 text-xs font-semibold uppercase tracking-[0.18em] text-[#0D47A1] shadow-sm transition hover:bg-white/90"
        >
          <ArrowLeft size={14} />
          Back to packages
        </button>

        <section className="rounded-[26px] border border-[#DCE4F2] bg-white shadow-[0_15px_40px_-30px_rgba(13,71,161,0.4)] p-6 space-y-4">
          <div className="flex flex-col gap-3">
            <p className="text-[12px] font-semibold uppercase tracking-[0.3em] text-[#0D47A1]">
              {pkg.type.replace('_', ' ')} Package
            </p>
            <h1 className="text-3xl font-semibold text-[#1D273C]">{packageName}</h1>
            <p className="text-sm text-[#5B6780]">
              {pkg.eventName ?? 'Occacia Event'} · {pkg.eventLocation ?? 'Sri Lanka'}
            </p>
          </div>
          <div className="flex flex-wrap justify-between gap-4">
            <p className="text-xs font-semibold uppercase tracking-[0.3em] text-[#9AA6BF]">
              Status
            </p>
            <span
              className={`inline-flex items-center px-3 py-1 rounded-full text-[10px] font-semibold uppercase tracking-[0.2em] ${expired ? 'bg-red-50 text-red-500 border border-red-100' : hasUnavailable ? 'bg-amber-50 text-amber-700 border border-amber-100' : 'bg-emerald-50 text-emerald-700 border border-emerald-100'}`}
            >
              {statusText}
            </span>
          </div>
          <div className="grid grid-cols-2 gap-4 text-sm text-[#4A5976]">
            <div className="rounded-2xl border border-[#E1E6EF] bg-[#F7F9FF] p-4">
              <p className="text-[10px] uppercase tracking-[0.3em]">Tasks</p>
              <p className="text-lg font-semibold text-[#0D47A1]">{pkg.items.length}</p>
            </div>
            <div className="rounded-2xl border border-[#E1E6EF] bg-[#F7F9FF] p-4">
              <p className="text-[10px] uppercase tracking-[0.3em]">Total</p>
              <p className="text-lg font-semibold text-[#0D47A1]">{formatCurrency(pkg.packageTotalPrice)}</p>
              <p className="text-xs">{currency}</p>
            </div>
          </div>
          <div className="flex flex-wrap gap-3">
            <button
              onClick={() => router.push(ROUTES.CUSTOMER.EVENT_PACKAGE_CONFIRM(eventId, packageId))}
              disabled={hasUnavailable || expired}
              className={`flex-1 min-w-[160px] rounded-full bg-[#0D47A1] px-4 py-2 text-sm font-semibold text-white transition disabled:opacity-60 disabled:cursor-not-allowed ${hasUnavailable || expired ? 'bg-[#0D47A1]' : ''}`}
            >
              {hasUnavailable ? 'Regenerate first' : 'Confirm package'}
            </button>
            <button
              onClick={() => router.push(ROUTES.CUSTOMER.EVENT_PACKAGE_CUSTOMIZE(eventId, packageId))}
              className="flex-1 min-w-[160px] rounded-full border border-[#0D47A1] px-4 py-2 text-sm font-semibold text-[#0D47A1] transition hover:bg-[#0D47A1] hover:text-white"
            >
              Customize package
            </button>
          </div>
        </section>

        <section className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-[#1D273C]">Selected tasks</h2>
            <span className="text-xs font-semibold uppercase tracking-[0.2em] text-[#5B6780]">{pkg.items.length} items</span>
          </div>
          <div className="space-y-2">
            {pkg.items.map((item, idx) => {
              const unavailable = !item.isAvailable;
              return (
                <article
                  key={item.taskId}
                  className={`flex flex-col gap-2 rounded-2xl border p-4 ${unavailable ? 'border-red-100 bg-red-50/60' : 'border-[#E1E6EF] bg-white'}`}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-semibold text-[#1D273C]">
                        {idx + 1}. {item.taskName}
                      </p>
                      <p className="text-[11px] uppercase tracking-[0.3em] text-[#9AA6BF]">
                        {item.offeringCategory || 'Experience'}
                      </p>
                    </div>
                    <span className="text-xs font-semibold text-[#5B6780]">{formatCurrency(item.taskPrice)}</span>
                  </div>
                  <div className="flex items-center justify-between text-sm text-[#5B6780]">
                    <p className="font-semibold text-[#173B7A]">{item.vendorName}</p>
                    <p className="text-xs uppercase tracking-[0.2em] text-[#FBBC05]">
                      {item.rating != null ? `★ ${item.rating.toFixed(1)}` : 'No rating'}
                    </p>
                  </div>
                  {item.offeringTitle && (
                    <p className="text-[13px] text-[#5B6780]">{item.offeringTitle}</p>
                  )}
                  {unavailable && (
                    <p className="text-xs font-semibold text-red-500">
                      This offering is unavailable. Please regenerate.
                    </p>
                  )}
                </article>
              );
            })}
          </div>
        </section>
      </div>
    </main>
  );
}
