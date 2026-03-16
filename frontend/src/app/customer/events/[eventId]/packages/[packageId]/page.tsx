'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft, Sparkles, CheckCircle2, Clock, Tag, AlertTriangle, RefreshCw } from 'lucide-react';
import { ROUTES } from '@/lib/routes';
import { packageService } from '@/services/customer/packageService';
import type { RecommendationPackage, PackageType } from '@/types/customer/package';
import { toast } from 'sonner';

// ─── Package Config ───────────────────────────────────────────────────────────

const PACKAGE_CONFIG: Record<PackageType, {
  label: string;
  badgeClass: string;
  accentClass: string;
  buttonClass: string;
  borderClass: string;
  icon: React.ReactNode;
}> = {
  BUDGET: {
    label: 'Budget',
    badgeClass: 'bg-gray-100 text-gray-600 border border-gray-200',
    accentClass: 'text-gray-800',
    buttonClass: 'bg-gray-600 hover:bg-gray-700 text-white',
    borderClass: 'border-gray-200',
    icon: <CheckCircle2 size={14} />,
  },
  RECOMMENDED: {
    label: 'Recommended',
    badgeClass: 'bg-emerald-50 text-emerald-600 border border-emerald-200',
    accentClass: 'text-emerald-600',
    buttonClass: 'bg-emerald-500 hover:bg-emerald-600 text-white',
    borderClass: 'border-emerald-300',
    icon: <svg viewBox="0 0 24 24" className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" /></svg>,
  },
  HIGH_QUALITY: {
    label: 'High-Quality',
    badgeClass: 'bg-purple-50 text-purple-600 border border-purple-200',
    accentClass: 'text-purple-600',
    buttonClass: 'bg-purple-600 hover:bg-purple-700 text-white',
    borderClass: 'border-purple-200',
    icon: <Sparkles size={14} />,
  },
};

// ─── Skeleton ─────────────────────────────────────────────────────────────────

function Skeleton() {
  return (
    <div className="animate-pulse space-y-4">
      <div className="h-8 bg-gray-100 rounded-xl w-48" />
      <div className="h-4 bg-gray-100 rounded w-64" />
      <div className="bg-white rounded-2xl border border-gray-200 p-6 space-y-4 mt-4">
        <div className="h-6 bg-gray-100 rounded w-32" />
        <div className="h-10 bg-gray-100 rounded w-24" />
        {[1, 2, 3, 4].map(i => (
          <div key={i} className="h-20 bg-gray-50 rounded-xl" />
        ))}
      </div>
    </div>
  );
}

// ─── Error State ──────────────────────────────────────────────────────────────

