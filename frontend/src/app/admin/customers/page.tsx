'use client';

import { useEffect, useMemo, useState } from 'react';
import {
  AlertCircle,
  CheckCircle2,
  ChevronRight,
  Loader2,
  Mail,
  Phone,
  RefreshCw,
  Search,
  ShieldAlert,
  Users,
} from 'lucide-react';
import { toast } from 'react-hot-toast';

import { userService } from '@/services/admin/userService';
import {
  AdminCustomer,
  CustomerAccountStatus,
} from '@/types/admin';

const STATUS_OPTIONS: Array<{
  value: 'ALL' | CustomerAccountStatus;
  label: string;
}> = [
  { value: 'ALL', label: 'All statuses' },
  { value: CustomerAccountStatus.ACTIVE, label: 'Active' },
  { value: CustomerAccountStatus.PENDING, label: 'Pending' },
  { value: CustomerAccountStatus.SUSPENDED, label: 'Suspended' },
  { value: CustomerAccountStatus.DISABLED, label: 'Disabled' },
];

const MANAGEABLE_STATUSES: CustomerAccountStatus[] = [
  CustomerAccountStatus.ACTIVE,
  CustomerAccountStatus.SUSPENDED,
  CustomerAccountStatus.DISABLED,
  CustomerAccountStatus.PENDING,
];

const PAGE_SIZE = 20;

function getStatusClasses(status: CustomerAccountStatus) {
  switch (status) {
    case CustomerAccountStatus.ACTIVE:
      return 'border border-emerald-200 bg-emerald-50 text-emerald-700';
    case CustomerAccountStatus.PENDING:
      return 'border border-amber-200 bg-amber-50 text-amber-700';
    case CustomerAccountStatus.SUSPENDED:
      return 'border border-orange-200 bg-orange-50 text-orange-700';
    case CustomerAccountStatus.DISABLED:
      return 'border border-rose-200 bg-rose-50 text-rose-700';
    default:
      return 'border border-gray-200 bg-gray-50 text-gray-700';
  }
}

function getStatusSummary(customers: AdminCustomer[]) {
  return customers.reduce(
    (acc, customer) => {
      acc.total += 1;
      acc[customer.status] += 1;
      return acc;
    },
    {
      total: 0,
      [CustomerAccountStatus.ACTIVE]: 0,
      [CustomerAccountStatus.PENDING]: 0,
      [CustomerAccountStatus.SUSPENDED]: 0,
      [CustomerAccountStatus.DISABLED]: 0,
    }
  );
}

