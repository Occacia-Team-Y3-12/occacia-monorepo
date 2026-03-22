import { featureFlags } from '@/config/featureFlags';
import { mockUserService } from '@/mocks/admin/userService';

import { apiUserService } from './userService.api';

export * from './userService.types';

export const userService = featureFlags.useAdminCustomersMock
  ? mockUserService
  : apiUserService;
