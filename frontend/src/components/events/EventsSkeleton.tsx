export function EventsSkeleton() {
  return (
    <div className="grid gap-5 sm:gap-6 md:grid-cols-2 2xl:grid-cols-3">
      {Array.from({ length: 6 }).map((_, index) => (
        <div
          key={`events-skeleton-${index}`}
          className="overflow-hidden rounded-[24px] border border-[#EAEAEA] bg-white shadow-[0_24px_70px_-34px_rgba(13,71,161,0.16)]"
        >
          <div className="h-52 animate-pulse bg-gradient-to-br from-[#F4F8FA] via-[#EAEAEA] to-[#C9C9C9]/60 sm:h-56 lg:h-60" />
          <div className="space-y-4 p-5 sm:p-6">
            <div className="h-4 w-24 animate-pulse rounded-full bg-[#C9C9C9]" />
            <div className="h-8 w-3/4 animate-pulse rounded-full bg-[#CCCCCC]" />
            <div className="space-y-2">
              <div className="h-3 w-full animate-pulse rounded-full bg-[#EAEAEA]" />
              <div className="h-3 w-5/6 animate-pulse rounded-full bg-[#EAEAEA]" />
              <div className="h-3 w-4/6 animate-pulse rounded-full bg-[#EAEAEA]" />
            </div>
            <div className="h-11 w-full animate-pulse rounded-full bg-[#4285F4]/20" />
          </div>
        </div>
      ))}
    </div>
  );
}
