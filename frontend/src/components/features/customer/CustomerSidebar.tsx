'use client';

import Image from 'next/image';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

type CustomerSidebarProps = {
  isOpen: boolean;
  isDesktopCollapsed: boolean;
  onToggleDesktopSidebar: () => void;
};

const CustomerSidebar = ({ isOpen, isDesktopCollapsed, onToggleDesktopSidebar }: CustomerSidebarProps) => {
  const pathname = usePathname();

  const isActivePath = (href: string): boolean => {
    if (href === '/customer/dashboard') {
      return pathname === href;
    }

    if (href === '/customer/events') {
      return pathname === href || (pathname.startsWith('/customer/events/') && pathname !== '/customer/events/new');
    }

    return pathname === href || pathname.startsWith(`${href}/`);
  };

  const navItems = [
    { href: '/customer/dashboard', label: 'Dashboard', icon: '/icons/customer/dashboard/dashboard.svg' },
    { href: '/customer/events', label: 'My Events', icon: '/icons/customer/dashboard/my_events.svg' },
    { href: '/customer/persona', label: 'People', icon: '/icons/customer/dashboard/people.svg' },
    { href: '/customer/settings', label: 'Settings', icon: '/icons/customer/dashboard/settings.svg' },
  ];

  return (
    <aside
      className={`fixed left-0 top-0 z-40 flex h-screen w-[240px] max-w-[85vw] flex-col overflow-y-auto border-r border-[#EAEAEA] bg-[#FFFFFF] px-4 py-5 transition-transform duration-300 ${
        isOpen ? 'translate-x-0' : '-translate-x-full'
      } ${isDesktopCollapsed ? 'lg:-translate-x-full' : 'lg:translate-x-0'}`}
    >
      <div className="mb-8 flex items-center gap-0">
        <Image src="/icons/logo.svg" alt="Occacia" width={59} height={59} className="ml-[-8px] h-[59px] w-[59px] shrink-0" />
        <span className="text-[26px] font-bold tracking-normal text-[#0D47A1]">Occacia</span>
        <div className="group relative ml-auto hidden lg:block">
          <button
            type="button"
            onClick={onToggleDesktopSidebar}
            className="h-10 w-10 items-center justify-center rounded-xl border border-[#CCCCCC] bg-[#FFFFFF] text-[#666666] lg:inline-flex"
            aria-label="Close sidebar"
          >
            <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3.5" y="4.5" width="17" height="15" rx="2.5" />
              <path d="M9 4.5v15" />
              <path d="M16 9.5 13 12l3 2.5" />
            </svg>
          </button>
          <span
            className="pointer-events-none absolute right-0 top-full z-50 mt-2 whitespace-nowrap rounded-2xl bg-black px-3 py-1.5 text-[13px] font-medium text-white opacity-0 shadow-[0_8px_18px_rgba(17,24,39,0.35)] transition-opacity duration-150 group-hover:opacity-100 group-focus-within:opacity-100"
            aria-hidden="true"
          >
            Close sidebar
          </span>
        </div>
      </div>

      <nav className="space-y-2">
        {navItems.map((item) => (
          
          <Link
            key={item.href}
            href={item.href}
              className={`group flex items-center gap-3 rounded-xl px-3 py-3 text-[15px] font-medium transition-all duration-200 ${
              isActivePath(item.href)
                ? 'bg-[#F4F8FA] text-[#0D47A1] shadow-[0_2px_8px_rgba(13,71,161,0.1)]'
                : 'text-[#666666] hover:bg-[#FAFAFA] hover:text-[#4285F4] hover:translate-x-[2px]'
            }`}
          >
            <Image
              src={item.icon}
              alt=""
              width={18}
              height={18}
              className={`h-[18px] w-[18px] transition-opacity duration-200 ${
                isActivePath(item.href) ? 'opacity-100' : 'opacity-80 group-hover:opacity-100'
              }`}
            />
            <span>{item.label}</span>
          </Link>
        ))}
      </nav>

      <div className="mt-auto w-[190px] rounded-lg bg-[#F4F8FA] px-2.5 py-2.5">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-[0.08em] text-[#666666]">Plan Usage</p>
          <div className="mt-2 h-2.5 w-[150px] rounded-full bg-[#EAEAEA]">
            <div className="h-full w-3/5 rounded-full bg-gradient-to-r from-[#0D47A1] to-[#4285F4]" />
          </div>
          <p className="mt-2 text-[11px] font-medium leading-none text-[#666666]">6 of 10 events used</p>
        </div>
      </div>

    </aside>
  );
};

export default CustomerSidebar;
