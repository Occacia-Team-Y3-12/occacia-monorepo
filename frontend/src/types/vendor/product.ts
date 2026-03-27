export type VendorProductCategory = 'CAKES' | 'FLOWERS' | 'GIFTS' | 'DECOR' | 'CATERING' | 'OTHER';

export interface VendorProduct {
  id: string;
  vendorId: string;
  name: string;
  description: string;
  sku: string;
  category: VendorProductCategory;
  price: number;
  stockQuantity: number;
  reorderLevel: number;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface CreateVendorProductData {
  name: string;
  description: string;
  sku: string;
  category: VendorProductCategory;
  price: number;
  stockQuantity: number;
  reorderLevel: number;
  isActive: boolean;
}

export type UpdateVendorProductData = Partial<CreateVendorProductData>;

export type VendorProductStatusFilter = 'all' | 'active' | 'inactive' | 'low_stock' | 'out_of_stock';
