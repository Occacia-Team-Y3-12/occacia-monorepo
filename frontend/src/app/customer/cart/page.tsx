'use client';

import Link from 'next/link';
import { ROUTES } from '@/lib/routes';

export default function CartPage() {
  const items = [];

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 py-6 px-4 sm:px-8">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-3xl sm:text-4xl font-bold text-gray-900">Shopping Cart</h1>
          <p className="text-gray-600 mt-2">Manage your cart items</p>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-8 py-12">
        {items.length === 0 ? (
          <div className="bg-white rounded-lg shadow-md p-12 text-center">
            <div className="text-6xl mb-4">🛒</div>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Your cart is empty</h2>
            <p className="text-gray-600 mb-8">Start shopping to add items to your cart</p>
            <Link href={ROUTES.CUSTOMER.PRODUCTS} className="inline-block bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-8 rounded-lg transition-colors">
              Continue Shopping
            </Link>
          </div>
        ) : (
          <div className="grid lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2 bg-white rounded-lg shadow-md p-6">Cart items will appear here</div>
            <div className="bg-white rounded-lg shadow-md p-6 h-fit">
              <h3 className="text-lg font-bold text-gray-900 mb-4">Order Summary</h3>
              <div className="text-center py-8 text-gray-500">No items to summarize</div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
