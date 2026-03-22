import {
  MOCK_EVENT,
  MOCK_PACKAGE,
  MOCK_SHORTLIST,
  createMockPackages,
} from '@/mocks/customerExperience';
import type { CustomerPackageService } from '@/services/customer/packageService.types';
import type {
  ConfirmPackageOrderResponse,
  FulfillmentRequest,
  OrderTask,
  PackageOrder,
} from '@/types/customer/order';
import type {
  PackageItem,
  RecommendationPackage,
  ShortlistedOffering,
} from '@/types/customer/package';

const sleep = (ms: number) =>
  new Promise((resolve) => setTimeout(resolve, ms));

const getPackageStorageKey = (eventId: string) => `packages_${eventId}`;

const getRandomId = (prefix: string) => {
  const randomPart =
    typeof globalThis.crypto !== 'undefined' &&
    typeof globalThis.crypto.randomUUID === 'function'
      ? globalThis.crypto.randomUUID().slice(0, 8)
      : `${Date.now()}`;

  return `${prefix}-${randomPart}`;
};

const getMockEventDate = () =>
  new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString();

const clonePackages = (packages: RecommendationPackage[]) =>
  packages.map((pkg) => ({
    ...pkg,
    items: pkg.items.map((item) => ({ ...item })),
  }));

const loadStoredPackages = (eventId: string): RecommendationPackage[] => {
  if (typeof window === 'undefined') {
    return [];
  }

  const stored = sessionStorage.getItem(getPackageStorageKey(eventId));

  if (!stored) {
    return [];
  }

  try {
    return JSON.parse(stored) as RecommendationPackage[];
  } catch {
    sessionStorage.removeItem(getPackageStorageKey(eventId));
    return [];
  }
};

const persistPackages = (
  eventId: string,
  packages: RecommendationPackage[]
) => {
  if (typeof window === 'undefined') {
    return;
  }

  sessionStorage.setItem(
    getPackageStorageKey(eventId),
    JSON.stringify(packages)
  );
};

const createMockPackageCatalog = (): RecommendationPackage[] =>
  createMockPackages().map((pkg) => ({
    ...pkg,
    name:
      pkg.name ??
      `${pkg.type.charAt(0)}${pkg.type
        .slice(1)
        .toLowerCase()
        .replace('_', ' ')} Package`,
    eventName: MOCK_EVENT.eventTitle,
    eventDate: getMockEventDate(),
    eventLocation: 'Colombo, Sri Lanka',
  }));

const getPackageOrThrow = (eventId: string, packageId: string) => {
  const pkg =
    loadStoredPackages(eventId).find((item) => item.packageId === packageId) ??
    null;

  if (!pkg) {
    throw new Error(`Mock package not found: ${packageId}`);
  }

  return pkg;
};

const buildShortlistForItem = (
  item: PackageItem
): ShortlistedOffering[] => [
  {
    offeringId: item.offeringId,
    offeringTitle: item.offeringTitle,
    vendorName: item.vendorName,
    taskPrice: item.taskPrice,
    rating: item.rating ?? 4.8,
    isBestMatch: true,
  },
  ...MOCK_SHORTLIST.map((offering, index) => ({
    ...offering,
    offeringId: `${item.taskId}-${offering.offeringId}`,
    offeringTitle:
      index === 0
        ? `${item.offeringCategory} Premium Match`
        : offering.offeringTitle,
    isBestMatch: false,
  })),
];