export default function AdminCustomersPage() {
  const [customers, setCustomers] = useState<AdminCustomer[]>([]);
  const [selectedCustomerId, setSelectedCustomerId] = useState<string | null>(null);
  const [selectedCustomer, setSelectedCustomer] = useState<AdminCustomer | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<'ALL' | CustomerAccountStatus>('ALL');
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [listLoading, setListLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [statusSaving, setStatusSaving] = useState(false);
  const [listError, setListError] = useState<string | null>(null);
  const [statusDraft, setStatusDraft] = useState<CustomerAccountStatus>(
    CustomerAccountStatus.ACTIVE
  );

  const filteredCustomers = useMemo(() => {
    const query = searchTerm.trim().toLowerCase();

    return customers.filter((customer) => {
      if (!query) return true;

      return (
        customer.full_name.toLowerCase().includes(query) ||
        customer.email.toLowerCase().includes(query) ||
        customer.customer_id.toLowerCase().includes(query) ||
        (customer.phone ?? '').toLowerCase().includes(query)
      );
    });
  }, [customers, searchTerm]);

  const summary = useMemo(() => getStatusSummary(customers), [customers]);

  useEffect(() => {
    void loadCustomers(false);
  }, [statusFilter]);

  useEffect(() => {
    if (!selectedCustomerId && customers.length > 0) {
      void loadCustomerDetail(customers[0].customer_id);
    }
  }, [customers, selectedCustomerId]);

  useEffect(() => {
    if (selectedCustomer) {
      setStatusDraft(selectedCustomer.status);
    }
  }, [selectedCustomer]);

  async function loadCustomers(loadMore: boolean) {
    setListLoading(true);
    setListError(null);

    try {
      const response = await userService.getCustomers({
        status: statusFilter === 'ALL' ? undefined : statusFilter,
        limit: PAGE_SIZE,
        cursor: loadMore ? nextCursor ?? undefined : undefined,
      });

      const nextItems = response.items;

      setCustomers((current) => {
        if (!loadMore) return nextItems;

        const seen = new Set(current.map((item) => item.customer_id));
        return [...current, ...nextItems.filter((item) => !seen.has(item.customer_id))];
      });
      setNextCursor(response.nextCursor ?? null);

      const targetCustomerId =
        selectedCustomerId && nextItems.some((item) => item.customer_id === selectedCustomerId)
          ? selectedCustomerId
          : null;

      if (!loadMore && !targetCustomerId) {
        setSelectedCustomerId(nextItems[0]?.customer_id ?? null);
        setSelectedCustomer(nextItems[0] ?? null);
      }
    } catch (error) {
      console.error(error);
      setListError('Failed to load customers.');
      toast.error('Failed to load customers');
    } finally {
      setListLoading(false);
    }
  }

  async function loadCustomerDetail(customerId: string) {
    setSelectedCustomerId(customerId);
    setDetailLoading(true);

    try {
      const customer = await userService.getCustomerById(customerId);
      setSelectedCustomer(customer);
      setStatusDraft(customer.status);
    } catch (error) {
      console.error(error);
      toast.error('Failed to load customer details');
    } finally {
      setDetailLoading(false);
    }
  }

  async function handleStatusUpdate() {
    if (!selectedCustomer || statusDraft === selectedCustomer.status) return;

    setStatusSaving(true);

    try {
      const updatedCustomer = await userService.updateCustomerStatus(
        selectedCustomer.customer_id,
        { status: statusDraft }
      );

      setSelectedCustomer(updatedCustomer);
      setCustomers((current) =>
        current.map((customer) =>
          customer.customer_id === updatedCustomer.customer_id ? updatedCustomer : customer
        )
      );
      toast.success(`Customer status updated to ${updatedCustomer.status}`);
    } catch (error) {
      console.error(error);
      toast.error('Failed to update customer status');
    } finally {
      setStatusSaving(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="border-b border-gray-200 bg-white px-4 py-6 sm:px-8">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 sm:text-4xl">
              Customer Management
            </h1>
            <p className="mt-2 text-gray-600">
              Review customer accounts and update activation status from the admin portal.
            </p>
          </div>
          <button
            type="button"
            onClick={() => void loadCustomers(false)}
            className="inline-flex items-center justify-center gap-2 rounded-xl border border-gray-200 bg-white px-4 py-2.5 text-sm font-semibold text-gray-700 transition-colors hover:bg-gray-50"
          >
            <RefreshCw className="h-4 w-4" />
            Refresh list
          </button>
        </div>
      </div>

      <div className="mx-auto flex max-w-7xl flex-col gap-6 px-4 py-8 sm:px-8">
        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <div className="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-gray-100">
            <p className="text-sm font-medium text-gray-500">Loaded customers</p>
            <p className="mt-3 text-3xl font-bold text-gray-900">{summary.total}</p>
          </div>
          <div className="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-gray-100">
            <p className="text-sm font-medium text-gray-500">Active</p>
            <p className="mt-3 text-3xl font-bold text-emerald-600">
              {summary[CustomerAccountStatus.ACTIVE]}
            </p>
          </div>
          <div className="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-gray-100">
            <p className="text-sm font-medium text-gray-500">Pending</p>
            <p className="mt-3 text-3xl font-bold text-amber-600">
              {summary[CustomerAccountStatus.PENDING]}
            </p>
          </div>
          <div className="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-gray-100">
            <p className="text-sm font-medium text-gray-500">Restricted</p>
            <p className="mt-3 text-3xl font-bold text-rose-600">
              {summary[CustomerAccountStatus.SUSPENDED] + summary[CustomerAccountStatus.DISABLED]}
            </p>
          </div>
        </section>

        <section className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
          <div className="overflow-hidden rounded-3xl bg-white shadow-sm ring-1 ring-gray-100">
            <div className="border-b border-gray-100 p-5">
              <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                <div>
                  <h2 className="text-xl font-semibold text-gray-900">Customers</h2>
                  <p className="mt-1 text-sm text-gray-500">
                    Select an account to inspect details and change status.
                  </p>
                </div>

                <div className="flex flex-col gap-3 md:flex-row">
                  <label className="relative min-w-[260px]">
                    <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
                    <input
                      type="search"
                      value={searchTerm}
                      onChange={(event) => setSearchTerm(event.target.value)}
                      placeholder="Search name, email, phone, or customer ID"
                      className="w-full rounded-xl border border-gray-200 py-2.5 pl-10 pr-4 text-sm text-gray-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                    />
                  </label>

                  <select
                    value={statusFilter}
                    onChange={(event) =>
                      setStatusFilter(
                        event.target.value as 'ALL' | CustomerAccountStatus
                      )
                    }
                    className="rounded-xl border border-gray-200 px-4 py-2.5 text-sm font-medium text-gray-700 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                  >
                    {STATUS_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>

            <div className="max-h-[780px] overflow-y-auto">
              {listLoading ? (
                <div className="flex min-h-[320px] items-center justify-center gap-3 text-sm text-gray-500">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Loading customers
                </div>
              ) : listError ? (
                <div className="flex min-h-[320px] flex-col items-center justify-center px-6 text-center">
                  <AlertCircle className="h-12 w-12 text-rose-400" />
                  <p className="mt-4 text-lg font-semibold text-gray-900">
                    Unable to load customers
                  </p>
                  <p className="mt-2 max-w-sm text-sm text-gray-500">{listError}</p>
                </div>
              ) : filteredCustomers.length === 0 ? (
                <div className="flex min-h-[320px] flex-col items-center justify-center px-6 text-center">
                  <Users className="h-12 w-12 text-gray-300" />
                  <p className="mt-4 text-lg font-semibold text-gray-900">
                    No matching customers
                  </p>
                  <p className="mt-2 max-w-sm text-sm text-gray-500">
                    Try adjusting the status filter or search term.
                  </p>
                </div>
              ) : (
                <div className="divide-y divide-gray-100">
                  {filteredCustomers.map((customer) => {
                    const isSelected = customer.customer_id === selectedCustomerId;

                    return (
                      <button
                        key={customer.customer_id}
                        type="button"
                        onClick={() => void loadCustomerDetail(customer.customer_id)}
                        className={`flex w-full items-center gap-4 px-5 py-4 text-left transition ${
                          isSelected ? 'bg-blue-50/70' : 'hover:bg-gray-50'
                        }`}
                      >
                        <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-slate-900 text-sm font-bold text-white">
                          {customer.full_name
                            .split(' ')
                            .map((part) => part[0])
                            .join('')
                            .slice(0, 2)
                            .toUpperCase()}
                        </div>

                        <div className="min-w-0 flex-1">
                          <div className="flex flex-wrap items-center gap-2">
                            <p className="truncate font-semibold text-gray-900">
                              {customer.full_name}
                            </p>
                            <span
                              className={`rounded-full px-2.5 py-1 text-xs font-semibold ${getStatusClasses(customer.status)}`}
                            >
                              {customer.status}
                            </span>
                          </div>
                          <p className="truncate text-sm text-gray-500">{customer.email}</p>
                          <p className="mt-1 text-xs uppercase tracking-[0.14em] text-gray-400">
                            {customer.customer_id}
                          </p>
                        </div>

                        <ChevronRight className="h-4 w-4 shrink-0 text-gray-300" />
                      </button>
                    );
                  })}
                </div>
              )}
            </div>

            {nextCursor && !listLoading && !listError && (
              <div className="border-t border-gray-100 p-4">
                <button
                  type="button"
                  onClick={() => void loadCustomers(true)}
                  className="w-full rounded-xl border border-gray-200 px-4 py-3 text-sm font-semibold text-gray-700 transition-colors hover:bg-gray-50"
                >
                  Load more customers
                </button>
              </div>
            )}
          </div>

          <div className="rounded-3xl bg-white shadow-sm ring-1 ring-gray-100">
            <div className="border-b border-gray-100 p-5">
              <h2 className="text-xl font-semibold text-gray-900">Customer Details</h2>
              <p className="mt-1 text-sm text-gray-500">
                Activate, suspend, or disable the selected account.
              </p>
            </div>

            {detailLoading ? (
              <div className="flex min-h-[540px] items-center justify-center gap-3 text-sm text-gray-500">
                <Loader2 className="h-4 w-4 animate-spin" />
                Loading customer details
              </div>
            ) : !selectedCustomer ? (
              <div className="flex min-h-[540px] flex-col items-center justify-center px-6 text-center">
                <ShieldAlert className="h-12 w-12 text-gray-300" />
                <p className="mt-4 text-lg font-semibold text-gray-900">
                  Select a customer
                </p>
                <p className="mt-2 max-w-sm text-sm text-gray-500">
                  Customer details and account controls will appear here.
                </p>
              </div>
            ) : (
              <div className="space-y-6 p-5">
                <div className="rounded-2xl bg-slate-950 p-5 text-white">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <p className="text-sm uppercase tracking-[0.2em] text-slate-300">
                        Customer profile
                      </p>
                      <h3 className="mt-3 text-2xl font-semibold">
                        {selectedCustomer.full_name}
                      </h3>
                      <p className="mt-2 text-sm text-slate-300">
                        {selectedCustomer.customer_id}
                      </p>
                    </div>
                    <span
                      className={`rounded-full px-3 py-1.5 text-xs font-semibold ${getStatusClasses(
                        selectedCustomer.status
                      )}`}
                    >
                      {selectedCustomer.status}
                    </span>
                  </div>
                </div>

                <div className="grid gap-4 rounded-2xl border border-gray-100 p-5">
                  <div className="flex items-start gap-3">
                    <Mail className="mt-0.5 h-4 w-4 text-gray-400" />
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-[0.16em] text-gray-400">
                        Email
                      </p>
                      <p className="mt-1 text-sm font-medium text-gray-900">
                        {selectedCustomer.email}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start gap-3">
                    <Phone className="mt-0.5 h-4 w-4 text-gray-400" />
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-[0.16em] text-gray-400">
                        Phone
                      </p>
                      <p className="mt-1 text-sm font-medium text-gray-900">
                        {selectedCustomer.phone || 'Not provided'}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start gap-3">
                    <CheckCircle2 className="mt-0.5 h-4 w-4 text-gray-400" />
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-[0.16em] text-gray-400">
                        Locale
                      </p>
                      <p className="mt-1 text-sm font-medium text-gray-900">
                        {selectedCustomer.locale || 'Not set'}
                      </p>
                    </div>
                  </div>
                </div>

                <div className="rounded-2xl border border-gray-100 p-5">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <h4 className="text-lg font-semibold text-gray-900">
                        Account status
                      </h4>
                      <p className="mt-1 text-sm text-gray-500">
                        Use `ACTIVE` to reactivate. Use `SUSPENDED` or `DISABLED` to deactivate access.
                      </p>
                    </div>
                  </div>

                  <div className="mt-5 space-y-4">
                    <label className="block">
                      <span className="mb-2 block text-sm font-medium text-gray-700">
                        New status
                      </span>
                      <select
                        value={statusDraft}
                        onChange={(event) =>
                          setStatusDraft(event.target.value as CustomerAccountStatus)
                        }
                        className="w-full rounded-xl border border-gray-200 px-4 py-3 text-sm font-medium text-gray-800 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                      >
                        {MANAGEABLE_STATUSES.map((status) => (
                          <option key={status} value={status}>
                            {status}
                          </option>
                        ))}
                      </select>
                    </label>

                    <div className="rounded-xl bg-amber-50 px-4 py-3 text-sm text-amber-800">
                      Changes apply immediately after confirmation.
                    </div>

                    <div className="flex flex-col gap-3 sm:flex-row">
                      <button
                        type="button"
                        onClick={handleStatusUpdate}
                        disabled={statusSaving || statusDraft === selectedCustomer.status}
                        className="inline-flex flex-1 items-center justify-center gap-2 rounded-xl bg-blue-600 px-4 py-3 text-sm font-semibold text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-blue-300"
                      >
                        {statusSaving ? (
                          <>
                            <Loader2 className="h-4 w-4 animate-spin" />
                            Saving
                          </>
                        ) : (
                          'Update status'
                        )}
                      </button>

                      <button
                        type="button"
                        onClick={() => setStatusDraft(selectedCustomer.status)}
                        disabled={statusSaving || statusDraft === selectedCustomer.status}
                        className="inline-flex flex-1 items-center justify-center rounded-xl border border-gray-200 px-4 py-3 text-sm font-semibold text-gray-700 transition-colors hover:bg-gray-50 disabled:cursor-not-allowed disabled:text-gray-400"
                      >
                        Reset
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
