'use client';

import { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ArrowRight, Package, SlidersHorizontal, Sparkles } from 'lucide-react';
import { ROUTES } from '@/lib/routes';
import { packageService } from '@/services/customer/packageService';

const getPreferredPackageId = async (eventId: string) => {
  const existingPackages = await packageService.getPackages(eventId);
  const packages =
    existingPackages.length > 0
      ? existingPackages
      : await packageService.generatePackages(eventId);

  const recommendedPackage =
    packages.find((pkg) => pkg.type === 'RECOMMENDED') ?? packages[0];

  if (!recommendedPackage) {
    throw new Error('No packages available for this event.');
  }

  return recommendedPackage.packageId;
};

export default function RecommendationsPage() {
  const params = useParams<{ eventId: string }>();
  const router = useRouter();
  const eventId = params?.eventId || '';

  const [isGeneratingRecommended, setIsGeneratingRecommended] = useState(false);
  const [isPreparingCustom, setIsPreparingCustom] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGenerateRecommended = async () => {
    if (!eventId) {
      return;
    }

    setIsGeneratingRecommended(true);
    setError(null);

    try {
      await packageService.generatePackages(eventId);
      router.push(ROUTES.CUSTOMER.EVENT_PACKAGES(eventId));
    } catch {
      setError('Unable to generate recommendation packages right now.');
      setIsGeneratingRecommended(false);
    }
  };

  const handleCreateCustomPackage = async () => {
    if (!eventId) {
      return;
    }

    setIsPreparingCustom(true);
    setError(null);

    try {
      const packageId = await getPreferredPackageId(eventId);
      router.push(ROUTES.CUSTOMER.EVENT_PACKAGE_CUSTOMIZE(eventId, packageId));
    } catch {
      setError('Unable to prepare a customizable package right now.');
      setIsPreparingCustom(false);
    }
  };

  return (
    <section className="mx-auto max-w-5xl px-4 py-10 sm:px-6">
      <div className="rounded-[28px] border border-[#DCE4F2] bg-[linear-gradient(135deg,#0D47A1_0%,#1562CC_52%,#4285F4_100%)] px-6 py-8 text-white shadow-[0_24px_70px_-34px_rgba(13,71,161,0.34)] sm:px-8 sm:py-10">
        <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-white/76">
          Package Recommendations
        </p>
        <h1 className="mt-2 text-3xl font-semibold tracking-[-0.04em] sm:text-4xl">
          Choose how you want to build your package
        </h1>
        <p className="mt-3 max-w-2xl text-sm leading-7 text-white/86 sm:text-base">
          Generate ready-made recommendation packages, or start from a curated base and customize each vendor choice yourself.
        </p>
      </div>

      {error ? (
        <div className="mt-5 rounded-2xl border border-[#F4CDCD] bg-[#FFF4F4] px-4 py-3 text-sm text-[#B23C3C]">
          {error}
        </div>
      ) : null}

      <div className="mt-8 grid gap-6 lg:grid-cols-2">
        <article className="rounded-[24px] border border-[#DCE4F2] bg-white p-6 shadow-[0_18px_48px_-32px_rgba(13,71,161,0.16)]">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[#EAF2FF] text-[#0D47A1]">
            <Sparkles className="h-6 w-6" />
          </div>
          <h2 className="mt-5 text-2xl font-semibold tracking-[-0.04em] text-[#0D47A1]">
            Generate Recommended Packages
          </h2>
          <p className="mt-3 text-sm leading-7 text-[#5B6780]">
            Let Occacia create curated package options such as budget, recommended, and high-quality bundles based on your confirmed tasks.
          </p>
          <div className="mt-6 rounded-2xl bg-[#F8FBFF] px-4 py-4 text-sm text-[#4A5976]">
            Includes:
            <div className="mt-2">Budget-friendly and premium package options</div>
            <div>Auto-matched vendors for each confirmed task</div>
            <div>Fastest path to package confirmation</div>
          </div>
          <button
            type="button"
            onClick={() => void handleGenerateRecommended()}
            disabled={isGeneratingRecommended || isPreparingCustom}
            className="mt-6 inline-flex w-full items-center justify-center gap-2 rounded-2xl bg-[#0D47A1] px-5 py-3 text-sm font-semibold text-white transition hover:bg-[#4285F4] disabled:opacity-60"
          >
            <Package className="h-4 w-4" />
            {isGeneratingRecommended ? 'Generating Packages...' : 'Generate Packages'}
          </button>
        </article>

        <article className="rounded-[24px] border border-[#DCE4F2] bg-white p-6 shadow-[0_18px_48px_-32px_rgba(13,71,161,0.16)]">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[#F3F6FB] text-[#0D47A1]">
            <SlidersHorizontal className="h-6 w-6" />
          </div>
          <h2 className="mt-5 text-2xl font-semibold tracking-[-0.04em] text-[#0D47A1]">
            Create Customized Package
          </h2>
          <p className="mt-3 text-sm leading-7 text-[#5B6780]">
            Start from the recommended package and replace vendors task-by-task to shape a more personalized combination before confirming.
          </p>
          <div className="mt-6 rounded-2xl bg-[#F8FBFF] px-4 py-4 text-sm text-[#4A5976]">
            Includes:
            <div className="mt-2">Alternative vendor shortlist for each task</div>
            <div>Manual swaps before final confirmation</div>
            <div>More control over the final package mix</div>
          </div>
          <button
            type="button"
            onClick={() => void handleCreateCustomPackage()}
            disabled={isGeneratingRecommended || isPreparingCustom}
            className="mt-6 inline-flex w-full items-center justify-center gap-2 rounded-2xl border border-[#0D47A1] bg-white px-5 py-3 text-sm font-semibold text-[#0D47A1] transition hover:bg-[#F4F8FA] disabled:opacity-60"
          >
            <ArrowRight className="h-4 w-4" />
            {isPreparingCustom ? 'Preparing Custom Package...' : 'Create Custom Package'}
          </button>
        </article>
      </div>
    </section>
  );
}