function ErrorState({ title, message, onBack }: { title: string; message: string; onBack: () => void }) {
  return (
    <div className="flex items-center justify-center min-h-[400px]">
      <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-10 text-center max-w-md w-full">
        <div className="w-14 h-14 bg-red-50 rounded-full flex items-center justify-center mx-auto mb-4">
          <AlertTriangle className="w-7 h-7 text-red-400" />
        </div>
        <h2 className="text-xl font-bold text-gray-900 mb-2">{title}</h2>
        <p className="text-sm text-gray-500 mb-6">{message}</p>
        <button onClick={onBack}
          className="inline-flex items-center gap-2 bg-gray-800 text-white px-6 py-3 rounded-xl font-semibold text-sm hover:bg-gray-900 transition">
          <ArrowLeft size={15} />
          Back to Packages
        </button>
      </div>
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function PackageDetailPage() {
  const params = useParams<{ eventId: string; packageId: string }>();
  const router = useRouter();
  const eventId = params?.eventId || '';
  const packageId = params?.packageId || '';

  const [pkg, setPkg] = useState<RecommendationPackage | null>(null);
  const [loading, setLoading] = useState(true);
  const [errorType, setErrorType] = useState<'not_found' | 'unauthorized' | 'fetch_error' | null>(null);
  const [expired, setExpired] = useState(false);
  const [remaining, setRemaining] = useState('');

  // Load from sessionStorage first, then API
  useEffect(() => {
    const loadPackage = async () => {
      // Try sessionStorage cache first
      const stored = sessionStorage.getItem(`packages_${eventId}`);
      if (stored) {
        const parsed: RecommendationPackage[] = JSON.parse(stored);
        const found = parsed.find(p => p.packageId === packageId);
        if (found) {
          setPkg(found);
          setLoading(false);
          return;
        }
      }

      // Fallback to API
      try {
        const data = await packageService.getPackageById(eventId, packageId);
        setPkg(data);
      } catch (err: unknown) {
        const status = (err as { response?: { status?: number } })?.response?.status;
        if (status === 404) setErrorType('not_found');
        else if (status === 403 || status === 401) setErrorType('unauthorized');
        else setErrorType('fetch_error');
      } finally {
        setLoading(false);
      }
    };

    loadPackage();
  }, [eventId, packageId]);

  // Countdown timer
  useEffect(() => {
    if (!pkg?.expiresAt) return;
    const tick = () => {
      const diff = new Date(pkg.expiresAt).getTime() - Date.now();
      if (diff <= 0) { setExpired(true); setRemaining('0:00'); return; }
      const m = Math.floor(diff / 60000);
      const s = Math.floor((diff % 60000) / 1000);
      setRemaining(`${m}:${s.toString().padStart(2, '0')}`);
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [pkg?.expiresAt]);

  // A1: Auto-redirect when expired
  useEffect(() => {
    if (expired) {
      sessionStorage.removeItem(`packages_${eventId}`);
      toast.error('Package expired. Please regenerate.');
      router.push(ROUTES.CUSTOMER.EVENT_PACKAGES(eventId));
    }
  }, [expired, eventId, router]);

  const handleSelectPackage = () => {
    toast.success(`${pkg ? PACKAGE_CONFIG[pkg.type].label : ''} package selected!`);
    // Navigate to next step (UC-16)
    router.push(ROUTES.CUSTOMER.EVENTS);
  };

  const goToPackages = () => router.push(ROUTES.CUSTOMER.EVENT_PACKAGES(eventId));

  if (loading) return <div className="max-w-2xl mx-auto"><Skeleton /></div>;

  // A2: Not found / Unauthorized
  if (errorType === 'not_found') return (
    <div className="max-w-2xl mx-auto">
      <ErrorState
        title="Package Not Found"
        message="This package does not exist or has been removed. Please go back and select another package."
        onBack={goToPackages}
      />
    </div>
  );

  if (errorType === 'unauthorized') return (
    <div className="max-w-2xl mx-auto">
      <ErrorState
        title="Access Denied"
        message="You do not have permission to view this package."
        onBack={goToPackages}
      />
    </div>
  );

  if (errorType === 'fetch_error') return (
    <div className="max-w-2xl mx-auto">
      <ErrorState
        title="Something Went Wrong"
        message="Could not load package details. Please try again."
        onBack={goToPackages}
      />
    </div>
  );

  if (!pkg) return null;

  const config = PACKAGE_CONFIG[pkg.type];

  // A3: Check for unavailable items
  const unavailableItems = pkg.items.filter(item => item.isAvailable === false);
  const hasUnavailable = unavailableItems.length > 0;

  return (
    <div className="max-w-2xl mx-auto">
      {/* Back */}
      <button
        onClick={goToPackages}
        className="inline-flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 mb-6 transition"
      >
        <ArrowLeft size={16} />
        Back to Packages
      </button>

      {/* Page title */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Package Details</h1>
        <p className="text-sm text-gray-500 mt-1">Review all included offerings before proceeding.</p>
      </div>

      {/* A3: Unavailable items banner */}
      {hasUnavailable && (
        <div className="mb-4 flex items-start gap-3 bg-amber-50 border border-amber-200 rounded-xl px-4 py-3">
          <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-sm font-semibold text-amber-800">Some offerings are no longer available</p>
            <p className="text-xs text-amber-600 mt-0.5">
              {unavailableItems.length} item{unavailableItems.length > 1 ? 's are' : ' is'} unavailable. Please regenerate packages to continue.
            </p>
          </div>
          <button
            onClick={goToPackages}
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-amber-700 hover:text-amber-900 transition whitespace-nowrap"
          >
            <RefreshCw size={12} />
            Regenerate
          </button>
        </div>
      )}

      <div className={`bg-white rounded-2xl border-2 ${config.borderClass} shadow-sm overflow-hidden`}>
        {/* Package header */}
        <div className="p-6 border-b border-gray-100">
          <div className="flex items-center justify-between mb-4">
            <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold ${config.badgeClass}`}>
              {config.icon}
              {config.label}
            </span>
            <div className={`flex items-center gap-1.5 text-xs ${expired ? 'text-red-500' : 'text-amber-500'}`}>
              <Clock size={12} />
              <span>{expired ? 'Expired' : `${remaining} remaining`}</span>
            </div>
          </div>

          <div>
            <p className="text-xs text-gray-400 uppercase tracking-widest mb-1">Total Package Price</p>
            <p className={`text-4xl font-bold ${config.accentClass}`}>
              ${pkg.packageTotalPrice.toLocaleString()}
            </p>
            <p className="text-xs text-gray-400 mt-1">{pkg.currency} · {pkg.items.length} tasks included</p>
          </div>
        </div>

        {/* Task breakdown */}
        <div className="p-6 space-y-3">
          <p className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-4">Included Tasks</p>

          {pkg.items.map((item) => {
            const unavailable = item.isAvailable === false;
            return (
              <div key={item.taskId} className={`rounded-xl border p-4 ${unavailable ? 'border-red-100 bg-red-50' : 'border-gray-100 bg-gray-50'}`}>
                <div className="flex items-center justify-between mb-2">
                  <p className="text-[10px] font-bold tracking-widest text-gray-400">{item.taskName}</p>
                  {unavailable && (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-red-100 text-red-500 text-[10px] font-semibold">
                      <AlertTriangle size={9} />
                      Unavailable
                    </span>
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
                  <div className="text-right shrink-0">
                    <p className={`text-sm font-bold ${unavailable ? 'text-red-400' : 'text-gray-800'}`}>
                      ${item.taskPrice.toLocaleString()}
                    </p>
                    <p className="text-[10px] text-gray-400 mt-0.5">{pkg.currency}</p>
                  </div>
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
                    {item.taskName.toLowerCase().replace(/ \/ /g, ' / ')}
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
                ${pkg.packageTotalPrice.toLocaleString()} <span className="text-xs font-normal text-gray-400">{pkg.currency}</span>
              </span>
            </div>
          </div>
        </div>

        {/* Action */}
        <div className="px-6 pb-6">
          <button
            onClick={handleSelectPackage}
            disabled={hasUnavailable}
            className={`w-full py-3.5 rounded-xl font-semibold text-sm transition ${hasUnavailable ? 'bg-gray-100 text-gray-400 cursor-not-allowed' : config.buttonClass}`}
          >
            {hasUnavailable ? 'Cannot Proceed — Regenerate Packages' : 'Select This Package'}
          </button>
        </div>
      </div>
    </div>
  );
}
