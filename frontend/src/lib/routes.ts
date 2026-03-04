export const ROUTES = {
  HOME: '/',
  CUSTOMER: {
    DASHBOARD: '/customer/dashboard',
    REGISTER: '/customer/register',
    PRODUCTS: '/customer/products',
    CART: '/customer/cart',
    ORDERS: '/customer/orders',
  },
  VENDOR: {
    LOGIN: '/vendor/auth/login',
    REGISTER: '/vendor/auth/register',
    VERIFY_EMAIL: '/vendor/auth/verify-email',
    DASHBOARD: '/vendor/dashboard',
    PENDING_APPROVAL: '/vendor/auth/pending-approval',
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
    USERS: '/admin/users',
    SETTINGS: '/admin/settings',
  },
} as const;

export const ROUTES_ALIAS = {
  VENDOR_DASHBOARD: ROUTES.VENDOR.DASHBOARD,
  VENDOR_PENDING_APPROVAL: ROUTES.VENDOR.PENDING_APPROVAL,
  VENDOR_ACTIVATED: ROUTES.VENDOR.ACTIVATED,
  VENDOR_PRODUCTS: ROUTES.VENDOR.PRODUCTS,
} as const;

