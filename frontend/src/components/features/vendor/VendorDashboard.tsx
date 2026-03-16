'use client';

import { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import { ROUTES } from '@/lib/routes';
import Modal from '@/components/ui/Modal';

type SidebarItem = {
	label: string;
  icon: string;
	badge?: number;
	active?: boolean;
};

type StatCard = {
	title: string;
	value: string;
	note: string;
	noteTone: 'green' | 'orange';
	iconBg: string;
	icon: string;
};

type OrderRow = {
	id: string;
	occasion: string;
	recipient: string;
	recipientMeta: string;
	budget: string;
	status: 'New Order' | 'Preparing' | 'Ready' | 'Delivered';
};

const sidebarItems: SidebarItem[] = [
  { label: 'Dashboard', icon: '/icons/vendor/dashboard/dashboard.svg', active: true },
  { label: 'Orders', icon: '/icons/vendor/dashboard/shopping-cart.svg', badge: 12 },
  { label: 'Packages', icon: '/icons/vendor/dashboard/clipboard.svg' },
  { label: 'Analytics', icon: '/icons/vendor/dashboard/calendar.svg' },
  { label: 'Recipients', icon: '/icons/vendor/dashboard/users.svg' },
];

const statCards: StatCard[] = [
  { title: 'New Orders Today', value: '24', note: '+12%', noteTone: 'green', iconBg: 'bg-blue-100', icon: '/icons/vendor/dashboard/stat-bag.svg' },
  { title: 'Awaiting Preparation', value: '8', note: 'Pending', noteTone: 'orange', iconBg: 'bg-amber-100', icon: '/icons/vendor/dashboard/stat-clock.svg' },
  { title: 'Revenue This Week', value: '$4,280', note: '+8%', noteTone: 'green', iconBg: 'bg-violet-100', icon: '/icons/vendor/dashboard/stat-currency.svg' },
  { title: 'Vendor Rating', value: '4.9', note: 'Excellent', noteTone: 'green', iconBg: 'bg-emerald-100', icon: '/icons/vendor/dashboard/stat-star.svg' },
];

const orders: OrderRow[] = [
	{
		id: '#OCC-7829',
		occasion: 'Birthday Surprise',
		recipient: 'Sarah (28, Artist)',
		recipientMeta: 'Loves minimalist design, vegan',
		budget: '$150',
		status: 'New Order',
	},
	{
		id: '#OCC-7828',
		occasion: 'Date Night',
		recipient: 'Couple - Alex & Jordan',
		recipientMeta: 'Adventurous, foodies, jazz lovers',
		budget: '$200',
		status: 'Preparing',
	},
	{
		id: '#OCC-7827',
		occasion: 'Hospital Visit',
		recipient: 'Grandpa Joe (78)',
		recipientMeta: 'Gardening enthusiast, diabetic',
		budget: '$85',
		status: 'Ready',
	},
	{
		id: '#OCC-7826',
		occasion: 'Dinner Out',
		recipient: 'Family of 4',
		recipientMeta: 'Kids ages 5 & 8, picky eaters',
		budget: '$120',
		status: 'Delivered',
	},
];

const statusPillClass: Record<OrderRow['status'], string> = {
	'New Order': 'bg-amber-100 text-amber-800',
	Preparing: 'bg-blue-100 text-blue-800',
	Ready: 'bg-violet-100 text-violet-800',
	Delivered: 'bg-emerald-100 text-emerald-800',
};

const recipientTypes = [
	{ label: 'Birthday Celebrants', value: 45, color: 'bg-blue-500' },
	{ label: 'Date Night Couples', value: 30, color: 'bg-violet-500' },
	{ label: 'Elderly Visits', value: 15, color: 'bg-emerald-500' },
];

export default function VendorDashboard() {
  const router = useRouter();
  const [isProfileMenuOpen, setIsProfileMenuOpen] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isLogoutModalOpen, setIsLogoutModalOpen] = useState(false);
  const profileMenuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (profileMenuRef.current && !profileMenuRef.current.contains(event.target as Node)) {
        setIsProfileMenuOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleLogout = () => {
    setIsProfileMenuOpen(false);
    setIsLogoutModalOpen(true);
  };

  const handleConfirmLogout = () => {
    setIsLogoutModalOpen(false);
    router.push(ROUTES.VENDOR.LOGIN);
  };

  return (
    <div className="min-h-screen bg-[#f4f6fb] text-slate-900">
      <div className="mx-auto flex w-full max-w-[1600px]">
        <aside
          className={`fixed inset-y-0 left-0 z-40 flex w-[250px] shrink-0 flex-col border-r border-slate-200 bg-white px-4 py-2 transform transition-transform duration-300 lg:static lg:min-h-screen lg:translate-x-0 ${
            isSidebarOpen ? 'translate-x-0' : '-translate-x-full'
          }`}
        >
          <div className="mb-2 flex items-center gap-2 py-1">
          <Image src="/icons/logo.svg" alt="Occacia" width={59} height={59} className="ml-[-8px] h-[59px] w-[59px] shrink-0" priority />
          <span className="text-[22px] font-extrabold tracking-tight text-[#1562CC]">OCCACIA</span>
          </div>

          <nav className="mt-6 space-y-1">
            {sidebarItems.map((item) => (
              <button
                key={item.label}
                onClick={() => setIsSidebarOpen(false)}
              className={`flex w-full items-center justify-between rounded-xl px-3 py-3 text-left text-base transition-colors xl:text-[18px]
                  ${item.active ? 'bg-blue-50 text-blue-700' : 'text-slate-600 hover:bg-slate-100'}
                `}
                type="button"
              >
                <span className="flex items-center gap-3 font-medium">
                  <Image src={item.icon} alt="" width={20} height={20} className="h-5 w-5 opacity-90" />
                  {item.label}
                </span>
                {item.badge ? (
                  <span className="rounded-full bg-blue-600 px-2 py-0.5 text-xs font-semibold text-white">{item.badge}</span>
                ) : null}
              </button>
            ))}
          </nav>

          <button
            type="button"
            onClick={handleLogout}
            className="mt-auto flex items-center gap-3 rounded-xl px-3 py-3 text-base font-medium text-slate-600 hover:bg-slate-100 xl:text-[18px]"
          >
            <Image src="/icons/vendor/dashboard/logout.svg" alt="" aria-hidden="true" width={20} height={20} className="h-5 w-5" />
            Logout
          </button>
        </aside>

        {isSidebarOpen && (
          <button
            type="button"
            aria-label="Close sidebar overlay"
            onClick={() => setIsSidebarOpen(false)}
            className="fixed inset-0 z-30 bg-black/25 lg:hidden"
          />
        )}

        <main className="min-w-0 flex-1 overflow-x-hidden">
        <header className="w-full border-b border-[#ECECF0] bg-[#F7F7FA] px-4 py-3 sm:px-6 sm:py-4">
            <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex w-full flex-col gap-3 sm:flex-row sm:items-center sm:gap-5 lg:w-auto">
            <button
              type="button"
              onClick={() => setIsSidebarOpen((prev) => !prev)}
              className="inline-flex h-10 w-10 items-center justify-center rounded-xl border border-[#E2E5EC] bg-white text-[#5B6478] lg:hidden"
              aria-label="Toggle sidebar"
            >
              <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M4 7h16M4 12h16M4 17h16" />
              </svg>
            </button>
        <div className="relative w-full sm:w-[320px] md:w-[360px]">
                  <input
                    type="search"
              placeholder="Search orders, recipients.."
              className="h-11 w-full rounded-full border border-[#E2E5EC] bg-[#EFF1F6] px-5 text-sm text-[#4A4F5C] outline-none placeholder:text-[#99A0AF]"
                  />
                </div>
              </div>

          <div className="flex items-center justify-between gap-2 sm:justify-end sm:gap-4">
                <button
                  type="button"
                  aria-label="Notifications"
                  className="relative inline-flex h-10 w-10 items-center justify-center rounded-full border border-[#E0E7F2] bg-white text-[#5B6478]"
                >
                  <Image src="/icons/vendor/dashboard/header-notification.svg" alt="" aria-hidden="true" width={20} height={20} className="h-5 w-5" />
                  <span className="absolute right-2 top-2 h-2 w-2 rounded-full bg-[#0D47A1]" />
                </button>

          <div className="hidden h-10 w-px bg-[#D9DEE8] sm:block" aria-hidden="true" />

                <div className="relative" ref={profileMenuRef}>
                  <button
                  type="button"
                  onClick={() => setIsProfileMenuOpen((prev) => !prev)}
                  className="flex items-center gap-2 sm:gap-3"
                  aria-label="Open vendor profile menu"
                  >
                  <span className="hidden text-[16px] font-semibold text-[#182039] sm:inline">Spring & Summer</span>
                  <span className="inline-flex h-12 w-12 items-center justify-center overflow-hidden rounded-full border-[3px] border-white bg-white shadow-[0_6px_18px_rgba(25,35,72,0.18)]">
                    <Image
                    src="/icons/vendor/dashboard/Spring & Summer logo.svg"
                    alt="Spring & Summer"
                    width={40}
                    height={40}
                    className="h-10 w-10 object-contain"
                    />
                  </span>
                  </button>

                  {isProfileMenuOpen && (
                  <div className="absolute right-0 top-full z-50 mt-2 w-40 rounded-xl border border-[#E5E8F0] bg-white p-2 shadow-[0_14px_28px_rgba(23,34,73,0.12)] sm:w-44">
                    <button
                    type="button"
                    className="w-full rounded-lg px-3 py-2 text-left text-sm font-medium text-[#1F293F] transition-colors hover:bg-[#F3F5FA]"
                    >
                    My Profile
                    </button>
                    <button
                    type="button"
                    onClick={handleLogout}
                    className="mt-1 w-full rounded-lg px-3 py-2 text-left text-sm font-medium text-[#C22525] transition-colors hover:bg-[#FFF1F1]"
                    >
                    Logout
                    </button>
                  </div>
                  )}
                </div>

              </div>
            </div>
          </header>

          <div className="p-4 sm:p-6">

          <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {statCards.map((card) => (
            <article key={card.title} className="rounded-2xl border border-slate-200 bg-white p-4 shadow-[0_4px_16px_rgba(15,23,42,0.06)] sm:p-5">
                <div className="mb-5 flex items-start justify-between">
                  <span className={`inline-flex h-11 w-11 items-center justify-center rounded-xl ${card.iconBg} text-slate-700`}>
                    <Image src={card.icon} alt="" aria-hidden="true" width={20} height={20} className="h-5 w-5" />
                  </span>
                  <span
                    className={`rounded-full px-3 py-1 text-sm font-semibold ${
                      card.noteTone === 'green' ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'
                    }`}
                  >
                    {card.note}
                  </span>
                </div>
                <p className="text-[28px] font-semibold leading-none tracking-tight text-slate-900">{card.value}</p>
                <p className="mt-2 text-sm text-slate-500">{card.title}</p>
              </article>
            ))}
          </section>

          <section className="mt-5 grid grid-cols-1 gap-5 xl:grid-cols-[1.85fr_0.85fr]">
              <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-[0_4px_16px_rgba(15,23,42,0.06)] sm:p-5">
              <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h2 className="text-lg font-semibold tracking-tight text-slate-900">Recent Orders</h2>
                  <p className="text-sm text-slate-500">Manage and fulfill customer orders</p>
                </div>
                <div className="flex w-full flex-wrap items-center gap-2 rounded-xl bg-slate-100 p-1 text-sm sm:w-auto">
                  <button type="button" className="rounded-lg bg-white px-3 py-2 font-medium text-blue-700 shadow-sm inline-flex items-center gap-2 sm:px-4">
                    <Image src="/icons/vendor/dashboard/filter-all-orders.svg" alt="All orders" width={16} height={16} className="h-4 w-4" />
                    All Orders
                  </button>
                  <button type="button" className="rounded-lg px-3 py-2 text-slate-600 inline-flex items-center gap-2 sm:px-4">
                    <Image src="/icons/vendor/dashboard/filter-pending.svg" alt="Pending" width={16} height={16} className="h-4 w-4" />
                    Pending
                  </button>
                  <button type="button" className="rounded-lg px-3 py-2 text-slate-600 inline-flex items-center gap-2 sm:px-4">
                    <Image src="/icons/vendor/dashboard/filter-completed.svg" alt="Completed" width={16} height={16} className="h-4 w-4" />
                    Completed
                  </button>
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full min-w-[680px] border-separate border-spacing-y-2 sm:min-w-[760px]">
                  <thead>
                    <tr className="text-left text-[12px] font-semibold uppercase tracking-wide text-slate-400">
                      <th className="px-2 py-1">Order ID</th>
                      <th className="px-2 py-1">Occasion</th>
                      <th className="px-2 py-1">Recipient Profile</th>
                      <th className="px-2 py-1">Budget</th>
                      <th className="px-2 py-1">Status</th>
                      <th className="px-2 py-1">Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {orders.map((order) => (
                      <tr key={order.id} className="rounded-xl bg-slate-50">
                    <td className="rounded-l-xl px-2 py-3 text-xs font-semibold text-blue-700 sm:text-sm">{order.id}</td>
                    <td className="px-2 py-3 text-sm font-semibold text-slate-800 sm:text-base">{order.occasion}</td>
                        <td className="px-2 py-3">
                      <div className="text-sm font-semibold text-slate-800 sm:text-base">{order.recipient}</div>
                      <div className="text-xs text-slate-500 sm:text-sm">{order.recipientMeta}</div>
                        </td>
                    <td className="px-2 py-3 text-sm font-semibold text-slate-800 sm:text-base">{order.budget}</td>
                        <td className="px-2 py-3">
                          <span className={`rounded-full px-3 py-1 text-xs font-semibold ${statusPillClass[order.status]}`}>{order.status}</span>
                        </td>
                        <td className="rounded-r-xl px-2 py-3 text-blue-600">
                          <button type="button" className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-white shadow-sm">
                            <Image src="/icons/vendor/dashboard/table-action-view.svg" alt="View" width={18} height={18} className="h-[18px] w-[18px]" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="mt-2 text-center">
                <Link href={ROUTES.VENDOR.ORDERS} className="inline-flex items-center gap-2 text-sm font-semibold text-blue-700 hover:text-blue-800">
                  View All Orders
                  <Image src="/icons/vendor/dashboard/link-view-orders.svg" alt="" aria-hidden="true" width={16} height={16} className="h-4 w-4" />
                </Link>
              </div>
            </div>

            <div className="space-y-5">
            <section className="rounded-2xl border border-slate-200 bg-white p-4 shadow-[0_4px_16px_rgba(15,23,42,0.06)] sm:p-5">
              <h3 className="mb-4 text-base font-semibold text-slate-900">Quick Actions</h3>
              <div className="space-y-3 text-sm">
              <button className="w-full rounded-xl bg-blue-600 px-4 py-3 font-semibold text-white shadow-md hover:bg-blue-700 inline-flex items-center justify-center gap-2" type="button">
                    <Image src="/icons/vendor/dashboard/quick-package.svg" alt="" aria-hidden="true" width={18} height={18} className="h-[18px] w-[18px]" />
                    Create New Package
                  </button>
                  <Link href={ROUTES.VENDOR.OFFERINGS} className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 font-semibold text-slate-700 hover:bg-slate-50 inline-flex items-center justify-center gap-2">
                    <Image src="/icons/vendor/dashboard/quick-inventory.svg" alt="" aria-hidden="true" width={18} height={18} className="h-[18px] w-[18px]" />
                    Manage Offerings
                  </Link>
                  <button className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 font-semibold text-slate-700 hover:bg-slate-50 inline-flex items-center justify-center gap-2" type="button">
                    <Image src="/icons/vendor/dashboard/quick-delivery.svg" alt="" aria-hidden="true" width={18} height={18} className="h-[18px] w-[18px]" />
                    Schedule Delivery
                  </button>
                </div>
              </section>

              <section className="rounded-2xl border border-slate-200 bg-white p-4 shadow-[0_4px_16px_rgba(15,23,42,0.06)] sm:p-5">
                <div className="mb-4 flex items-center justify-between">
                <h3 className="text-base font-semibold text-slate-900">Top Recipient Types</h3>
                  <button type="button" className="text-sm font-semibold text-blue-700 hover:text-blue-800 inline-flex items-center gap-1.5">
                    <Image src="/icons/vendor/dashboard/link-report.svg" alt="" aria-hidden="true" width={16} height={16} className="h-4 w-4" />
                    View Report
                  </button>
                </div>

                <div className="space-y-4">
                  {recipientTypes.map((item) => (
                    <div key={item.label}>
                      <div className="mb-1 flex items-center justify-between text-sm text-slate-700">
                        <span>{item.label}</span>
                        <span className="font-semibold">{item.value}%</span>
                      </div>
                      <div className="h-2 rounded-full bg-slate-200">
                        <div className={`h-2 rounded-full ${item.color}`} style={{ width: `${item.value}%` }} />
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            </div>
          </section>
          </div>
        </main>

        <Modal
          isOpen={isLogoutModalOpen}
          onClose={() => setIsLogoutModalOpen(false)}
          size="md"
          className="rounded-2xl"
        >
          <div className="text-center">
            <div className="mx-auto mb-4 inline-flex h-14 w-14 items-center justify-center rounded-full bg-rose-100 text-rose-600">
              <svg viewBox="0 0 24 24" className="h-7 w-7" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
                <path d="M8 21H6a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h2" strokeLinecap="round" />
                <path d="M16 17l4-5-4-5" strokeLinecap="round" strokeLinejoin="round" />
                <path d="M10 12h10" strokeLinecap="round" />
              </svg>
            </div>

            <h3 className="text-2xl font-semibold text-slate-900">Log Out</h3>
            <p className="mt-2 text-sm leading-relaxed text-slate-600">
              Are you sure you want to log out from the vendor portal?
            </p>

            <div className="mt-6 flex items-center justify-center gap-3">
              <button
                type="button"
                onClick={() => setIsLogoutModalOpen(false)}
                className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleConfirmLogout}
                className="rounded-lg bg-[#1565c0] px-4 py-2 text-sm font-medium text-white hover:bg-[#0d47a1]"
              >
                Yes, Log Out
              </button>
            </div>
          </div>
        </Modal>
      </div>
    </div>
  );
}
