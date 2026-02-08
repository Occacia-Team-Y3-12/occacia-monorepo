'use client';

import { useState } from 'react';
import Image from 'next/image';

export default function VendorRegister() {
  const [formData, setFormData] = useState({
    username: '',
    fullName: '',
    email: '',
    password: '',
    confirmPassword: '',
    address: '',
    nicNumber: '',
    gender: ''
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    console.log('Form submitted:', formData);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#c5d3e0] relative overflow-hidden p-4">
      <div className="absolute inset-0 opacity-20">
        <svg className="w-full h-full" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <pattern id="network" x="0" y="0" width="150" height="150" patternUnits="userSpaceOnUse">
              <circle cx="20" cy="20" r="3" fill="#ffffff" />
              <circle cx="130" cy="40" r="3" fill="#ffffff" />
              <circle cx="70" cy="100" r="3" fill="#ffffff" />
              <circle cx="40" cy="130" r="3" fill="#ffffff" />
              <circle cx="110" cy="110" r="3" fill="#ffffff" />
              <line x1="20" y1="20" x2="130" y2="40" stroke="#ffffff" strokeWidth="1.5" />
              <line x1="130" y1="40" x2="110" y2="110" stroke="#ffffff" strokeWidth="1.5" />
              <line x1="110" y1="110" x2="70" y2="100" stroke="#ffffff" strokeWidth="1.5" />
              <line x1="70" y1="100" x2="40" y2="130" stroke="#ffffff" strokeWidth="1.5" />
              <line x1="20" y1="20" x2="40" y2="130" stroke="#ffffff" strokeWidth="1.5" />
              <line x1="20" y1="20" x2="70" y2="100" stroke="#ffffff" strokeWidth="1.5" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#network)" />
        </svg>
      </div>

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
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <input
              type="text"
              name="username"
              placeholder="User Name"
              value={formData.username}
              onChange={handleChange}
              className="w-full px-4 py-3 border border-[#d1dce5] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#1e88e5] text-[#2c3e50] placeholder-[#8b9db0] bg-[#f8fafb]"
            />

            <input
              type="text"
              name="fullName"
              placeholder="Full Name"
              value={formData.fullName}
              onChange={handleChange}
              className="w-full px-4 py-3 border border-[#d1dce5] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#1e88e5] text-[#2c3e50] placeholder-[#8b9db0] bg-[#f8fafb]"
            />

            <input
              type="email"
              name="email"
              placeholder="Email Address"
              value={formData.email}
              onChange={handleChange}
              className="w-full px-4 py-3 border border-[#d1dce5] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#1e88e5] text-[#2c3e50] placeholder-[#8b9db0] bg-[#f8fafb]"
            />

            <div className="grid grid-cols-2 gap-4">
              <input
                type="password"
                name="password"
                placeholder="Password"
                value={formData.password}
                onChange={handleChange}
                className="px-4 py-3 border border-[#d1dce5] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#1e88e5] text-[#2c3e50] placeholder-[#8b9db0] bg-[#f8fafb]"
              />
              <input
                type="password"
                name="confirmPassword"
                placeholder="Confirm password"
                value={formData.confirmPassword}
                onChange={handleChange}
                className="px-4 py-3 border border-[#d1dce5] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#1e88e5] text-[#2c3e50] placeholder-[#8b9db0] bg-[#f8fafb]"
              />
            </div>

            <input
              type="text"
              name="address"
              placeholder="Address"
              value={formData.address}
              onChange={handleChange}
              className="w-full px-4 py-3 border border-[#d1dce5] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#1e88e5] text-[#2c3e50] placeholder-[#8b9db0] bg-[#f8fafb]"
            />

            <div className="grid grid-cols-2 gap-4">
              <input
                type="text"
                name="nicNumber"
                placeholder="NIC Number"
                value={formData.nicNumber}
                onChange={handleChange}
                className="px-4 py-3 border border-[#d1dce5] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#1e88e5] text-[#2c3e50] placeholder-[#8b9db0] bg-[#f8fafb]"
              />
              <input
                type="text"
                name="gender"
                placeholder="Gender"
                value={formData.gender}
                onChange={handleChange}
                className="px-4 py-3 border border-[#d1dce5] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#1e88e5] text-[#2c3e50] placeholder-[#8b9db0] bg-[#f8fafb]"
              />
            </div>

            <div className="flex justify-center pt-4">
              <button
                type="submit"
                className="bg-[#1565c0] hover:bg-[#0d47a1] text-white font-medium px-8 py-3 rounded-lg transition-colors duration-200 leading-tight"
              >
                Create<br />vendor account
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
