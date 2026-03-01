'use client';

export default function VendorDashboardPage() {
  const chartData = [
    { label: 'Jan', orders: 120, revenue: 400 },
    { label: 'Feb', orders: 110, revenue: 300 },
    { label: 'Mar', orders: 150, revenue: 500 },
    { label: 'Apr', orders: 200, revenue: 620 },
    { label: 'May', orders: 280, revenue: 750 },
    { label: 'Jun', orders: 320, revenue: 890 },
  ];

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 py-4 md:py-6 px-4 sm:px-8">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-2xl sm:text-3xl md:text-4xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600 mt-1 md:mt-2 text-sm md:text-base">View detailed sales and order analytics</p>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-8 py-8 md:py-12">
        {/* Charts Row */}
        <div className="grid lg:grid-cols-2 gap-6 md:gap-8 mb-6 md:mb-8">
          {/* Orders Chart */}
          <div className="bg-white rounded-lg shadow-md p-4 md:p-6">
            <h3 className="text-base md:text-lg font-bold text-gray-900 mb-3 md:mb-4">Monthly Orders</h3>
            <div className="h-48 md:h-64 bg-gradient-to-br from-emerald-50 to-green-50 rounded-lg flex items-end justify-around p-2 md:p-4">
              {chartData.map((item, index) => (
                <div key={index} className="flex flex-col items-center gap-2 flex-1 h-full">
                  <div
                    className="w-full bg-gradient-to-t from-emerald-500 to-emerald-400 rounded-t"
                    style={{ height: `${(item.orders / 400) * 100}%` }}
                  />
                  <span className="text-xs font-semibold text-gray-600">{item.label}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Revenue Chart */}
          <div className="bg-white rounded-lg shadow-md p-4 md:p-6">
            <h3 className="text-base md:text-lg font-bold text-gray-900 mb-3 md:mb-4">Monthly Revenue</h3>
            <div className="h-48 md:h-64 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg flex items-end justify-around p-2 md:p-4">
              {chartData.map((item, index) => (
                <div key={index} className="flex flex-col items-center gap-2 flex-1 h-full">
                  <div
                    className="w-full bg-gradient-to-t from-blue-500 to-blue-400 rounded-t"
                    style={{ height: `${(item.revenue / 1000) * 100}%` }}
                  />
                  <span className="text-xs font-semibold text-gray-600">{item.label}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Top Products */}
        <div className="bg-white rounded-lg shadow-md p-4 md:p-6">
          <h3 className="text-base md:text-lg font-bold text-gray-900 mb-3 md:mb-4">Top Products</h3>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-2 md:py-3 px-2 md:px-4 font-semibold text-gray-900 text-sm md:text-base">Product</th>
                  <th className="text-left py-2 md:py-3 px-2 md:px-4 font-semibold text-gray-900 text-sm md:text-base">Sales</th>
                  <th className="text-left py-2 md:py-3 px-2 md:px-4 font-semibold text-gray-900 text-sm md:text-base">Revenue</th>
                  <th className="text-left py-2 md:py-3 px-2 md:px-4 font-semibold text-gray-900 text-sm md:text-base">Rating</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-gray-200 hover:bg-gray-50">
                  <td colSpan={4} className="py-6 md:py-8 px-2 md:px-4 text-center text-gray-500 text-sm md:text-base">
                    No products sold yet
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
