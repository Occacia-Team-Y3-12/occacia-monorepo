'use client';

import { Offering } from '@/types/vendor/offering';
import { Edit2, Tag, DollarSign, Star } from 'lucide-react';

const tierColors: Record<string, string> = {
  BUDGET: 'bg-gray-100 text-gray-700',
  STANDARD: 'bg-blue-100 text-blue-700',
  PREMIUM: 'bg-purple-100 text-purple-700',
  LUXURY: 'bg-yellow-100 text-yellow-700',
};

interface OfferingCardProps {
  offering: Offering;
  onEdit: (offering: Offering) => void;
}

export default function OfferingCard({ offering, onEdit }: OfferingCardProps) {
  const categoryLabel = offering.category.charAt(0) + offering.category.slice(1).toLowerCase();
  const tierLabel = offering.qualityTier.charAt(0) + offering.qualityTier.slice(1).toLowerCase();

  return (
    <article className="bg-white border border-slate-200 rounded-2xl p-5 hover:shadow-md transition shadow-[0_4px_16px_rgba(15,23,42,0.06)]">
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-slate-900 text-base truncate">{offering.title}</h3>
          <p className="text-sm text-slate-500 mt-1 line-clamp-2">{offering.description}</p>
        </div>
        <button onClick={() => onEdit(offering)}
          className="ml-3 p-2 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition flex-shrink-0"
          aria-label="Edit offering">
          <Edit2 size={16} />
        </button>
      </div>

      <div className="flex flex-wrap gap-2 mt-4">
        <span className="inline-flex items-center gap-1 text-xs bg-slate-100 text-slate-600 px-2.5 py-1 rounded-full font-medium">
          <Tag size={11} /> {categoryLabel}
        </span>
        <span className={`inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full font-medium ${tierColors[offering.qualityTier]}`}>
          <Star size={11} /> {tierLabel}
        </span>
        <span className="inline-flex items-center gap-1 text-xs bg-emerald-100 text-emerald-700 px-2.5 py-1 rounded-full font-medium">
          <DollarSign size={11} /> ${offering.price.toLocaleString()}
        </span>
        <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${offering.isActive ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-600'}`}>
          {offering.isActive ? '● Active' : '● Inactive'}
        </span>
      </div>
    </article>
  );
}
