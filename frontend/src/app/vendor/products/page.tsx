'use client';

import { useState } from 'react';
import Link from 'next/link';

export default function VendorProductsPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const products = [];

  const categories = ['all', 'Electronics', 'Clothing', 'Food', 'Books', 'Other'];

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 py-4 md:py-6 px-4 sm:px-8">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl md:text-4xl font-bold text-gray-900">Products</h1>
            <p className="text-gray-600 mt-1 md:mt-2 text-sm md:text-base">Manage your product inventory</p>
          </div>
          <button className="bg-emerald-600 hover:bg-emerald-700 text-white font-semibold py-2 px-4 md:px-6 rounded-lg transition-colors text-sm md:text-base w-full sm:w-auto">
            Add Product
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-8 py-8 md:py-12">
        {/* Filters */}
        <div className="bg-white rounded-lg shadow-md p-4 md:p-6 mb-6 md:mb-8">
          <div className="grid md:grid-cols-2 gap-3 md:gap-4">
            <div>
              <label className="block text-xs md:text-sm font-semibold text-gray-900 mb-2">Search Products</label>
              <input
                type="text"
                placeholder="Search by name, SKU, etc..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full px-3 md:px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 text-sm md:text-base"
              />
            </div>
            <div>
              <label className="block text-xs md:text-sm font-semibold text-gray-900 mb-2">Category</label>
              <select
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
                className="w-full px-3 md:px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 text-sm md:text-base"
              >
                {categories.map((cat) => (
                  <option key={cat} value={cat}>
                    {cat}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Products Grid */}
        {products.length === 0 ? (
          <div className="bg-white rounded-lg shadow-md p-8 md:p-12 text-center">
            <div className="text-4xl md:text-6xl mb-3 md:mb-4">📦</div>
            <h2 className="text-xl md:text-2xl font-bold text-gray-900 mb-3 md:mb-4">No products yet</h2>
            <p className="text-gray-600 mb-6 md:mb-8 text-sm md:text-base">Start by adding your first product</p>
            <button className="bg-emerald-600 hover:bg-emerald-700 text-white font-semibold py-2 md:py-3 px-6 md:px-8 rounded-lg transition-colors text-sm md:text-base">
              Add Your First Product
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {products.map((product, index) => (
              <div key={index} className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow">
                <div className="h-40 md:h-48 bg-gray-200"></div>
                <div className="p-3 md:p-4">
                  <h3 className="font-bold text-gray-900 mb-2">Product {index + 1}</h3>
                  <p className="text-emerald-600 font-semibold mb-3">$0.00</p>
                  <button className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-semibold py-2 rounded transition-colors text-sm">
                    Edit
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
