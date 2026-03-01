'use client';

import Link from 'next/link';

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24 bg-gradient-to-b from-blue-50 to-white">
      <div className="text-center">
        <h1 className="text-5xl font-bold text-gray-900 mb-4">Welcome to Occacia</h1>
        <p className="text-xl text-gray-600 mb-12">Your trusted marketplace platform</p>
        
        <div className="flex gap-6 justify-center">
          <Link 
            href="/customers/login"
            className="px-8 py-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-semibold"
          >
            Login as Customer
          </Link>
          <Link 
            href="/vendor/login"
            className="px-8 py-4 bg-green-600 text-white rounded-lg hover:bg-green-700 transition font-semibold"
          >
            Login as Vendor
          </Link>
          <Link 
            href="/admin/login"
            className="px-8 py-4 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition font-semibold"
          >
            Admin Login
          </Link>
        </div>
      </div>
    </main>
  );
}
