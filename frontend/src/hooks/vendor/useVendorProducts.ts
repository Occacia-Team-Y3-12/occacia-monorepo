'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { toast } from 'sonner';

import { vendorProductService } from '@/services/vendor/vendorProductService';
import type {
  CreateVendorProductData,
  UpdateVendorProductData,
  VendorProduct,
  VendorProductCategory,
  VendorProductStatusFilter,
} from '@/types/vendor/product';

type ProductStats = {
  total: number;
  active: number;
  lowStock: number;
  outOfStock: number;
};

const isOutOfStock = (product: VendorProduct) => product.stockQuantity <= 0;
const isLowStock = (product: VendorProduct) => product.stockQuantity > 0 && product.stockQuantity <= product.reorderLevel;

export function useVendorProducts() {
  const [products, setProducts] = useState<VendorProduct[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<'all' | VendorProductCategory>('all');
  const [statusFilter, setStatusFilter] = useState<VendorProductStatusFilter>('all');

  const fetchProducts = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await vendorProductService.getAll();
      setProducts(data);
    } catch {
      toast.error('Failed to load products.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchProducts();
  }, [fetchProducts]);

  const filteredProducts = useMemo(() => {
    return products.filter((product) => {
      const normalizedSearch = searchTerm.trim().toLowerCase();
      const matchesSearch =
        normalizedSearch.length === 0 ||
        product.name.toLowerCase().includes(normalizedSearch) ||
        product.sku.toLowerCase().includes(normalizedSearch);

      const matchesCategory = categoryFilter === 'all' || product.category === categoryFilter;

      const matchesStatus =
        statusFilter === 'all' ||
        (statusFilter === 'active' && product.isActive) ||
        (statusFilter === 'inactive' && !product.isActive) ||
        (statusFilter === 'low_stock' && isLowStock(product)) ||
        (statusFilter === 'out_of_stock' && isOutOfStock(product));

      return matchesSearch && matchesCategory && matchesStatus;
    });
  }, [products, searchTerm, categoryFilter, statusFilter]);

  const stats = useMemo<ProductStats>(() => {
    return {
      total: products.length,
      active: products.filter((product) => product.isActive).length,
      lowStock: products.filter((product) => isLowStock(product)).length,
      outOfStock: products.filter((product) => isOutOfStock(product)).length,
    };
  }, [products]);

  const createProduct = useCallback(async (data: CreateVendorProductData) => {
    setIsSaving(true);
    try {
      const createdProduct = await vendorProductService.create(data);
      setProducts((previousProducts) => [createdProduct, ...previousProducts]);
      toast.success('Product created successfully.');
      return createdProduct;
    } finally {
      setIsSaving(false);
    }
  }, []);

  const updateProduct = useCallback(async (id: string, data: UpdateVendorProductData) => {
    setIsSaving(true);
    try {
      const updatedProduct = await vendorProductService.update(id, data);
      setProducts((previousProducts) =>
        previousProducts.map((product) => (product.id === id ? updatedProduct : product))
      );
      toast.success('Product updated successfully.');
      return updatedProduct;
    } finally {
      setIsSaving(false);
    }
  }, []);

  const toggleProductActive = useCallback(async (id: string) => {
    setIsSaving(true);
    try {
      const updatedProduct = await vendorProductService.toggleActive(id);
      setProducts((previousProducts) =>
        previousProducts.map((product) => (product.id === id ? updatedProduct : product))
      );
      toast.success(`Product ${updatedProduct.isActive ? 'activated' : 'deactivated'}.`);
      return updatedProduct;
    } finally {
      setIsSaving(false);
    }
  }, []);

  const clearFilters = useCallback(() => {
    setSearchTerm('');
    setCategoryFilter('all');
    setStatusFilter('all');
  }, []);

  return {
    products,
    filteredProducts,
    stats,
    isLoading,
    isSaving,
    searchTerm,
    setSearchTerm,
    categoryFilter,
    setCategoryFilter,
    statusFilter,
    setStatusFilter,
    createProduct,
    updateProduct,
    toggleProductActive,
    clearFilters,
    refreshProducts: fetchProducts,
  };
}
