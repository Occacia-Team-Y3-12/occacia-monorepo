// frontend/src/services/adminService.ts

import { featureFlags } from '@/config/featureFlags';
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
  VendorType,
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

const MOCK_VENDORS_KEY = 'occacia_admin_vendors_mock';
const MOCK_ORGANIZATIONS_KEY = 'occacia_admin_organizations_mock';

const seedVendors: Vendor[] = [
  {
    id: 101,
    business_name: 'Studio North Events',
    business_email: 'north@occacia.dev',
    business_phone: '+94 77 111 2200',
    business_address: '12 Flower Rd, Colombo',
    business_type: 'Event Styling',
    description: 'Boutique event styling and decor studio.',
    status: VendorStatus.PENDING,
    vendor_type: VendorType.ORGANIZATION,
    organization_id: 201,
    created_at: new Date(Date.now() - 7 * 86400000).toISOString(),
  },
  {
    id: 102,
    business_name: 'Kandy Lens House',
    business_email: 'lens@occacia.dev',
    business_phone: '+94 71 555 8800',
    business_address: '88 Lake View, Kandy',
    business_type: 'Photography',
    description: 'Photography for intimate celebrations.',
    status: VendorStatus.APPROVED,
    vendor_type: VendorType.INDIVIDUAL,
    created_at: new Date(Date.now() - 14 * 86400000).toISOString(),
  },
  {
    id: 103,
    business_name: 'Golden Hour Catering',
    business_email: 'hello@goldenhour.dev',
    business_phone: '+94 76 222 1100',
    business_address: '5 Temple Lane, Galle',
    business_type: 'Catering',
    description: 'Specialised in curated tasting menus.',
    status: VendorStatus.REJECTED,
    status_reason: 'Missing business verification document.',
    vendor_type: VendorType.ORGANIZATION,
    organization_id: 202,
    created_at: new Date(Date.now() - 20 * 86400000).toISOString(),
  },
];

const seedOrganizations: Organization[] = [
  {
    id: 201,
    name: 'North Collective',
    legal_name: 'North Collective (Pvt) Ltd',
    registration_number: 'PV-22019',
    email: 'ops@northcollective.dev',
    phone: '+94 11 222 3344',
    address: '12 Flower Rd, Colombo',
    website: 'https://northcollective.dev',
    description: 'Creative event production company.',
    status: OrganizationStatus.PENDING,
    created_at: new Date(Date.now() - 8 * 86400000).toISOString(),
  },
  {
    id: 202,
    name: 'Golden Hour Group',
    legal_name: 'Golden Hour Group (Pvt) Ltd',
    registration_number: 'PV-12011',
    email: 'team@goldenhour.dev',
    phone: '+94 91 330 7788',
    address: '5 Temple Lane, Galle',
    website: 'https://goldenhour.dev',
    description: 'Food and hospitality collective.',
    status: OrganizationStatus.REJECTED,
    status_reason: 'Tax certificate was expired.',
    created_at: new Date(Date.now() - 18 * 86400000).toISOString(),
  },
];

function loadCollection<T>(storageKey: string, fallback: T[]): T[] {
  if (typeof window === 'undefined') {
    return fallback;
  }

  const stored = localStorage.getItem(storageKey);
  if (!stored) {
    localStorage.setItem(storageKey, JSON.stringify(fallback));
    return fallback;
  }

  try {
    return JSON.parse(stored) as T[];
  } catch {
    localStorage.setItem(storageKey, JSON.stringify(fallback));
    return fallback;
  }
}

