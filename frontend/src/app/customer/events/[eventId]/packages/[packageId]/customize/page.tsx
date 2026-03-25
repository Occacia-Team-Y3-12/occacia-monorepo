'use client';

import { useState, useEffect, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft, Star, X, ChevronDown } from 'lucide-react';
import { toast } from 'sonner';
import { ROUTES } from '@/lib/routes';
import { packageService } from '@/services/customer/packageService';
import type { PackageItem, ShortlistedOffering } from '@/types/customer/package';
import { formatCurrency } from '@/lib/currency';

// ─── Task Row ─────────────────────────────────────────────────────────────────

function TaskRow({
  item,
  shortlist,
  onSelect,
  onRemove,
}: {
  item: PackageItem;
  shortlist: ShortlistedOffering[];
  onSelect: (taskId: string, offering: ShortlistedOffering) => void;
  onRemove: (taskId: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const selected = shortlist.find((o) => o.offeringId === item.offeringId) ?? shortlist[0];
  const ratingValue =
    selected?.rating ??
    (typeof selected?.score === 'number'
      ? Number((selected.score / 2).toFixed(1))
      : undefined);
  const currencyLabel = selected?.currency || 'LKR';

  return (
    <div className="bg-white rounded-2xl border border-gray-200 p-4 relative">
      {/* Remove */}
      <button
        onClick={() => onRemove(item.taskId)}
        className="absolute top-4 right-4 text-gray-300 hover:text-gray-500 transition"
      >
        <X size={16} />
      </button>

      {/* Task name + current */}
      <p className="text-sm font-semibold text-gray-900 mb-0.5">{item.taskName}</p>
      <p className="text-xs text-gray-400 mb-3">
        {item.vendorName} · {currencyLabel} {item.taskPrice.toLocaleString()}
      </p>

      {/* Dropdown trigger */}
      <div className="relative">
        <button
          onClick={() => setOpen(v => !v)}
          className="w-full flex items-center justify-between gap-2 border border-gray-200 rounded-xl px-4 py-2.5 bg-white hover:bg-gray-50 transition text-sm"
        >
            <div className="flex flex-wrap items-center gap-3">
              <span className="font-medium text-gray-800">{selected?.vendorName}</span>
              <span className="inline-flex items-center gap-1 text-amber-400 text-xs font-semibold">
                <Star size={11} fill="currentColor" />
                {ratingValue ?? '—'}
              </span>
              <span className="text-xs uppercase tracking-widest text-gray-500">Rank {selected?.rank ?? '-'}</span>
              <span className="font-semibold text-gray-700">
                {currencyLabel} {selected?.taskPrice.toLocaleString()}
              </span>
              {selected?.isBestMatch && (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-50 border border-emerald-200 text-[10px] font-semibold text-emerald-600">
                  ✦ Best Match
                </span>
              )}
            </div>
            <ChevronDown size={15} className={`text-gray-400 transition-transform ${open ? 'rotate-180' : ''}`} />
          </button>

        {/* Dropdown options */}
        {open && (
          <div className="absolute z-10 top-full mt-1 w-full bg-white border border-gray-200 rounded-xl shadow-lg overflow-hidden">
            {shortlist.map(offering => (
              <button
                key={offering.offeringId}
                onClick={() => { onSelect(item.taskId, offering); setOpen(false); }}
                className={`w-full flex items-center justify-between px-4 py-3 text-sm hover:bg-gray-50 transition ${offering.offeringId === item.offeringId ? 'bg-indigo-50' : ''}`}
              >
              <div className="flex flex-wrap items-center gap-3">
                <span className="font-medium text-gray-800">{offering.vendorName}</span>
                <span className="inline-flex items-center gap-1 text-amber-400 text-xs font-semibold">
                  <Star size={11} fill="currentColor" />
                  {offering.rating ?? Number((offering.score ?? 0).toFixed(1))}
                </span>
                <span className="text-xs uppercase tracking-widest text-gray-500">Rank {offering.rank ?? '-'}</span>
                {offering.isBestMatch && (
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-50 border border-emerald-200 text-[10px] font-semibold text-emerald-600">
                    ✦ Best Match
                  </span>
                )}
              </div>
              <span className="font-semibold text-gray-700">
                {offering.currency || 'LKR'} {offering.taskPrice.toLocaleString()}
              </span>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function CustomizePackagePage() {
  const params = useParams<{ eventId: string; packageId: string }>();
  const router = useRouter();
  const eventId = params?.eventId || '';
  const packageId = params?.packageId || '';

  const [items, setItems] = useState<PackageItem[]>([]);
  const [shortlists, setShortlists] = useState<Record<string, ShortlistedOffering[]>>({});
  const [saving, setSaving] = useState(false);
  const [packageLabel, setPackageLabel] = useState('Package');
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    const loadPackage = async () => {
      try {
        const pkg = await packageService.getPackageById(eventId, packageId);
        const shortlistEntries = await Promise.all(
          pkg.items.map(async (item) => [
            item.taskId,
            await packageService.getTaskRecommendations(eventId, item.taskId),
          ] as const)
        );

        if (!active) {
          return;
        }

        setPackageLabel(
          `${pkg.type.charAt(0)}${pkg.type
            .slice(1)
            .toLowerCase()
            .replace('_', ' ')} Package`
        );
        setItems(pkg.items);
        setShortlists(Object.fromEntries(shortlistEntries));
        setLoadError(null);
      } catch {
        if (active) {
          setLoadError('Unable to load package recommendations.');
        }
      }
    };

    void loadPackage();

    return () => {
      active = false;
    };
  }, [eventId, packageId]);

  const handleSelect = useCallback((taskId: string, offering: ShortlistedOffering) => {
    setItems(prev => prev.map(item =>
      item.taskId === taskId
        ? { ...item, offeringId: offering.offeringId, offeringTitle: offering.offeringTitle, vendorName: offering.vendorName, taskPrice: offering.taskPrice, rating: offering.rating }
        : item
    ));
  }, []);

  const handleRemove = useCallback((taskId: string) => {
    setItems(prev => prev.filter(item => item.taskId !== taskId));
  }, []);

  const totalPrice = items.reduce((sum, item) => sum + item.taskPrice, 0);

  const handleSave = async () => {
    setSaving(true);
    try {
      await packageService.updatePackage(eventId, packageId, items.map(i => ({ taskId: i.taskId, offeringId: i.offeringId })));
      toast.success('Customization saved!');
      router.push(ROUTES.CUSTOMER.EVENT_TRACKING(eventId));
    } catch {
      toast.error('Failed to save customization.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <main className="max-w-6xl mx-auto px-4 sm:px-6 py-8 space-y-6">
      {loadError && (
        <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {loadError}
        </div>
      )}

      <section className="overflow-hidden rounded-[28px] border border-[#DCE4F2] bg-[linear-gradient(140deg,#FFFFFF_0%,#F6FAFF_52%,#EEF5FF_100%)] px-6 py-6 shadow-[0_24px_60px_-36px_rgba(13,71,161,0.2)]">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[#0D47A1]">Package Builder</p>
            <h1 className="mt-2 text-3xl font-semibold tracking-tight text-[#173B7A]">{packageLabel}</h1>
            <p className="mt-1 text-sm text-[#5B6780]">Handpick from the AI-curated shortlist for each task.</p>
          </div>
          <button
            onClick={() => router.push(ROUTES.CUSTOMER.EVENT_PACKAGE_DETAIL(eventId, packageId))}
            className="inline-flex items-center gap-2 rounded-full border border-white/50 bg-white/20 px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-white transition hover:bg-white/30"
          >
            <ArrowLeft size={14} />
            Back to Package
          </button>
        </div>
      </section>

      <div className="flex flex-col gap-6 lg:flex-row">
        {/* Left — Tasks */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between mb-4">
            <p className="text-sm font-semibold text-gray-700">Tasks ({items.length})</p>
            <p className="text-xs text-indigo-400">Select alternative vendors from the shortlist</p>
          </div>

          <div className="space-y-3">
            {items.map(item => (
              <TaskRow
                key={item.taskId}
                item={item}
                shortlist={shortlists[item.taskId] ?? []}
                onSelect={handleSelect}
                onRemove={handleRemove}
              />
            ))}
          </div>
        </div>

        {/* Right — Live Summary */}
        <div className="w-full lg:w-80 shrink-0 rounded-[26px] border border-[#DCE4F2] bg-white p-6 shadow-[0_18px_48px_-32px_rgba(13,71,161,0.18)]">
          <div className="rounded-[22px] bg-gradient-to-br from-[#0D47A1] to-[#1765CC] px-4 py-5 text-white">
            <p className="text-xs uppercase tracking-[0.24em] text-white/70">Live Summary</p>
            <p className="mt-2 text-2xl font-semibold tracking-tight">{formatCurrency(totalPrice)}</p>
            <p className="text-[11px] text-white/80">{items.length} task{items.length !== 1 ? 's' : ''} in scope</p>
          </div>
          <div className="mt-5 space-y-3">
            {items.map((item) => (
              <div key={item.taskId} className="flex justify-between text-xs font-semibold text-[#4A5976]">
                <span>{item.taskName}</span>
                <span>{formatCurrency(item.taskPrice)}</span>
              </div>
            ))}
          </div>
          <button
            onClick={handleSave}
            disabled={saving || items.length === 0}
            className="mt-6 inline-flex w-full items-center justify-center gap-2 rounded-full bg-[#0D47A1] px-5 py-3 text-sm font-semibold text-white transition hover:bg-[#1D59D0] disabled:opacity-60 disabled:cursor-not-allowed"
          >
            {saving ? 'Saving...' : 'Save Customization'}
          </button>
        </div>
      </div>
    </main>
  );
}
