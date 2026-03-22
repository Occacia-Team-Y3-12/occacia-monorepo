import { featureFlags } from '@/config/featureFlags';
import { mockPackageService } from '@/mocks/customer/packageService';

import { apiPackageService } from './packageService.api';

export const packageService = featureFlags.useCustomerPackagesMock
  ? mockPackageService
  : apiPackageService;
