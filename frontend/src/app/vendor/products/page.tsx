'use client';

import { FormEvent, useEffect, useMemo, useState } from 'react';
import { Box, PackageOpen, Pencil, Plus, Power, RefreshCcw, Search, TriangleAlert } from 'lucide-react';
import { toast } from 'sonner';

import VendorPortalShell from '@/components/features/vendor/VendorPortalShell';
import Modal from '@/components/ui/Modal';
import { useVendorProducts } from '@/hooks/vendor/useVendorProducts';
import { formatCurrency } from '@/lib/currency';
import type {
  CreateVendorProductData,
  VendorProduct,
  VendorProductCategory,
  VendorProductStatusFilter,
} from '@/types/vendor/product';

type ProductFormState = {
  name: string;
  description: string;
  sku: string;
  category: VendorProductCategory;
  price: string;
  stockQuantity: string;
  reorderLevel: string;
  isActive: boolean;
};

const categoryOptions: Array<{ value: VendorProductCategory; label: string }> = [
  { value: 'CAKES', label: 'Cakes' },
  { value: 'FLOWERS', label: 'Flowers' },
  { value: 'GIFTS', label: 'Gifts' },
  { value: 'DECOR', label: 'Decor' },
  { value: 'CATERING', label: 'Catering' },
  { value: 'OTHER', label: 'Other' },
];

const statusOptions: Array<{ value: VendorProductStatusFilter; label: string }> = [
  { value: 'all', label: 'All Statuses' },
  { value: 'active', label: 'Active' },
  { value: 'inactive', label: 'Inactive' },
  { value: 'low_stock', label: 'Low Stock' },
  { value: 'out_of_stock', label: 'Out of Stock' },
];

const defaultFormState: ProductFormState = {
  name: '',
  description: '',
  sku: '',
  category: 'CAKES',
  price: '',
  stockQuantity: '',
  reorderLevel: '5',
  isActive: true,
};

const getProductStatus = (product: VendorProduct): { label: string; className: string } => {
  if (!product.isActive) {
    return { label: 'Inactive', className: 'bg-slate-100 text-slate-600' };
  }
  if (product.stockQuantity <= 0) {
    return { label: 'Out of Stock', className: 'bg-rose-100 text-rose-700' };
  }
  if (product.stockQuantity <= product.reorderLevel) {
    return { label: 'Low Stock', className: 'bg-amber-100 text-amber-700' };
  }
  return { label: 'Active', className: 'bg-emerald-100 text-emerald-700' };
};

function toFormState(product: VendorProduct): ProductFormState {
  return {
    name: product.name,
    description: product.description,
    sku: product.sku,
    category: product.category,
    price: String(product.price),
    stockQuantity: String(product.stockQuantity),
    reorderLevel: String(product.reorderLevel),
    isActive: product.isActive,
  };
}

function mapToPayload(formState: ProductFormState): CreateVendorProductData | null {
  const name = formState.name.trim();
  const description = formState.description.trim();
  const sku = formState.sku.trim().toUpperCase();
  const price = Number(formState.price);
  const stockQuantity = Number(formState.stockQuantity);
  const reorderLevel = Number(formState.reorderLevel);

  if (!name || !description || !sku) {
    return null;
  }
  if (Number.isNaN(price) || Number.isNaN(stockQuantity) || Number.isNaN(reorderLevel)) {
    return null;
  }
  if (price < 0 || stockQuantity < 0 || reorderLevel < 0) {
    return null;
  }

  return {
    name,
    description,
    sku,
    category: formState.category,
    price,
    stockQuantity,
    reorderLevel,
    isActive: formState.isActive,
  };
}

