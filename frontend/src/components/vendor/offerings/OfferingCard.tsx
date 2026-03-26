'use client';

import { Offering } from '@/types/vendor/offering';
import { Edit2, Tag, DollarSign, Star } from 'lucide-react';

const tierColors: Record<string, string> = {
  BUDGET: 'bg-slate-100 text-slate-700',
  STANDARD: 'bg-[#EAF2FF] text-[#1565c0]',
  PREMIUM: 'bg-[#EEF0FF] text-[#3F51B5]',
  LUXURY: 'bg-[#FFF8E6] text-[#8A6B00]',
};

interface OfferingCardProps {
  offering: Offering;
  onEdit: (offering: Offering) => void;
}

export default function OfferingCard({ offering, onEdit }: OfferingCardProps) {
  const categoryLabel = offering.category.charAt(0) + offering.category.slice(1).toLowerCase();
  const tierLabel = offering.qualityTier.charAt(0) + offering.qualityTier.slice(1).toLowerCase();

  return (
    <article className="rounded-2xl border border-[#E2E5EC] bg-white p-5 shadow-[0_4px_16px_rgba(15,23,42,0.06)] transition hover:border-[#C9D7EE] hover:shadow-[0_8px_20px_rgba(15,23,42,0.08)]">
      <div className="mb-3 flex items-start justify-between">
        <div className="min-w-0 flex-1">
          <h3 className="truncate text-base font-semibold text-[#1F293F]">{offering.title}</h3>
          <p className="mt-1 line-clamp-2 text-sm text-[#5B6478]">{offering.description}</p>
        </div>
        <button
          onClick={() => onEdit(offering)}
          className="ml-3 flex-shrink-0 rounded-lg p-2 text-[#7A859B] transition hover:bg-[#EFF4FC] hover:text-[#1565c0]"
          aria-label="Edit offering"
        >
          <Edit2 size={16} />
        </button>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600">
          <Tag size={11} /> {categoryLabel}
        </span>
        <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium ${tierColors[offering.qualityTier]}`}>
          <Star size={11} /> {tierLabel}
        </span>
        <span className="inline-flex items-center gap-1 rounded-full bg-[#EAF2FF] px-2.5 py-1 text-xs font-medium text-[#1565c0]">
          <DollarSign size={11} /> ${offering.price.toLocaleString()}
        </span>
        <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${offering.isActive ? 'bg-[#EAF2FF] text-[#0D47A1]' : 'bg-[#FFF1F1] text-[#C22525]'}`}>
          {offering.isActive ? 'Active' : 'Inactive'}
        </span>
      </div>
    </article>
  );
}
