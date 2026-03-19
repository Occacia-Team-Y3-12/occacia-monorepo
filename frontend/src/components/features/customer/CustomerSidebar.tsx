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

    return pathname === href || pathname.startsWith(`${href}/`);
  };

  const navItems = [
    { href: '/customer/dashboard', label: 'Dashboard', icon: '/icons/customer/dashboard/dashboard.svg' },
    { href: '/customer/events', label: 'My Events', icon: '/icons/customer/dashboard/my_events.svg' },
    { href: '/customer/people', label: 'People', icon: '/icons/customer/dashboard/people.svg' },
    { href: '/customer/settings', label: 'Settings', icon: '/icons/customer/dashboard/settings.svg' },
  ];

  return (
    <aside
      className={`fixed left-0 top-0 z-40 flex h-screen w-[240px] max-w-[85vw] flex-col overflow-y-auto border-r border-[#ECECF0] bg-[#FFFFFF] px-4 py-5 transition-transform duration-300 ${
        isOpen ? 'translate-x-0' : '-translate-x-full'
      } ${isDesktopCollapsed ? 'lg:-translate-x-full' : 'lg:translate-x-0'}`}
    >
      <div className="mb-8 flex items-center gap-2">
        <Image src="/icons/logo.svg" alt="Occacia" width={59} height={59} className="ml-[-8px] h-[59px] w-[59px] shrink-0" />
        <span className="text-[22px] font-extrabold tracking-tight text-[#1562CC]">OCCACIA</span>
        <button
          type="button"
          onClick={onToggleDesktopSidebar}
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

      <nav className="space-y-2">
        {navItems.map((item) => (
          
          <Link
            key={item.href}
            href={item.href}
            className={`group flex items-center gap-3 rounded-xl px-3 py-3 text-[15px] font-medium transition-all duration-200 ${
              isActivePath(item.href)
                ? 'bg-[#EBE5FF] text-[#3A2B68] shadow-[0_2px_8px_rgba(58,43,104,0.08)]'
                : 'text-[#667085] hover:bg-[#F0F1F6] hover:text-[#3A2B68] hover:translate-x-[2px]'
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

      <div className="mt-auto w-[190px] rounded-lg bg-[#EFF1F5] px-2.5 py-2.5">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-[0.08em] text-[#92A0B5]">Plan Usage</p>
          <div className="mt-2 h-2.5 w-[150px] rounded-full bg-[#D1D7E2]">
            <div className="h-full w-3/5 rounded-full bg-[#4C24D6]" />
          </div>
          <p className="mt-2 text-[11px] font-medium leading-none text-[#5F708D]">6 of 10 events used</p>
        </div>
      </div>

    </aside>
  );
};

export default CustomerSidebar;