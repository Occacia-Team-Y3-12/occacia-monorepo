'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft, Sparkles, CheckCircle2, AlertTriangle, RefreshCw, MapPin, CalendarDays, Tag, Info } from 'lucide-react';
import { ROUTES } from '@/lib/routes';
import { packageService } from '@/services/customer/packageService';
import type { RecommendationPackage, PackageType } from '@/types/customer/package';
import { toast } from 'sonner';

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

function getInitials(name: string) {
  return name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2);
}

function VendorAvatar({ name }: { name: string }) {
  return (
    <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center text-xs font-bold shrink-0">
      {getInitials(name)}
    </div>
  );
}

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
  const unavailableItems = pkg.items.filter(i => i.isAvailable === false);
  const hasUnavailable = unavailableItems.length > 0;
  const packageName = pkg.name ?? `${config.label} Package`;

  return (
    <div className="max-w-2xl mx-auto">
      <button onClick={goToPackages}
        className="inline-flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 mb-6 transition">
        <ArrowLeft size={16} /> Back to Packages
      </button>

      {/* Package header card */}
      <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6 mb-4">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-blue-500">
            <svg viewBox="0 0 24 24" className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="2" y="7" width="20" height="14" rx="2" /><path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2" />
            </svg>
          </span>
          <h1 className="text-lg font-bold text-gray-900">{packageName}</h1>
        </div>
        <p className="text-xs text-gray-400 mb-4">Package ID: {pkg.packageId}</p>

        {/* Event metadata row */}
        {(pkg.eventName || pkg.eventDate || pkg.eventLocation) && (
          <div className="flex flex-wrap gap-4 bg-gray-50 rounded-xl px-4 py-3">
            {pkg.eventName && (
              <div className="flex items-center gap-2 min-w-0">
                <Tag size={13} className="text-blue-400 shrink-0" />
                <div>
                  <p className="text-[10px] text-gray-400">Event</p>
                  <p className="text-xs font-semibold text-gray-700">{pkg.eventName}</p>
                </div>
              </div>
            )}
            {pkg.eventDate && (
              <div className="flex items-center gap-2 min-w-0">
                <CalendarDays size={13} className="text-blue-400 shrink-0" />
                <div>
                  <p className="text-[10px] text-gray-400">Date</p>
                  <p className="text-xs font-semibold text-gray-700">
                    {new Date(pkg.eventDate).toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })}
                  </p>
                </div>
              </div>
            )}
            {pkg.eventLocation && (
              <div className="flex items-center gap-2 min-w-0">
                <MapPin size={13} className="text-blue-400 shrink-0" />
                <div>
                  <p className="text-[10px] text-gray-400">Location</p>
                  <p className="text-xs font-semibold text-gray-700">{pkg.eventLocation}</p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Unavailable banner */}
      {hasUnavailable && (
        <div className="mb-4 flex items-start gap-3 bg-amber-50 border border-amber-200 rounded-xl px-4 py-3">
          <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-sm font-semibold text-amber-800">Some offerings are no longer available</p>
            <p className="text-xs text-amber-600 mt-0.5">
              {unavailableItems.length} item{unavailableItems.length > 1 ? 's are' : ' is'} unavailable. Please regenerate packages.
            </p>
          </div>
          <button onClick={goToPackages}
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-amber-700 hover:text-amber-900 transition whitespace-nowrap">
            <RefreshCw size={12} /> Regenerate
          </button>
        </div>
      )}

      {/* Tasks & Selected Vendors */}
      <h2 className="text-sm font-bold text-gray-700 mb-3">
        Tasks &amp; Selected Vendors ({pkg.items.length})
      </h2>

      <div className="space-y-3 mb-4">
        {pkg.items.map((item, idx) => {
          const unavailable = item.isAvailable === false;
          return (
            <div key={item.taskId} className={`bg-white rounded-2xl border shadow-sm overflow-hidden ${unavailable ? 'border-red-100' : 'border-gray-200'}`}>
              {/* Task header row */}
              <div className="flex items-center justify-between px-4 pt-4 pb-2">
                <div className="flex items-center gap-3">
                  <span className="w-6 h-6 rounded-full bg-gray-100 text-gray-500 text-xs font-bold flex items-center justify-center shrink-0">
                    {idx + 1}
                  </span>
                  <div>
                    <p className="text-sm font-bold text-gray-900">{item.taskName}</p>
                    <p className="text-xs text-gray-400">{item.offeringCategory}</p>
                  </div>
                </div>
                <span className={`text-[10px] font-semibold px-2.5 py-1 rounded-full border ${unavailable ? 'bg-red-50 text-red-500 border-red-200' : 'bg-gray-50 text-gray-500 border-gray-200'}`}>
                  {unavailable ? 'Unavailable' : 'Draft'}
                </span>
              </div>

              {/* Vendor row */}
              <div className="flex items-center justify-between px-4 pb-4">
                <div className="flex items-center gap-3">
                  <VendorAvatar name={item.vendorName} />
                  <div>
                    <p className={`text-sm font-semibold ${unavailable ? 'text-red-400 line-through' : 'text-gray-800'}`}>
                      {item.vendorName}
                    </p>
                    <p className="text-xs text-gray-400">{item.offeringTitle}</p>
                  </div>
                </div>
                <div className="text-right shrink-0">
                  <p className={`text-sm font-bold ${unavailable ? 'text-red-400' : 'text-gray-900'}`}>
                    ${item.taskPrice.toLocaleString()}
                  </p>
                  {item.rating != null && (
                    <p className="text-xs text-amber-500 mt-0.5">★ {item.rating.toFixed(1)}</p>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Package Total + CTA */}
      <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6">
        <div className="flex items-center justify-between mb-4">
          <span className="text-sm font-semibold text-gray-600">Package Total</span>
          <span className={`text-3xl font-bold ${config.accentClass}`}>
            ${pkg.packageTotalPrice.toLocaleString()}
          </span>
        </div>

        <div className="flex items-start gap-2 bg-blue-50 border border-blue-100 rounded-xl px-3 py-2.5 mb-4">
          <Info size={13} className="text-blue-400 shrink-0 mt-0.5" />
          <p className="text-xs text-blue-600">
            Cash on pickup only. No in-app payment required. By confirming, vendors will be notified and tasks will move to{' '}
            <span className="font-semibold text-amber-600">Pending</span> status.
          </p>
        </div>

        <button
          onClick={() => router.push(ROUTES.CUSTOMER.EVENT_PACKAGE_CONFIRM(eventId, packageId))}
          disabled={hasUnavailable || expired}
          className={`w-full py-3.5 rounded-xl font-semibold text-sm transition flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed ${config.buttonClass}`}
        >
          {hasUnavailable ? 'Cannot Proceed — Regenerate Packages' : 'Confirm Package →'}
        </button>
      </div>
    </div>
  );
}
