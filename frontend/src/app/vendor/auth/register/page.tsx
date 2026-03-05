'use client';

import { useState, useEffect } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { ROUTES } from '@/lib/routes';
import {
  VendorFormData,
  validateVendorField,
  isVendorAccountValid,
  isVendorFinalValid
} from '@/lib/validation';

export default function VendorRegister() {
  const router = useRouter();
  const [step, setStep] = useState<'account' | 'organization'>('account');
  const [orgChoice, setOrgChoice] = useState<'join' | 'create' | ''>('');

  const [formData, setFormData] = useState<VendorFormData>({
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

  const [errors, setErrors] = useState<Partial<Record<keyof VendorFormData, string>>>({});
  const [isAccountValid, setIsAccountValid] = useState(false);
  const [isFinalValid, setIsFinalValid] = useState(false);

  // validation helpers
  const validateField = (
    name: keyof VendorFormData,
    value: string,
    data: VendorFormData = formData
  ): string => {
    const error = validateVendorField(name, value, data, orgChoice);
    setErrors((prev) => ({ ...prev, [name]: error }));
    return error;
  };

  const isAccountStepValid = (data: VendorFormData) => isVendorAccountValid(data);
  const isFinalStepValid = (data: VendorFormData, org: typeof orgChoice) =>
    isVendorFinalValid(data, org);

  // organization-related validation should fire when choice changes
  useEffect(() => {
    if (orgChoice === 'join') {
      validateField('organizationCode', formData.organizationCode);
    } else if (orgChoice === 'create') {
      (['businessName', 'businessRegNumber', 'businessAddress', 'businessPhone', 'businessEmail'] as Array<keyof VendorFormData>).forEach(
        (f) => validateField(f, formData[f])
      );
    }
  }, [orgChoice]);

  // update validity when account step changes
  useEffect(() => {
    setIsAccountValid(isAccountStepValid(formData));
  }, [
    formData.username,
    formData.fullName,
    formData.email,
    formData.password,
    formData.confirmPassword,
    formData.address,
    formData.nicNumber,
    formData.gender
  ]);

  // update validity when organization step changes
  useEffect(() => {
    setIsFinalValid(isFinalStepValid(formData, orgChoice));
  }, [
    formData.organizationCode,
    formData.businessName,
    formData.businessRegNumber,
    formData.businessAddress,
    formData.businessPhone,
    formData.businessEmail,
    orgChoice
  ]);

  const handleAccountSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (isAccountStepValid(formData)) {
      setStep('organization');
    } else {
      // trigger errors for all account fields
      (['username', 'fullName', 'email', 'password', 'confirmPassword', 'address', 'nicNumber', 'gender'] as Array<keyof VendorFormData>).forEach((field) =>
        validateField(field, formData[field])
      );
    }
  };

  const handleFinalSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isFinalStepValid(formData, orgChoice)) {
      // show errors for relevant fields
      if (orgChoice === 'join') {
        validateField('organizationCode', formData.organizationCode);
      } else if (orgChoice === 'create') {
        (['businessName', 'businessRegNumber', 'businessAddress', 'businessPhone', 'businessEmail'] as Array<keyof VendorFormData>).forEach((field) =>
          validateField(field, formData[field])
        );
      }
      return;
    }

    // Call mock API endpoint (ready for production API swap)
    try {
      const response = await fetch('/api/v1/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...formData,
          organizationType: orgChoice
        })
      });

      const data = await response.json();

      if (response.ok && data.status === 'pending_verification') {
        // Generate mock token based on response
        const mockToken = data.data?.token || `mock_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        router.push(`${ROUTES.VENDOR.VERIFY_EMAIL}?token=${mockToken}`);
      } else {
        console.error('Registration error:', data.message);
      }
    } catch (error) {
      console.error('Registration failed:', error);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => {
      const updated = { ...prev, [name]: value } as VendorFormData;
      validateField(name as keyof VendorFormData, value, updated);
      return updated;
    });
  };

  return (
    <div className="min-h-screen flex items-center justify-center relative overflow-hidden p-4">
      <Image src="/images/background.png" alt="Background" fill className="object-cover" priority />

      <div className="flex flex-col md:flex-row bg-white rounded-3xl shadow-2xl overflow-hidden max-w-5xl w-full relative z-10">
        <div className="w-full md:w-2/5 bg-gradient-to-br from-[#f5f7f9] to-white p-6 md:p-12 flex flex-col items-center justify-center">
          <div className="mb-4 md:mb-8">
            <Image src="/icons/logo.svg" alt="Occacia Logo" width={120} height={120} priority className="md:w-[180px] md:h-[180px]" />
          </div>
          <h1 className="text-2xl md:text-4xl font-bold text-[#2c3e50] mb-2">OCCACIA</h1>
          <p className="text-base md:text-xl text-[#5a6c7d] font-medium">VENDOR PORTAL</p>
        </div>

        <div className="w-full md:w-3/5 p-6 md:p-12">
          <h2 className="text-2xl md:text-3xl font-semibold text-[#5a6c7d] mb-6 md:mb-8 text-center">SIGN UP</h2>

          {step === 'account' ? (
            <form onSubmit={handleAccountSubmit} className="space-y-4">
              <div>
                <input
                  type="text"
                  name="username"
                  placeholder="User Name"
                  value={formData.username}
                  onChange={handleChange}
                  className={`w-full px-4 py-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#1e88e5] text-[#2c3e50] placeholder-[#8b9db0] bg-[#f8fafb] border ${
                    errors.username ? 'border-red-500' : 'border-[#d1dce5]'
                  }`}
                />
                {errors.username && <p className="text-red-600 text-sm mt-1">{errors.username}</p>}
              </div>

              <div>
                <input
                  type="text"
                  name="fullName"
                  placeholder="Full Name"
                  value={formData.fullName}
                  onChange={handleChange}
                  className={`w-full px-4 py-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#1e88e5] text-[#2c3e50] placeholder-[#8b9db0] bg-[#f8fafb] border ${
                    errors.fullName ? 'border-red-500' : 'border-[#d1dce5]'
                  }`}
                />
                {errors.fullName && <p className="text-red-600 text-sm mt-1">{errors.fullName}</p>}
              </div>

              <div>
                <input
                  type="email"
                  name="email"
                  placeholder="Email Address"
                  value={formData.email}
                  onChange={handleChange}
                  className={`w-full px-4 py-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#1e88e5] text-[#2c3e50] placeholder-[#8b9db0] bg-[#f8fafb] border ${
                    errors.email ? 'border-red-500' : 'border-[#d1dce5]'
                  }`}
                />
                {errors.email && <p className="text-red-600 text-sm mt-1">{errors.email}</p>}
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <input
                    type="password"
                    name="password"
                    placeholder="Password"
                    value={formData.password}
                    onChange={handleChange}
                    className={`w-full px-4 py-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#1e88e5] text-[#2c3e50] placeholder-[#8b9db0] bg-[#f8fafb] border ${
                      errors.password ? 'border-red-500' : 'border-[#d1dce5]'
                    }`}
                  />
                  {errors.password && <p className="text-red-600 text-sm mt-1">{errors.password}</p>}
                </div>
                <div>
                  <input
                    type="password"
                    name="confirmPassword"
                    placeholder="Confirm password"
                    value={formData.confirmPassword}
                    onChange={handleChange}
                    className={`w-full px-4 py-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#1e88e5] text-[#2c3e50] placeholder-[#8b9db0] bg-[#f8fafb] border ${
                      errors.confirmPassword ? 'border-red-500' : 'border-[#d1dce5]'
                    }`}
                  />
                  {errors.confirmPassword && <p className="text-red-600 text-sm mt-1">{errors.confirmPassword}</p>}
                </div>
              </div>

              <div>
                <input
                  type="text"
                  name="address"
                  placeholder="Address"
                  value={formData.address}
                  onChange={handleChange}
                  className={`w-full px-4 py-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#1e88e5] text-[#2c3e50] placeholder-[#8b9db0] bg-[#f8fafb] border ${
                    errors.address ? 'border-red-500' : 'border-[#d1dce5]'
                  }`}
                />
                {errors.address && <p className="text-red-600 text-sm mt-1">{errors.address}</p>}
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <input
                    type="text"
                    name="nicNumber"
                    placeholder="NIC Number"
                    value={formData.nicNumber}
                    onChange={handleChange}
                    className={`w-full px-4 py-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#1e88e5] text-[#2c3e50] placeholder-[#8b9db0] bg-[#f8fafb] border ${
                      errors.nicNumber ? 'border-red-500' : 'border-[#d1dce5]'
                    }`}
                  />
                  {errors.nicNumber && <p className="text-red-600 text-sm mt-1">{errors.nicNumber}</p>}
                </div>
                <div>
                  <select
                    name="gender"
                    value={formData.gender}
                    onChange={handleChange}
                    className={`w-full px-4 py-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#1e88e5] text-[#2c3e50] bg-[#f8fafb] border ${
                      errors.gender ? 'border-red-500' : 'border-[#d1dce5]'
                    }`}
                  >
                    <option value="">Select Gender</option>
                    <option value="male">Male</option>
                    <option value="female">Female</option>
                    <option value="other">Other</option>
                  </select>
                  {errors.gender && <p className="text-red-600 text-sm mt-1">{errors.gender}</p>}
                </div>
              </div>

              <div className="flex justify-center pt-4">
                <button
                  type="submit"
                  disabled={!isAccountValid}
                  className="bg-[#1565c0] hover:bg-[#0d47a1] text-white font-medium px-8 py-3 rounded-lg transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
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
                <div>
                  <input
                    type="text"
                    name="organizationCode"
                    placeholder="Organization Code"
                    value={formData.organizationCode}
                    onChange={handleChange}
                    className={`w-full px-4 py-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#1e88e5] text-[#2c3e50] placeholder-[#8b9db0] bg-[#f8fafb] border ${
                      errors.organizationCode ? 'border-red-500' : 'border-[#d1dce5]'
                    }`}
                  />
                  {errors.organizationCode && (
                    <p className="text-red-600 text-sm mt-1">{errors.organizationCode}</p>
                  )}
                </div>
              )}

              {orgChoice === 'create' && (
                <>
                  <div>
                    <input
                      type="text"
                      name="businessName"
                      placeholder="Business Name"
                      value={formData.businessName}
                      onChange={handleChange}
                      className={`w-full px-4 py-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#1e88e5] text-[#2c3e50] placeholder-[#8b9db0] bg-[#f8fafb] border ${
                        errors.businessName ? 'border-red-500' : 'border-[#d1dce5]'
                      }`}
                    />
                    {errors.businessName && <p className="text-red-600 text-sm mt-1">{errors.businessName}</p>}
                  </div>

                  <div>
                    <input
                      type="text"
                      name="businessRegNumber"
                      placeholder="Business Registration Number"
                      value={formData.businessRegNumber}
                      onChange={handleChange}
                      className={`w-full px-4 py-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#1e88e5] text-[#2c3e50] placeholder-[#8b9db0] bg-[#f8fafb] border ${
                        errors.businessRegNumber ? 'border-red-500' : 'border-[#d1dce5]'
                      }`}
                    />
                    {errors.businessRegNumber && (
                      <p className="text-red-600 text-sm mt-1">{errors.businessRegNumber}</p>
                    )}
                  </div>

                  <div>
                    <input
                      type="text"
                      name="businessAddress"
                      placeholder="Business Address"
                      value={formData.businessAddress}
                      onChange={handleChange}
                      className={`w-full px-4 py-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#1e88e5] text-[#2c3e50] placeholder-[#8b9db0] bg-[#f8fafb] border ${
                        errors.businessAddress ? 'border-red-500' : 'border-[#d1dce5]'
                      }`}
                    />
                    {errors.businessAddress && (
                      <p className="text-red-600 text-sm mt-1">{errors.businessAddress}</p>
                    )}
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <input
                        type="tel"
                        name="businessPhone"
                        placeholder="Business Phone"
                        value={formData.businessPhone}
                        onChange={handleChange}
                        className={`w-full px-4 py-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#1e88e5] text-[#2c3e50] placeholder-[#8b9db0] bg-[#f8fafb] border ${
                          errors.businessPhone ? 'border-red-500' : 'border-[#d1dce5]'
                        }`}
                      />
                      {errors.businessPhone && (
                        <p className="text-red-600 text-sm mt-1">{errors.businessPhone}</p>
                      )}
                    </div>

                    <div>
                      <input
                        type="email"
                        name="businessEmail"
                        placeholder="Business Email"
                        value={formData.businessEmail}
                        onChange={handleChange}
                        className={`w-full px-4 py-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#1e88e5] text-[#2c3e50] placeholder-[#8b9db0] bg-[#f8fafb] border ${
                          errors.businessEmail ? 'border-red-500' : 'border-[#d1dce5]'
                        }`}
                      />
                      {errors.businessEmail && (
                        <p className="text-red-600 text-sm mt-1">{errors.businessEmail}</p>
                      )}
                    </div>
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
                  disabled={!isFinalValid}
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
