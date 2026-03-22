import { featureFlags } from '@/config/featureFlags';
import { mockVendorAuthService } from '@/mocks/vendor/authService';

import { apiVendorAuthService } from './authService.api';

export const vendorAuthService = featureFlags.useVendorAuthMock
  ? mockVendorAuthService
  : apiVendorAuthService;
