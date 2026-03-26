'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { toast } from 'sonner';
import { Plus, PackageOpen } from 'lucide-react';
import OfferingCard from '@/components/vendor/offerings/OfferingCard';
import OfferingForm from '@/components/vendor/offerings/OfferingForm';
import VendorPortalShell from '@/components/features/vendor/VendorPortalShell';
import { Offering, CreateOfferingData } from '@/types/vendor/offering';
import { offeringService } from '@/services/vendor/offeringService';
import { ROUTES } from '@/lib/routes';

export default function OfferingsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [offerings, setOfferings] = useState<Offering[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [editingOffering, setEditingOffering] = useState<Offering | null>(null);

  useEffect(() => {
    fetchOfferings();
  }, []);

  useEffect(() => {
    if (searchParams.get('new') === '1') {
      setEditingOffering(null);
      setShowForm(true);
      router.replace(ROUTES.VENDOR.OFFERINGS, { scroll: false });
    }
  }, [searchParams, router]);

  const fetchOfferings = async () => {
    setIsLoading(true);
    try {
      const data = await offeringService.getAll();
      setOfferings(data);
    } catch (error: any) {
      if (error.response?.status === 401) {
        toast.error('Session expired. Please login again.');
        router.push(ROUTES.VENDOR.LOGIN);
      } else {
        toast.error('Failed to load offerings');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreate = async (data: CreateOfferingData) => {
    setIsSaving(true);
    try {
      const newOffering = await offeringService.create(data);
      setOfferings(prev => [newOffering, ...prev]);
      setShowForm(false);
      toast.success('Offering created successfully!');
    } catch (error: any) {
      toast.error(error.response?.data?.message || 'Failed to create offering. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleUpdate = async (data: CreateOfferingData) => {
    if (!editingOffering) return;
    setIsSaving(true);
    try {
      const updated = await offeringService.update(editingOffering.id, data);
      setOfferings(prev => prev.map(o => o.id === updated.id ? updated : o));
      setEditingOffering(null);
      toast.success('Offering updated successfully!');
    } catch (error: any) {
      if (error.response?.status === 404) {
        toast.error('Offering not found or you are not authorized to edit it.');
      } else {
        toast.error(error.response?.data?.message || 'Failed to update offering. Please try again.');
      }
    } finally {
      setIsSaving(false);
    }
  };

  const handleEdit = (offering: Offering) => {
    setEditingOffering(offering);
    setShowForm(false);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleCancel = () => {
    setShowForm(false);
    setEditingOffering(null);
  };

  return (
    <VendorPortalShell>
      <div className="w-full">
        <div className="mb-8 flex items-center justify-between rounded-2xl border border-[#E2E5EC] bg-white px-4 py-5 shadow-[0_4px_16px_rgba(15,23,42,0.06)] sm:px-6">
          <div>
            <h1 className="text-2xl font-bold text-[#1F293F]">Manage Offerings</h1>
            <p className="mt-1 text-sm text-[#5B6478]">Create and manage your offerings for AI-based recommendations</p>
          </div>
          {!showForm && !editingOffering && (
            <button
              onClick={() => setShowForm(true)}
              className="inline-flex items-center gap-2 rounded-xl bg-[#1565c0] px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-[#0d47a1]"
            >
              <Plus size={18} />
              Add New Offering
            </button>
          )}
        </div>

        {/* Form Panel */}
        {(showForm || editingOffering) && (
          <div className="mb-8 rounded-2xl border border-[#E2E5EC] bg-white p-6 shadow-[0_4px_16px_rgba(15,23,42,0.06)]">
            <h2 className="mb-5 text-lg font-semibold text-[#1F293F]">
              {editingOffering ? `Edit: ${editingOffering.title}` : 'New Offering'}
            </h2>
            <OfferingForm
              initialData={editingOffering || undefined}
              onSubmit={editingOffering ? handleUpdate : handleCreate}
              isLoading={isSaving}
              onCancel={handleCancel}
            />
          </div>
        )}

        {/* Offerings List */}
        {isLoading ? (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="animate-pulse rounded-2xl border border-[#E2E5EC] bg-white p-5">
                <div className="mb-3 h-4 w-3/4 rounded bg-slate-200"></div>
                <div className="mb-2 h-3 w-full rounded bg-slate-200"></div>
                <div className="mb-4 h-3 w-2/3 rounded bg-slate-200"></div>
                <div className="flex gap-2">
                  <div className="h-6 w-20 rounded-full bg-slate-200"></div>
                  <div className="h-6 w-20 rounded-full bg-slate-200"></div>
                </div>
              </div>
            ))}
          </div>
        ) : offerings.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-[#D7DEEA] bg-[#F8FAFD] py-20 text-center">
            <PackageOpen className="mx-auto mb-4 h-14 w-14 text-[#9BA4B5]" />
            <h3 className="mb-2 text-lg font-semibold text-[#1F293F]">No offerings yet</h3>
            <p className="mb-6 text-sm text-[#5B6478]">Create your first offering to get started with AI-based recommendations</p>
            <button
              onClick={() => setShowForm(true)}
              className="inline-flex items-center gap-2 rounded-xl bg-[#1565c0] px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-[#0d47a1]"
            >
              <Plus size={18} />
              Add New Offering
            </button>
          </div>
        ) : (
          <>
            <p className="mb-4 text-sm text-[#5B6478]">{offerings.length} offering{offerings.length !== 1 ? 's' : ''} total</p>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              {offerings.map(offering => (
                <OfferingCard key={offering.id} offering={offering} onEdit={handleEdit} />
              ))}
            </div>
          </>
        )}
      </div>
    </VendorPortalShell>
  );
}
