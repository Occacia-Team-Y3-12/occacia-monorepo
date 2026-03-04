'use client';

import Image from 'next/image';

export default function VendorDashboardPage() {
  return (
    <div className="min-h-screen relative">
      <Image src="/images/background.png" alt="Background" fill className="object-cover" priority />
      
      {/* Header */}
      <div className="bg-white border-b px-8 py-3 relative z-10">
        <div className="flex items-center justify-between">
          <div className="flex items-center -my-2">
            <img src="/icons/logo.svg" alt="Occacia Logo" className="h-16" />
          </div>
          <div className="flex items-center gap-12">
            <nav className="flex gap-12">
              <a href="#" className="text-blue-600 font-semibold border-b-2 border-blue-600 pb-1 text-sm">DASHBOARD</a>
              <a href="#" className="text-gray-600 hover:text-blue-600 text-sm">ORDERS</a>
              <a href="#" className="text-gray-600 hover:text-blue-600 text-sm">ITEMS & SERVICES</a>
            </nav>
            <div className="flex items-center gap-2">
              <img src="/icons/vendor/dashboard/Spring & Summer logo.svg" alt="Spring & Summer" className="h-8" />
              <span className="text-gray-700 text-sm mb-2">Spring & Summer</span>
            </div>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="px-8 py-8 relative z-10">
        <div className="grid grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-xl shadow-lg p-6 flex items-center justify-between">
            <div>
              <div className="text-3xl font-bold text-gray-800">100,205.00 LKR</div>
              <div className="text-sm text-gray-500 mt-1">TOTAL PROFIT THIS MONTH</div>
            </div>
            <div className="w-16 h-16 bg-gray-100 rounded-lg flex items-center justify-center">
              <img src="/icons/vendor/dashboard/profit.svg" alt="Profit" className="w-8 h-8" />
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-lg p-6 flex items-center justify-between">
            <div>
              <div className="text-3xl font-bold text-gray-800">1025</div>
              <div className="text-sm text-gray-500 mt-1">COMPLETED ORDERS THIS MONTH</div>
            </div>
            <div className="w-16 h-16 bg-gray-100 rounded-lg flex items-center justify-center">
              <svg className="w-8 h-8 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 10a2 2 0 002 2h2a2 2 0 002-2V7a2 2 0 00-2-2h-2a2 2 0 00-2 2" />
              </svg>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-lg p-6 flex items-center justify-between">
            <div>
              <div className="text-3xl font-bold text-gray-800">25</div>
              <div className="text-sm text-gray-500 mt-1">ONGOING ORDERS</div>
            </div>
            <div className="w-16 h-16 bg-gray-100 rounded-lg flex items-center justify-center">
              <svg className="w-8 h-8 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 10a2 2 0 002 2h2a2 2 0 002-2V7a2 2 0 00-2-2h-2a2 2 0 00-2 2" />
              </svg>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-lg p-6 flex items-center justify-between">
            <div>
              <div className="text-3xl font-bold text-gray-800">4.5 / 5 <span className="text-sm text-gray-500">(1200 USERS)</span></div>
              <div className="text-sm text-gray-500 mt-1">Your SCORE</div>
            </div>
            <div className="w-16 h-16 bg-gray-100 rounded-lg flex items-center justify-center">
              <svg className="w-8 h-8 text-gray-600" fill="currentColor" viewBox="0 0 20 20">
                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
              </svg>
            </div>
          </div>
        </div>

        {/* Bottom Section */}
        <div className="grid grid-cols-3 gap-6">
          {/* Recent Activity */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-bold text-gray-700 mb-6">Recent Activity Feed</h2>
            <div className="bg-blue-50 rounded-lg p-4">
              <div className="space-y-4 max-h-80 overflow-y-auto pr-2">
                <div className="bg-white rounded-lg p-4 border border-gray-200 h-[72px] flex flex-col justify-center">
                  <div className="text-sm text-gray-700">New order received from Thisal</div>
                  <div className="text-xs text-gray-500 mt-1">2 min ago</div>
                </div>
                <div className="bg-white rounded-lg p-4 border border-gray-200 h-[72px] flex flex-col justify-center">
                  <div className="text-sm text-gray-700">Payment received for Order #1025 : 8,500 LKR</div>
                  <div className="text-xs text-gray-500 mt-1">12 min ago</div>
                </div>
                <div className="bg-white rounded-lg p-4 border border-gray-200 h-[72px] flex flex-col justify-center">
                  <div className="text-sm text-gray-700">New order received from Janith</div>
                  <div className="text-xs text-gray-500 mt-1">17min ago</div>
                </div>
                <div className="bg-white rounded-lg p-4 border border-gray-200 h-[72px] flex flex-col justify-center">
                  <div className="text-sm text-gray-700">Order #1024 completed</div>
                  <div className="text-xs text-gray-500 mt-1">25 min ago</div>
                </div>
                <div className="bg-white rounded-lg p-4 border border-gray-200 h-[72px] flex flex-col justify-center">
                  <div className="text-sm text-gray-700">New order received from Kamal</div>
                  <div className="text-xs text-gray-500 mt-1">35 min ago</div>
                </div>
                <div className="bg-white rounded-lg p-4 border border-gray-200 h-[72px] flex flex-col justify-center">
                  <div className="text-sm text-gray-700">Payment received for Order #1023 : 12,300 LKR</div>
                  <div className="text-xs text-gray-500 mt-1">45 min ago</div>
                </div>
              </div>
            </div>
          </div>

          {/* Platform Overview */}
          <div className="col-span-2">
            <h2 className="text-xl font-bold text-gray-700 mb-6 mt-6">Platform Overview</h2>
            <div className="grid grid-cols-3 gap-6">
              <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl shadow-lg p-6 text-white">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <div className="text-4xl font-bold">342</div>
                    <div className="text-sm mt-1">Total Orders</div>
                  </div>
                  <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M3 1a1 1 0 000 2h1.22l.305 1.222a.997.997 0 00.01.042l1.358 5.43-.893.892C3.74 11.846 4.632 14 6.414 14H15a1 1 0 000-2H6.414l1-1H14a1 1 0 00.894-.553l3-6A1 1 0 0017 3H6.28l-.31-1.243A1 1 0 005 1H3zM16 16.5a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0zM6.5 18a1.5 1.5 0 100-3 1.5 1.5 0 000 3z" />
                  </svg>
                </div>
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between"><span>Completion Rate:</span><span>87%</span></div>
                  <div className="flex justify-between"><span>Avg Response:</span><span>2.3 min</span></div>
                </div>
              </div>

              <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl shadow-lg p-6 text-white">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <div className="text-4xl font-bold">42</div>
                    <div className="text-sm mt-1">Active Orders</div>
                  </div>
                  <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between"><span>On process:</span><span>18</span></div>
                  <div className="flex justify-between"><span>Prepared:</span><span>360</span></div>
                </div>
              </div>

              <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl shadow-lg p-6 text-white">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <div className="text-4xl font-bold">4.6</div>
                    <div className="text-sm mt-1">Average Rating</div>
                  </div>
                  <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                  </svg>
                </div>
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between"><span>Total Reviews:</span><span>1,247</span></div>
                  <div className="flex justify-between"><span>Pending Moderation:</span><span>23</span></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}


