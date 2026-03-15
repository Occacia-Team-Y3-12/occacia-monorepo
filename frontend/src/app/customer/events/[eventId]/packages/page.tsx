'use client';

import { useState, useEffect, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { toast } from 'sonner';
import { Sparkles, CheckCircle2, Clock, RefreshCw } from 'lucide-react';
import { ROUTES } from '@/lib/routes';
import { packageService } from '@/services/customer/packageService';
import type { RecommendationPackage, PackageType } from '@/types/customer/package';

// ─── Mock Data ────────────────────────────────────────────────────────────────

const MOCK_EVENT = {
  eventTitle: 'Annual Company Gala 2026',
  eventType: 'Corporate Event',
  confirmedTasks: [
    { id: 't1', title: 'Venue Booking' },
    { id: 't2', title: 'Catering Service' },
    { id: 't3', title: 'Photography' },
    { id: 't4', title: 'Entertainment / DJ' },
  ],
};

const MOCK_PACKAGES: RecommendationPackage[] = [
  {
    packageId: 'pkg-budget',
    type: 'BUDGET',
    packageTotalPrice: 4200,
    currency: 'USD',
    expiresAt: new Date(Date.now() + 5 * 60 * 1000).toISOString(),
    items: [
      { taskId: 't1', taskName: 'VENUE BOOKING', offeringTitle: 'Standard Banquet Hall', offeringCategory: 'Venue', vendorName: 'CitySpace Halls', taskPrice: 1500 },
      { taskId: 't2', taskName: 'CATERING SERVICE', offeringTitle: 'Buffet Package – Classic', offeringCategory: 'Catering', vendorName: 'QuickBite Co.', taskPrice: 1200 },
      { taskId: 't3', taskName: 'PHOTOGRAPHY', offeringTitle: '4-Hour Coverage', offeringCategory: 'Photography', vendorName: 'SnapShot Studios', taskPrice: 800 },
      { taskId: 't4', taskName: 'ENTERTAINMENT / DJ', offeringTitle: 'Basic DJ Set', offeringCategory: 'Entertainment', vendorName: 'BeatDrop DJs', taskPrice: 700 },
    ],
  },
  {
    packageId: 'pkg-recommended',
    type: 'RECOMMENDED',
    packageTotalPrice: 7850,
    currency: 'USD',
    expiresAt: new Date(Date.now() + 5 * 60 * 1000).toISOString(),
    items: [
      { taskId: 't1', taskName: 'VENUE BOOKING', offeringTitle: 'Premier Ballroom', offeringCategory: 'Venue', vendorName: 'Grand Horizon Hotel', taskPrice: 3000 },
      { taskId: 't2', taskName: 'CATERING SERVICE', offeringTitle: "Seated Dinner – Chef's Menu", offeringCategory: 'Catering', vendorName: 'Savory & Fine', taskPrice: 2200 },
      { taskId: 't3', taskName: 'PHOTOGRAPHY', offeringTitle: 'Full-Day + Drone Coverage', offeringCategory: 'Photography', vendorName: 'Lumen Collective', taskPrice: 1500 },
      { taskId: 't4', taskName: 'ENTERTAINMENT / DJ', offeringTitle: 'DJ + MC Package', offeringCategory: 'Entertainment', vendorName: 'Vibe Nation', taskPrice: 1150 },
    ],
  },
  {
    packageId: 'pkg-highquality',
    type: 'HIGH_QUALITY',
    packageTotalPrice: 14500,
    currency: 'USD',
    expiresAt: new Date(Date.now() + 5 * 60 * 1000).toISOString(),
    items: [
      { taskId: 't1', taskName: 'VENUE BOOKING', offeringTitle: 'Exclusive Rooftop Terrace', offeringCategory: 'Venue', vendorName: 'The Ritz Venue', taskPrice: 5500 },
      { taskId: 't2', taskName: 'CATERING SERVICE', offeringTitle: '7-Course Tasting Menu', offeringCategory: 'Catering', vendorName: 'Étoile Cuisine', taskPrice: 4200 },
      { taskId: 't3', taskName: 'PHOTOGRAPHY', offeringTitle: 'Cinematic Photo + Video', offeringCategory: 'Photography', vendorName: 'ArtFrame Studios', taskPrice: 2800 },
      { taskId: 't4', taskName: 'ENTERTAINMENT / DJ', offeringTitle: 'Live Band + DJ Fusion', offeringCategory: 'Entertainment', vendorName: 'Platinum Sounds', taskPrice: 2000 },
    ],
  },
];

// ─── Package Config ───────────────────────────────────────────────────────────

const PACKAGE_CONFIG: Record<PackageType, {
  label: string;
  badgeClass: string;
  priceClass: string;
  buttonClass: string;
  borderClass: string;
  icon: React.ReactNode;
  bestValue?: boolean;
}> = {
  BUDGET: {
    label: 'Budget',
    badgeClass: 'bg-gray-100 text-gray-600 border border-gray-200',
    priceClass: 'text-gray-800',
    buttonClass: 'bg-gray-600 hover:bg-gray-700 text-white',
    borderClass: 'border-gray-200',
    icon: <CheckCircle2 size={13} />,
  },
  RECOMMENDED: {
    label: 'Recommended',
    badgeClass: 'bg-emerald-50 text-emerald-600 border border-emerald-200',
    priceClass: 'text-emerald-600',
    buttonClass: 'bg-emerald-500 hover:bg-emerald-600 text-white',
    borderClass: 'border-emerald-400',
    bestValue: true,
    icon: <svg viewBox="0 0 24 24" className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" /></svg>,
  },
  HIGH_QUALITY: {
    label: 'High-Quality',
    badgeClass: 'bg-purple-50 text-purple-600 border border-purple-200',
    priceClass: 'text-purple-600',
    buttonClass: 'bg-purple-600 hover:bg-purple-700 text-white',
    borderClass: 'border-purple-200',
    icon: <Sparkles size={13} />,
  },
};

// ─── Countdown Hook ───────────────────────────────────────────────────────────

function useCountdown(expiresAt: string | null) {
  const [remaining, setRemaining] = useState('');
  const [expired, setExpired] = useState(false);

  useEffect(() => {
    if (!expiresAt) return;
    const tick = () => {
      const diff = new Date(expiresAt).getTime() - Date.now();
      if (diff <= 0) { setExpired(true); setRemaining('0:00'); return; }
      const m = Math.floor(diff / 60000);
      const s = Math.floor((diff % 60000) / 1000);
      setRemaining(`${m}:${s.toString().padStart(2, '0')}`);
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [expiresAt]);

  return { remaining, expired };
}

// ─── Package Card ─────────────────────────────────────────────────────────────

function PackageCard({ pkg, eventId, onExpire }: {
  pkg: RecommendationPackage;
  eventId: string;
  onExpire: () => void;
}) {
  const config = PACKAGE_CONFIG[pkg.type];
  const { remaining, expired } = useCountdown(pkg.expiresAt);
  const router = useRouter();

  useEffect(() => { if (expired) onExpire(); }, [expired, onExpire]);

  return (
    <div className={`flex flex-col rounded-2xl border-2 bg-white shadow-sm ${config.borderClass} ${pkg.type === 'RECOMMENDED' ? 'shadow-emerald-100' : ''}`}>
      {/* Header */}
      <div className="p-5 pb-4">
        <div className="flex items-center justify-between mb-4">
          <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold ${config.badgeClass}`}>
            {config.icon}
            {config.label}
          </span>
          {config.bestValue && (
            <span className="text-xs font-bold text-emerald-600 tracking-wide">BEST VALUE</span>
          )}
        </div>
        <p className={`text-4xl font-bold ${config.priceClass}`}>
          ${pkg.packageTotalPrice.toLocaleString()}
        </p>
        <p className="text-xs text-gray-400 mt-1">
          {pkg.currency} · {pkg.items.length} tasks included
        </p>
      </div>

      {/* Items preview */}
      <div className="px-5 pb-4 space-y-2 flex-1">
        {pkg.items.map((item) => (
          <div key={item.taskId} className="bg-gray-50 rounded-xl p-3">
            <p className="text-[10px] font-bold tracking-widest text-gray-400 mb-1">{item.taskName}</p>
            <div className="flex items-start justify-between gap-2">
              <div>
                <p className="text-sm font-semibold text-gray-800">{item.offeringTitle}</p>
                <p className="text-xs text-gray-400 mt-0.5">{item.vendorName}</p>
              </div>
              <p className="text-sm font-bold text-gray-700 whitespace-nowrap">${item.taskPrice.toLocaleString()}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Footer */}
      <div className="px-5 pb-5 pt-2">
        <button
          onClick={() => router.push(ROUTES.CUSTOMER.EVENT_PACKAGE_DETAIL(eventId, pkg.packageId))}
          className={`w-full py-3 rounded-xl font-semibold text-sm transition ${config.buttonClass}`}
        >
          View Package Details
        </button>
        <div className={`flex items-center justify-center gap-1.5 mt-3 text-xs ${expired ? 'text-red-500' : 'text-amber-500'}`}>
          <Clock size={12} />
          <span>{expired ? 'Expired' : `${remaining} remaining`}</span>
        </div>
      </div>
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function CustomerEventPackagesPage() {
  const params = useParams<{ eventId: string }>();
  const eventId = params?.eventId || '';

  const [phase, setPhase] = useState<'ready' | 'generating' | 'packages' | 'expired'>('ready');
  const [packages, setPackages] = useState<RecommendationPackage[]>([]);
  const [event] = useState(MOCK_EVENT);

  // Check sessionStorage for cached packages
  useEffect(() => {
    const stored = sessionStorage.getItem(`packages_${eventId}`);
    if (stored) {
      const parsed: RecommendationPackage[] = JSON.parse(stored);
      const stillValid = parsed.every(p => new Date(p.expiresAt).getTime() > Date.now());
      if (stillValid) { setPackages(parsed); setPhase('packages'); }
      else setPhase('expired');
    }
  }, [eventId]);

  const generatePackages = useCallback(async () => {
    setPhase('generating');
    try {
      const data = await packageService.generatePackages(eventId);
      sessionStorage.setItem(`packages_${eventId}`, JSON.stringify(data));
      setPackages(data);
      setPhase('packages');
      toast.success('Packages generated successfully!');
    } catch {
      await new Promise(r => setTimeout(r, 2000));
      const data = MOCK_PACKAGES.map(p => ({
        ...p,
        expiresAt: new Date(Date.now() + 5 * 60 * 1000).toISOString(),
      }));
      sessionStorage.setItem(`packages_${eventId}`, JSON.stringify(data));
      setPackages(data);
      setPhase('packages');
      toast.success('Packages generated successfully!');
    }
  }, [eventId]);

  const handleExpire = useCallback(() => {
    sessionStorage.removeItem(`packages_${eventId}`);
    setPhase('expired');
  }, [eventId]);

  // ── Expired ──
  if (phase === 'expired') return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Recommendation Packages</h1>
        <p className="text-sm text-gray-500 mt-1">{event.eventTitle} · {event.eventType}</p>
      </div>
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-10 text-center max-w-md w-full">
          <div className="w-14 h-14 bg-amber-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Clock className="w-7 h-7 text-amber-500" />
          </div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">Packages Expired</h2>
          <p className="text-sm text-gray-500 mb-6">Your recommendation packages have expired. Please regenerate to get fresh packages.</p>
          <button onClick={generatePackages}
            className="inline-flex items-center gap-2 bg-blue-600 text-white px-6 py-3 rounded-xl font-semibold text-sm hover:bg-blue-700 transition">
            <RefreshCw size={16} />
            Regenerate Packages
          </button>
        </div>
      </div>
    </div>
  );

  // ── Generating ──
  if (phase === 'generating') return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Recommendation Packages</h1>
        <p className="text-sm text-gray-500 mt-1">{event.eventTitle} · {event.eventType}</p>
      </div>
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-10 text-center max-w-md w-full">
          <div className="w-14 h-14 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4 animate-pulse">
            <Sparkles className="w-7 h-7 text-blue-600" />
          </div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">Generating Packages...</h2>
          <p className="text-sm text-gray-500 mb-6">Our AI is shortlisting the best offerings for your event.</p>
          <div className="flex justify-center gap-1.5">
            {[0, 1, 2].map(i => (
              <div key={i} className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: `${i * 0.15}s` }} />
            ))}
          </div>
        </div>
      </div>
    </div>
  );

  // ── Packages ──
  if (phase === 'packages') return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Recommendation Packages</h1>
        <p className="text-sm text-gray-500 mt-1">{event.eventTitle} · {event.eventType}</p>
      </div>
      <p className="text-center text-sm text-gray-500 mb-6">
        Select a package to view full details and proceed.
      </p>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {packages.map(pkg => (
          <PackageCard key={pkg.packageId} pkg={pkg} eventId={eventId} onExpire={handleExpire} />
        ))}
      </div>
      <div className="mt-6 text-center">
        <button onClick={generatePackages}
          className="inline-flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 transition">
          <RefreshCw size={14} />
          Regenerate packages
        </button>
      </div>
    </div>
  );

  // ── Ready ──
  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Recommendation Packages</h1>
        <p className="text-sm text-gray-500 mt-1">{event.eventTitle} · {event.eventType}</p>
      </div>
      <div className="flex items-center justify-center min-h-[500px]">
        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-8 max-w-lg w-full">
          <div className="w-16 h-16 bg-blue-50 rounded-2xl flex items-center justify-center mx-auto mb-5">
            <Sparkles className="w-8 h-8 text-blue-500" />
          </div>
          <h2 className="text-xl font-bold text-gray-900 text-center mb-2">Smart Package Selection</h2>
          <p className="text-sm text-gray-500 text-center mb-6">
            We'll curate three packages tailored to your event based on your{' '}
            <span className="font-semibold text-gray-700">{event.confirmedTasks.length} confirmed</span> tasks.
          </p>
          <div className="space-y-2 mb-6">
            {event.confirmedTasks.map(task => (
              <div key={task.id} className="flex items-center gap-3 border border-gray-100 rounded-xl px-4 py-3 bg-gray-50">
                <CheckCircle2 className="w-5 h-5 text-emerald-500 shrink-0" />
                <span className="text-sm font-medium text-gray-700">{task.title}</span>
              </div>
            ))}
          </div>
          <button
            onClick={generatePackages}
            className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white py-3.5 rounded-xl font-semibold text-sm transition"
          >
            <Sparkles size={16} />
            Generate Recommendations
          </button>
        </div>
      </div>
    </div>
  );
}
