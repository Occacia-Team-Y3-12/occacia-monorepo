'use client';

import { useEffect, useRef, useState } from 'react';
import Image from 'next/image';

type CustomerHeaderProps = {
  isSidebarOpen: boolean;
  onToggleSidebar: () => void;
};

const CustomerHeader = ({ isSidebarOpen, onToggleSidebar }: CustomerHeaderProps) => {
  const [isProfileMenuOpen, setIsProfileMenuOpen] = useState(false);
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

  return (
    <header
      className="flex min-h-[88px] flex-col gap-3 border-b border-[#ECECF0] bg-[#F7F7FA] px-4 py-3 transition-all duration-300 sm:flex-row sm:items-center sm:justify-between sm:px-6 sm:py-0 lg:ml-[240px]"
    >
      <div className="flex w-full flex-col gap-2 sm:w-auto sm:flex-row sm:items-center sm:gap-5">
        {isSidebarOpen ? (
          <button
            onClick={onToggleSidebar}
            className="inline-flex h-10 w-10 items-center justify-center rounded-xl border border-[#E2E5EC] bg-white text-[#5B6478] lg:hidden"
            aria-label="Close sidebar"
          >
            <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M6 6l12 12M18 6 6 18" />
            </svg>
          </button>
        ) : (
          <button onClick={onToggleSidebar} className="flex shrink-0 items-center gap-3 self-start lg:hidden" aria-label="Open sidebar">
            <Image src="/icons/logo.svg" alt="Occacia" width={59} height={59} className="h-[59px] w-[59px]" />
            <span className="whitespace-nowrap text-[22px] font-extrabold tracking-tight text-[#1562CC]">OCCACIA</span>
          </button>
        )}

        <div className="relative w-full sm:w-[320px] md:w-[360px]">
          <input
            type="search"
            placeholder="Search events,people.."
            className="h-11 w-full rounded-full border border-[#E2E5EC] bg-[#EFF1F6] px-5 text-sm text-[#4A4F5C] outline-none placeholder:text-[#99A0AF]"
          />
        </div>
      </div>

      <div className="flex w-full items-center justify-end gap-3 sm:w-auto sm:gap-5">
        <button
          aria-label="Notifications"
          className="relative flex h-14 w-14 items-center justify-center rounded-3xl bg-[#EEF1F6]"
        >
          <svg viewBox="0 0 24 24" className="h-7 w-7 text-[#5B6478]" fill="none" stroke="currentColor" strokeWidth="1.8">
            <path d="M14.857 17.082a2.857 2.857 0 0 1-5.714 0" />
            <path d="M6.286 8.51a5.714 5.714 0 1 1 11.428 0v4.248l1.143 2.286v1.143H5.143V15.04l1.143-2.286V8.51Z" />
          </svg>
          <span className="absolute right-4 top-3.5 h-2.5 w-2.5 rounded-full bg-[#2443F4]" />
        </button>

        <span className="h-14 w-px bg-[#D9DEE8]" aria-hidden="true" />

        <div className="relative" ref={profileMenuRef}>
          <button
            onClick={() => setIsProfileMenuOpen((prev) => !prev)}
            className="flex items-center gap-4"
            aria-label="Open profile menu"
          >
            <span className="hidden text-[17px] font-semibold text-[#182039] sm:inline">Alex Rivera</span>
            <span className="inline-flex h-12 w-12 items-center justify-center overflow-hidden rounded-full border-[3px] border-white bg-[#F4CE95] shadow-[0_6px_18px_rgba(25,35,72,0.18)]">
              <Image
                src="/icons/customer/dashboard/profile.svg"
                alt="Alex Rivera"
                width={48}
                height={48}
                className="h-full w-full object-contain"
              />
            </span>
          </button>

          {isProfileMenuOpen && (
            <div className="absolute right-0 top-full z-50 mt-2 w-44 rounded-xl border border-[#E5E8F0] bg-white p-2 shadow-[0_14px_28px_rgba(23,34,73,0.12)]">
              <button className="w-full rounded-lg px-3 py-2 text-left text-sm font-medium text-[#1F293F] transition-colors hover:bg-[#F3F5FA]">
                My Profile
              </button>
              <button className="mt-1 w-full rounded-lg px-3 py-2 text-left text-sm font-medium text-[#C22525] transition-colors hover:bg-[#FFF1F1]">
                Logout
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

export default CustomerHeader;