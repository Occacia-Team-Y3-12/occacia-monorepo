'use client';

import { useState } from 'react';

interface AdminSettings {
  platformName: string;
  supportEmail: string;
  supportPhone: string;
  commissionRate: string;
  taxRate: string;
  orderNotifications: boolean;
  vendorSignupNotifications: boolean;
  systemAlerts: boolean;
}

export default function AdminSettingsPage() {
  const [saved, setSaved] = useState(false);
  const [settings, setSettings] = useState<AdminSettings>({
    platformName: 'Occacia',
    supportEmail: 'support@occacia.com',
    supportPhone: '+1 (555) 000-0000',
    commissionRate: '10',
    taxRate: '5',
    orderNotifications: true,
    vendorSignupNotifications: true,
    systemAlerts: true,
  });

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    setSettings((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const handleSave = () => {
    // TODO: Replace with actual API call to save settings
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 py-6 px-4 sm:px-8">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-3xl sm:text-4xl font-bold text-gray-900">Settings</h1>
          <p className="text-gray-600 mt-2">Manage platform configuration</p>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-4xl mx-auto px-4 sm:px-8 py-12">
        {saved && (
          <div className="mb-6 bg-green-50 border border-green-200 rounded-lg p-4 text-green-800 font-semibold">
            ✓ Settings saved successfully
          </div>
        )}

        {/* General Settings */}
        <div className="bg-white rounded-lg shadow-md p-8 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">General Settings</h2>
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-semibold text-gray-900 mb-2">Platform Name</label>
              <input
                type="text"
                name="platformName"
                value={settings.platformName}
                onChange={handleInputChange}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-900 mb-2">Support Email</label>
              <input
                type="email"
                name="supportEmail"
                value={settings.supportEmail}
                onChange={handleInputChange}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-900 mb-2">Support Phone</label>
              <input
                type="tel"
                name="supportPhone"
                value={settings.supportPhone}
                onChange={handleInputChange}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>
        </div>

        {/* Commission Settings */}
        <div className="bg-white rounded-lg shadow-md p-8 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Commission Settings</h2>
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-semibold text-gray-900 mb-2">Vendor Commission Rate (%)</label>
              <input
                type="number"
                name="commissionRate"
                value={settings.commissionRate}
                onChange={handleInputChange}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-900 mb-2">Tax Rate (%)</label>
              <input
                type="number"
                name="taxRate"
                value={settings.taxRate}
                onChange={handleInputChange}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>
        </div>

        {/* Notification Settings */}
        <div className="bg-white rounded-lg shadow-md p-8 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Notifications</h2>
          <div className="space-y-4">
            <label className="flex items-center">
              <input
                type="checkbox"
                name="orderNotifications"
                checked={settings.orderNotifications}
                onChange={handleInputChange}
                className="w-4 h-4 rounded border-gray-300"
              />
              <span className="ml-3 text-gray-700">Send order notifications</span>
            </label>
            <label className="flex items-center">
              <input
                type="checkbox"
                name="vendorSignupNotifications"
                checked={settings.vendorSignupNotifications}
                onChange={handleInputChange}
                className="w-4 h-4 rounded border-gray-300"
              />
              <span className="ml-3 text-gray-700">Send vendor signup notifications</span>
            </label>
            <label className="flex items-center">
              <input
                type="checkbox"
                name="systemAlerts"
                checked={settings.systemAlerts}
                onChange={handleInputChange}
                className="w-4 h-4 rounded border-gray-300"
              />
              <span className="ml-3 text-gray-700">Send system alerts</span>
            </label>
          </div>
        </div>

        {/* Save Button */}
        <div className="flex flex-col gap-3 sm:flex-row sm:gap-4">
          <button
            onClick={handleSave}
            className="w-full rounded-lg bg-indigo-600 px-8 py-3 font-semibold text-white transition-colors hover:bg-indigo-700 sm:w-auto"
          >
            Save Settings
          </button>
          <button className="w-full rounded-lg bg-gray-200 px-8 py-3 font-semibold text-gray-900 transition-colors hover:bg-gray-300 sm:w-auto">
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}
