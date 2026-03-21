export const featureFlags = {
  useAdminCustomersMock:
    process.env.NEXT_PUBLIC_USE_ADMIN_CUSTOMERS_MOCK === 'true',
} as const;
