export const ROUTES = {
  HOME: '/',
  VENDOR: {
    LOGIN: '/vendor/login',
    REGISTER: '/vendor/register',
    VERIFY_EMAIL: '/vendor/verify-email',
    DASHBOARD: '/vendor/dashboard',
    PENDING_APPROVAL: '/vendor/pending-approval',
    ACTIVATED: '/vendor/activated',
    PRODUCTS: '/vendor/products',
    ORDERS: '/vendor/orders',
  },
  VENDORS: {
    DASHBOARD: '/vendors/dashboard',
    PENDING_APPROVAL: '/vendors/pending-approval',
  },
  ADMIN: {
    DASHBOARD: '/admin',
    APPROVALS: '/admin/approvals',
  },
} as const;

export const ROUTES_ALIAS = {
  VENDOR_DASHBOARD: ROUTES.VENDOR.DASHBOARD,
  VENDOR_PENDING_APPROVAL: ROUTES.VENDOR.PENDING_APPROVAL,
  VENDOR_ACTIVATED: ROUTES.VENDOR.ACTIVATED,
  VENDOR_PRODUCTS: ROUTES.VENDOR.PRODUCTS,
} as const;

