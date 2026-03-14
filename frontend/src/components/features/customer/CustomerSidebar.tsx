'use client';

import Image from 'next/image';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

type CustomerSidebarProps = {
  isOpen: boolean;
};

const CustomerSidebar = ({ isOpen }: CustomerSidebarProps) => {
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
      className={`fixed left-0 top-0 z-40 h-screen w-[240px] max-w-[85vw] overflow-y-auto border-r border-[#ECECF0] bg-[#FFFFFF] px-4 py-5 transition-transform duration-300 ${
        isOpen ? 'translate-x-0' : '-translate-x-full'
      } lg:translate-x-0`}
    >
      <div className="mb-8 flex items-center gap-2">
        <Image src="/icons/logo.svg" alt="Occacia" width={59} height={59} className="ml-[-8px] h-[59px] w-[59px] shrink-0" />
        <span className="text-[22px] font-extrabold tracking-tight text-[#1562CC]">OCCACIA</span>
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

      <div className="absolute bottom-8 left-4 right-4 flex items-center gap-3 rounded-2xl bg-[#EEF0F7] px-4 py-4">
        <span className="inline-flex h-12 w-12 items-center justify-center overflow-hidden rounded-full bg-[#F4CE95]">
          <Image
            src="/icons/customer/dashboard/profile.svg"
            alt="Alex Rivera"
            width={48}
            height={48}
            className="h-full w-full object-contain"
          />
        </span>
        <p className="text-[17px] font-semibold leading-none text-[#182039]">Alex Rivera</p>
      </div>
    </aside>
  );
};

export default CustomerSidebar;