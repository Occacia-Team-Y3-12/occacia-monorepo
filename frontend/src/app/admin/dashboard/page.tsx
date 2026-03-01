'use client';

export default function AdminDashboardPage() {
  const chartData = [
    { label: 'Jan', value: 400 },
    { label: 'Feb', value: 520 },
    { label: 'Mar', value: 480 },
    { label: 'Apr', value: 620 },
    { label: 'May', value: 750 },
    { label: 'Jun', value: 890 },
  ];

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 py-6 px-4 sm:px-8">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-3xl sm:text-4xl font-bold text-gray-900">Analytics</h1>
          <p className="text-gray-600 mt-2">View platform analytics and insights</p>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-8 py-12">
        {/* Charts Row */}
        <div className="grid lg:grid-cols-2 gap-8 mb-8">
          {/* Revenue Chart */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-bold text-gray-900 mb-4">Monthly Revenue</h3>
            <div className="h-64 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg flex items-end justify-around p-4">
              {chartData.map((item, index) => (
                <div key={index} className="flex flex-col items-center gap-2 flex-1 h-full">
                  <div
                    className="w-full bg-gradient-to-t from-blue-500 to-blue-400 rounded-t"
                    style={{ height: `${(item.value / 1000) * 100}%` }}
                  />
                  <span className="text-xs font-semibold text-gray-600">{item.label}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Orders Chart */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-bold text-gray-900 mb-4">Total Orders</h3>
            <div className="h-64 bg-gradient-to-br from-green-50 to-emerald-50 rounded-lg flex items-end justify-around p-4">
              {chartData.map((item, index) => (
                <div key={index} className="flex flex-col items-center gap-2 flex-1 h-full">
                  <div
                    className="w-full bg-gradient-to-t from-green-500 to-green-400 rounded-t"
                    style={{ height: `${(item.value / 1000) * 100}%` }}
                  />
                  <span className="text-xs font-semibold text-gray-600">{item.label}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Top Vendors */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-bold text-gray-900 mb-4">Top Vendors</h3>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4 font-semibold text-gray-900">Vendor Name</th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-900">Orders</th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-900">Revenue</th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-900">Status</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-gray-200 hover:bg-gray-50">
                  <td className="py-3 px-4 text-gray-600">No data</td>
                  <td className="py-3 px-4 text-gray-600">-</td>
                  <td className="py-3 px-4 text-gray-600">-</td>
                  <td className="py-3 px-4">
                    <span className="px-2 py-1 bg-gray-100 text-gray-600 rounded text-sm">N/A</span>
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
