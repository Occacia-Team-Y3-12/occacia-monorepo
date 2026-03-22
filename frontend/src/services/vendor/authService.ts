import { featureFlags } from '@/config/featureFlags';

import { apiVendorAuthService } from './authService.api';
import { mockVendorAuthService } from './authService.mock';

export const vendorAuthService = featureFlags.useVendorAuthMock
  ? mockVendorAuthService
  : apiVendorAuthService;
