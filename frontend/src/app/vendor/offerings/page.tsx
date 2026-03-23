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
      <div className="mx-auto max-w-5xl">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-2xl font-bold text-slate-900">Manage Offerings</h1>
              <p className="text-slate-500 text-sm mt-1">Create and manage your offerings for AI-based recommendations</p>
            </div>
            {!showForm && !editingOffering && (
              <button onClick={() => setShowForm(true)}
                className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2.5 rounded-xl text-sm font-semibold hover:bg-blue-700 transition shadow-sm">
                <Plus size={18} />
                Add New Offering
              </button>
            )}
          </div>

          {/* Form Panel */}
          {(showForm || editingOffering) && (
            <div className="bg-white rounded-2xl border border-slate-200 p-6 mb-8 shadow-[0_4px_16px_rgba(15,23,42,0.06)]">
              <h2 className="text-lg font-semibold text-slate-900 mb-5">
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
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="bg-white border border-slate-200 rounded-2xl p-5 animate-pulse">
                  <div className="h-4 bg-slate-200 rounded w-3/4 mb-3"></div>
                  <div className="h-3 bg-slate-200 rounded w-full mb-2"></div>
                  <div className="h-3 bg-slate-200 rounded w-2/3 mb-4"></div>
                  <div className="flex gap-2">
                    <div className="h-6 bg-slate-200 rounded-full w-20"></div>
                    <div className="h-6 bg-slate-200 rounded-full w-20"></div>
                  </div>
                </div>
              ))}
            </div>
          ) : offerings.length === 0 ? (
            <div className="text-center py-20 bg-white rounded-2xl border border-slate-200 shadow-[0_4px_16px_rgba(15,23,42,0.06)]">
              <PackageOpen className="w-14 h-14 text-slate-300 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-slate-700 mb-2">No offerings yet</h3>
              <p className="text-slate-500 text-sm mb-6">Create your first offering to get started with AI-based recommendations</p>
              <button onClick={() => setShowForm(true)}
                className="inline-flex items-center gap-2 bg-blue-600 text-white px-5 py-2.5 rounded-xl text-sm font-semibold hover:bg-blue-700 transition">
                <Plus size={18} />
                Add New Offering
              </button>
            </div>
          ) : (
            <>
              <p className="text-sm text-slate-500 mb-4">{offerings.length} offering{offerings.length !== 1 ? 's' : ''} total</p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
