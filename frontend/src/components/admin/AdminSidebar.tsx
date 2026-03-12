// frontend/src/components/admin/AdminSidebar.tsx

'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { motion } from 'framer-motion';
import {
  LayoutDashboard,
  Store,
  Building2,
  Shield,
  Users,
  HelpCircle,
  ClipboardList,
  ShoppingBag,
  Bell,
} from 'lucide-react';

interface NavItem {
  label: string;
  href: string;
  icon: React.ElementType;
  badge?: number;
}

const navItems: NavItem[] = [
  { label: 'Dashboard', href: '/admin', icon: LayoutDashboard },
  { label: 'Vendors', href: '/admin/vendors', icon: Store },
  { label: 'Organizations', href: '/admin/organizations', icon: Building2 },
  { label: 'Admins', href: '/admin/admins', icon: Shield },
  { label: 'Customers', href: '/admin/customers', icon: Users },
  { label: 'Inquiries', href: '/admin/inquiries', icon: HelpCircle },
  { 
    label: 'Pending Requests', 
    href: '/admin/pending-requests', 
    icon: ClipboardList,
    badge: 12 // This would be dynamic from API
  },
  { label: 'Package Orders', href: '/admin/orders', icon: ShoppingBag },
];

export default function AdminSidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 z-40 h-screen w-64 border-r border-gray-200 bg-white">
      <div className="flex h-full flex-col">
        {/* Logo */}
        <div className="flex h-16 items-center border-b border-gray-200 px-6">
          <Link href="/admin" className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600 text-white font-bold">
              O
            </div>
            <span className="text-lg font-bold text-gray-900">Occacia</span>
          </Link>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto px-4 py-4">
          <ul className="space-y-1">
            {navItems.map((item) => {
              const isActive = pathname === item.href;
              const Icon = item.icon;

              return (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    className={`group relative flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium transition-all ${
                      isActive
                        ? 'bg-blue-50 text-blue-600'
                        : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                    }`}
                  >
                    {isActive && (
                      <motion.div
                        layoutId="sidebarActive"
                        className="absolute left-0 top-1/2 h-8 w-1 -translate-y-1/2 rounded-r-full bg-blue-600"
                      />
                    )}
                    <Icon className={`h-5 w-5 ${isActive ? 'text-blue-600' : 'text-gray-400 group-hover:text-gray-600'}`} />
                    <span>{item.label}</span>
                    {item.badge && (
                      <span className="ml-auto flex h-5 min-w-[20px] items-center justify-center rounded-full bg-red-500 px-1.5 text-xs font-bold text-white">
                        {item.badge}
                      </span>
                    )}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        {/* User Profile */}
        <div className="border-t border-gray-200 p-4">
          <button className="flex w-full items-center gap-3 rounded-xl p-2 hover:bg-gray-50">
            <div className="h-9 w-9 rounded-full bg-gradient-to-br from-blue-500 to-purple-600" />
            <div className="flex-1 text-left">
              <p className="text-sm font-medium text-gray-900">Admin User</p>
              <p className="text-xs text-gray-500">admin@occacia.com</p>
            </div>
          </button>
        </div>
      </div>
    </aside>
  );
}