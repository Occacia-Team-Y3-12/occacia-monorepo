import { featureFlags } from '@/config/featureFlags';

import { apiPackageService } from './packageService.api';
import { mockPackageService } from './packageService.mock';

export const packageService = featureFlags.useCustomerPackagesMock
  ? mockPackageService
  : apiPackageService;
