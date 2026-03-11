'use client';

import Image from 'next/image';
import Link from 'next/link';
import { ROUTES } from '@/lib/routes';

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center relative overflow-hidden bg-gradient-to-br from-gray-100 to-gray-200">
      <Image src="/images/background.png" alt="Background" fill className="object-cover" priority />

      <div className="relative z-10 w-full max-w-6xl px-4 sm:px-6 md:px-8">
        <div className="flex justify-center mb-12 md:mb-16">
          <div className="flex items-center gap-4 md:gap-6">
            <Image src="/icons/logo.svg" alt="Occacia Logo" width={120} height={120} priority className="sm:w-[140px] sm:h-[140px] md:w-[180px] md:h-[180px] lg:w-[200px] lg:h-[200px]" />
            <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-bold text-[#2c3e50]">OCCACIA</h1>
          </div>
        </div>

        <div className="relative">
          <div className="grid grid-cols-1 md:grid-cols-2 items-stretch">
            <div className="flex flex-col items-start justify-between px-6 sm:px-8 md:px-12 py-6 md:py-8 h-full md:pr-16">
              <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-[#2c3e50] mb-6 md:mb-8 text-left w-full">For Customers</h2>
              <p className="flex-1 text-left text-[#5a6c7d] mb-8 md:mb-12 text-base md:text-lg">
                Thousands of people find it easy to get personalized recommendation along with their budget while saving time
              </p>
              <Link
                href="/login"
                className="bg-[#1565c0] hover:bg-[#0d47a1] text-white font-medium inline-flex items-center justify-center w-full max-w-[320px] h-12 rounded-lg transition-colors duration-200 text-base md:text-lg"
              >
                Login as Customer
              </Link>
            </div>

            <div className="flex flex-col items-start justify-between px-6 sm:px-8 md:px-12 py-6 md:py-8 h-full md:pl-16">
              <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-[#2c3e50] mb-6 md:mb-8 text-left w-full">For Business</h2>
              <p className="flex-1 text-left text-[#5a6c7d] mb-8 md:mb-12 text-base md:text-lg">
                Thousands of businesses have embraced the new way to interact with customers.
              </p>
              <Link
                href={ROUTES.VENDOR.LOGIN}
                className="bg-[#1565c0] hover:bg-[#0d47a1] text-white font-medium inline-flex items-center justify-center w-full max-w-[320px] h-12 rounded-lg transition-colors duration-200 text-base md:text-lg"
              >
                Login as Vendor
              </Link>
            </div>
          </div>
          <div className="hidden md:block absolute left-1/2 top-1/2 w-px h-[350px] bg-black/50 -translate-x-1/2 -translate-y-1/2" />
        </div>

        <div className="text-center mt-8 md:mt-16">
          <p className="text-gray-500">Copyright © 2025 Occacia</p>
        </div>
      </div>
    </div>
  );
}

