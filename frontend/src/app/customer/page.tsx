'use client';

import { useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { ROUTES } from '@/lib/routes';

const stats = [
  { label: 'Total Orders', value: '12', icon: '📦' },
  { label: 'Total Spent', value: '$1,245', icon: '💰' },
  { label: 'Active Carts', value: '2', icon: '🛒' },
  { label: 'Saved Items', value: '8', icon: '❤️' },
];

export default function CustomerPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Hero Section */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-800 text-white py-12 px-4 sm:px-8">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-3xl sm:text-4xl font-bold mb-2">Welcome Back</h1>
          <p className="text-blue-100 text-lg">Manage your orders and shopping experience</p>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-8 py-12">
        {/* Stats Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
          {stats.map((stat, index) => (
            <div key={index} className="bg-white rounded-lg shadow-md p-6 text-center hover:shadow-lg transition-shadow">
              <div className="text-4xl mb-3">{stat.icon}</div>
              <p className="text-gray-600 text-sm mb-2">{stat.label}</p>
              <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
            </div>
          ))}
        </div>

        {/* Quick Actions */}
        <div className="bg-white rounded-lg shadow-md p-8 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Quick Actions</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <Link href={ROUTES.CUSTOMER.PRODUCTS} className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors text-center">
              Browse Products
            </Link>
            <Link href={ROUTES.CUSTOMER.CART} className="bg-green-600 hover:bg-green-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors text-center">
              View Cart
            </Link>
            <Link href={ROUTES.CUSTOMER.ORDERS} className="bg-purple-600 hover:bg-purple-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors text-center">
              My Orders
            </Link>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="bg-white rounded-lg shadow-md p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Recent Activity</h2>
          <div className="text-center py-12 text-gray-500">
            <p className="text-lg">No recent activity</p>
          </div>
        </div>
      </div>
    </div>
  );
}
