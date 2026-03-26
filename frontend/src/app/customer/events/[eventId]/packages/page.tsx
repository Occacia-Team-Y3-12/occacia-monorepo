'use client';

import { useState, useEffect, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { toast } from 'sonner';
import { Sparkles, CheckCircle2, Clock, RefreshCw } from 'lucide-react';
import { ROUTES } from '@/lib/routes';
import { packageService } from '@/services/customer/packageService';
import { formatCurrency } from '@/lib/currency';
import type { RecommendationPackage, PackageType } from '@/types/customer/package';

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

const PHASE_LABELS: Record<'ready' | 'generating' | 'packages' | 'expired', string> = {
  ready: 'Ready to generate',
  generating: 'Generating packs',
  packages: 'Packages ready',
  expired: 'Expired',
};

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
    <div
      className={`flex flex-col rounded-[26px] border border-[#DCE4F2] bg-white shadow-[0_18px_48px_-32px_rgba(13,71,161,0.2)] ${pkg.type === 'RECOMMENDED' ? 'ring-2 ring-emerald-200' : ''}`}
    >
      {/* Header */}
      <div className="px-6 pt-6 pb-4">
        <div className="flex items-center justify-between mb-4">
          <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold ${config.badgeClass}`}>
            {config.icon}
            {config.label}
          </span>
          {config.bestValue && (
            <span className="text-xs font-bold text-emerald-600 tracking-wide">BEST VALUE</span>
          )}
        </div>
        <p className={`text-3xl font-semibold ${config.priceClass}`}>
          {formatCurrency(pkg.packageTotalPrice)}
        </p>
        <p className="text-[11px] text-[#5B6780] mt-1">
          {pkg.currency} · {pkg.items.length} tasks included
        </p>
      </div>

      {/* Items preview */}
      <div className="px-6 pb-4 space-y-3 flex-1">
        {pkg.items.map((item) => (
          <div key={item.taskId} className="bg-[#F7F9FF] rounded-2xl p-3">
            <p className="text-[10px] font-bold tracking-widest text-[#9AA6BF] mb-1">{item.taskName}</p>
            <div className="flex items-start justify-between gap-2">
              <div>
                <p className="text-sm font-semibold text-[#1D273C]">{item.offeringTitle}</p>
                <p className="text-xs text-[#5B6780] mt-0.5">{item.vendorName}</p>
              </div>
              <p className="text-sm font-semibold text-[#0D47A1] whitespace-nowrap">{formatCurrency(item.taskPrice)}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Footer */}
      <div className="px-6 pb-6 pt-2">
        <button
          onClick={() => router.push(ROUTES.CUSTOMER.EVENT_PACKAGE_DETAIL(eventId, pkg.packageId))}
          className={`w-full py-3 rounded-full font-semibold text-sm transition ${config.buttonClass}`}
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
  const router = useRouter();
  const eventId = params?.eventId || '';

  const [phase, setPhase] = useState<'ready' | 'generating' | 'packages' | 'expired'>('ready');
  const [packages, setPackages] = useState<RecommendationPackage[]>([]);
  const eventTitle = packages[0]?.eventName || 'Current Event';
  const eventSubtitle = eventId ? `Event ${eventId}` : 'Event';
  const confirmedTasks = packages[0]?.items ?? [];

  const toPackageArray = (value: unknown): RecommendationPackage[] =>
    Array.isArray(value) ? value : [];

  useEffect(() => {
    let active = true;

    const loadPackages = async () => {
      try {
        const existingPackages = await packageService.getPackages(eventId);
        const normalizedPackages = toPackageArray(existingPackages);

        if (!active || normalizedPackages.length === 0) {
          return;
        }

        const stillValid = normalizedPackages.every(
          (pkg) => new Date(pkg.expiresAt).getTime() > Date.now()
        );

        if (stillValid) {
          setPackages(normalizedPackages);
          setPhase('packages');
          return;
        }

        packageService.clearCachedPackages(eventId);
        setPhase('expired');
      } catch {
        if (active) {
          setPhase('ready');
        }
      }
    };

    void loadPackages();

    return () => {
      active = false;
    };
  }, [eventId]);

  const generatePackages = useCallback(async () => {
    setPhase('generating');
    try {
      const data = await packageService.generatePackages(eventId);
      setPackages(toPackageArray(data));
      setPhase('packages');
      toast.success('Packages generated successfully!');
    } catch {
      setPhase('ready');
      toast.error('Failed to generate packages. Please try again.');
    }
  }, [eventId]);

  const handleExpire = useCallback(() => {
    packageService.clearCachedPackages(eventId);
    setPhase('expired');
  }, [eventId]);

  const heroSubtitle = `${eventTitle} · ${eventSubtitle}`;
  const summaryCards = [
    {
      title: 'Confirmed Tasks',
      value: confirmedTasks.length,
      description: 'Tasks fueling the recommendations.',
    },
    {
      title: 'Active Packages',
      value: phase === 'packages' ? packages.length : 0,
      description: 'Fresh AI-curated options ready for review.',
    },
    {
      title: 'Workflow Stage',
      value: PHASE_LABELS[phase],
      description: 'Current experience status.',
    },
  ];

  const renderPhaseContent = () => {
    const cardClass = 'rounded-[26px] border border-[#DCE4F2] bg-white p-6 shadow-[0_18px_48px_-32px_rgba(13,71,161,0.24)]';

    if (phase === 'expired') {
      return (
        <div className={cardClass}>
          <div className="flex items-start gap-4">
            <Clock className="w-7 h-7 text-amber-500 shrink-0" />
            <div>
              <p className="text-lg font-semibold text-[#0D47A1]">Packages Expired</p>
              <p className="text-sm text-[#4A5976] mt-1">
                Your recommendation packages have expired. Please regenerate to get fresh selections tailored to your confirmed tasks.
              </p>
            </div>
          </div>
          <div className="mt-6 flex justify-end">
            <button
              onClick={generatePackages}
              className="inline-flex items-center gap-2 rounded-full border border-transparent bg-white px-5 py-2 text-sm font-semibold text-[#0D47A1] shadow-sm transition hover:bg-white/80"
            >
              <RefreshCw size={16} />
              Regenerate Packages
            </button>
          </div>
        </div>
      );
    }

    if (phase === 'generating') {
      return (
        <div className={`${cardClass} text-center`}>
          <div className="flex flex-col items-center gap-3">
            <div className="w-16 h-16 bg-blue-50 rounded-2xl flex items-center justify-center">
              <Sparkles className="w-8 h-8 text-[#0D47A1]" />
            </div>
            <p className="text-lg font-semibold text-[#0D47A1]">Generating Packages...</p>
            <p className="text-sm text-[#4A5976]">
              Our AI is shortlisting the best offerings for your event. This may take a few moments.
            </p>
            <div className="flex justify-center gap-1.5 mt-2">
              {[0, 1, 2].map(i => (
                <div
                  key={i}
                  className="w-2.5 h-2.5 bg-[#0D47A1] rounded-full animate-bounce"
                  style={{ animationDelay: `${i * 0.15}s` }}
                />
              ))}
            </div>
          </div>
        </div>
      );
    }

    if (phase === 'packages') {
      return (
        <div className="space-y-6">
          <div className={cardClass}>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-semibold text-[#5B6780] uppercase tracking-[0.2em]">Recommendation Packages</p>
                <p className="text-lg font-semibold text-[#0D47A1] mt-1">Explore your curated options</p>
              </div>
              <p className="text-xs font-semibold text-[#4A5976]">{packages.length} package{packages.length !== 1 ? 's' : ''} ready</p>
            </div>
            <p className="text-sm text-[#4A5976] mt-3">
              Select a package to view full details and proceed with confirmation.
            </p>
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
            {packages.map(pkg => (
              <PackageCard key={pkg.packageId} pkg={pkg} eventId={eventId} onExpire={handleExpire} />
            ))}
          </div>
          <div className="flex justify-center">
            <button
              onClick={generatePackages}
              className="inline-flex items-center gap-2 rounded-full border border-[#DCE4F2] px-5 py-2 text-sm font-semibold text-[#0D47A1] transition hover:bg-white"
            >
              <RefreshCw size={14} />
              Regenerate packages
            </button>
          </div>
        </div>
      );
    }

    return (
      <div className={`${cardClass} space-y-6 max-w-3xl mx-auto`}>
        <div className="text-center space-y-3">
          <div className="w-16 h-16 bg-[#E1EBFF] rounded-2xl flex items-center justify-center mx-auto">
            <Sparkles className="w-8 h-8 text-[#0D47A1]" />
          </div>
          <p className="text-lg font-semibold text-[#0D47A1]">Smart Package Selection</p>
          <p className="text-sm text-[#4A5976]">
            We'll curate packages tailored to your event based on your{' '}
            <span className="font-semibold text-[#173B7A]">{confirmedTasks.length} confirmed</span> tasks.
          </p>
        </div>
        <div className="space-y-2">
          {confirmedTasks.map(task => (
            <div
              key={task.taskId}
              className="flex items-center gap-3 rounded-2xl border border-[#E1E6EF] bg-[#F7F9FF] px-4 py-3"
            >
              <CheckCircle2 className="w-5 h-5 text-[#34A853] shrink-0" />
              <span className="text-sm font-medium text-[#1D273C]">{task.taskName}</span>
            </div>
          ))}
        </div>
        <button
          onClick={generatePackages}
          className="w-full flex items-center justify-center gap-2 rounded-full bg-[#0D47A1] px-6 py-3 text-sm font-semibold text-white transition hover:bg-[#1B5FAD]"
        >
          <Sparkles size={16} />
          Generate Recommendations
        </button>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-[#F3F5F9] text-[#1D273C]">
      <section className="relative overflow-hidden rounded-[32px] border border-[#DCE4F2] bg-[linear-gradient(135deg,#0D47A1_0%,#1562CC_48%,#4285F4_100%)] px-6 py-8 text-white shadow-[0_24px_70px_-34px_rgba(13,71,161,0.34)] sm:px-8 sm:py-10">
        <div className="absolute inset-y-0 right-0 w-[40%] bg-[radial-gradient(circle_at_top_right,rgba(255,255,255,0.24),transparent_60%)]" />
        <div className="relative flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-2xl space-y-3">
            <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-white/75">
              Recommendation Workspace
            </p>
            <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">
              Recommendation Packages
            </h1>
            <p className="text-sm leading-7 text-white/86 sm:text-base">{heroSubtitle}</p>
          </div>
          <div className="flex flex-wrap gap-3">
            <button
              onClick={() => router.push(ROUTES.CUSTOMER.EVENTS)}
              className="inline-flex items-center justify-center gap-2 rounded-full border border-white/60 bg-white/20 px-5 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-white transition hover:bg-white/30"
            >
              View All Events
            </button>
            <button
              onClick={generatePackages}
              className="inline-flex items-center justify-center gap-2 rounded-full bg-white px-5 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-[#0D47A1] transition hover:bg-white/90"
            >
              Regenerate
            </button>
          </div>
        </div>
      </section>

      <section className="max-w-6xl mx-auto px-4 sm:px-6 py-10 space-y-10">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {summaryCards.map((card) => (
            <div key={card.title} className="rounded-[24px] border border-[#DCE4F2] bg-white p-5 shadow-[0_12px_40px_-28px_rgba(0,0,0,0.3)]">
              <p className="text-xs font-semibold uppercase tracking-[0.3em] text-[#9AA6BF]">{card.title}</p>
              <p className="mt-3 text-3xl font-semibold text-[#0D47A1]">
                {card.value}
              </p>
              <p className="mt-2 text-sm text-[#4A5976]">
                {card.description}
              </p>
            </div>
          ))}
        </div>

        <div className="space-y-6">
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.3em] text-[#9AA6BF]">Package Control Center</p>
              <h2 className="text-2xl font-semibold text-[#1D273C]">Current Status</h2>
            </div>
            <span className="rounded-full border border-[#DCE4F2] bg-white px-4 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-[#0D47A1]">
              {PHASE_LABELS[phase]}
            </span>
          </div>
          {renderPhaseContent()}
        </div>
      </section>
    </div>
  );
}
