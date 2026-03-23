'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { toast } from 'sonner';
import { ArrowLeft } from 'lucide-react';
import OfferingForm from '@/components/vendor/offerings/OfferingForm';
import VendorPortalShell from '@/components/features/vendor/VendorPortalShell';
import { Offering, CreateOfferingData } from '@/types/vendor/offering';
import { offeringService } from '@/services/vendor/offeringService';
import { ROUTES } from '@/lib/routes';

export default function OfferingDetailPage() {
  const router = useRouter();
  const params = useParams();
  const id = params.id as string;

  const [offering, setOffering] = useState<Offering | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    const fetchOffering = async () => {
      try {
        const data = await offeringService.getById(id);
        setOffering(data);
      } catch (error: any) {
        if (error.response?.status === 404 || error.response?.status === 403) {
          toast.error('Offering not found or you are not authorized to view it.');
        } else if (error.response?.status === 401) {
          toast.error('Session expired. Please login again.');
          router.push(ROUTES.VENDOR.LOGIN);
          return;
        } else {
          toast.error('Failed to load offering.');
        }
        router.push('/vendor/offerings');
      } finally {
        setIsLoading(false);
      }
    };
    fetchOffering();
  }, [id, router]);

  const handleUpdate = async (data: CreateOfferingData) => {
    setIsSaving(true);
    try {
      const updated = await offeringService.update(id, data);
      setOffering(updated);
      toast.success('Offering updated successfully!');
      router.push('/vendor/offerings');
    } catch (error: any) {
      if (error.response?.status === 404 || error.response?.status === 403) {
        toast.error('Offering not found or you are not authorized to edit it.');
      } else {
        toast.error(error.response?.data?.message || 'Failed to update offering. Please try again.');
      }
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <VendorPortalShell>
      <div className="mx-auto max-w-2xl">
          <button onClick={() => router.push('/vendor/offerings')}
            className="inline-flex items-center gap-2 text-sm text-slate-600 hover:text-slate-900 mb-6 transition">
            <ArrowLeft size={16} />
            Back to Offerings
          </button>

          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-[0_4px_16px_rgba(15,23,42,0.06)]">
            <h1 className="text-xl font-bold text-slate-900 mb-1">Edit Offering</h1>
            {offering && <p className="text-sm text-slate-500 mb-6">{offering.title}</p>}

            {isLoading ? (
              <div className="space-y-4 animate-pulse">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="h-10 bg-slate-200 rounded-lg"></div>
                ))}
              </div>
            ) : offering ? (
              <OfferingForm
                initialData={offering}
                onSubmit={handleUpdate}
                isLoading={isSaving}
                onCancel={() => router.push('/vendor/offerings')}
              />
            ) : null}
          </div>
      </div>
    </VendorPortalShell>
  );
}
