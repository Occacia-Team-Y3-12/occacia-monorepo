// frontend/src/services/adminService.ts

import {api} from './api';
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

export const adminService = {
  // Vendors
  getVendors: async (params: ListParams = {}): Promise<VendorListResponse> => {
    const { data } = await api.get('/admin/vendors', { params });
    return data;
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
    const { data } = await api.get('/admin/organizations', { params });
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
      statusData
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
};