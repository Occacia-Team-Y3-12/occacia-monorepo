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
    `w-full rounded-lg border px-3 py-2.5 text-sm transition focus:outline-none focus:ring-2 focus:ring-[#4285F4]/30 ${
      errors[field] ? 'border-[#EA4335] bg-[#FFF1F1]' : 'border-[#D7DEEA] bg-[#F9FBFF] focus:border-[#4285F4]'
    }`;

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div>
        <label className="mb-1.5 block text-sm font-medium text-[#3D475C]">Title *</label>
        <input
          type="text"
          name="title"
          value={formData.title}
          onChange={handleChange}
          placeholder="e.g. Premium Wedding Photography Package"
          className={inputClass('title')}
          disabled={isLoading}
        />
        {errors.title && <p className="mt-1 text-xs text-[#C22525]">{errors.title}</p>}
      </div>

      <div>
        <label className="mb-1.5 block text-sm font-medium text-[#3D475C]">Description *</label>
        <textarea
          name="description"
          value={formData.description}
          onChange={handleChange}
          rows={3}
          placeholder="Describe your offering in detail..."
          className={inputClass('description')}
          disabled={isLoading}
        />
        <div className="mt-1 flex justify-between">
          {errors.description ? <p className="text-xs text-[#C22525]">{errors.description}</p> : <span />}
          <span className="text-xs text-[#8A93A6]">{formData.description.length}/500</span>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div>
          <label className="mb-1.5 block text-sm font-medium text-[#3D475C]">Category *</label>
          <select
            name="category"
            value={formData.category}
            onChange={handleChange}
            className={inputClass('category')}
            disabled={isLoading}
          >
            {CATEGORIES.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
          </select>
          {errors.category && <p className="mt-1 text-xs text-[#C22525]">{errors.category}</p>}
        </div>

        <div>
          <label className="mb-1.5 block text-sm font-medium text-[#3D475C]">Quality Tier *</label>
          <select
            name="qualityTier"
            value={formData.qualityTier}
            onChange={handleChange}
            className={inputClass('qualityTier')}
            disabled={isLoading}
          >
            {QUALITY_TIERS.map(t => (
              <option key={t.value} value={t.value}>{t.label} - {t.desc}</option>
            ))}
          </select>
          {errors.qualityTier && <p className="mt-1 text-xs text-[#C22525]">{errors.qualityTier}</p>}
        </div>
      </div>

      <div>
        <label className="mb-1.5 block text-sm font-medium text-[#3D475C]">Price (USD) *</label>
        <div className="relative">
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-sm text-[#8A93A6]">$</span>
          <input
            type="number"
            name="price"
            value={formData.price || ''}
            onChange={handleChange}
            min={1}
            max={1000000}
            step={0.01}
            placeholder="0.00"
            className={`${inputClass('price')} pl-7`}
            disabled={isLoading}
          />
        </div>
        {errors.price && <p className="mt-1 text-xs text-[#C22525]">{errors.price}</p>}
      </div>

      <div className="flex items-center gap-3 rounded-lg border border-[#D7DEEA] bg-[#F5F8FE] p-3">
        <input
          type="checkbox"
          id="isActive"
          name="isActive"
          checked={formData.isActive}
          onChange={handleChange}
          className="h-4 w-4 cursor-pointer rounded border-[#BCC8DD] text-[#1565c0] focus:ring-[#4285F4]/40"
          disabled={isLoading}
        />
        <div>
          <label htmlFor="isActive" className="cursor-pointer text-sm font-medium text-[#3D475C]">Active Offering</label>
          <p className="text-xs text-[#5B6478]">Active offerings are available for AI-based recommendation shortlisting</p>
        </div>
      </div>

      <div className="flex gap-3 pt-2">
        <button
          type="submit"
          disabled={isLoading}
          className="flex-1 rounded-lg bg-[#1565c0] py-2.5 text-sm font-medium text-white transition hover:bg-[#0d47a1] disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isLoading ? 'Saving...' : initialData ? 'Update Offering' : 'Create Offering'}
        </button>
        <button
          type="button"
          onClick={onCancel}
          disabled={isLoading}
          className="flex-1 rounded-lg border border-[#D7DEEA] py-2.5 text-sm font-medium text-[#3D475C] transition hover:bg-[#F3F6FB]"
        >
          Cancel
        </button>
      </div>
    </form>
  );
}
