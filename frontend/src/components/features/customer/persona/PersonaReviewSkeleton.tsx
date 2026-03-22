'use client';

export function PersonaReviewSkeleton() {
  return (
    <div className="space-y-5 animate-pulse">
      <div className="rounded-[36px] border border-[#DCE4F2] bg-white p-6">
        <div className="h-4 w-28 rounded-full bg-[#E6EDF8]" />
        <div className="mt-4 h-12 w-72 rounded-2xl bg-[#E6EDF8]" />
        <div className="mt-3 h-4 w-full max-w-xl rounded-full bg-[#E6EDF8]" />
        <div className="mt-2 h-4 w-full max-w-lg rounded-full bg-[#E6EDF8]" />
      </div>

      <div className="rounded-[32px] border border-[#DCE4F2] bg-white p-6">
        <div className="h-6 w-48 rounded-full bg-[#E6EDF8]" />
        <div className="mt-5 grid gap-3 sm:grid-cols-2">
          {Array.from({ length: 4 }).map((_, index) => (
            <div key={index} className="h-24 rounded-[24px] bg-[#E6EDF8]" />
          ))}
        </div>
      </div>

      {Array.from({ length: 3 }).map((_, index) => (
        <div key={index} className="rounded-[32px] border border-[#DCE4F2] bg-white p-6">
          <div className="h-6 w-40 rounded-full bg-[#E6EDF8]" />
          <div className="mt-4 h-12 w-full rounded-2xl bg-[#E6EDF8]" />
          <div className="mt-4 flex flex-wrap gap-3">
            {Array.from({ length: 8 }).map((__, chipIndex) => (
              <div key={chipIndex} className="h-10 w-24 rounded-full bg-[#E6EDF8]" />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
