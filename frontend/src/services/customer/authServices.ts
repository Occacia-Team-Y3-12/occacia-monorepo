import { featureFlags } from '@/config/featureFlags';
import { mockCustomerAuthService } from '@/mocks/customer/authService';

import { apiCustomerAuthService } from './authService.api';

export const customerAuthService = featureFlags.useCustomerAuthMock
  ? mockCustomerAuthService
  : apiCustomerAuthService;
