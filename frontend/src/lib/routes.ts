export const ROUTES = {
  HOME: '/',
  VENDOR: {
    LOGIN: '/vendor/login',
    REGISTER: '/vendor/register',
    VERIFY_EMAIL: '/vendor/verify-email',
    DASHBOARD: '/vendor/dashboard',
  },
  VENDORS: {
    DASHBOARD: '/vendors/dashboard',
    PENDING_APPROVAL: '/vendors/pending-approval',
  },
} as const;

