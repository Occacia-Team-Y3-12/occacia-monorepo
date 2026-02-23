'use client';

import { useState } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { ROUTES } from '@/lib/routes';


export default function VendorRegister() {
  const router = useRouter();
  const [step, setStep] = useState<'account' | 'organization'>('account');
  const [orgChoice, setOrgChoice] = useState<'join' | 'create' | ''>('');

  const [formData, setFormData] = useState({
    username: '',
    fullName: '',
    email: '',
    password: '',
    confirmPassword: '',
    address: '',
    nicNumber: '',
    gender: '',
    organizationCode: '',
    businessName: '',
    businessRegNumber: '',
    businessAddress: '',
    businessPhone: '',
    businessEmail: ''
  });

  const handleAccountSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setStep('organization');
  };

  const handleFinalSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await fetch('/api/v1/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...formData,
          organizationType: orgChoice
        })
      });
      if (response.ok) {
        router.push(ROUTES.VENDOR.VERIFY_EMAIL);
      }

    } catch (error) {
      console.error('Registration failed:', error);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  return (
    <div className="min-h-screen flex items-center justify-center relative overflow-hidden p-4">
      <Image src="/images/background.png" alt="Background" fill className="object-cover" priority />

      <div className="flex bg-white rounded-3xl shadow-2xl overflow-hidden max-w-5xl w-full relative z-10">
        <div className="w-2/5 bg-gradient-to-br from-[#f5f7f9] to-white p-12 flex flex-col items-center justify-center">
          <div className="mb-8">
            <Image src="/images/logo.png" alt="Occacia Logo" width={180} height={180} priority />
          </div>
          <h1 className="text-4xl font-bold text-[#2c3e50] mb-2">OCCACIA</h1>
          <p className="text-xl text-[#5a6c7d] font-medium">VENDOR PORTAL</p>
        </div>

        <div className="w-3/5 p-12">
          <h2 className="text-3xl font-semibold text-[#5a6c7d] mb-8 text-center">SIGN UP</h2>

          {step === 'account' ? (
            <form onSubmit={handleAccountSubmit} className="space-y-4">
              <input
                type="text"
                name="username"
                placeholder="User Name"
                value={formData.username}
                onChange={handleChange}
                required
                className="w-full px-4 py-3 border border-[#d1dce5] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#1e88e5] text-[#2c3e50] placeholder-[#8b9db0] bg-[#f8fafb]"
              />

              <input
                type="text"
                name="fullName"
                placeholder="Full Name"
                value={formData.fullName}
                onChange={handleChange}
                required
                className="w-full px-4 py-3 border border-[#d1dce5] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#1e88e5] text-[#2c3e50] placeholder-[#8b9db0] bg-[#f8fafb]"
              />

              <input
                type="email"
                name="email"
                placeholder="Email Address"
                value={formData.email}
                onChange={handleChange}
                required
                className="w-full px-4 py-3 border border-[#d1dce5] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#1e88e5] text-[#2c3e50] placeholder-[#8b9db0] bg-[#f8fafb]"
              />

              <div className="grid grid-cols-2 gap-4">
                <input
                  type="password"
                  name="password"
                  placeholder="Password"
                  value={formData.password}
                  onChange={handleChange}
                  required
                  className="px-4 py-3 border border-[#d1dce5] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#1e88e5] text-[#2c3e50] placeholder-[#8b9db0] bg-[#f8fafb]"
                />
                <input
                  type="password"
                  name="confirmPassword"
                  placeholder="Confirm password"
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  required
                  className="px-4 py-3 border border-[#d1dce5] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#1e88e5] text-[#2c3e50] placeholder-[#8b9db0] bg-[#f8fafb]"
                />
              </div>

              <input
                type="text"
                name="address"
                placeholder="Address"
                value={formData.address}
                onChange={handleChange}
                required
                className="w-full px-4 py-3 border border-[#d1dce5] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#1e88e5] text-[#2c3e50] placeholder-[#8b9db0] bg-[#f8fafb]"
              />

              <div className="grid grid-cols-2 gap-4">
                <input
                  type="text"
                  name="nicNumber"
                  placeholder="NIC Number"
                  value={formData.nicNumber}
                  onChange={handleChange}
                  required
                  className="px-4 py-3 border border-[#d1dce5] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#1e88e5] text-[#2c3e50] placeholder-[#8b9db0] bg-[#f8fafb]"
                />
                <select
                  name="gender"
                  value={formData.gender}
                  onChange={handleChange}
                  required
                  className="px-4 py-3 border border-[#d1dce5] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#1e88e5] text-[#2c3e50] bg-[#f8fafb]"
                >
                  <option value="">Select Gender</option>
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                  <option value="other">Other</option>
                </select>
              </div>

              <div className="flex justify-center pt-4">
                <button
                  type="submit"
                  className="bg-[#1565c0] hover:bg-[#0d47a1] text-white font-medium px-8 py-3 rounded-lg transition-colors duration-200"
                >
                  Next
                </button>
              </div>
            </form>
          ) : (
            <form onSubmit={handleFinalSubmit} className="space-y-4">
              <div className="mb-6">
                <p className="text-[#5a6c7d] mb-4 font-medium">Do you belong to an organization?</p>
                <div className="space-y-2">
                  <label className="flex items-center space-x-3 cursor-pointer">
                    <input
                      type="radio"
                      name="orgChoice"
                      value="join"
                      checked={orgChoice === 'join'}
                      onChange={(e) => setOrgChoice(e.target.value as 'join')}
                      className="w-4 h-4 text-[#1e88e5]"
                    />
                    <span className="text-[#2c3e50]">Join existing organization</span>
                  </label>
                  <label className="flex items-center space-x-3 cursor-pointer">
                    <input
                      type="radio"
                      name="orgChoice"
                      value="create"
                      checked={orgChoice === 'create'}
                      onChange={(e) => setOrgChoice(e.target.value as 'create')}
                      className="w-4 h-4 text-[#1e88e5]"
                    />
                    <span className="text-[#2c3e50]">Create new organization</span>
                  </label>
                </div>
              </div>

              {orgChoice === 'join' && (
                <input
                  type="text"
                  name="organizationCode"
                  placeholder="Organization Code"
                  value={formData.organizationCode}
                  onChange={handleChange}
                  required
                  className="w-full px-4 py-3 border border-[#d1dce5] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#1e88e5] text-[#2c3e50] placeholder-[#8b9db0] bg-[#f8fafb]"
                />
              )}

              {orgChoice === 'create' && (
                <>
                  <input
                    type="text"
                    name="businessName"
                    placeholder="Business Name"
                    value={formData.businessName}
                    onChange={handleChange}
                    required
                    className="w-full px-4 py-3 border border-[#d1dce5] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#1e88e5] text-[#2c3e50] placeholder-[#8b9db0] bg-[#f8fafb]"
                  />
                  <input
                    type="text"
                    name="businessRegNumber"
                    placeholder="Business Registration Number"
                    value={formData.businessRegNumber}
                    onChange={handleChange}
                    required
                    className="w-full px-4 py-3 border border-[#d1dce5] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#1e88e5] text-[#2c3e50] placeholder-[#8b9db0] bg-[#f8fafb]"
                  />
                  <input
                    type="text"
                    name="businessAddress"
                    placeholder="Business Address"
                    value={formData.businessAddress}
                    onChange={handleChange}
                    required
                    className="w-full px-4 py-3 border border-[#d1dce5] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#1e88e5] text-[#2c3e50] placeholder-[#8b9db0] bg-[#f8fafb]"
                  />
                  <div className="grid grid-cols-2 gap-4">
                    <input
                      type="tel"
                      name="businessPhone"
                      placeholder="Business Phone"
                      value={formData.businessPhone}
                      onChange={handleChange}
                      required
                      className="px-4 py-3 border border-[#d1dce5] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#1e88e5] text-[#2c3e50] placeholder-[#8b9db0] bg-[#f8fafb]"
                    />
                    <input
                      type="email"
                      name="businessEmail"
                      placeholder="Business Email"
                      value={formData.businessEmail}
                      onChange={handleChange}
                      required
                      className="px-4 py-3 border border-[#d1dce5] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#1e88e5] text-[#2c3e50] placeholder-[#8b9db0] bg-[#f8fafb]"
                    />
                  </div>
                </>
              )}

              <div className="flex justify-between pt-4">
                <button
                  type="button"
                  onClick={() => setStep('account')}
                  className="bg-gray-300 hover:bg-gray-400 text-[#2c3e50] font-medium px-8 py-3 rounded-lg transition-colors duration-200"
                >
                  Back
                </button>
                <button
                  type="submit"
                  disabled={!orgChoice}
                  className="bg-[#1565c0] hover:bg-[#0d47a1] text-white font-medium px-8 py-3 rounded-lg transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Create vendor account
                </button>
              </div>
            </form>
          )}

          <div className="mt-6 text-center">
            <p className="text-[#5a6c7d] text-sm">
              Already have an account?{' '}
              <Link href={ROUTES.VENDOR.LOGIN} className="text-[#1e88e5] hover:underline font-medium">
                Click here
              </Link>
            </p>
          </div>

        </div>
      </div>
    </div>
  );
}
