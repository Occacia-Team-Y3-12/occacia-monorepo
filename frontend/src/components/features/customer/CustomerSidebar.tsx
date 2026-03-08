'use client';

import Image from 'next/image';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

type CustomerSidebarProps = {
  isOpen: boolean;
};

const CustomerSidebar = ({ isOpen }: CustomerSidebarProps) => {
  const pathname = usePathname();

  const navItems = [
    { href: '/customer/dashboard', label: 'Dashboard', icon: '/icons/customer/dashboard/dashboard.svg' },
    { href: '/customer/events', label: 'My Events', icon: '/icons/customer/dashboard/my_events.svg' },
    { href: '/customer/people', label: 'People', icon: '/icons/customer/dashboard/peoples.svg' },
    { href: '/customer/settings', label: 'Settings', icon: '/icons/customer/dashboard/settings.svg' },
  ];

  return (
    <aside
      className={`fixed left-0 top-0 z-40 h-screen w-[240px] max-w-[85vw] overflow-y-auto border-r border-[#ECECF0] bg-[#F5F5F8] px-4 py-5 transition-transform duration-300 ${
        isOpen ? 'translate-x-0' : '-translate-x-full'
      }`}
    >
      <div className="mb-8 flex items-center gap-3 px-2">
        <Image src="/icons/logo.svg" alt="Occacia" width={59} height={59} className="h-[59px] w-[59px]" />
        <span className="text-[22px] font-extrabold tracking-tight text-[#1562CC]">OCCACIA</span>
      </div>

      <nav className="space-y-2">
        {navItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={`flex items-center gap-3 rounded-xl px-3 py-3 text-[15px] font-medium transition-colors ${
              pathname === item.href
                ? 'bg-[#EBE5FF] text-[#3A2B68]'
                : 'text-[#667085] hover:bg-[#F0F1F6] hover:text-[#3A2B68]'
            }`}
          >
            <Image src={item.icon} alt="" width={18} height={18} className="h-[18px] w-[18px] opacity-80" />
            <span>{item.label}</span>
          </Link>
        ))}
      </nav>

      <div className="absolute bottom-20 left-4 right-4 rounded-2xl bg-[#EEF0F7] px-4 py-3">
        <p className="text-[11px] font-semibold uppercase tracking-wide text-[#7180A8]">Plan Usage</p>
        <div className="mt-2 h-1.5 rounded-full bg-[#D9DFEE]">
          <div className="h-1.5 w-[60%] rounded-full bg-[#8EA0C9]" />
        </div>
        <p className="mt-2 text-[11px] text-[#7B859C]">6 of 10 events used</p>
      </div>

      <button className="absolute bottom-8 left-7 text-sm font-medium text-[#6E7381] transition-colors hover:text-[#3A2B68]">
        Logout
      </button>
    </aside>
  );
};

export default CustomerSidebar;