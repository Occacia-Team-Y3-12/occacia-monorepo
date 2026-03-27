const envFlag = (value: string | undefined, defaultValue = false) => {
  if (value == null) {
    return defaultValue;
  }

  return value === 'true';
};

const enableFrontendMocks = envFlag(
  process.env.NEXT_PUBLIC_ENABLE_FRONTEND_MOCKS
);

export const featureFlags = {
  enableFrontendMocks,
  useAdminAuthMock: envFlag(
    process.env.NEXT_PUBLIC_USE_ADMIN_AUTH_MOCK,
    enableFrontendMocks
  ),
  useAdminCustomersMock: envFlag(
    process.env.NEXT_PUBLIC_USE_ADMIN_CUSTOMERS_MOCK,
    enableFrontendMocks
  ),
  useAdminDashboardMock: envFlag(
    process.env.NEXT_PUBLIC_USE_ADMIN_DASHBOARD_MOCK,
    enableFrontendMocks
  ),
  useAdminOperationsMock: envFlag(
    process.env.NEXT_PUBLIC_USE_ADMIN_OPERATIONS_MOCK,
    enableFrontendMocks
  ),
  useCustomerAuthMock: envFlag(
    process.env.NEXT_PUBLIC_USE_CUSTOMER_AUTH_MOCK,
    enableFrontendMocks
  ),
  useCustomerOrdersMock: envFlag(
    process.env.NEXT_PUBLIC_USE_CUSTOMER_ORDERS_MOCK,
    enableFrontendMocks
  ),
  useCustomerPersonaMock: envFlag(
    process.env.NEXT_PUBLIC_USE_CUSTOMER_PERSONA_MOCK,
    enableFrontendMocks
  ),
  useVendorAuthMock: envFlag(
    process.env.NEXT_PUBLIC_USE_VENDOR_AUTH_MOCK,
    enableFrontendMocks
  ),
  useVendorOfferingsMock: envFlag(
    process.env.NEXT_PUBLIC_USE_VENDOR_OFFERINGS_MOCK,
    enableFrontendMocks
  ),
  useVendorProductsMock: envFlag(
    process.env.NEXT_PUBLIC_USE_VENDOR_PRODUCTS_MOCK,
    enableFrontendMocks
  ),
  useVendorTasksMock: envFlag(
    process.env.NEXT_PUBLIC_USE_VENDOR_TASKS_MOCK,
    enableFrontendMocks
  ),
  useCustomerPackagesMock: envFlag(
    process.env.NEXT_PUBLIC_USE_CUSTOMER_PACKAGES_MOCK,
    enableFrontendMocks
  ),
  useCustomerPlanningMockApi: envFlag(
    process.env.NEXT_PUBLIC_USE_CUSTOMER_PLANNING_MOCK_API,
    enableFrontendMocks
  ),
} as const;
