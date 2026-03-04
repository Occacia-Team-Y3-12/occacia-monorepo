'use client';

import Link from 'next/link';
import { ROUTES } from '@/lib/routes';

const stats = [
  { label: 'Total Users', value: '1,234', color: 'bg-blue-100', textColor: 'text-blue-700', icon: '👥' },
  { label: 'Total Orders', value: '5,678', color: 'bg-green-100', textColor: 'text-green-700', icon: '📦' },
  { label: 'Total Revenue', value: '$45,200', color: 'bg-purple-100', textColor: 'text-purple-700', icon: '💰' },
  { label: 'Pending Approvals', value: '12', color: 'bg-orange-100', textColor: 'text-orange-700', icon: '⏳' },
];

const quickLinks = [
  { label: 'Manage Users', href: ROUTES.ADMIN.USERS, icon: '👤' },
  { label: 'View Settings', href: ROUTES.ADMIN.SETTINGS, icon: '⚙️' },
  { label: 'Analytics', href: ROUTES.ADMIN.DASHBOARD, icon: '📊' },
];

export default function AdminPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Hero Section */}
      <div className="bg-gradient-to-r from-indigo-700 to-indigo-900 text-white py-12 px-4 sm:px-8">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-3xl sm:text-4xl font-bold mb-2">Admin Dashboard</h1>
          <p className="text-indigo-100 text-lg">Manage your platform and monitor key metrics</p>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-8 py-12">
        {/* Stats Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
          {stats.map((stat, index) => (
            <div key={index} className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
              <div className={`${stat.color} w-12 h-12 rounded-lg flex items-center justify-center text-2xl mb-4`}>
                {stat.icon}
              </div>
              <p className="text-gray-600 text-sm mb-2">{stat.label}</p>
              <p className={`text-3xl font-bold ${stat.textColor}`}>{stat.value}</p>
            </div>
          ))}
        </div>

        {/* Quick Actions */}
        <div className="grid lg:grid-cols-3 gap-8 mb-8">
          <div className="lg:col-span-2 bg-white rounded-lg shadow-md p-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Quick Actions</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {quickLinks.map((link, index) => (
                <Link
                  key={index}
                  href={link.href}
                  className="flex items-center gap-3 p-4 border border-gray-200 rounded-lg hover:border-indigo-500 hover:bg-indigo-50 transition-all group"
                >
                  <div className="text-3xl">{link.icon}</div>
                  <span className="font-semibold text-gray-900 group-hover:text-indigo-700">{link.label}</span>
                </Link>
              ))}
            </div>
          </div>

          {/* System Status */}
          <div className="bg-white rounded-lg shadow-md p-8">
            <h3 className="text-xl font-bold text-gray-900 mb-4">System Status</h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-gray-600">API Server</span>
                <span className="inline-block w-3 h-3 bg-green-500 rounded-full"></span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600">Database</span>
                <span className="inline-block w-3 h-3 bg-green-500 rounded-full"></span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600">Storage</span>
                <span className="inline-block w-3 h-3 bg-green-500 rounded-full"></span>
              </div>
            </div>
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
