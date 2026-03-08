'use client';

import Image from 'next/image';

type CustomerHeaderProps = {
  isSidebarOpen: boolean;
  onToggleSidebar: () => void;
};

const CustomerHeader = ({ isSidebarOpen, onToggleSidebar }: CustomerHeaderProps) => {
  return (
    <header
      className={`flex h-[88px] items-center justify-between border-b border-[#ECECF0] bg-[#F7F7FA] px-6 transition-all duration-300 ${
        isSidebarOpen ? 'ml-[240px]' : 'ml-0'
      }`}
    >
      <div className="flex items-center gap-5">
        {isSidebarOpen ? (
          <button
            onClick={onToggleSidebar}
            className="inline-flex h-10 w-10 items-center justify-center rounded-xl border border-[#E2E5EC] bg-white text-[#5B6478]"
            aria-label="Close sidebar"
          >
            <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M6 6l12 12M18 6 6 18" />
            </svg>
          </button>
        ) : (
          <button onClick={onToggleSidebar} className="flex items-center gap-3" aria-label="Open sidebar">
            <Image src="/icons/logo.svg" alt="Occacia" width={59} height={59} className="h-[59px] w-[59px]" />
            <span className="text-[22px] font-extrabold tracking-tight text-[#1562CC]">OCCACIA</span>
          </button>
        )}

        <div className="relative w-[360px] max-w-full">
          <input
            type="search"
            placeholder="Search events,people.."
            className="h-11 w-full rounded-full border border-[#E2E5EC] bg-[#EFF1F6] px-5 text-sm text-[#4A4F5C] outline-none placeholder:text-[#99A0AF]"
          />
        </div>
      </div>

      <div className="flex items-center gap-5">
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

        <div className="flex items-center gap-4">
          <span className="text-[17px] font-semibold text-[#182039]">Alex Rivera</span>
          <span className="inline-flex h-12 w-12 items-center justify-center overflow-hidden rounded-full border-[3px] border-white bg-[#F4CE95] shadow-[0_6px_18px_rgba(25,35,72,0.18)]">
            <Image
              src="/icons/customer/dashboard/profile.svg"
              alt="Alex Rivera"
              width={48}
              height={48}
              className="h-full w-full object-contain"
            />
          </span>
        </div>
      </div>
    </header>
  );
};

export default CustomerHeader;