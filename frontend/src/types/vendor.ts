// frontend/src/types/vendor.ts

export enum VendorStatus {
  PENDING = 'pending',
  APPROVED = 'approved',
  REJECTED = 'rejected',
}

export enum OrganizationStatus {
  PENDING = 'pending',
  APPROVED = 'approved',
  REJECTED = 'rejected',
}

export enum VendorType {
  INDIVIDUAL = 'individual',
  ORGANIZATION = 'organization',
}

export interface Vendor {
  id: number;
  business_name: string;
  business_email: string;
  business_phone?: string;
  business_address?: string;
  business_type?: string;
  description?: string;
  status: VendorStatus;
  status_reason?: string;
  vendor_type: VendorType;
  organization_id?: number;
  logo_url?: string;
  reviewed_by?: number;
  reviewed_at?: string;
  created_at: string;
  updated_at?: string;
}

export interface Organization {
  id: number;
  name: string;
  legal_name: string;
  registration_number?: string;
  tax_id?: string;
  email: string;
  phone?: string;
  address?: string;
  website?: string;
  description?: string;
  status: OrganizationStatus;
  status_reason?: string;
  logo_url?: string;
  business_license_url?: string;
  tax_certificate_url?: string;
  reviewed_by?: number;
  reviewed_at?: string;
  created_at: string;
  updated_at?: string;
  vendors?: Vendor[];
}

export interface VendorListResponse {
  items: Vendor[];
  total: number;
  page: number;
  page_size: number;
}

export interface OrganizationListResponse {
  items: Organization[];
  total: number;
  page: number;
  page_size: number;
}

export interface StatusUpdateRequest {
  status: VendorStatus | OrganizationStatus;
  status_reason?: string;
}

export interface PendingStats {
  vendors_pending: number;
  organizations_pending: number;
  total_pending: number;
}