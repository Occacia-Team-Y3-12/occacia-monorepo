'use client';

import { useState } from 'react';
import { toast } from 'sonner';
import { z } from 'zod';
import { CreateOfferingData, OfferingCategory, QualityTier, Offering } from '@/types/vendor/offering';

const offeringSchema = z.object({
  title: z.string().min(3, 'Title must be at least 3 characters').max(100, 'Title must not exceed 100 characters'),
  description: z.string().min(10, 'Description must be at least 10 characters').max(500, 'Description must not exceed 500 characters'),
  category: z.enum(['CATERING', 'PHOTOGRAPHY', 'VENUE', 'DECORATION', 'MUSIC', 'TRANSPORT', 'OTHER']),
  price: z.preprocess((val) => parseFloat(val as string), z.number().min(1, 'Price must be at least $1').max(1000000, 'Price must not exceed $1,000,000')),
  qualityTier: z.enum(['BUDGET', 'STANDARD', 'PREMIUM', 'LUXURY']),
  isActive: z.boolean(),
});

type OfferingFormErrors = Partial<Record<keyof CreateOfferingData, string>>;

interface OfferingFormProps {
  initialData?: Offering;
  onSubmit: (data: CreateOfferingData) => Promise<void>;
  isLoading: boolean;
  onCancel: () => void;
}

const CATEGORIES: { value: OfferingCategory; label: string }[] = [
  { value: 'CATERING', label: 'Catering' },
  { value: 'PHOTOGRAPHY', label: 'Photography' },
  { value: 'VENUE', label: 'Venue' },
  { value: 'DECORATION', label: 'Decoration' },
  { value: 'MUSIC', label: 'Music' },
  { value: 'TRANSPORT', label: 'Transport' },
  { value: 'OTHER', label: 'Other' },
];

const QUALITY_TIERS: { value: QualityTier; label: string; desc: string }[] = [
  { value: 'BUDGET', label: 'Budget', desc: 'Cost-effective option' },
  { value: 'STANDARD', label: 'Standard', desc: 'Regular quality' },
  { value: 'PREMIUM', label: 'Premium', desc: 'High quality' },
  { value: 'LUXURY', label: 'Luxury', desc: 'Top-tier experience' },
];

export default function OfferingForm({ initialData, onSubmit, isLoading, onCancel }: OfferingFormProps) {
  const [formData, setFormData] = useState<CreateOfferingData>({
    title: initialData?.title || '',
    description: initialData?.description || '',
    category: initialData?.category || 'CATERING',
    price: initialData?.price || 0,
    qualityTier: initialData?.qualityTier || 'STANDARD',
    isActive: initialData?.isActive ?? true,
  });
  const [errors, setErrors] = useState<OfferingFormErrors>({});

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox'
        ? (e.target as HTMLInputElement).checked
        : name === 'price' ? parseFloat(value) || 0
        : value,
    }));
    if (errors[name as keyof CreateOfferingData]) {
      setErrors(prev => ({ ...prev, [name]: undefined }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      offeringSchema.parse(formData);
      setErrors({});
      await onSubmit(formData);
    } catch (error: any) {
      if (error.errors) {
        const fieldErrors: OfferingFormErrors = {};
        error.errors.forEach((err: any) => {
          fieldErrors[err.path[0] as keyof CreateOfferingData] = err.message;
        });
        setErrors(fieldErrors);
        toast.error('Please fix the validation errors');
      }
    }
  };

  const inputClass = (field: keyof CreateOfferingData) =>
    `w-full border rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition ${
      errors[field] ? 'border-red-400 bg-red-50' : 'border-slate-200 bg-white'
    }`;

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-1.5">Title *</label>
        <input type="text" name="title" value={formData.title} onChange={handleChange}
          placeholder="e.g. Premium Wedding Photography Package"
          className={inputClass('title')} disabled={isLoading} />
        {errors.title && <p className="text-xs text-red-500 mt-1">{errors.title}</p>}
      </div>

      <div>
        <label className="block text-sm font-medium text-slate-700 mb-1.5">Description *</label>
        <textarea name="description" value={formData.description} onChange={handleChange} rows={3}
          placeholder="Describe your offering in detail..."
          className={inputClass('description')} disabled={isLoading} />
        <div className="flex justify-between mt-1">
          {errors.description ? <p className="text-xs text-red-500">{errors.description}</p> : <span />}
          <span className="text-xs text-slate-400">{formData.description.length}/500</span>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1.5">Category *</label>
          <select name="category" value={formData.category} onChange={handleChange}
            className={inputClass('category')} disabled={isLoading}>
            {CATEGORIES.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
          </select>
          {errors.category && <p className="text-xs text-red-500 mt-1">{errors.category}</p>}
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1.5">Quality Tier *</label>
          <select name="qualityTier" value={formData.qualityTier} onChange={handleChange}
            className={inputClass('qualityTier')} disabled={isLoading}>
            {QUALITY_TIERS.map(t => (
              <option key={t.value} value={t.value}>{t.label} — {t.desc}</option>
            ))}
          </select>
          {errors.qualityTier && <p className="text-xs text-red-500 mt-1">{errors.qualityTier}</p>}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-slate-700 mb-1.5">Price (USD) *</label>
        <div className="relative">
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-sm">$</span>
          <input type="number" name="price" value={formData.price || ''} onChange={handleChange}
            min={1} max={1000000} step={0.01} placeholder="0.00"
            className={`${inputClass('price')} pl-7`} disabled={isLoading} />
        </div>
        {errors.price && <p className="text-xs text-red-500 mt-1">{errors.price}</p>}
      </div>

      <div className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg border border-slate-200">
        <input type="checkbox" id="isActive" name="isActive" checked={formData.isActive}
          onChange={handleChange} className="w-4 h-4 text-blue-600 rounded cursor-pointer" disabled={isLoading} />
        <div>
          <label htmlFor="isActive" className="text-sm font-medium text-slate-700 cursor-pointer">Active Offering</label>
          <p className="text-xs text-slate-500">Active offerings are available for AI-based recommendation shortlisting</p>
        </div>
      </div>

      <div className="flex gap-3 pt-2">
        <button type="submit" disabled={isLoading}
          className="flex-1 bg-blue-600 text-white py-2.5 rounded-lg font-medium hover:bg-blue-700 transition disabled:bg-blue-400 disabled:cursor-not-allowed text-sm">
          {isLoading ? 'Saving...' : initialData ? 'Update Offering' : 'Create Offering'}
        </button>
        <button type="button" onClick={onCancel} disabled={isLoading}
          className="flex-1 border border-slate-200 text-slate-700 py-2.5 rounded-lg font-medium hover:bg-slate-50 transition text-sm">
          Cancel
        </button>
      </div>
    </form>
  );
}
