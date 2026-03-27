'use client';

import { useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { ROUTES } from '@/lib/routes';
import VendorPortalShell from '@/components/features/vendor/VendorPortalShell';

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

type OrderFilter = 'all' | 'pending' | 'completed';

const statCards: StatCard[] = [
  { title: 'New Orders Today', value: '24', note: '+12%', noteTone: 'green', iconBg: 'bg-blue-100', icon: '/icons/vendor/dashboard/stat-bag.svg' },
  { title: 'Awaiting Preparation', value: '8', note: 'Pending', noteTone: 'orange', iconBg: 'bg-amber-100', icon: '/icons/vendor/dashboard/stat-clock.svg' },
  { title: 'Revenue This Week', value: 'LKR 4,280', note: '+8%', noteTone: 'green', iconBg: 'bg-violet-100', icon: '/icons/vendor/dashboard/stat-currency.svg' },
  { title: 'Vendor Rating', value: '4.9', note: 'Excellent', noteTone: 'green', iconBg: 'bg-emerald-100', icon: '/icons/vendor/dashboard/stat-star.svg' },
];

const orders: OrderRow[] = [
  {
    id: '#OCC-7829',
    occasion: 'Birthday Surprise',
    recipient: 'Sarah (28, Artist)',
    recipientMeta: 'Loves minimalist design, vegan',
    budget: 'LKR 150',
    status: 'New Order',
  },
  {
    id: '#OCC-7828',
    occasion: 'Date Night',
    recipient: 'Couple - Alex & Jordan',
    recipientMeta: 'Adventurous, foodies, jazz lovers',
    budget: 'LKR 200',
    status: 'Preparing',
  },
  {
    id: '#OCC-7827',
    occasion: 'Hospital Visit',
    recipient: 'Grandpa Joe (78)',
    recipientMeta: 'Gardening enthusiast, diabetic',
    budget: 'LKR 85',
    status: 'Ready',
  },
  {
    id: '#OCC-7826',
    occasion: 'Dinner Out',
    recipient: 'Family of 4',
    recipientMeta: 'Kids ages 5 & 8, picky eaters',
    budget: 'LKR 120',
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

const orderFilterOptions: Array<{
  value: OrderFilter;
  label: string;
  icon: string;
  iconAlt: string;
}> = [
  { value: 'all', label: 'All Orders', icon: '/icons/vendor/dashboard/filter-all-orders.svg', iconAlt: 'All orders' },
  { value: 'pending', label: 'Pending', icon: '/icons/vendor/dashboard/filter-pending.svg', iconAlt: 'Pending' },
  { value: 'completed', label: 'Completed', icon: '/icons/vendor/dashboard/filter-completed.svg', iconAlt: 'Completed' },
];

function getOrderFilter(status: OrderRow['status']): Exclude<OrderFilter, 'all'> {
  if (status === 'Ready' || status === 'Delivered') {
    return 'completed';
  }

  return 'pending';
}

function buildOrdersHref(filter: OrderFilter): string {
  if (filter === 'all') {
    return ROUTES.VENDOR.ORDERS;
  }

  return `${ROUTES.VENDOR.ORDERS}?status=${filter}`;
}

export default function VendorDashboard() {
  const [orderFilter, setOrderFilter] = useState<OrderFilter>('all');
  const [isRecipientReportOpen, setIsRecipientReportOpen] = useState(false);

  const filteredOrders =
    orderFilter === 'all'
      ? orders
      : orders.filter((order) => getOrderFilter(order.status) === orderFilter);

  return (
    <VendorPortalShell>
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
              {orderFilterOptions.map((option) => {
                const isActive = orderFilter === option.value;

                return (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => setOrderFilter(option.value)}
                    className={`inline-flex items-center gap-2 rounded-lg px-3 py-2 sm:px-4 ${
                      isActive ? 'bg-white font-medium text-blue-700 shadow-sm' : 'text-slate-600'
                    }`}
                  >
                    <Image src={option.icon} alt={option.iconAlt} width={16} height={16} className="h-4 w-4" />
                    {option.label}
                  </button>
                );
              })}
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
                {filteredOrders.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="rounded-xl bg-slate-50 px-4 py-8 text-center text-sm text-slate-500">
                      No {orderFilter === 'all' ? 'orders' : orderFilter} orders to show right now.
                    </td>
                  </tr>
                ) : (
                  filteredOrders.map((order) => (
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
                        <Link
                          href={buildOrdersHref(getOrderFilter(order.status))}
                          className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-white shadow-sm transition hover:bg-slate-100"
                          aria-label={`View ${order.id}`}
                        >
                          <Image src="/icons/vendor/dashboard/table-action-view.svg" alt="View" width={18} height={18} className="h-[18px] w-[18px]" />
                        </Link>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          <div className="mt-2 text-center">
            <Link href={buildOrdersHref(orderFilter)} className="inline-flex items-center gap-2 text-sm font-semibold text-blue-700 hover:text-blue-800">
              View All Orders
              <Image src="/icons/vendor/dashboard/link-view-orders.svg" alt="" aria-hidden="true" width={16} height={16} className="h-4 w-4" />
            </Link>
          </div>
        </div>

        <div className="space-y-5">
          <section className="rounded-2xl border border-slate-200 bg-white p-4 shadow-[0_4px_16px_rgba(15,23,42,0.06)] sm:p-5">
            <h3 className="mb-4 text-base font-semibold text-slate-900">Quick Actions</h3>
            <div className="space-y-3 text-sm">
              <Link href={ROUTES.VENDOR.OFFERINGS_NEW} className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-blue-600 px-4 py-3 font-semibold text-white shadow-md hover:bg-blue-700">
                <Image src="/icons/vendor/dashboard/quick-package.svg" alt="" aria-hidden="true" width={18} height={18} className="h-[18px] w-[18px]" />
                Create New Package
              </Link>
              <Link href={ROUTES.VENDOR.OFFERINGS} className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 font-semibold text-slate-700 hover:bg-slate-50 inline-flex items-center justify-center gap-2">
                <Image src="/icons/vendor/dashboard/quick-inventory.svg" alt="" aria-hidden="true" width={18} height={18} className="h-[18px] w-[18px]" />
                Manage Offerings
              </Link>
              <Link href={ROUTES.VENDOR.ACTIVITIES} className="inline-flex w-full items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-3 font-semibold text-slate-700 hover:bg-slate-50">
                <Image src="/icons/vendor/dashboard/quick-delivery.svg" alt="" aria-hidden="true" width={18} height={18} className="h-[18px] w-[18px]" />
                Schedule Delivery
              </Link>
            </div>
          </section>

          <section className="rounded-2xl border border-slate-200 bg-white p-4 shadow-[0_4px_16px_rgba(15,23,42,0.06)] sm:p-5">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-base font-semibold text-slate-900">Top Recipient Types</h3>
              <button
                type="button"
                onClick={() => setIsRecipientReportOpen((previous) => !previous)}
                className="inline-flex items-center gap-1.5 text-sm font-semibold text-blue-700 hover:text-blue-800"
              >
                <Image src="/icons/vendor/dashboard/link-report.svg" alt="" aria-hidden="true" width={16} height={16} className="h-4 w-4" />
                {isRecipientReportOpen ? 'Hide Report' : 'View Report'}
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

            {isRecipientReportOpen ? (
              <div className="mt-4 rounded-xl border border-blue-100 bg-blue-50 px-4 py-3 text-sm text-slate-700">
                Birthday celebrations remain your strongest segment, while date-night packages are the clearest growth area for upcoming campaigns and featured offerings.
              </div>
            ) : null}
          </section>
        </div>
      </section>
    </VendorPortalShell>
  );
}
