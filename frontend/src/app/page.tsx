import Image from 'next/image';
import Link from 'next/link';
import { ROUTES } from '@/lib/routes';

export default function Home() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center relative overflow-hidden bg-gradient-to-br from-gray-100 to-gray-200">
      <Image src="/images/background.png" alt="" aria-hidden={true} fill sizes="100vw" className="object-cover" priority />

      <div className="relative z-10 w-full max-w-6xl px-4 sm:px-6 md:px-8 py-6 sm:py-8">
        <div className="flex justify-center mb-8 sm:mb-12 md:mb-16">
          <div className="flex flex-col sm:flex-row items-center gap-3 sm:gap-4 md:gap-6">
            <Image 
              src="/icons/logo.svg" 
              alt="Occacia Logo" 
              width={80} 
              height={80} 
              priority 
              className="w-20 h-20 sm:w-28 sm:h-28 md:w-36 md:h-36 lg:w-44 lg:h-44 xl:w-[200px] xl:h-[200px]" 
            />
            <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl xl:text-7xl font-bold text-[#2c3e50]">OCCACIA</h1>
          </div>
        </div>

        <div className="relative">
          <div className="grid grid-cols-1 md:grid-cols-2 items-stretch gap-6 md:gap-0">
            <div className="flex flex-col items-start justify-between px-4 sm:px-6 md:px-8 lg:px-12 py-6 sm:py-8 h-full md:pr-8 lg:pr-16">
              <h2 className="text-xl sm:text-2xl md:text-3xl lg:text-4xl font-bold text-[#2c3e50] mb-4 sm:mb-6 md:mb-8 text-left w-full">For Customers</h2>
              <p className="flex-1 text-left text-[#5a6c7d] mb-6 sm:mb-8 md:mb-12 text-sm sm:text-base md:text-lg">
                Thousands of people find it easy to get personalized recommendations that fit their budget while saving time
              </p>
              <Link
                href={ROUTES.CUSTOMER.LOGIN}
                className="bg-[#1565c0] hover:bg-[#0d47a1] text-white font-medium inline-flex items-center justify-center w-full sm:max-w-[280px] md:max-w-[320px] h-11 sm:h-12 rounded-lg transition-colors duration-200 text-sm sm:text-base md:text-lg"
              >
                Login as Customer
              </Link>
            </div>

            <div className="flex flex-col items-start justify-between px-4 sm:px-6 md:px-8 lg:px-12 py-6 sm:py-8 h-full md:pl-8 lg:pl-16">
              <h2 className="text-xl sm:text-2xl md:text-3xl lg:text-4xl font-bold text-[#2c3e50] mb-4 sm:mb-6 md:mb-8 text-left w-full">For Business</h2>
              <p className="flex-1 text-left text-[#5a6c7d] mb-6 sm:mb-8 md:mb-12 text-sm sm:text-base md:text-lg">
                Thousands of businesses have embraced the new way to interact with customers.
              </p>
              <Link
                href={ROUTES.VENDOR.LOGIN}
                className="bg-[#1565c0] hover:bg-[#0d47a1] text-white font-medium inline-flex items-center justify-center w-full sm:max-w-[280px] md:max-w-[320px] h-11 sm:h-12 rounded-lg transition-colors duration-200 text-sm sm:text-base md:text-lg"
              >
                Login as Vendor
              </Link>
            </div>
          </div>
          <div className="hidden md:block absolute left-1/2 top-1/2 w-px h-[280px] sm:h-[320px] md:h-[350px] bg-black/50 -translate-x-1/2 -translate-y-1/2" />
        </div>

        <div className="text-center mt-6 sm:mt-8 md:mt-16">
          <p className="text-gray-500 text-sm sm:text-base">Copyright © 2025 Occacia</p>
        </div>
      </div>
    </main>
  );
}
