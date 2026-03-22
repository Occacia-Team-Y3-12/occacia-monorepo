'use client';

import { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import Image from 'next/image';
import { ROUTES } from '@/lib/routes';
import Modal from '@/components/ui/Modal';

type VendorPortalShellProps = {
  children: React.ReactNode;
};

type SidebarItem = {
  label: string;
  href: string;
  icon: string;
  badge?: number;
};

const sidebarItems: SidebarItem[] = [
  { label: 'Dashboard', href: ROUTES.VENDOR.DASHBOARD, icon: '/icons/vendor/dashboard/dashboard.svg' },
  { label: 'Activities', href: ROUTES.VENDOR.ACTIVITIES, icon: '/icons/vendor/dashboard/calendar.svg' },
  { label: 'Offerings', href: ROUTES.VENDOR.OFFERINGS, icon: '/icons/vendor/dashboard/clipboard.svg' },
  { label: 'Orders', href: ROUTES.VENDOR.ORDERS, icon: '/icons/vendor/dashboard/shopping-cart.svg', badge: 12 },
  { label: 'Products', href: ROUTES.VENDOR.PRODUCTS, icon: '/icons/vendor/dashboard/users.svg' },
  { label: 'Tasks', href: ROUTES.VENDOR.TASKS, icon: '/icons/vendor/dashboard/calendar.svg' },
];

export default function VendorPortalShell({ children }: VendorPortalShellProps) {
  const router = useRouter();
  const pathname = usePathname();
  const [isProfileMenuOpen, setIsProfileMenuOpen] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isDesktopSidebarCollapsed, setIsDesktopSidebarCollapsed] = useState(false);
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

  const isSidebarItemActive = (href: string) => {
    if (href === ROUTES.VENDOR.DASHBOARD) {
      return pathname === href;
    }

    return pathname === href || pathname.startsWith(`${href}/`);
  };

  return (
    <div className="min-h-screen bg-[#f4f6fb] text-slate-900">
      <div className="mx-auto flex w-full max-w-[1600px]">
        <aside
          className={`fixed inset-y-0 left-0 z-40 flex w-[250px] shrink-0 flex-col border-r border-slate-200 bg-white px-4 py-2 transform transition-transform duration-300 lg:static lg:min-h-screen lg:translate-x-0 ${
            isSidebarOpen ? 'translate-x-0' : '-translate-x-full'
          } ${isDesktopSidebarCollapsed ? 'lg:hidden' : 'lg:flex lg:relative'}`}
        >
          <div className="mb-2 flex items-center gap-0 py-1">
            <Image src="/icons/logo.svg" alt="Occacia" width={59} height={59} className="ml-[-8px] h-[59px] w-[59px] shrink-0" priority />
            <span className="text-[26px] font-bold tracking-normal text-[#0D47A1]">Occacia</span>
            <button
              type="button"
              onClick={() => setIsDesktopSidebarCollapsed(true)}
              className="ml-auto hidden h-10 w-10 items-center justify-center rounded-xl border border-[#E2E5EC] bg-white text-[#5B6478] lg:inline-flex"
              aria-label="Close sidebar"
            >
              <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3.5" y="4.5" width="17" height="15" rx="2.5" />
                <path d="M9 4.5v15" />
                <path d="M16 9.5 13 12l3 2.5" />
              </svg>
            </button>
          </div>

          <nav className="mt-6 space-y-1">
            {sidebarItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setIsSidebarOpen(false)}
                className={`flex w-full items-center justify-between rounded-xl px-3 py-3 text-left text-base transition-colors xl:text-[18px] ${
                  isSidebarItemActive(item.href)
                    ? 'bg-blue-50 text-blue-700'
                    : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                <span className="flex items-center gap-3 font-medium">
                  <Image src={item.icon} alt="" width={20} height={20} className="h-5 w-5 opacity-90" />
                  {item.label}
                </span>
                {item.badge ? (
                  <span className="rounded-full bg-blue-600 px-2 py-0.5 text-xs font-semibold text-white">{item.badge}</span>
                ) : null}
              </Link>
            ))}
          </nav>
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
                {isDesktopSidebarCollapsed && (
                  <div className="-ml-2 group relative hidden shrink-0 items-center gap-1 lg:flex">
                    <button
                      type="button"
                      onClick={() => setIsDesktopSidebarCollapsed(false)}
                      className="relative h-14 w-14 overflow-hidden rounded-xl"
                      aria-label="Open sidebar"
                    >
                      <Image src="/icons/logo.svg" alt="Occacia" width={56} height={56} className="h-14 w-14" />
                      <span className="absolute inset-0 inline-flex items-center justify-center bg-white/85 text-[#5B6478] opacity-0 transition-opacity duration-150 group-hover:opacity-100">
                        <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round">
                          <rect x="3.5" y="4.5" width="17" height="15" rx="2.5" />
                          <path d="M9 4.5v15" />
                          <path d="M13 9.5 16 12l-3 2.5" />
                        </svg>
                      </span>
                    </button>
                    <span className="whitespace-nowrap text-[26px] font-bold tracking-normal text-[#0D47A1]">Occacia</span>
                  </div>
                )}

                {isSidebarOpen ? (
                  <button
                    type="button"
                    onClick={() => setIsSidebarOpen(false)}
                    className="inline-flex h-10 w-10 items-center justify-center rounded-xl border border-[#E2E5EC] bg-white text-[#5B6478] lg:hidden"
                    aria-label="Close sidebar"
                  >
                    <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M6 6l12 12M18 6 6 18" />
                    </svg>
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={() => setIsSidebarOpen(true)}
                    className="-ml-2 flex shrink-0 items-center gap-1 self-start lg:hidden"
                    aria-label="Open sidebar"
                  >
                    <Image src="/icons/logo.svg" alt="Occacia" width={59} height={59} className="h-[59px] w-[59px]" />
                    <span className="whitespace-nowrap text-[26px] font-bold tracking-normal text-[#0D47A1]">Occacia</span>
                  </button>
                )}

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
            {children}
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
