'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowLeft } from 'lucide-react';
import { toast } from 'sonner';

import OfferingForm from '@/components/vendor/offerings/OfferingForm';
import VendorPortalShell from '@/components/features/vendor/VendorPortalShell';
import { CreateOfferingData } from '@/types/vendor/offering';
import { offeringService } from '@/services/vendor/offeringService';
import { ROUTES } from '@/lib/routes';

export default function NewOfferingPage() {
  const router = useRouter();
  const [isSaving, setIsSaving] = useState(false);

  const handleCreate = async (data: CreateOfferingData) => {
    setIsSaving(true);
    try {
      await offeringService.create(data);
      toast.success('Offering created successfully!');
    } catch (error: any) {
      if (error.response?.status === 401) {
        toast.error('Session expired. Please login again.');
        router.push(ROUTES.VENDOR.LOGIN);
        throw error;
      }

      toast.error(error.response?.data?.message || 'Failed to create offering. Please try again.');
      throw error;
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <VendorPortalShell>
      <div className="w-full">
        <button
          onClick={() => router.push(ROUTES.VENDOR.OFFERINGS)}
          className="mb-6 inline-flex items-center gap-2 text-sm text-[#5B6478] transition hover:text-[#1F293F]"
        >
          <ArrowLeft size={16} />
          Back to Offerings
        </button>

        <div className="rounded-2xl border border-[#E2E5EC] bg-white p-6 shadow-[0_4px_16px_rgba(15,23,42,0.06)]">
          <h1 className="mb-1 text-xl font-bold text-[#1F293F]">New Offering</h1>
          <p className="mb-6 text-sm text-[#5B6478]">Enter offering details and create it.</p>

          <OfferingForm
            onSubmit={handleCreate}
            isLoading={isSaving}
            onCancel={() => router.push(ROUTES.VENDOR.OFFERINGS)}
            submitRedirectHref={ROUTES.VENDOR.OFFERINGS}
          />
        </div>
      </div>
    </VendorPortalShell>
  );
}
