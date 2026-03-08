'use client';

import Link from 'next/link';
import { ROUTES } from '@/lib/routes';

const stats = [
  { label: 'Total Products', value: '45', color: 'bg-blue-100', textColor: 'text-blue-700', icon: '📐' },
  { label: 'Total Orders', value: '234', color: 'bg-green-100', textColor: 'text-green-700', icon: '📦' },
  { label: 'Revenue', value: '$12,450', color: 'bg-purple-100', textColor: 'text-purple-700', icon: '💰' },
  { label: 'Pending Orders', value: '8', color: 'bg-orange-100', textColor: 'text-orange-700', icon: '⏳' },
];

const quickLinks = [
  { label: 'Add New Product', href: ROUTES.VENDOR.PRODUCTS, icon: '➕' },
  { label: 'View Orders', href: ROUTES.VENDOR.ORDERS, icon: '📦' },
  { label: 'My Products', href: ROUTES.VENDOR.PRODUCTS, icon: '🃐' },
];

export default function VendorPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Hero Section */}
      <div className="bg-gradient-to-r from-emerald-700 to-emerald-900 text-white py-8 md:py-12 px-4 sm:px-8">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-2xl sm:text-3xl md:text-4xl font-bold mb-2">Vendor Dashboard</h1>
          <p className="text-emerald-100 text-base md:text-lg">Manage your products and orders</p>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-8 py-8 md:py-12">
        {/* Stats Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6 mb-8 md:mb-12">
          {stats.map((stat, index) => (
            <div key={index} className="bg-white rounded-lg shadow-md p-4 md:p-6 hover:shadow-lg transition-shadow">
              <div className={`${stat.color} w-12 h-12 rounded-lg flex items-center justify-center text-2xl mb-4`}>
                {stat.icon}
              </div>
              <p className="text-gray-600 text-sm mb-2">{stat.label}</p>
              <p className="text-2xl md:text-3xl font-bold ${stat.textColor}">{stat.value}</p>
            </div>
          ))}
        </div>

        {/* Quick Actions */}
        <div className="grid lg:grid-cols-3 gap-6 md:gap-8 mb-6 md:mb-8">
          <div className="lg:col-span-2 bg-white rounded-lg shadow-md p-6 md:p-8">
            <h2 className="text-xl md:text-2xl font-bold text-gray-900 mb-4 md:mb-6">Quick Actions</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {quickLinks.map((link, index) => (
                <Link
                  key={index}
                  href={link.href}
                  className="flex items-center gap-3 p-4 border border-gray-200 rounded-lg hover:border-emerald-500 hover:bg-emerald-50 transition-all group"
                >
                  <div className="text-3xl">{link.icon}</div>
                  <span className="font-semibold text-gray-900 group-hover:text-emerald-700">{link.label}</span>
                </Link>
              ))}
            </div>
          </div>

          {/* Performance */}
          <div className="bg-white rounded-lg shadow-md p-6 md:p-8">
            <h3 className="text-lg md:text-xl font-bold text-gray-900 mb-4">Performance</h3>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between mb-2">
                  <span className="text-sm font-semibold text-gray-700">Order Fulfillment</span>
                  <span className="text-sm font-semibold text-emerald-600">95%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className="bg-emerald-500 h-2 rounded-full" style={{ width: '95%' }}></div>
                </div>
              </div>
              <div>
                <div className="flex justify-between mb-2">
                  <span className="text-sm font-semibold text-gray-700">Customer Rating</span>
                  <span className="text-sm font-semibold text-emerald-600">4.8/5</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className="bg-emerald-500 h-2 rounded-full" style={{ width: '96%' }}></div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Recent Orders */}
        <div className="bg-white rounded-lg shadow-md p-6 md:p-8">
          <h2 className="text-xl md:text-2xl font-bold text-gray-900 mb-4 md:mb-6">Recent Orders</h2>
          <div className="text-center py-12 text-gray-500">
            <p className="text-lg">No recent orders</p>
          </div>
        </div>
      </div>
    </div>
  );
}