const buildConfirmPackageResponse = (
  eventId: string,
  pkg: RecommendationPackage,
  idempotencyKey: string
): ConfirmPackageOrderResponse => {
  const now = new Date().toISOString();
  const packageOrderId = getRandomId('order');
  const respondBy = new Date(
    Date.now() + 48 * 60 * 60 * 1000
  ).toISOString();

  const packageOrder: PackageOrder = {
    packageOrderId,
    eventId,
    packageId: pkg.packageId,
    packageOrderTotalPrice: pkg.packageTotalPrice,
    currency: pkg.currency,
    status: 'CREATED',
    createdAt: now,
    statusUpdatedAt: now,
    idempotencyKey,
  };

  const tasks: OrderTask[] = pkg.items.map((item) => ({
    taskId: item.taskId,
    eventId,
    name: item.taskName,
    status: 'PENDING',
    selectedOfferingId: item.offeringId,
    createdAt: now,
    updatedAt: now,
  }));

  const fulfillmentRequests: FulfillmentRequest[] = pkg.items.map((item) => ({
    fulfillmentRequestId: getRandomId('fr'),
    packageOrderId,
    taskId: item.taskId,
    vendorId: `vendor-${item.offeringId}`,
    offeringId: item.offeringId,
    status: 'SENT',
    requestedAt: now,
    respondBy,
    attemptNo: 1,
  }));

  return {
    packageOrder,
    tasks,
    fulfillmentRequests,
    packageName:
      pkg.name ??
      `${pkg.type.charAt(0)}${pkg.type
        .slice(1)
        .toLowerCase()
        .replace('_', ' ')} Package`,
    eventName: pkg.eventName,
    eventDate: pkg.eventDate,
  };
};

export const mockPackageService: CustomerPackageService = {
  async getPackages(eventId) {
    await sleep(150);
    return clonePackages(loadStoredPackages(eventId));
  },

  async getPackageById(eventId, packageId) {
    await sleep(150);
    return { ...getPackageOrThrow(eventId, packageId) };
  },

  async generatePackages(eventId) {
    await sleep(1200);

    const packages = createMockPackageCatalog();
    persistPackages(eventId, packages);

    return clonePackages(packages);
  },

  async getTaskRecommendations(eventId, taskId) {
    await sleep(200);

    const item =
      loadStoredPackages(eventId)
        .flatMap((pkg) => pkg.items)
        .find((pkgItem) => pkgItem.taskId === taskId) ??
      MOCK_PACKAGE.items.find((pkgItem) => pkgItem.taskId === taskId) ??
      MOCK_PACKAGE.items[0];

    return buildShortlistForItem({ ...item, taskId });
  },

  async updatePackage(eventId, packageId, items) {
    await sleep(250);

    const packages = loadStoredPackages(eventId);
    const packageIndex = packages.findIndex((pkg) => pkg.packageId === packageId);

    if (packageIndex < 0) {
      throw new Error(`Mock package not found: ${packageId}`);
    }

    const currentPackage = packages[packageIndex];
    const updatedItems = items.reduce<PackageItem[]>(
      (nextItems, { taskId, offeringId }) => {
        const currentItem = currentPackage.items.find(
          (item) => item.taskId === taskId
        );

        if (!currentItem) {
          return nextItems;
        }

        const selectedOffering = buildShortlistForItem(currentItem).find(
          (offering) => offering.offeringId === offeringId
        );

        if (!selectedOffering) {
          return nextItems;
        }

        nextItems.push({
          ...currentItem,
          offeringId: selectedOffering.offeringId,
          offeringTitle: selectedOffering.offeringTitle,
          vendorName: selectedOffering.vendorName,
          taskPrice: selectedOffering.taskPrice,
          rating: selectedOffering.rating,
        });

        return nextItems;
      },
      []
    );

    const updatedPackage: RecommendationPackage = {
      ...currentPackage,
      items: updatedItems,
      packageTotalPrice: updatedItems.reduce(
        (total, item) => total + item.taskPrice,
        0
      ),
    };

    packages[packageIndex] = updatedPackage;
    persistPackages(eventId, packages);

    return { ...updatedPackage };
  },

  async confirmPackage(eventId, packageId, idempotencyKey) {
    await sleep(500);

    const pkg = getPackageOrThrow(eventId, packageId);
    return buildConfirmPackageResponse(eventId, pkg, idempotencyKey);
  },

  clearCachedPackages(eventId) {
    if (typeof window === 'undefined') {
      return;
    }

    sessionStorage.removeItem(getPackageStorageKey(eventId));
  },
};
