'use client';

import { useState, useEffect, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft, Star, X, ChevronDown } from 'lucide-react';
import { toast } from 'sonner';
import { ROUTES } from '@/lib/routes';
import { packageService } from '@/services/customer/packageService';
import type { PackageItem, ShortlistedOffering } from '@/types/customer/package';

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
  const selected = shortlist.find(o => o.offeringId === item.offeringId) ?? shortlist[0];

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
        {item.vendorName} · ${item.taskPrice.toLocaleString()}
      </p>

      {/* Dropdown trigger */}
      <div className="relative">
        <button
          onClick={() => setOpen(v => !v)}
          className="w-full flex items-center justify-between gap-2 border border-gray-200 rounded-xl px-4 py-2.5 bg-white hover:bg-gray-50 transition text-sm"
        >
          <div className="flex items-center gap-3">
            <span className="font-medium text-gray-800">{selected?.vendorName}</span>
            <span className="flex items-center gap-1 text-amber-400 text-xs font-semibold">
              <Star size={11} fill="currentColor" />
              {selected?.rating}
            </span>
            <span className="font-semibold text-gray-700">${selected?.taskPrice.toLocaleString()}</span>
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
                <div className="flex items-center gap-3">
                  <span className="font-medium text-gray-800">{offering.vendorName}</span>
                  <span className="flex items-center gap-1 text-amber-400 text-xs font-semibold">
                    <Star size={11} fill="currentColor" />
                    {offering.rating}
                  </span>
                  {offering.isBestMatch && (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-50 border border-emerald-200 text-[10px] font-semibold text-emerald-600">
                      ✦ Best Match
                    </span>
                  )}
                </div>
                <span className="font-semibold text-gray-700">${offering.taskPrice.toLocaleString()}</span>
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
      router.push(ROUTES.CUSTOMER.EVENT_PACKAGE_DETAIL(eventId, packageId));
    } catch {
      toast.error('Failed to save customization.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div>
      {loadError && (
        <div className="mb-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {loadError}
        </div>
      )}
      {/* Header */}
      <div className="mb-6">
        <button
          onClick={() => router.push(ROUTES.CUSTOMER.EVENT_PACKAGE_DETAIL(eventId, packageId))}
          className="inline-flex items-center gap-2 text-gray-500 hover:text-gray-700 transition mb-1"
        >
          <ArrowLeft size={16} />
        </button>
        <h1 className="text-xl font-bold text-gray-900">Customize Package</h1>
        <p className="text-xs text-indigo-500 mt-0.5">Event {eventId} · Package {packageId}</p>
      </div>

      <div className="flex gap-6 items-start">
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
        <div className="w-72 shrink-0 bg-white rounded-2xl border border-gray-200 p-5 sticky top-6">
          <p className="text-base font-bold text-gray-900 mb-1">Live Summary</p>
          <p className="text-xs text-gray-400 mb-4">{packageLabel}</p>

          <div className="space-y-2 mb-4">
            {items.map(item => (
              <div key={item.taskId} className="flex justify-between text-sm">
                <span className="text-gray-600">{item.taskName}</span>
                <span className="font-medium text-gray-800">${item.taskPrice.toLocaleString()}</span>
              </div>
            ))}
          </div>

          <div className="border-t border-gray-100 pt-3 flex justify-between items-center mb-5">
            <span className="text-sm font-semibold text-gray-700">Total</span>
            <span className="text-2xl font-bold text-gray-900">${totalPrice.toLocaleString()}</span>
          </div>

          <button
            onClick={handleSave}
            disabled={saving || items.length === 0}
            className="w-full py-3 rounded-xl bg-indigo-400 hover:bg-indigo-500 text-white font-semibold text-sm transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {saving ? 'Saving...' : 'Save Customization'}
          </button>
        </div>
      </div>
    </div>
  );
}
