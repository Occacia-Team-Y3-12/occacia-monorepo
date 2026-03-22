const envFlag = (value: string | undefined, defaultValue = false) => {
  if (value == null) {
    return defaultValue;
  }

  return value === 'true';
};

export const featureFlags = {
  useAdminCustomersMock: envFlag(
    process.env.NEXT_PUBLIC_USE_ADMIN_CUSTOMERS_MOCK
  ),
  useCustomerAuthMock: envFlag(
    process.env.NEXT_PUBLIC_USE_CUSTOMER_AUTH_MOCK
  ),
  useVendorAuthMock: envFlag(process.env.NEXT_PUBLIC_USE_VENDOR_AUTH_MOCK),
  useCustomerPackagesMock: envFlag(
    process.env.NEXT_PUBLIC_USE_CUSTOMER_PACKAGES_MOCK
  ),
  useCustomerPlanningMockApi: envFlag(
    process.env.NEXT_PUBLIC_USE_CUSTOMER_PLANNING_MOCK_API,
    true
  ),
} as const;