export default function VendorProductsPage() {
  const {
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
    refreshProducts,
  } = useVendorProducts();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [activeProduct, setActiveProduct] = useState<VendorProduct | null>(null);
  const [formState, setFormState] = useState<ProductFormState>(defaultFormState);
  const [formError, setFormError] = useState('');

  const isEditing = Boolean(activeProduct);
  const productCountLabel = `${filteredProducts.length} product${filteredProducts.length !== 1 ? 's' : ''}`;

  const hasAnyFilter = useMemo(() => {
    return searchTerm.trim().length > 0 || categoryFilter !== 'all' || statusFilter !== 'all';
  }, [searchTerm, categoryFilter, statusFilter]);

  useEffect(() => {
    if (!isModalOpen) {
      setFormError('');
    }
  }, [isModalOpen]);

  const openCreateModal = () => {
    setActiveProduct(null);
    setFormState(defaultFormState);
    setFormError('');
    setIsModalOpen(true);
  };

  const openEditModal = (product: VendorProduct) => {
    setActiveProduct(product);
    setFormState(toFormState(product));
    setFormError('');
    setIsModalOpen(true);
  };

  const handleSubmitProduct = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const payload = mapToPayload(formState);

    if (!payload) {
      setFormError('Please fill all required fields and provide valid non-negative numeric values.');
      return;
    }

    try {
      if (activeProduct) {
        await updateProduct(activeProduct.id, payload);
      } else {
        await createProduct(payload);
      }
      setIsModalOpen(false);
      setActiveProduct(null);
      setFormState(defaultFormState);
      setFormError('');
    } catch {
      setFormError('Unable to save product right now. Please try again.');
    }
  };

  const handleToggleProduct = async (product: VendorProduct) => {
    try {
      await toggleProductActive(product.id);
    } catch {
      toast.error('Failed to update product status.');
    }
  };

  const statCards = [
    {
      title: 'Total Products',
      value: stats.total,
      subtitle: 'Items in your catalog',
      toneClass: 'bg-blue-100 text-blue-700',
      icon: <Box className="h-5 w-5" />,
    },
    {
      title: 'Active Products',
      value: stats.active,
      subtitle: 'Visible to customers',
      toneClass: 'bg-emerald-100 text-emerald-700',
      icon: <PackageOpen className="h-5 w-5" />,
    },
    {
      title: 'Low Stock',
      value: stats.lowStock,
      subtitle: 'Needs replenishment soon',
      toneClass: 'bg-amber-100 text-amber-700',
      icon: <TriangleAlert className="h-5 w-5" />,
    },
    {
      title: 'Out Of Stock',
      value: stats.outOfStock,
      subtitle: 'Currently unavailable',
      toneClass: 'bg-rose-100 text-rose-700',
      icon: <TriangleAlert className="h-5 w-5" />,
    },
  ];

  return (
    <VendorPortalShell>
      <div className="w-full space-y-5">
        <section className="flex flex-col gap-4 rounded-2xl border border-[#E2E5EC] bg-white px-4 py-5 shadow-[0_4px_16px_rgba(15,23,42,0.06)] sm:flex-row sm:items-center sm:justify-between sm:px-6">
          <div>
            <h1 className="text-3xl font-bold text-[#1F293F]">Products</h1>
            <p className="mt-1 text-sm text-[#5B6478]">Manage your product catalog, stock levels, and visibility.</p>
          </div>

          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => void refreshProducts()}
              className="inline-flex items-center gap-2 rounded-xl border border-[#D7DEEA] px-3 py-2 text-sm font-semibold text-[#1F293F] transition hover:bg-slate-50"
            >
              <RefreshCcw className="h-4 w-4" />
              Refresh
            </button>
            <button
              type="button"
              onClick={openCreateModal}
              className="inline-flex items-center gap-2 rounded-xl bg-[#1565c0] px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-[#0d47a1]"
            >
              <Plus className="h-4 w-4" />
              Add Product
            </button>
          </div>
        </section>

        <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {statCards.map((card) => (
            <article key={card.title} className="rounded-2xl border border-slate-200 bg-white p-4 shadow-[0_4px_16px_rgba(15,23,42,0.06)]">
              <div className="mb-4 flex items-center justify-between">
                <span className={`inline-flex h-11 w-11 items-center justify-center rounded-xl ${card.toneClass}`}>{card.icon}</span>
              </div>
              <p className="text-[28px] font-semibold leading-none tracking-tight text-slate-900">{card.value}</p>
              <p className="mt-2 text-sm font-semibold text-slate-700">{card.title}</p>
              <p className="text-xs text-slate-500">{card.subtitle}</p>
            </article>
          ))}
        </section>

        <section className="rounded-2xl border border-[#E2E5EC] bg-white p-4 shadow-[0_4px_16px_rgba(15,23,42,0.06)] sm:p-5">
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div className="relative w-full md:max-w-[360px]">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <input
                type="search"
                value={searchTerm}
                onChange={(event) => setSearchTerm(event.target.value)}
                placeholder="Search by name or SKU"
                className="h-11 w-full rounded-xl border border-[#DCE2EE] bg-white pl-9 pr-3 text-sm text-[#1F293F] outline-none transition focus:border-[#1565c0]"
              />
            </div>

            <div className="grid w-full grid-cols-1 gap-2 sm:grid-cols-2 md:w-auto md:min-w-[420px]">
              <select
                value={categoryFilter}
                onChange={(event) => setCategoryFilter(event.target.value as 'all' | VendorProductCategory)}
                className="h-11 rounded-xl border border-[#DCE2EE] bg-white px-3 text-sm text-[#1F293F] outline-none transition focus:border-[#1565c0]"
              >
                <option value="all">All Categories</option>
                {categoryOptions.map((category) => (
                  <option key={category.value} value={category.value}>
                    {category.label}
                  </option>
                ))}
              </select>

              <select
                value={statusFilter}
                onChange={(event) => setStatusFilter(event.target.value as VendorProductStatusFilter)}
                className="h-11 rounded-xl border border-[#DCE2EE] bg-white px-3 text-sm text-[#1F293F] outline-none transition focus:border-[#1565c0]"
              >
                {statusOptions.map((status) => (
                  <option key={status.value} value={status.value}>
                    {status.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="mt-4 flex flex-wrap items-center justify-between gap-2 border-t border-[#EEF1F6] pt-3 text-sm">
            <p className="text-[#5B6478]">{isLoading ? 'Loading products...' : productCountLabel}</p>
            {hasAnyFilter ? (
              <button
                type="button"
                onClick={clearFilters}
                className="font-semibold text-[#1565c0] transition hover:text-[#0d47a1]"
              >
                Clear Filters
              </button>
            ) : null}
          </div>

          <div className="mt-4 overflow-x-auto">
            {isLoading ? (
              <div className="space-y-3">
                {[...Array(4)].map((_, index) => (
                  <div key={index} className="animate-pulse rounded-xl border border-[#E9EDF5] bg-[#F9FAFC] p-4">
                    <div className="h-4 w-1/3 rounded bg-slate-200" />
                    <div className="mt-3 h-3 w-3/4 rounded bg-slate-200" />
                    <div className="mt-2 h-3 w-2/3 rounded bg-slate-200" />
                  </div>
                ))}
              </div>
            ) : filteredProducts.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-[#D7DEEA] bg-[#F8FAFD] py-16 text-center">
                <PackageOpen className="mx-auto mb-4 h-14 w-14 text-[#9BA4B5]" />
                <h3 className="mb-2 text-lg font-semibold text-[#1F293F]">
                  {hasAnyFilter ? 'No matching products found' : 'No products yet'}
                </h3>
                <p className="mb-6 text-sm text-[#5B6478]">
                  {hasAnyFilter
                    ? 'Try changing filters or search keywords.'
                    : 'Create your first product to start managing your catalog.'}
                </p>
                <button
                  type="button"
                  onClick={hasAnyFilter ? clearFilters : openCreateModal}
                  className="inline-flex items-center gap-2 rounded-xl bg-[#1565c0] px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-[#0d47a1]"
                >
                  {hasAnyFilter ? 'Reset Filters' : 'Add Product'}
                </button>
              </div>
            ) : (
              <table className="w-full min-w-[860px] border-separate border-spacing-y-2">
                <thead>
                  <tr className="text-left text-[12px] font-semibold uppercase tracking-wide text-slate-400">
                    <th className="px-2 py-1">Product</th>
                    <th className="px-2 py-1">SKU</th>
                    <th className="px-2 py-1">Category</th>
                    <th className="px-2 py-1">Price</th>
                    <th className="px-2 py-1">Stock</th>
                    <th className="px-2 py-1">Status</th>
                    <th className="px-2 py-1">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredProducts.map((product) => {
                    const status = getProductStatus(product);
                    const isStockAlert = product.stockQuantity <= product.reorderLevel;

                    return (
                      <tr key={product.id} className="rounded-xl bg-slate-50">
                        <td className="rounded-l-xl px-2 py-3">
                          <div className="text-sm font-semibold text-slate-800">{product.name}</div>
                          <div className="text-xs text-slate-500">{product.description}</div>
                        </td>
                        <td className="px-2 py-3 text-sm font-medium text-slate-700">{product.sku}</td>
                        <td className="px-2 py-3 text-sm text-slate-700">
                          {categoryOptions.find((category) => category.value === product.category)?.label ?? product.category}
                        </td>
                        <td className="px-2 py-3 text-sm font-semibold text-slate-800">{formatCurrency(product.price)}</td>
                        <td className="px-2 py-3">
                          <span
                            className={`rounded-full px-3 py-1 text-xs font-semibold ${
                              isStockAlert ? 'bg-amber-100 text-amber-700' : 'bg-blue-100 text-blue-700'
                            }`}
                          >
                            {product.stockQuantity} in stock
                          </span>
                        </td>
                        <td className="px-2 py-3">
                          <span className={`rounded-full px-3 py-1 text-xs font-semibold ${status.className}`}>{status.label}</span>
                        </td>
                        <td className="rounded-r-xl px-2 py-3">
                          <div className="flex items-center gap-2">
                            <button
                              type="button"
                              onClick={() => openEditModal(product)}
                              className="inline-flex items-center gap-1.5 rounded-lg border border-[#D7DEEA] bg-white px-3 py-1.5 text-xs font-semibold text-[#1F293F] transition hover:bg-slate-100"
                            >
                              <Pencil className="h-3.5 w-3.5" />
                              Edit
                            </button>
                            <button
                              type="button"
                              onClick={() => void handleToggleProduct(product)}
                              disabled={isSaving}
                              className="inline-flex items-center gap-1.5 rounded-lg border border-[#D7DEEA] bg-white px-3 py-1.5 text-xs font-semibold text-[#1F293F] transition hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-60"
                            >
                              <Power className="h-3.5 w-3.5" />
                              {product.isActive ? 'Deactivate' : 'Activate'}
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            )}
          </div>
        </section>
      </div>

      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        size="xl"
        className="rounded-2xl"
        title={isEditing ? 'Edit Product' : 'Add Product'}
      >
        <form className="space-y-4" onSubmit={(event) => void handleSubmitProduct(event)}>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <label className="space-y-1 text-sm">
              <span className="font-medium text-slate-700">Product Name</span>
              <input
                type="text"
                value={formState.name}
                onChange={(event) => setFormState((previous) => ({ ...previous, name: event.target.value }))}
                className="h-10 w-full rounded-lg border border-[#D7DEEA] px-3 text-sm text-slate-800 outline-none focus:border-[#1565c0]"
                placeholder="Ex: Classic Butter Cake"
                required
              />
            </label>

            <label className="space-y-1 text-sm">
              <span className="font-medium text-slate-700">SKU</span>
              <input
                type="text"
                value={formState.sku}
                onChange={(event) => setFormState((previous) => ({ ...previous, sku: event.target.value }))}
                className="h-10 w-full rounded-lg border border-[#D7DEEA] px-3 text-sm text-slate-800 outline-none focus:border-[#1565c0]"
                placeholder="Ex: CK-CLASSIC-001"
                required
              />
            </label>
          </div>

          <label className="space-y-1 text-sm">
            <span className="font-medium text-slate-700">Description</span>
            <textarea
              value={formState.description}
              onChange={(event) => setFormState((previous) => ({ ...previous, description: event.target.value }))}
              rows={3}
              className="w-full rounded-lg border border-[#D7DEEA] px-3 py-2 text-sm text-slate-800 outline-none focus:border-[#1565c0]"
              placeholder="Describe this product..."
              required
            />
          </label>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <label className="space-y-1 text-sm">
              <span className="font-medium text-slate-700">Category</span>
              <select
                value={formState.category}
                onChange={(event) =>
                  setFormState((previous) => ({ ...previous, category: event.target.value as VendorProductCategory }))
                }
                className="h-10 w-full rounded-lg border border-[#D7DEEA] px-3 text-sm text-slate-800 outline-none focus:border-[#1565c0]"
              >
                {categoryOptions.map((category) => (
                  <option key={category.value} value={category.value}>
                    {category.label}
                  </option>
                ))}
              </select>
            </label>

            <label className="space-y-1 text-sm">
              <span className="font-medium text-slate-700">Price (LKR)</span>
              <input
                type="number"
                min="0"
                step="0.01"
                value={formState.price}
                onChange={(event) => setFormState((previous) => ({ ...previous, price: event.target.value }))}
                className="h-10 w-full rounded-lg border border-[#D7DEEA] px-3 text-sm text-slate-800 outline-none focus:border-[#1565c0]"
                required
              />
            </label>
          </div>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <label className="space-y-1 text-sm">
              <span className="font-medium text-slate-700">Stock Quantity</span>
              <input
                type="number"
                min="0"
                value={formState.stockQuantity}
                onChange={(event) => setFormState((previous) => ({ ...previous, stockQuantity: event.target.value }))}
                className="h-10 w-full rounded-lg border border-[#D7DEEA] px-3 text-sm text-slate-800 outline-none focus:border-[#1565c0]"
                required
              />
            </label>

            <label className="space-y-1 text-sm">
              <span className="font-medium text-slate-700">Reorder Level</span>
              <input
                type="number"
                min="0"
                value={formState.reorderLevel}
                onChange={(event) => setFormState((previous) => ({ ...previous, reorderLevel: event.target.value }))}
                className="h-10 w-full rounded-lg border border-[#D7DEEA] px-3 text-sm text-slate-800 outline-none focus:border-[#1565c0]"
                required
              />
            </label>
          </div>

          <label className="inline-flex items-center gap-2 text-sm font-medium text-slate-700">
            <input
              type="checkbox"
              checked={formState.isActive}
              onChange={(event) => setFormState((previous) => ({ ...previous, isActive: event.target.checked }))}
              className="h-4 w-4 rounded border-[#D7DEEA] text-[#1565c0] focus:ring-[#1565c0]"
            />
            Mark product as active
          </label>

          {formError ? (
            <p className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">{formError}</p>
          ) : null}

          <div className="flex items-center justify-end gap-2 border-t border-[#EEF1F6] pt-4">
            <button
              type="button"
              onClick={() => setIsModalOpen(false)}
              className="rounded-lg border border-[#D7DEEA] px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-100"
              disabled={isSaving}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="rounded-lg bg-[#1565c0] px-4 py-2 text-sm font-semibold text-white transition hover:bg-[#0d47a1] disabled:cursor-not-allowed disabled:opacity-70"
              disabled={isSaving}
            >
              {isSaving ? 'Saving...' : isEditing ? 'Update Product' : 'Create Product'}
            </button>
          </div>
        </form>
      </Modal>
    </VendorPortalShell>
  );
}
