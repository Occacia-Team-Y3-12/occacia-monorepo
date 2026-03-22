import { featureFlags } from '@/config/featureFlags';
import { mockAdminService } from '@/mocks/admin/adminService';
import { api } from './api';
import {
  Vendor,
  Organization,
  VendorListResponse,
  OrganizationListResponse,
  StatusUpdateRequest,
  PendingStats,
  VendorStatus,
  OrganizationStatus,
} from '@/types/vendor';

interface ListParams {
  page?: number;
  limit?: number;
  status?: VendorStatus | OrganizationStatus;
  search?: string;
}

function normalizeVendorStatus(value?: string): VendorStatus {
  const normalized = (value || '').toUpperCase();
  if (normalized === 'APPROVED') return VendorStatus.APPROVED;
  if (normalized === 'REJECTED') return VendorStatus.REJECTED;
  return VendorStatus.PENDING;
}

function mapVendor(raw: any): Vendor {
  return {
    id: raw.id,
    business_name: raw.business_name || raw.display_name || 'Unnamed vendor',
    business_email: raw.business_email || raw.email || '',
    business_phone: raw.business_phone || raw.phone || raw.contact_phone || '',
    business_address: raw.business_address || raw.location_base || '',
    business_type: raw.business_type || '',
    description: raw.description || '',
    status: normalizeVendorStatus(raw.approval_status || raw.status),
    status_reason: raw.status_reason || '',
    vendor_type: raw.vendor_type || 'individual',
    organization_id: raw.organization_id,
    logo_url: raw.logo_url,
    reviewed_by: raw.reviewed_by,
    reviewed_at: raw.reviewed_at || raw.approved_at,
    created_at: raw.created_at || raw.approved_at || new Date().toISOString(),
    updated_at: raw.updated_at,
  };
}

const apiAdminService = {
  // Vendors
  getVendors: async (params: ListParams = {}): Promise<VendorListResponse> => {
    const { status, page = 1, limit = 20 } = params;
    const queryParams = {
      approval_status: status?.toUpperCase(),
    };
    const { data } = await api.get('/admin/vendors', { params: queryParams });

    const items = Array.isArray(data)
      ? data.map(mapVendor)
      : Array.isArray(data?.items)
      ? data.items.map(mapVendor)
      : [];

    return {
      items,
      total: typeof data?.total === 'number' ? data.total : items.length,
      page,
      page_size: limit,
    };
  },

  getVendorById: async (id: number): Promise<Vendor> => {
    const { data } = await api.get(`/admin/vendors/${id}`);
    return data;
  },

  updateVendorStatus: async (
    id: number,
    statusData: StatusUpdateRequest
  ): Promise<Vendor> => {
    const { data } = await api.put(`/admin/vendors/${id}/status`, statusData);
    return data;
  },

  // Organizations
  getOrganizations: async (
    params: ListParams = {}
  ): Promise<OrganizationListResponse> => {
    const { page = 1, limit = 20, status, search } = params;
    const dataParams = {
      skip: Math.max(0, (page - 1) * limit),
      limit,
      status,
      search,
    };
    const { data } = await api.get('/admin/organizations', { params: dataParams });
    return data;
  },

  getOrganizationById: async (id: number): Promise<Organization> => {
    const { data } = await api.get(`/admin/organizations/${id}`);
    return data;
  },

  updateOrganizationStatus: async (
    id: number,
    statusData: StatusUpdateRequest
  ): Promise<Organization> => {
    const { data } = await api.put(
      `/admin/organizations/${id}/status`,
      {
        status: statusData.status,
        reason: statusData.reason ?? statusData.status_reason,
      }
    );
    return data;
  },

  deleteOrganization: async (id: number): Promise<void> => {
    await api.delete(`/admin/organizations/${id}`);
  },

  // Stats
  getPendingStats: async (): Promise<PendingStats> => {
    const { data } = await api.get('/admin/vendors/stats/pending');
    return data;
  },

  approveVendor: async (id: number): Promise<Vendor> => {
    const { data } = await api.post(`/admin/vendors/${id}/approve`);
    return mapVendor(data);
  },

  rejectVendor: async (id: number, reason?: string): Promise<Vendor> => {
    const { data } = await api.post(`/admin/vendors/${id}/reject`, {
      reason: reason?.trim() || undefined,
    });
    return mapVendor(data);
  },
};

export const adminService = featureFlags.useAdminOperationsMock
  ? mockAdminService
  : apiAdminService;
