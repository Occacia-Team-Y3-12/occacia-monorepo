'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';

import { ROUTES } from '@/lib/routes';
import { dashboardService } from '@/services/admin/dashboardService';
import type { AdminDashboardMetricsResponse, HealthStatusResponse } from '@/types/admin';

type DashboardCard = {
  label: string;
  value: number;
  subLabel: string;
  href: string;
};

export default function AdminDashboardPage() {
  const [metrics, setMetrics] = useState<AdminDashboardMetricsResponse | null>(null);
  const [health, setHealth] = useState<HealthStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const [dashboardData, healthData] = await Promise.all([
          dashboardService.getAdminDashboardMetrics(),
          dashboardService.getHealthStatus(),
        ]);
        if (!cancelled) {
          setMetrics(dashboardData);
          setHealth(healthData);
        }
      } catch {
        if (!cancelled) {
          setError('Failed to load admin dashboard metrics.');
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, []);

  const cards = useMemo<DashboardCard[]>(() => {
    if (!metrics) return [];
    return [
      {
        label: 'Pending Vendors',
        value: metrics.vendors.pending,
        subLabel: `Total vendors: ${metrics.vendors.total}`,
        href: ROUTES.ADMIN.PENDING_VENDORS,
      },
      {
        label: 'Customers',
        value: metrics.users.active,
        subLabel: `Pending users: ${metrics.users.pending}`,
        href: ROUTES.ADMIN.CUSTOMERS,
      },
      {
        label: 'User Management',
        value: metrics.users.total,
        subLabel: `Active users: ${metrics.users.active}`,
        href: ROUTES.ADMIN.USERS,
      },
      {
        label: 'Settings / System',
        value: metrics.events.total,
        subLabel: `Orders pending: ${metrics.packageOrders.pending}`,
        href: ROUTES.ADMIN.SETTINGS,
      },
    ];
  }, [metrics]);

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Admin Dashboard</h1>
        <p className="mt-2 text-gray-600">System-wide metrics and quick actions for operations.</p>
      </div>

      {loading ? (
        <div className="rounded-2xl border border-gray-200 bg-white p-8 text-sm text-gray-600">
          Loading dashboard...
        </div>
      ) : error ? (
        <div className="rounded-2xl border border-red-200 bg-red-50 p-8 text-sm text-red-700">
          {error}
        </div>
      ) : (
        <>
          <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {cards.map((card) => (
              <Link
                key={card.label}
                href={card.href}
                className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm transition hover:border-blue-300 hover:shadow"
              >
                <p className="text-sm font-medium text-gray-500">{card.label}</p>
                <p className="mt-3 text-3xl font-bold text-gray-900">{card.value}</p>
                <p className="mt-2 text-xs text-gray-500">{card.subLabel}</p>
              </Link>
            ))}
          </section>

          <section className="mt-6 grid gap-4 lg:grid-cols-2">
            <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
              <h2 className="text-lg font-semibold text-gray-900">System Health</h2>
              <div className="mt-4 space-y-2 text-sm text-gray-700">
                <p>Status: {health?.status ?? 'unknown'}</p>
                <p>System: {health?.system ?? 'unknown'}</p>
                <p>Version: {health?.version ?? 'unknown'}</p>
                <p>Uptime: {health?.uptimeSeconds ?? 0}s</p>
              </div>
            </div>

            <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
              <h2 className="text-lg font-semibold text-gray-900">Snapshot</h2>
              <div className="mt-4 space-y-2 text-sm text-gray-700">
                <p>Users: {metrics?.users.total ?? 0}</p>
                <p>Vendors: {metrics?.vendors.total ?? 0}</p>
                <p>Events: {metrics?.events.total ?? 0}</p>
                <p>Package Orders: {metrics?.packageOrders.total ?? 0}</p>
                <p className="pt-2 text-xs text-gray-500">
                  Generated at: {metrics?.generatedAt ? new Date(metrics.generatedAt).toLocaleString() : 'N/A'}
                </p>
              </div>
            </div>
          </section>
        </>
      )}
    </div>
  );
}
