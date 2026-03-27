import type {
  CreateVendorProductData,
  UpdateVendorProductData,
  VendorProduct,
} from '@/types/vendor/product';

const MOCK_PRODUCTS_KEY = 'occacia_vendor_products_mock';

const seedProducts: VendorProduct[] = [
  {
    id: 'prod-201',
    vendorId: 'mock-vendor-1',
    name: 'Classic Butter Cake',
    description: 'Soft vanilla butter cake suitable for birthdays and intimate celebrations.',
    sku: 'CK-CLASSIC-001',
    category: 'CAKES',
    price: 4500,
    stockQuantity: 14,
    reorderLevel: 6,
    isActive: true,
    createdAt: new Date(Date.now() - 12 * 86400000).toISOString(),
    updatedAt: new Date(Date.now() - 2 * 86400000).toISOString(),
  },
  {
    id: 'prod-202',
    vendorId: 'mock-vendor-1',
    name: 'Rose Celebration Bouquet',
    description: 'Fresh mixed-rose bouquet with gift wrapping and message card.',
    sku: 'FL-ROSE-007',
    category: 'FLOWERS',
    price: 3800,
    stockQuantity: 4,
    reorderLevel: 5,
    isActive: true,
    createdAt: new Date(Date.now() - 10 * 86400000).toISOString(),
    updatedAt: new Date(Date.now() - 1 * 86400000).toISOString(),
  },
  {
    id: 'prod-203',
    vendorId: 'mock-vendor-1',
    name: 'Premium Gift Hamper',
    description: 'Curated snack and beverage hamper for festive gifting.',
    sku: 'GF-HAMPER-013',
    category: 'GIFTS',
    price: 6200,
    stockQuantity: 0,
    reorderLevel: 3,
    isActive: true,
    createdAt: new Date(Date.now() - 16 * 86400000).toISOString(),
    updatedAt: new Date(Date.now() - 4 * 86400000).toISOString(),
  },
  {
    id: 'prod-204',
    vendorId: 'mock-vendor-1',
    name: 'Minimal Table Decor Set',
    description: 'Neutral themed table decor kit with centerpieces and runners.',
    sku: 'DC-MIN-004',
    category: 'DECOR',
    price: 7600,
    stockQuantity: 9,
    reorderLevel: 2,
    isActive: false,
    createdAt: new Date(Date.now() - 20 * 86400000).toISOString(),
    updatedAt: new Date(Date.now() - 9 * 86400000).toISOString(),
  },
];

function loadProducts(): VendorProduct[] {
  if (typeof window === 'undefined') {
    return seedProducts;
  }

  const stored = localStorage.getItem(MOCK_PRODUCTS_KEY);
  if (!stored) {
    localStorage.setItem(MOCK_PRODUCTS_KEY, JSON.stringify(seedProducts));
    return seedProducts;
  }

  try {
    return JSON.parse(stored) as VendorProduct[];
  } catch {
    localStorage.setItem(MOCK_PRODUCTS_KEY, JSON.stringify(seedProducts));
    return seedProducts;
  }
}

function persistProducts(products: VendorProduct[]) {
  if (typeof window !== 'undefined') {
    localStorage.setItem(MOCK_PRODUCTS_KEY, JSON.stringify(products));
  }
}

export const mockVendorProductService = {
  getAll: async (): Promise<VendorProduct[]> => {
    await new Promise((resolve) => setTimeout(resolve, 150));
    return loadProducts().sort((left, right) => right.updatedAt.localeCompare(left.updatedAt));
  },

  create: async (data: CreateVendorProductData): Promise<VendorProduct> => {
    await new Promise((resolve) => setTimeout(resolve, 180));

    const products = loadProducts();
    const createdProduct: VendorProduct = {
      id: `prod-${Date.now()}`,
      vendorId: 'mock-vendor-1',
      ...data,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    persistProducts([createdProduct, ...products]);
    return createdProduct;
  },

  update: async (id: string, data: UpdateVendorProductData): Promise<VendorProduct> => {
    await new Promise((resolve) => setTimeout(resolve, 180));

    const products = loadProducts();
    const index = products.findIndex((product) => product.id === id);
    if (index < 0) {
      throw new Error('Product not found.');
    }

    products[index] = {
      ...products[index],
      ...data,
      updatedAt: new Date().toISOString(),
    };

    persistProducts(products);
    return products[index];
  },

  toggleActive: async (id: string): Promise<VendorProduct> => {
    await new Promise((resolve) => setTimeout(resolve, 150));

    const products = loadProducts();
    const index = products.findIndex((product) => product.id === id);
    if (index < 0) {
      throw new Error('Product not found.');
    }

    products[index] = {
      ...products[index],
      isActive: !products[index].isActive,
      updatedAt: new Date().toISOString(),
    };

    persistProducts(products);
    return products[index];
  },
};
