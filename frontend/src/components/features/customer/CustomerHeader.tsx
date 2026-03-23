'use client';

import { useEffect, useRef, useState } from 'react';
import Image from 'next/image';
import { usePathname, useRouter } from 'next/navigation';
import { toast } from 'sonner';

import { useCustomerAuth } from '@/app/context/AuthContext';
import { ROUTES } from '@/lib/routes';

type CustomerHeaderProps = {
  isSidebarOpen: boolean;
  isDesktopSidebarCollapsed: boolean;
  onToggleSidebar: () => void;
  onToggleDesktopSidebar: () => void;
};

const CustomerHeader = ({ isSidebarOpen, isDesktopSidebarCollapsed, onToggleSidebar, onToggleDesktopSidebar }: CustomerHeaderProps) => {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useCustomerAuth();
  const [isProfileMenuOpen, setIsProfileMenuOpen] = useState(false);
  const [savedEventTitle, setSavedEventTitle] = useState("Sister's Birthday");

  const handleLogout = async () => {
    try {
      await logout();
      setIsProfileMenuOpen(false);
      router.replace(ROUTES.CUSTOMER.LOGIN);
    } catch (error) {
      toast.error(
        error instanceof Error && error.message
          ? error.message
          : 'Logout failed. Please try again.'
      );
    }
  };
  const profileMenuRef = useRef<HTMLDivElement>(null);

  const isEventsRootPage = pathname === '/customer/events' || pathname === '/customer/events/new';
  const isEventDetailPage = pathname.startsWith('/customer/events/') && pathname !== '/customer/events/new';
  const isEventFlow = isEventsRootPage || isEventDetailPage;

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (profileMenuRef.current && !profileMenuRef.current.contains(event.target as Node)) {
        setIsProfileMenuOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  useEffect(() => {
    if (!isEventDetailPage) {
      return;
    }

    const title = window.sessionStorage.getItem('customer:lastEventTitle');
    if (title && title.trim()) {
      setSavedEventTitle(title.trim());
    }
  }, [isEventDetailPage]);

  return (
    <header
      className={`flex border-b border-[#EAEAEA] bg-[#FFFFFF] px-4 transition-all duration-300 sm:px-6 ${
        isDesktopSidebarCollapsed ? 'lg:ml-0' : 'lg:ml-[240px]'
      } ${
        isEventFlow
          ? 'min-h-[92px] flex-wrap items-center justify-between py-2 sm:py-0'
          : 'min-h-[88px] items-center justify-between py-3 sm:py-0'
      }`}
    >
      <div
        className={`order-1 flex items-center gap-3 sm:gap-5 ${
          isEventFlow ? 'w-auto flex-nowrap' : 'w-auto flex-row'
        }`}
      >
        {isDesktopSidebarCollapsed && (
          <div className="-ml-2 group relative hidden shrink-0 items-center gap-0 lg:flex">
            <button
              type="button"
              onClick={onToggleDesktopSidebar}
              className="relative h-14 w-14 overflow-hidden rounded-xl"
              aria-label="Open sidebar"
            >
              <Image src="/icons/logo.svg" alt="Occacia" width={56} height={56} className="h-14 w-14" />
              <span className="absolute inset-0 inline-flex items-center justify-center opacity-0 transition-opacity duration-150 group-hover:opacity-100 group-focus-within:opacity-100 group-active:opacity-100">
                <span className="inline-flex h-10 w-10 items-center justify-center rounded-xl border border-[#CCCCCC] bg-[#FFFFFF] text-[#666666]">
                  <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round">
                    <rect x="3.5" y="4.5" width="17" height="15" rx="2.5" />
                    <path d="M9 4.5v15" />
                    <path d="M13 9.5 16 12l-3 2.5" />
                  </svg>
                </span>
              </span>
            </button>
            <span className="whitespace-nowrap text-[26px] font-bold tracking-normal text-[#0D47A1]">Occacia</span>
            <span
              className="pointer-events-none absolute left-7 top-full z-50 mt-2 -translate-x-1/2 whitespace-nowrap rounded-2xl bg-black px-3 py-1.5 text-[13px] font-medium text-white opacity-0 shadow-[0_8px_18px_rgba(17,24,39,0.35)] transition-opacity duration-150 group-hover:opacity-100 group-focus-within:opacity-100"
              aria-hidden="true"
            >
              Open sidebar
            </span>
          </div>
        )}

        {isSidebarOpen ? (
          <button
            onClick={onToggleSidebar}
            className="inline-flex h-10 w-10 items-center justify-center rounded-xl border border-[#CCCCCC] bg-[#FFFFFF] text-[#666666] lg:hidden"
            aria-label="Close sidebar"
          >
            <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M6 6l12 12M18 6 6 18" />
            </svg>
          </button>
        ) : (
          <button onClick={onToggleSidebar} className="-ml-2 flex shrink-0 items-center gap-1 self-start lg:hidden" aria-label="Open sidebar">
            <Image src="/icons/logo.svg" alt="Occacia" width={59} height={59} className="h-[59px] w-[59px]" />
            <span className="whitespace-nowrap text-[26px] font-bold tracking-normal text-[#0D47A1]">Occacia</span>
          </button>
        )}

        <div className={`h-14 min-w-0 shrink items-center rounded-xl border border-transparent px-1 ${isEventFlow ? 'hidden sm:flex' : 'flex'}`}>
          {isEventFlow ? (
          <p className="inline-flex min-w-0 items-center overflow-hidden whitespace-nowrap text-[16px] leading-[1] text-[#666666]">
              <span className="font-medium text-[#0D47A1]">Events</span>
              <span className="px-2 leading-[1] text-[#666666]">&gt;</span>
              <span className="truncate font-semibold leading-[1] text-[#0D47A1]">{isEventsRootPage ? 'Create New Event' : savedEventTitle}</span>
            </p>
          ) : (
            <></>
          )}
        </div>
      </div>

      <div className={`order-2 flex items-center justify-end ${isEventFlow ? 'w-auto gap-5' : 'w-auto gap-3 sm:gap-5'}`}>
        <button
          aria-label="Notifications"
          className="relative flex h-14 w-14 items-center justify-center rounded-3xl bg-[#F4F8FA]"
        >
          <svg viewBox="0 0 24 24" className="h-7 w-7 text-[#666666]" fill="none" stroke="currentColor" strokeWidth={1.8}>
            <path d="M14.857 17.082a2.857 2.857 0 0 1-5.714 0" />
            <path d="M6.286 8.51a5.714 5.714 0 1 1 11.428 0v4.248l1.143 2.286v1.143H5.143V15.04l1.143-2.286V8.51Z" />
          </svg>
          <span className="absolute right-4 top-3.5 h-2.5 w-2.5 rounded-full bg-[#4285F4]" />
        </button>

        {isEventFlow && <span className="h-10 w-px bg-[#EAEAEA]" aria-hidden="true" />}

        {!isEventFlow && <span className="h-14 w-px bg-[#EAEAEA]" aria-hidden="true" />}

        <div className="relative" ref={profileMenuRef}>
          <button
            onClick={() => setIsProfileMenuOpen((prev) => !prev)}
            className={`flex items-center ${isEventFlow ? 'gap-4 pl-1' : 'gap-4'}`}
            aria-label="Open profile menu"
          >
            <span className={`${isEventFlow ? 'hidden md:inline' : 'hidden sm:inline'} whitespace-nowrap text-[17px] font-semibold text-[#0D47A1]`}>{user?.fullName || user?.username || 'Account'}</span>
            <span className="inline-flex h-12 w-12 items-center justify-center overflow-hidden rounded-full border-[3px] border-[#FFFFFF] bg-[#F4F8FA] shadow-[0_6px_18px_rgba(13,71,161,0.18)]">
              <Image
                src="/icons/customer/dashboard/profile.svg"
                alt="Alex Rivers"
                width={48}
                height={48}
                className="h-full w-full object-contain"
              />
            </span>
          </button>

          {isProfileMenuOpen && (
            <div className="absolute right-0 top-full z-50 mt-2 w-44 rounded-xl border border-[#EAEAEA] bg-[#FFFFFF] p-2 shadow-[0_14px_28px_rgba(13,71,161,0.12)]">
              <button className="w-full rounded-lg px-3 py-2 text-left text-sm font-medium text-[#666666] transition-colors hover:bg-[#F4F8FA]">
                My Profile
              </button>
              <button onClick={handleLogout} className="mt-1 w-full rounded-lg px-3 py-2 text-left text-sm font-medium text-[#EA4335] transition-colors hover:bg-[#FAFAFA]">
                Logout
              </button>
            </div>
          )}
        </div>
      </div>

      {isEventFlow && (
        <div className="order-3 w-full pb-1 pl-2 sm:hidden">
          <p className="inline-flex min-w-0 items-center overflow-hidden whitespace-nowrap text-[14px] leading-[1] text-[#666666]">
            <span className="font-medium text-[#0D47A1]">Events</span>
            <span className="px-2 leading-[1] text-[#666666]">&gt;</span>
            <span className="truncate font-semibold leading-[1] text-[#0D47A1]">{isEventsRootPage ? 'Create New Event' : savedEventTitle}</span>
          </p>
        </div>
      )}
    </header>
  );
};

export default CustomerHeader;
