'use client';

import Image from 'next/image';
import Link from 'next/link';
import { ROUTES } from '@/lib/routes';

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center relative overflow-hidden bg-gradient-to-br from-gray-100 to-gray-200">
      <Image src="/images/background.png" alt="Background" fill className="object-cover" priority />

      <div className="relative z-10 w-full max-w-6xl px-8">
        <div className="flex justify-center mb-16">
          <div className="flex items-center gap-4">
            <Image src="/images/logo.png" alt="Occacia Logo" width={80} height={80} priority />
            <h1 className="text-5xl font-bold text-[#2c3e50]">OCCACIA</h1>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-8 divide-x divide-gray-300">
          <div className="flex flex-col items-center justify-center px-12">
            <h2 className="text-4xl font-bold text-[#2c3e50] mb-8">For Customers</h2>
            <p className="text-center text-[#5a6c7d] mb-12 text-lg">
              Thousands of people find it easy to get personalized recommendation along with their budget while saving time
            </p>
            <Link
              href="/login"
              className="bg-[#1565c0] hover:bg-[#0d47a1] text-white font-medium px-16 py-4 rounded-lg transition-colors duration-200 text-lg"
            >
              Login as Customer
            </Link>
          </div>

          <div className="flex flex-col items-center justify-center px-12">
            <h2 className="text-4xl font-bold text-[#2c3e50] mb-8">For Business</h2>
            <p className="text-center text-[#5a6c7d] mb-12 text-lg">
              Thousands of businesses have embraced the new way to interact with customers.
            </p>
            <Link
              href={ROUTES.VENDOR.LOGIN}
              className="bg-[#1565c0] hover:bg-[#0d47a1] text-white font-medium px-16 py-4 rounded-lg transition-colors duration-200 text-lg"
            >
              Login as Vendor
            </Link>
          </div>
        </div>

        <div className="text-center mt-16">
          <p className="text-gray-500">Copyright © 2025 Occacia</p>
        </div>
      </div>
    </div>
  );
}
