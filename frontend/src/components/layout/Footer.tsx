'use client';

import Link from 'next/link';
import Image from 'next/image';
import { ROUTES } from '@/lib/routes';

export default function Footer() {
  return (
    <footer className="bg-gray-900 text-gray-300 mt-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          {/* Brand */}
          <div>
            <div className="flex items-center gap-2 mb-4">
              <Image src="/images/logo.png" alt="Occacia Logo" width={40} height={40} />
              <span className="font-bold text-lg text-white">Occacia</span>
            </div>
            <p className="text-sm text-gray-400">
              Your trusted platform for shopping and selling.
            </p>
          </div>

          {/* Customer Links */}
          <div>
            <h3 className="font-bold text-white mb-4">For Customers</h3>
            <ul className="space-y-2">
              <li>
                <Link href={ROUTES.CUSTOMER.PRODUCTS} className="text-gray-400 hover:text-white transition-colors">
                  Browse Products
                </Link>
              </li>
              <li>
                <Link href={ROUTES.CUSTOMER.ORDERS} className="text-gray-400 hover:text-white transition-colors">
                  My Orders
                </Link>
              </li>
              <li>
                <Link href={ROUTES.CUSTOMER.CART} className="text-gray-400 hover:text-white transition-colors">
                  Shopping Cart
                </Link>
              </li>
              <li>
                <Link href="#" className="text-gray-400 hover:text-white transition-colors">
                  Help & Support
                </Link>
              </li>
            </ul>
          </div>

          {/* Vendor Links */}
          <div>
            <h3 className="font-bold text-white mb-4">For Vendors</h3>
            <ul className="space-y-2">
              <li>
                <Link href={ROUTES.VENDOR.LOGIN} className="text-gray-400 hover:text-white transition-colors">
                  Vendor Login
                </Link>
              </li>
              <li>
                <Link href={ROUTES.VENDOR.REGISTER} className="text-gray-400 hover:text-white transition-colors">
                  Start Selling
                </Link>
              </li>
              <li>
                <Link href="#" className="text-gray-400 hover:text-white transition-colors">
                  Seller Guide
                </Link>
              </li>
              <li>
                <Link href="#" className="text-gray-400 hover:text-white transition-colors">
                  Commission Info
                </Link>
              </li>
            </ul>
          </div>

          {/* Connect */}
          <div>
            <h3 className="font-bold text-white mb-4">Connect</h3>
            <ul className="space-y-2">
              <li>
                <Link href="#" className="text-gray-400 hover:text-white transition-colors">
                  About Us
                </Link>
              </li>
              <li>
                <Link href="#" className="text-gray-400 hover:text-white transition-colors">
                  Contact Us
                </Link>
              </li>
              <li>
                <Link href="#" className="text-gray-400 hover:text-white transition-colors">
                  Privacy Policy
                </Link>
              </li>
              <li>
                <Link href="#" className="text-gray-400 hover:text-white transition-colors">
                  Terms of Service
                </Link>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Section */}
        <div className="border-t border-gray-700 pt-8">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <p className="text-gray-400 text-sm">© 2026 Occacia. All rights reserved.</p>
            <div className="flex gap-6 mt-4 md:mt-0">
              <Link href="#" className="text-gray-400 hover:text-white transition-colors">
                <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M8.29 20v-7.21H5.93v-2.88h2.36V7.79c0-2.33 1.43-3.61 3.48-3.61.99 0 1.84.07 2.09.1v2.42h-1.44c-1.13 0-1.35.53-1.35 1.32v1.73h2.69l-.35 2.88h-2.34V20H8.29z" />
                </svg>
              </Link>
              <Link href="#" className="text-gray-400 hover:text-white transition-colors">
                <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M23.953 4.57a10 10 0 01-2.825.775 4.958 4.958 0 002.163-2.723c-.951.555-2.005.959-3.127 1.184a4.92 4.92 0 00-8.384 4.482C7.69 8.095 4.067 6.13 1.64 3.162a4.822 4.822 0 00-.666 2.475c0 1.71.87 3.213 2.188 4.096a4.904 4.904 0 01-2.228-.616v.06a4.923 4.923 0 003.946 4.827 4.996 4.996 0 01-2.212.085 4.936 4.936 0 004.604 3.417 9.867 9.867 0 01-6.102 2.105c-.39 0-.779-.023-1.17-.067a14.028 14.028 0 007.557 2.209c9.053 0 13.998-7.496 13.998-13.985 0-.21 0-.42-.015-.63A9.935 9.935 0 0024 4.59z" />
                </svg>
              </Link>
              <Link href="#" className="text-gray-400 hover:text-white transition-colors">
                <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.521 17.34c-.24.65-.934 1.085-1.576 1.083-.484-.002-.956-.193-1.424-.533-.743-.626-1.262-1.535-1.269-2.26-.007-.729.522-1.554 1.265-2.224.742-.672 1.941-1.173 2.891-.115.15.101.28.262.38.437.118.238.126.521.06.778a.961.961 0 01-.322.56c-.584.523-1.571.737-2.891.146-.466-.23-.913-.636-1.122-1.278-.21-.642-.122-1.58.871-2.406.992-.826 2.754-1.223 4.218-.429.527.28.93.742 1.15 1.193.219.452.226.96.12 1.414-.106.454-.393.926-.788 1.236-.394.31-.855.528-1.31.545.11.305.244.578.391.822.312.559.878 1.065 1.659 1.281.785.216 1.75.042 2.183-.524.432-.486.543-1.236.273-1.72-.27-.484-.905-.726-1.566-.666-.661.06-1.297.448-1.662 1.067zm-4.753-5.35c-.178.34-.588.641-1.094.7-.505.06-1.076-.163-1.157-.73-.081-.567.314-1.067.91-1.157.595-.09 1.203.227 1.34.902.137.676-.404 1.244-.999 1.185zm3.248 1.554c-.393.628-1.268 1.084-2.001 1.063-.733-.021-1.367-.596-1.366-1.322.001-.726.63-1.315 1.362-1.336.733-.02 1.629.425 2.005 1.095zm3.271-2.973c-.29.427-.854.77-1.41.77-.556 0-1.12-.343-1.41-.77-.29-.427-.29-1.113 0-1.54.29-.427.854-.77 1.41-.77.556 0 1.12.343 1.41.77.29.427.29 1.113 0 1.54z" />
                </svg>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}
