import { featureFlags } from '@/config/featureFlags';

import { apiCustomerAuthService } from './authService.api';
import { mockCustomerAuthService } from './authService.mock';

export const customerAuthService = featureFlags.useCustomerAuthMock
  ? mockCustomerAuthService
  : apiCustomerAuthService;
