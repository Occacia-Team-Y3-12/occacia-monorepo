import { Card, CardHeader, CardBody } from '@/components/ui/Card';

const DashboardCards = () => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {/* Orders Card */}
      <Card hoverable>
        <CardHeader>
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-800">Recent Orders</h3>
            <span className="text-2xl">📦</span>
          </div>
        </CardHeader>
        <CardBody>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Order #12345</span>
              <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">Delivered</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Order #12344</span>
              <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">Processing</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Order #12343</span>
              <span className="px-2 py-1 bg-yellow-100 text-yellow-800 text-xs rounded-full">Pending</span>
            </div>
          </div>
          <div className="mt-4 pt-3 border-t">
            <p className="text-2xl font-bold text-gray-800">12</p>
            <p className="text-sm text-gray-500">Total Orders</p>
          </div>
        </CardBody>
      </Card>

      {/* Bookings Card */}
      <Card hoverable>
        <CardHeader>
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-800">Upcoming Bookings</h3>
            <span className="text-2xl">📅</span>
          </div>
        </CardHeader>
        <CardBody>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <div>
                <p className="text-sm font-medium text-gray-800">Spa Appointment</p>
                <p className="text-xs text-gray-500">Dec 15, 2024</p>
              </div>
              <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">Confirmed</span>
            </div>
            <div className="flex justify-between items-center">
              <div>
                <p className="text-sm font-medium text-gray-800">Massage Therapy</p>
                <p className="text-xs text-gray-500">Dec 18, 2024</p>
              </div>
              <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">Confirmed</span>
            </div>
          </div>
          <div className="mt-4 pt-3 border-t">
            <p className="text-2xl font-bold text-gray-800">5</p>
            <p className="text-sm text-gray-500">Active Bookings</p>
          </div>
        </CardBody>
      </Card>

      {/* Profile Card */}
      <Card hoverable>
        <CardHeader>
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-800">Profile</h3>
            <span className="text-2xl">👤</span>
          </div>
        </CardHeader>
        <CardBody>
          <div className="space-y-3">
            <div className="flex items-center space-x-3">
              <div className="w-12 h-12 bg-blue-500 rounded-full flex items-center justify-center">
                <span className="text-white font-medium">JD</span>
              </div>
              <div>
                <p className="font-medium text-gray-800">John Doe</p>
                <p className="text-sm text-gray-500">john.doe@email.com</p>
              </div>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Member Since</span>
                <span className="text-sm font-medium">Jan 2024</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Status</span>
                <span className="px-2 py-1 bg-gold-100 text-gold-800 text-xs rounded-full">Premium</span>
              </div>
            </div>
          </div>
        </CardBody>
      </Card>
    </div>
  );
};

export default DashboardCards;