function persistCollection<T>(storageKey: string, items: T[]) {
  if (typeof window !== 'undefined') {
    localStorage.setItem(storageKey, JSON.stringify(items));
  }
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

const mockAdminService = {
  getVendors: async (params: ListParams = {}): Promise<VendorListResponse> => {
    const { page = 1, limit = 20, status, search } = params;
    let items = loadCollection(MOCK_VENDORS_KEY, seedVendors);

    if (status) {
      items = items.filter((vendor) => vendor.status === status);
    }

    if (search?.trim()) {
      const term = search.trim().toLowerCase();
      items = items.filter((vendor) =>
        [vendor.business_name, vendor.business_email, vendor.business_type]
          .filter(Boolean)
          .some((value) => value!.toLowerCase().includes(term))
      );
    }

    return {
      items: items.slice((page - 1) * limit, page * limit),
      total: items.length,
      page,
      page_size: limit,
    };
  },

  getVendorById: async (id: number): Promise<Vendor> => {
    const vendor = loadCollection(MOCK_VENDORS_KEY, seedVendors).find(
      (item) => item.id === id
    );

    if (!vendor) {
      throw new Error(`Vendor not found: ${id}`);
    }

    return vendor;
  },

  updateVendorStatus: async (
    id: number,
    statusData: StatusUpdateRequest
  ): Promise<Vendor> => {
    const vendors = loadCollection(MOCK_VENDORS_KEY, seedVendors);
    const index = vendors.findIndex((item) => item.id === id);

    if (index < 0) {
      throw new Error(`Vendor not found: ${id}`);
    }

    vendors[index] = {
      ...vendors[index],
      status: statusData.status as VendorStatus,
      status_reason: statusData.reason ?? statusData.status_reason,
      reviewed_at: new Date().toISOString(),
    };

    persistCollection(MOCK_VENDORS_KEY, vendors);
    return vendors[index];
  },

  getOrganizations: async (
    params: ListParams = {}
  ): Promise<OrganizationListResponse> => {
    const { page = 1, limit = 20, status, search } = params;
    let items = loadCollection(MOCK_ORGANIZATIONS_KEY, seedOrganizations);

    if (status) {
      items = items.filter((organization) => organization.status === status);
    }

    if (search?.trim()) {
      const term = search.trim().toLowerCase();
      items = items.filter((organization) =>
        [organization.name, organization.email, organization.legal_name]
          .filter(Boolean)
          .some((value) => value!.toLowerCase().includes(term))
      );
    }

    return {
      items: items.slice((page - 1) * limit, page * limit),
      total: items.length,
      page,
      page_size: limit,
    };
  },

  getOrganizationById: async (id: number): Promise<Organization> => {
    const organization = loadCollection(
      MOCK_ORGANIZATIONS_KEY,
      seedOrganizations
    ).find((item) => item.id === id);

    if (!organization) {
      throw new Error(`Organization not found: ${id}`);
    }

    return organization;
  },

  updateOrganizationStatus: async (
    id: number,
    statusData: StatusUpdateRequest
  ): Promise<Organization> => {
    const organizations = loadCollection(
      MOCK_ORGANIZATIONS_KEY,
      seedOrganizations
    );
    const index = organizations.findIndex((item) => item.id === id);

    if (index < 0) {
      throw new Error(`Organization not found: ${id}`);
    }

    organizations[index] = {
      ...organizations[index],
      status: statusData.status as OrganizationStatus,
      status_reason: statusData.reason ?? statusData.status_reason,
      reviewed_at: new Date().toISOString(),
    };

    persistCollection(MOCK_ORGANIZATIONS_KEY, organizations);
    return organizations[index];
  },

  deleteOrganization: async (id: number): Promise<void> => {
    const organizations = loadCollection(
      MOCK_ORGANIZATIONS_KEY,
      seedOrganizations
    ).filter((item) => item.id !== id);

    persistCollection(MOCK_ORGANIZATIONS_KEY, organizations);
  },

  getPendingStats: async (): Promise<PendingStats> => {
    const vendors = loadCollection(MOCK_VENDORS_KEY, seedVendors);
    const organizations = loadCollection(
      MOCK_ORGANIZATIONS_KEY,
      seedOrganizations
    );
    const vendors_pending = vendors.filter(
      (item) => item.status === VendorStatus.PENDING
    ).length;
    const organizations_pending = organizations.filter(
      (item) => item.status === OrganizationStatus.PENDING
    ).length;

    return {
      vendors_pending,
      organizations_pending,
      total_pending: vendors_pending + organizations_pending,
    };
  },

  approveVendor: async (id: number): Promise<Vendor> =>
    mockAdminService.updateVendorStatus(id, {
      status: VendorStatus.APPROVED,
    }),

  rejectVendor: async (id: number, reason?: string): Promise<Vendor> =>
    mockAdminService.updateVendorStatus(id, {
      status: VendorStatus.REJECTED,
      reason,
    }),
};

export const adminService = featureFlags.useAdminOperationsMock
  ? mockAdminService
  : apiAdminService;
