'use client';

import { useState } from 'react';
import Link from 'next/link';

export default function ProductsPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const products = [];

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 py-6 px-4 sm:px-8">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-3xl sm:text-4xl font-bold text-gray-900">Products</h1>
          <p className="text-gray-600 mt-2">Browse our collection</p>
        </div>
      </div>

      {/* Search and Filter */}
      <div className="max-w-7xl mx-auto px-4 sm:px-8 py-8">
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <input
            type="text"
            placeholder="Search products..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Products Grid */}
        {products.length === 0 ? (
          <div className="bg-white rounded-lg shadow-md p-12 text-center">
            <div className="text-6xl mb-4">🔍</div>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">No products available</h2>
            <p className="text-gray-600">Check back soon for new products</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {products.map((product, index) => (
              <div key={index} className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow">
                <div className="h-48 bg-gray-200"></div>
                <div className="p-4">
                  <h3 className="font-bold text-gray-900">Product {index + 1}</h3>
                  <p className="text-gray-600 text-sm">$0.00</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
