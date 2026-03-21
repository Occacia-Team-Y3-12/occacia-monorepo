import { featureFlags } from '@/config/featureFlags';

import { apiUserService } from './userService.api';
import { mockUserService } from './userService.mock';

export * from './userService.types';

export const userService = featureFlags.useAdminCustomersMock
  ? mockUserService
  : apiUserService;
